"""
Archon V6 - Complete Implementation

Features:
- Multi-framework support (Pydantic AI, LangGraph, CrewAI, AutoGen)
- Code validation loop (V4)
- Persistent checkpointing (SQLite)
- Pydantic AI 1.11.1 compatibility
"""

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated, List, Optional
from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import Client, create_client
import logfire
import os
import sys
import re

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from archon.code_validator import CodeValidator, format_validation_feedback  # noqa: E402
from archon.framework_config import get_framework, detect_framework, FRAMEWORKS  # noqa: E402
from archon.multi_framework_coder import (  # noqa: E402
    get_coder_for_framework,
    list_documentation_pages_helper,
    MultiFrameworkDeps
)

# Load environment variables
load_dotenv()

# Configure logfire to suppress warnings
logfire.configure(send_to_logfire='never')

# Initialize clients
base_url = os.getenv('BASE_URL', 'https://api.openai.com/v1')
api_key = os.getenv('LLM_API_KEY', 'no-llm-api-key-provided')
is_ollama = "localhost" in base_url.lower()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Initialize code validator
code_validator = CodeValidator(timeout=5)

# Initialize agents
reasoner_llm_model = os.getenv('REASONER_MODEL', 'o3-mini')
reasoner = Agent(
    OpenAIModel(reasoner_llm_model, base_url=base_url, api_key=api_key),
    system_prompt="""You are an expert at coding AI agents across multiple frameworks:
- Pydantic AI
- LangGraph
- CrewAI
- AutoGen

Your job is to define comprehensive scope for AI agent projects.""",
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


# Define state schema
class AgentState(TypedDict):
    latest_user_message: str
    messages: Annotated[List[bytes], lambda x, y: x + y]
    scope: str
    framework: str
    validation_failed: Optional[bool]
    validation_feedback: Optional[str]
    validation_attempt: Optional[int]


# Scope Definition Node
async def define_scope_with_reasoner(state: AgentState):
    """Define scope and detect framework"""
    try:
        # Detect framework from user message
        framework = detect_framework(state['latest_user_message'])
        framework_info = get_framework(framework)

        print(f"Detected framework: {framework_info.display_name}")

        # Get documentation pages for the framework
        documentation_pages = await list_documentation_pages_helper(supabase, framework)

        if not documentation_pages:
            doc_note = f"\nNote: No documentation found for {framework_info.display_name}. You may need to run the crawler first."
            documentation_pages_str = doc_note
        else:
            documentation_pages_str = "\n".join(documentation_pages[:50])  # Limit to first 50

        # Create scope with reasoner
        prompt = f"""
        User AI Agent Request: {state['latest_user_message']}
        Target Framework: {framework_info.display_name}

        Create detailed scope document for the AI agent including:
        - Architecture diagram
        - Core components
        - External dependencies
        - Testing strategy
        - Framework-specific best practices

        Available documentation pages for {framework_info.display_name}:
        {documentation_pages_str}

        Include a list of relevant documentation pages in the scope.
        """

        result = await reasoner.run(prompt)
        scope = result.output

        # Save scope to file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        scope_path = os.path.join(parent_dir, "workbench", f"scope_{framework}.md")
        os.makedirs(os.path.join(parent_dir, "workbench"), exist_ok=True)

        with open(scope_path, "w", encoding="utf-8") as f:
            f.write(scope)

        return {
            "scope": scope,
            "framework": framework,
            "validation_attempt": 0
        }

    except Exception as e:
        print(f"Error in scope definition: {e}")
        return {
            "scope": f"Error defining scope: {str(e)}",
            "framework": "pydantic_ai",
            "validation_attempt": 0
        }


# Coding Node
async def coder_agent(state: AgentState, writer):
    """Generate code using framework-specific coder"""
    try:
        # Get framework-specific coder
        framework = state.get('framework', 'pydantic_ai')
        framework_coder = get_coder_for_framework(framework)

        # Prepare dependencies
        deps = MultiFrameworkDeps(
            supabase=supabase,
            openai_client=openai_client,
            reasoner_output=state['scope'],
            framework=framework
        )

        # Get message history
        from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
        message_history: list[ModelMessage] = []
        for message_row in state['messages']:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        # Add validation feedback if present
        user_message = state['latest_user_message']
        if state.get('validation_failed') and state.get('validation_feedback'):
            user_message = f"""
{state['latest_user_message']}

IMPORTANT: The previous code had validation issues. Please fix these problems:

{state['validation_feedback']}

Please regenerate the code with these issues fixed.
"""

        # Run the agent
        if is_ollama:
            writer = get_stream_writer()
            result = await framework_coder.run(user_message, deps=deps, message_history=message_history)
            writer(result.output)
        else:
            async with framework_coder.run_stream(
                user_message,
                deps=deps,
                message_history=message_history
            ) as result:
                async for chunk in result.stream_text(delta=True):
                    writer(chunk)

        return {"messages": [result.new_messages_json()], "validation_failed": False}

    except Exception as e:
        print(f"Error in coder agent: {e}")
        return {
            "messages": [],
            "validation_failed": True,
            "validation_feedback": f"Error generating code: {str(e)}"
        }


# Code Validation Node
async def validate_generated_code(state: AgentState):
    """Validate generated code"""
    try:
        if not state.get('messages'):
            return {"validation_failed": False}

        # Extract code from last message
        from pydantic_ai.messages import ModelMessagesTypeAdapter
        last_message_bytes = state['messages'][-1]
        messages = ModelMessagesTypeAdapter.validate_json(last_message_bytes)

        code_blocks = []
        for msg in messages:
            if hasattr(msg, 'content'):
                content = str(msg.content)
                # Extract code blocks
                python_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)
                code_blocks.extend(python_blocks)
                generic_blocks = re.findall(r'```\n(.*?)\n```', content, re.DOTALL)
                for block in generic_blocks:
                    if block not in python_blocks:
                        code_blocks.append(block)

        if not code_blocks:
            return {"validation_failed": False}

        # Validate each code block
        all_results = []
        for i, code in enumerate(code_blocks):
            is_valid, results = await code_validator.validate_all(
                code,
                skip_execution=True  # Skip execution for safety
            )
            all_results.append((f"Code Block {i+1}", is_valid, results))

        # Check if validation failed
        any_failed = any(not is_valid for _, is_valid, _ in all_results)
        attempt = state.get('validation_attempt', 0)
        max_attempts = 3

        if any_failed and attempt < max_attempts:
            feedback_parts = []
            for block_name, is_valid, results in all_results:
                if not is_valid:
                    feedback = format_validation_feedback(results)
                    feedback_parts.append(f"## {block_name}\n{feedback}")

            return {
                "validation_failed": True,
                "validation_feedback": "\n\n".join(feedback_parts),
                "validation_attempt": attempt + 1
            }

        return {
            "validation_failed": False,
            "validation_feedback": None,
            "validation_attempt": 0
        }

    except Exception as e:
        print(f"Error in validation: {e}")
        return {"validation_failed": False}


