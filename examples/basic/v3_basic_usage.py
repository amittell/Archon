"""
Archon V3 - Basic Usage Example

This example demonstrates the simplest way to use Archon to create an AI agent.
Archon V3 uses Pydantic AI with RAG over documentation.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from archon.archon_graph import agentic_flow
from langgraph.types import Command


async def main():
    """Run a simple agent creation workflow"""

    # Configuration for the conversation thread
    config = {
        "configurable": {
            "thread_id": "example_basic_v3"
        }
    }

    print("=" * 80)
    print("ARCHON V3 - BASIC USAGE EXAMPLE")
    print("=" * 80)
    print("\nThis example will create a simple weather forecasting agent.\n")

    # Step 1: Initial request
    print("\n[Step 1] Sending initial request...")
    initial_message = """
    Create a weather forecasting agent that can:
    - Get current weather for a location
    - Provide a 3-day forecast
    - Handle errors gracefully

    Use simple, clean code with good error messages.
    """

    response_text = ""
    async for msg in agentic_flow.astream(
        {"latest_user_message": initial_message},
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 1 Complete] Received {len(response_text)} characters")

    # Step 2: Request refinement
    print("\n" + "=" * 80)
    print("[Step 2] Requesting refinement...")
    refinement_message = "Add a function to convert temperature between Celsius and Fahrenheit"

    response_text = ""
    async for msg in agentic_flow.astream(
        Command(resume=refinement_message),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 2 Complete] Received {len(response_text)} characters")

    # Step 3: Finalize
    print("\n" + "=" * 80)
    print("[Step 3] Finalizing...")
    final_message = "That looks perfect, thank you!"

    response_text = ""
    async for msg in agentic_flow.astream(
        Command(resume=final_message),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print("\n\n" + "=" * 80)
    print("EXAMPLE COMPLETE!")
    print("=" * 80)
    print("\nKey Features of V3:")
    print("  ✓ RAG over Pydantic AI documentation")
    print("  ✓ Streaming responses")
    print("  ✓ Multi-turn conversations")
    print("  ✓ Reasoner LLM for scope definition")
    print("  ✓ Automatic code generation")
    print("\nGenerated code is saved in: workbench/scope.md")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user.")
    except Exception as e:
        print(f"\n\nError running example: {e}")
        print("\nMake sure you have:")
        print("  1. Set up your .env file with API keys")
        print("  2. Run: pip install -r requirements.txt")
        print("  3. Set up Supabase database with documentation")
