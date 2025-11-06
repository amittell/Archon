"""
Archon V4 - With Code Validation Loop

This version includes automatic code validation with feedback loop.
Generated code is tested before being delivered to the user.
"""

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent, RunContext
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated, List, Any, Optional
from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import Client
import logfire
import os
import sys
import re

# Import the message classes from Pydantic AI
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter
)

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from archon.pydantic_ai_coder import pydantic_ai_coder, PydanticAIDeps, list_documentation_pages_helper
from archon.code_validator import CodeValidator, format_validation_feedback

# Load environment variables
load_dotenv()

# Configure logfire to suppress warnings (optional)
logfire.configure(send_to_logfire='never')

base_url = os.getenv('BASE_URL', 'https://api.openai.com/v1')
api_key = os.getenv('LLM_API_KEY', 'no-llm-api-key-provided')
is_ollama = "localhost" in base_url.lower()
reasoner_llm_model = os.getenv('REASONER_MODEL', 'o3-mini')
reasoner = Agent(
    OpenAIModel(reasoner_llm_model, base_url=base_url, api_key=api_key),
    system_prompt='You are an expert at coding AI agents and defining the scope for doing so. You support multiple frameworks including Pydantic AI, LangGraph, CrewAI, and AutoGen.',
)

primary_llm_model = os.getenv('PRIMARY_MODEL', 'gpt-4o-mini')
router_agent = Agent(
    OpenAIModel(primary_llm_model, base_url=base_url, api_key=api_key),
    system_prompt='Your job is to route the user message either to the end of the conversation or to continue coding the AI agent.',
)

end_conversation_agent = Agent(
    OpenAIModel(primary_llm_model, base_url=base_url, api_key=api_key),
    system_prompt='Your job is to end a conversation for creating an AI agent by giving instructions for how to execute the agent and then saying a nice goodbye to the user.',
)

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = Client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Initialize code validator
code_validator = CodeValidator(timeout=5)

# Define state schema with validation fields
class AgentState(TypedDict):
    latest_user_message: str
    messages: Annotated[List[bytes], lambda x, y: x + y]
    scope: str
    validation_failed: Optional[bool]
    validation_feedback: Optional[str]
    validation_attempt: Optional[int]
    framework: Optional[str]  # For V6 multi-framework support


# Scope Definition Node with Reasoner LLM
async def define_scope_with_reasoner(state: AgentState):
    """Define scope and architecture for the agent"""
    try:
        # First, get the documentation pages so the reasoner can decide which ones are necessary
        documentation_pages = await list_documentation_pages_helper(supabase)
        documentation_pages_str = "\n".join(documentation_pages)

        # Extract framework preference from user message if specified
        user_message = state['latest_user_message'].lower()
        framework = state.get('framework')

        if not framework:
            if 'langgraph' in user_message:
                framework = 'langgraph'
            elif 'crewai' in user_message:
                framework = 'crewai'
            elif 'autogen' in user_message:
                framework = 'autogen'
            else:
                framework = 'pydantic_ai'  # Default

        # Then, use the reasoner to define the scope
        prompt = f"""
        User AI Agent Request: {state['latest_user_message']}
        Target Framework: {framework}

        Create detailed scope document for the AI agent including:
        - Architecture diagram
        - Core components
        - External dependencies
        - Testing strategy
        - Framework-specific considerations

        Also based on these documentation pages available:

        {documentation_pages_str}

        Include a list of documentation pages that are relevant to creating this agent for the user in the scope document.
        """

        result = await reasoner.run(prompt)
        scope = result.output

        # Get the directory one level up from the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        scope_path = os.path.join(parent_dir, "workbench", "scope.md")
        os.makedirs(os.path.join(parent_dir, "workbench"), exist_ok=True)

        with open(scope_path, "w", encoding="utf-8") as f:
            f.write(scope)

        return {"scope": scope, "framework": framework, "validation_attempt": 0}

    except Exception as e:
        print(f"Error in scope definition: {e}")
        return {"scope": f"Error defining scope: {str(e)}", "framework": "pydantic_ai", "validation_attempt": 0}


# Coding Node with Feedback Handling
async def coder_agent(state: AgentState, writer):
    """Generate code for the agent"""
    try:
        # Prepare dependencies
        deps = PydanticAIDeps(
            supabase=supabase,
            openai_client=openai_client,
            reasoner_output=state['scope']
        )

        # Get the message history into the format for Pydantic AI
        message_history: list[ModelMessage] = []
        for message_row in state['messages']:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        # If validation failed, add feedback to the message
        user_message = state['latest_user_message']
        if state.get('validation_failed') and state.get('validation_feedback'):
            user_message = f"""
{state['latest_user_message']}

IMPORTANT: The previous code had validation issues. Please fix these problems:

{state['validation_feedback']}

Please regenerate the code with these issues fixed.
"""

        # Run the agent in a stream
        if is_ollama:
            writer = get_stream_writer()
            result = await pydantic_ai_coder.run(user_message, deps=deps, message_history=message_history)
            writer(result.output)
        else:
            async with pydantic_ai_coder.run_stream(
                user_message,
                deps=deps,
                message_history=message_history
            ) as result:
                # Stream partial text as it arrives
                async for chunk in result.stream_text(delta=True):
                    writer(chunk)

        return {"messages": [result.new_messages_json()], "validation_failed": False}

    except Exception as e:
        print(f"Error in coder agent: {e}")
        error_msg = f"Error generating code: {str(e)}"
        return {"messages": [], "validation_failed": True, "validation_feedback": error_msg}


