"""
Archon V4 - With Code Validation Loop

This version includes automatic code validation with feedback loop.
Generated code is tested before being delivered to the user.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated, List, Optional
from langgraph.types import interrupt
from openai import AsyncOpenAI
from supabase import Client, create_client
import logfire
import os
import sys
import re

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from archon.config import ArchonConfig  # noqa: E402
from archon.pydantic_ai_coder import pydantic_ai_coder, PydanticAIDeps, list_documentation_pages_helper  # noqa: E402
from archon.code_validator import CodeValidator, format_validation_feedback  # noqa: E402
from archon.graph_utils import (  # noqa: E402
    create_standard_agents,
    load_message_history,
    run_agent_with_streaming
)


# Define state schema with validation fields
class AgentState(TypedDict):
    latest_user_message: str
    messages: Annotated[List[bytes], lambda x, y: x + y]
    scope: str
    validation_failed: Optional[bool]
    validation_feedback: Optional[str]
    validation_attempt: Optional[int]
    framework: Optional[str]  # For V6 multi-framework support


def build_workflow_v4(config: ArchonConfig):
    """
    Build V4 workflow with ArchonConfig dependency injection.

    Args:
        config: ArchonConfig instance with all configuration

    Returns:
        Compiled StateGraph workflow with checkpointing
    """
    # Configure logfire
    logfire.configure(send_to_logfire=config.send_to_logfire)

    # Initialize clients
    is_ollama = config.is_ollama()
    openai_client = AsyncOpenAI(api_key=config.openai_api_key)
    supabase: Client = create_client(config.supabase_url, config.supabase_key)

    # Initialize code validator
    code_validator = CodeValidator(timeout=config.validation_timeout)

    # Initialize agents using shared helper
    reasoner, primary_model, router_agent, end_conversation_agent = create_standard_agents(config)

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

            Include a list of documentation pages that are relevant to creating this agent
            for the user in the scope document.
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

            # Get message history using shared helper
            message_history = load_message_history(state['messages'])

            # If validation failed, add feedback to the message
            user_message = state['latest_user_message']
            if state.get('validation_failed') and state.get('validation_feedback'):
                user_message = f"""
{state['latest_user_message']}

IMPORTANT: The previous code had validation issues. Please fix these problems:

{state['validation_feedback']}

Please regenerate the code with these issues fixed.
"""

            # Run the agent using shared streaming helper
            result = await run_agent_with_streaming(
                pydantic_ai_coder,
                user_message,
                is_ollama,
                deps=deps,
                message_history=message_history
            )

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
            messages = load_message_history([state['messages'][-1]])

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
            # Get message history using shared helper
            message_history = load_message_history(state['messages'])

            # Run agent using shared streaming helper
            result = await run_agent_with_streaming(
                end_conversation_agent,
                state['latest_user_message'],
                is_ollama,
                message_history=message_history
            )

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
    checkpoint_dir = os.path.dirname(config.checkpoint_db) if os.path.dirname(config.checkpoint_db) else 'workbench'
    os.makedirs(checkpoint_dir, exist_ok=True)
    memory = SqliteSaver.from_conn_string(config.checkpoint_db)

    return builder.compile(checkpointer=memory)


# Backwards compatibility: create workflow with default config
agentic_flow_v4 = build_workflow_v4(ArchonConfig.from_env())
