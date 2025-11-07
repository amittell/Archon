"""
Archon V6 - Multi-Framework Example

This example demonstrates Archon V6's ability to generate agents for multiple frameworks:
- Pydantic AI
- LangGraph
- CrewAI
- AutoGen

V6 automatically detects the framework from your request and uses framework-specific
documentation and templates.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from archon.archon_graph_v6 import agentic_flow
from langgraph.types import Command


async def create_agent_with_framework(framework_name: str, description: str):
    """Create an agent using a specific framework"""

    config = {
        "configurable": {
            "thread_id": f"example_v6_{framework_name.lower()}"
        }
    }

    print("\n" + "=" * 80)
    print(f"Creating {framework_name} Agent")
    print("=" * 80)

    # Create request that mentions the framework
    initial_message = f"""
    Using {framework_name}, create {description}

    Please use {framework_name} best practices and include:
    - Clear code structure
    - Proper error handling
    - Good documentation
    """

    print(f"\n[Framework: {framework_name}]")
    print(f"Request: {description}")
    print("\nGenerating code...\n")

    response_text = ""
    async for msg in agentic_flow.astream(
        {"latest_user_message": initial_message},
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n✓ Generated {framework_name} agent ({len(response_text)} chars)")

    # Finalize
    final_message = "That's perfect, thank you!"
    async for msg in agentic_flow.astream(
        Command(resume=final_message),
        config,
        stream_mode="custom"
    ):
        pass  # Just consume the goodbye message

    return response_text


async def main():
    """Demonstrate multi-framework capabilities"""

    print("=" * 80)
    print("ARCHON V6 - MULTI-FRAMEWORK EXAMPLE")
    print("=" * 80)
    print("\nArchon V6 supports 4 AI agent frameworks:")
    print("  1. Pydantic AI - Simple, type-safe agents")
    print("  2. LangGraph - Complex multi-agent workflows")
    print("  3. CrewAI - Role-based agent collaboration")
    print("  4. AutoGen - Microsoft's multi-agent framework")
    print("\nFramework is auto-detected from your message!")
    print("=" * 80)

    # Example 1: Pydantic AI
    await create_agent_with_framework(
        "Pydantic AI",
        "a simple customer support agent that can answer FAQs"
    )

    # Example 2: LangGraph
    await create_agent_with_framework(
        "LangGraph",
        "a research workflow with multiple specialized agents"
    )

    # Example 3: CrewAI
    await create_agent_with_framework(
        "CrewAI",
        "a content creation crew with writer, editor, and reviewer roles"
    )

    # Example 4: AutoGen
    await create_agent_with_framework(
        "AutoGen",
        "a coding assistant with code execution capabilities"
    )

    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETE!")
    print("=" * 80)
    print("\nKey Features of V6:")
    print("  ✓ All V4 features (validation, checkpointing)")
    print("  ✓ Support for 4 frameworks")
    print("  ✓ Framework auto-detection")
    print("  ✓ Framework-specific RAG")
    print("  ✓ Framework-specific templates")
    print("  ✓ Framework-specific system prompts")
    print("\nFramework Detection Examples:")
    print("  'Use Pydantic AI...' → Pydantic AI coder")
    print("  'Build a LangGraph...' → LangGraph coder")
    print("  'Create a CrewAI...' → CrewAI coder")
    print("  'With AutoGen...' → AutoGen coder")
    print("  No framework mentioned → Pydantic AI (default)")
    print("\nGenerated scopes saved to: workbench/scope_*.md")
    print("=" * 80)


async def demonstrate_framework_features():
    """Show unique features of each framework"""

    print("\n" + "=" * 80)
    print("FRAMEWORK COMPARISON")
    print("=" * 80)

    frameworks = {
        "Pydantic AI": {
            "best_for": "Simple, type-safe agents with validation",
            "key_features": [
                "Built-in Pydantic validation",
                "Streaming support",
                "Simple tool definition with @agent.tool",
                "Multiple model support"
            ],
            "use_cases": [
                "Customer support bots",
                "Data extraction agents",
                "Simple Q&A systems"
            ]
        },
        "LangGraph": {
            "best_for": "Complex multi-agent workflows with state management",
            "key_features": [
                "StateGraph for complex flows",
                "Persistent checkpointing",
                "Conditional edges and routing",
                "Human-in-the-loop support"
            ],
            "use_cases": [
                "Research pipelines",
                "Multi-step reasoning",
                "Agentic workflows with validation"
            ]
        },
        "CrewAI": {
            "best_for": "Role-based agent collaboration",
            "key_features": [
                "Role-based agents with backstories",
                "Task delegation",
                "Sequential/parallel processes",
                "Built-in collaboration patterns"
            ],
            "use_cases": [
                "Content creation teams",
                "Research crews",
                "Multi-role simulations"
            ]
        },
        "AutoGen": {
            "best_for": "Conversational agents with code execution",
            "key_features": [
                "AssistantAgent + UserProxyAgent pattern",
                "Built-in code execution",
                "GroupChat for multi-agent conversations",
                "Human input modes"
            ],
            "use_cases": [
                "Coding assistants",
                "Data analysis agents",
                "Interactive problem solving"
            ]
        }
    }

    for framework, details in frameworks.items():
        print(f"\n{framework}")
        print("-" * 40)
        print(f"Best For: {details['best_for']}")
        print("\nKey Features:")
        for feature in details['key_features']:
            print(f"  • {feature}")
        print("\nUse Cases:")
        for use_case in details['use_cases']:
            print(f"  • {use_case}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        # Run main examples
        asyncio.run(main())

        # Show framework comparison
        asyncio.run(demonstrate_framework_features())

    except KeyboardInterrupt:
        print("\n\nExample interrupted by user.")
    except Exception as e:
        print(f"\n\nError running example: {e}")
        print("\nMake sure you have:")
        print("  1. Set up your .env file with API keys")
        print("  2. Run: pip install -r requirements.txt")
        print("  3. Set up Supabase with ALL framework documentation")
        print("     Run: python archon/crawl_multi_framework_docs.py --all")