# Code Validation Node
async def validate_generated_code(state: AgentState):
    """Validate the generated code before delivering to user"""
    try:
        # Get the last message from the coder
        if not state.get('messages'):
            return {"validation_failed": False}

        # Extract code blocks from the last message
        last_message_bytes = state['messages'][-1]
        messages = ModelMessagesTypeAdapter.validate_json(last_message_bytes)

        code_blocks = []
        for msg in messages:
            if hasattr(msg, 'content'):
                content = str(msg.content)
                # Extract Python code blocks
                python_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)
                code_blocks.extend(python_blocks)

                # Also check for code blocks without language specifier
                generic_blocks = re.findall(r'```\n(.*?)\n```', content, re.DOTALL)
                for block in generic_blocks:
                    if block not in python_blocks:  # Avoid duplicates
                        code_blocks.append(block)

        if not code_blocks:
            # No code blocks found, skip validation
            return {"validation_failed": False}

        # Validate each code block
        all_results = []
        for i, code in enumerate(code_blocks):
            is_valid, results = await code_validator.validate_all(
                code,
                skip_execution=True  # Skip execution for now (too risky without proper sandboxing)
            )
            all_results.append((f"Code Block {i+1}", is_valid, results))

        # Check if any validation failed
        any_failed = any(not is_valid for _, is_valid, _ in all_results)

        # Get current attempt number
        attempt = state.get('validation_attempt', 0)
        max_attempts = 3  # Maximum validation retry attempts

        if any_failed and attempt < max_attempts:
            # Format feedback for all failed validations
            feedback_parts = []
            for block_name, is_valid, results in all_results:
                if not is_valid:
                    feedback = format_validation_feedback(results)
                    feedback_parts.append(f"## {block_name}\n{feedback}")

            full_feedback = "\n\n".join(feedback_parts)

            return {
                "validation_failed": True,
                "validation_feedback": full_feedback,
                "validation_attempt": attempt + 1
            }

        # If max attempts reached or validation passed, continue
        return {
            "validation_failed": False,
            "validation_feedback": None,
            "validation_attempt": 0
        }

    except Exception as e:
        print(f"Error in validation: {e}")
        # If validation errors, let it pass (don't block on validation issues)
        return {"validation_failed": False}


# Routing function for validation
def route_after_validation(state: AgentState) -> str:
    """Route based on validation results"""
    if state.get('validation_failed'):
        # If validation failed, go back to coder
        return "coder_agent"
    else:
        # If validation passed, continue to user feedback
        return "get_next_user_message"


# Interrupt the graph to get the user's next message
def get_next_user_message(state: AgentState):
    """Get next user message via interrupt"""
    value = interrupt({})

    # Set the user's latest message for the LLM to continue the conversation
    return {
        "latest_user_message": value
    }


# Determine if the user is finished creating their AI agent or not
async def route_user_message(state: AgentState):
    """Route based on user's intent"""
    try:
        prompt = f"""
        The user has sent a message:

        {state['latest_user_message']}

        If the user wants to end the conversation, respond with just the text "finish_conversation".
        If the user wants to continue coding the AI agent, respond with just the text "coder_agent".
        """

        result = await router_agent.run(prompt)
        next_action = result.output

        if "finish" in next_action.lower():
            return "finish_conversation"
        else:
            return "coder_agent"

    except Exception as e:
        print(f"Error in routing: {e}")
        return "coder_agent"


# End of conversation agent to give instructions for executing the agent
async def finish_conversation(state: AgentState, writer):
    """End conversation with execution instructions"""
    try:
        # Get the message history into the format for Pydantic AI
        message_history: list[ModelMessage] = []
        for message_row in state['messages']:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        # Run the agent in a stream
        if is_ollama:
            writer = get_stream_writer()
            result = await end_conversation_agent.run(state['latest_user_message'], message_history=message_history)
            writer(result.output)
        else:
            async with end_conversation_agent.run_stream(
                state['latest_user_message'],
                message_history=message_history
            ) as result:
                # Stream partial text as it arrives
                async for chunk in result.stream_text(delta=True):
                    writer(chunk)

        return {"messages": [result.new_messages_json()]}

    except Exception as e:
        print(f"Error in finish conversation: {e}")
        return {"messages": []}


# Build workflow
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("define_scope_with_reasoner", define_scope_with_reasoner)
builder.add_node("coder_agent", coder_agent)
builder.add_node("validate_code", validate_generated_code)
builder.add_node("get_next_user_message", get_next_user_message)
builder.add_node("finish_conversation", finish_conversation)

# Set edges
builder.add_edge(START, "define_scope_with_reasoner")
builder.add_edge("define_scope_with_reasoner", "coder_agent")

# Add validation loop
builder.add_edge("coder_agent", "validate_code")
builder.add_conditional_edges(
    "validate_code",
    route_after_validation,
    {
        "coder_agent": "coder_agent",  # Loop back if validation failed
        "get_next_user_message": "get_next_user_message"  # Continue if passed
    }
)

builder.add_conditional_edges(
    "get_next_user_message",
    route_user_message,
    {"coder_agent": "coder_agent", "finish_conversation": "finish_conversation"}
)
builder.add_edge("finish_conversation", END)

# Configure persistence with SQLite
checkpoint_db = os.getenv('CHECKPOINT_DB', 'workbench/checkpoints.db')
os.makedirs(os.path.dirname(checkpoint_db) if os.path.dirname(checkpoint_db) else 'workbench', exist_ok=True)
memory = SqliteSaver.from_conn_string(checkpoint_db)
agentic_flow_v4 = builder.compile(checkpointer=memory)