def route_after_validation(state: AgentState) -> str:
    """Route after validation"""
    if state.get('validation_failed'):
        return "coder_agent"
    else:
        return "get_next_user_message"


def get_next_user_message(state: AgentState):
    """Get next user message"""
    value = interrupt({})
    return {"latest_user_message": value}


async def route_user_message(state: AgentState):
    """Route based on user intent"""
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


async def finish_conversation(state: AgentState, writer):
    """End conversation"""
    try:
        from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
        message_history: list[ModelMessage] = []
        for message_row in state['messages']:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        if is_ollama:
            writer = get_stream_writer()
            result = await end_conversation_agent.run(state['latest_user_message'], message_history=message_history)
            writer(result.output)
        else:
            async with end_conversation_agent.run_stream(
                state['latest_user_message'],
                message_history=message_history
            ) as result:
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
builder.add_edge("coder_agent", "validate_code")
builder.add_conditional_edges(
    "validate_code",
    route_after_validation,
    {"coder_agent": "coder_agent", "get_next_user_message": "get_next_user_message"}
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
agentic_flow = builder.compile(checkpointer=memory)

# Export for backwards compatibility
agentic_flow_v6 = agentic_flow

print("\n" + "="*60)
print("Archon V6 Initialized")
print("="*60)
print(f"Supported Frameworks: {', '.join(FRAMEWORKS.keys())}")
print("Validation: Enabled")
print(f"Checkpointing: SQLite ({checkpoint_db})")
print("="*60 + "\n")
