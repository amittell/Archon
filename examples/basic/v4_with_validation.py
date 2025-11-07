"""
Archon V4 - Code Validation Example

This example demonstrates Archon V4's automatic code validation loop.
Generated code is validated before delivery, with automatic retry on failures.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from archon.archon_graph_v4 import agentic_flow_v4
from langgraph.types import Command


async def main():
    """Run an agent creation workflow with validation"""

    # Configuration for the conversation thread
    config = {
        "configurable": {
            "thread_id": "example_validation_v4"
        }
    }

    print("=" * 80)
    print("ARCHON V4 - CODE VALIDATION EXAMPLE")
    print("=" * 80)
    print("\nThis example demonstrates automatic code validation.")
    print("V4 validates generated code using 5 checks:")
    print("  1. Syntax validation (AST parsing)")
    print("  2. Import checking")
    print("  3. Security scanning (dangerous patterns)")
    print("  4. Agent structure validation")
    print("  5. Sandbox execution (optional)")
    print("\nIf validation fails, the agent automatically retries (max 3 attempts).\n")

    # Step 1: Request an agent that might have issues
    print("\n[Step 1] Creating an agent...")
    initial_message = """
    Create a simple calculator agent with Pydantic AI that can:
    - Add two numbers
    - Subtract two numbers
    - Multiply two numbers
    - Divide two numbers

    Make sure to include proper error handling for division by zero.
    Use the latest Pydantic AI API (1.11.1) with result.output instead of result.data.
    """

    print("\nSending request (validation will run automatically)...")
    response_text = ""
    async for msg in agentic_flow_v4.astream(
        {"latest_user_message": initial_message},
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 1 Complete] Generated and validated code ({len(response_text)} chars)")

    # Step 2: Check validation results
    print("\n" + "=" * 80)
    print("[Step 2] Validation Process")
    print("=" * 80)
    print("\nThe generated code was automatically validated:")
    print("  ✓ Syntax check - ensures valid Python")
    print("  ✓ Import check - verifies all imports are available")
    print("  ✓ Security scan - checks for dangerous patterns (eval, exec, etc.)")
    print("  ✓ Structure check - validates agent structure (Agent definition, system_prompt)")
    print("  ✓ All checks passed!")

    # Step 3: Request modification
    print("\n" + "=" * 80)
    print("[Step 3] Requesting modification...")
    modification_message = "Add a square root function and power function"

    response_text = ""
    async for msg in agentic_flow_v4.astream(
        Command(resume=modification_message),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 3 Complete] Modified code validated ({len(response_text)} chars)")

    # Step 4: Finalize
    print("\n" + "=" * 80)
    print("[Step 4] Finalizing...")
    final_message = "Perfect! That's exactly what I needed."

    response_text = ""
    async for msg in agentic_flow_v4.astream(
        Command(resume=final_message),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print("\n\n" + "=" * 80)
    print("EXAMPLE COMPLETE!")
    print("=" * 80)
    print("\nKey Features of V4:")
    print("  ✓ All V3 features (RAG, streaming, multi-turn)")
    print("  ✓ Automatic code validation (5 checks)")
    print("  ✓ Validation feedback loop (max 3 retries)")
    print("  ✓ SQLite checkpointing (persistent conversations)")
    print("  ✓ Detailed validation feedback")
    print("\nValidation prevents common issues:")
    print("  • Syntax errors")
    print("  • Missing imports")
    print("  • Security vulnerabilities")
    print("  • Malformed agent structures")
    print("\nCheckpoint saved to: workbench/checkpoints.db")
    print("=" * 80)


async def demonstrate_validation_failure():
    """
    Example showing how validation catches issues.

    This is a conceptual demonstration - in practice, the agent
    would automatically retry when validation fails.
    """
    from archon.code_validator import CodeValidator

    validator = CodeValidator()

    print("\n" + "=" * 80)
    print("BONUS: Validation Failure Example")
    print("=" * 80)

    # Example 1: Syntax error
    bad_code_syntax = """
    def broken_function(
        # Missing closing parenthesis
        print("This won't work")
    """

    print("\n[Test 1] Validating code with syntax error...")
    is_valid, results = await validator.validate_all(bad_code_syntax, skip_execution=True)
    print(f"Result: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    for check_name, result in results:
        status = "✓" if result.is_valid else "✗"
        print(f"  {status} {check_name}: {result.message}")

    # Example 2: Dangerous pattern
    bad_code_security = """
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o-mini', system_prompt='Test agent')

# This is dangerous!
user_input = input("Enter code: ")
eval(user_input)  # Security risk!
"""

    print("\n[Test 2] Validating code with security risk...")
    is_valid, results = await validator.validate_all(bad_code_security, skip_execution=True)
    print(f"Result: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    for check_name, result in results:
        status = "✓" if result.is_valid else "✗"
        print(f"  {status} {check_name}: {result.message}")
        if not result.is_valid and result.details.get('issues'):
            for issue in result.details['issues']:
                if isinstance(issue, dict):
                    print(f"    → Line {issue.get('line')}: {issue.get('warning')}")

    print("\n" + "=" * 80)
    print("When V4 detects these issues, it automatically:")
    print("  1. Formats detailed feedback")
    print("  2. Sends feedback to the coder agent")
    print("  3. Agent regenerates code with fixes")
    print("  4. Validates again (up to 3 attempts)")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())

        # Show validation examples
        print("\n\n")
        asyncio.run(demonstrate_validation_failure())

    except KeyboardInterrupt:
        print("\n\nExample interrupted by user.")
    except Exception as e:
        print(f"\n\nError running example: {e}")
        print("\nMake sure you have:")
        print("  1. Set up your .env file with API keys")
        print("  2. Run: pip install -r requirements.txt")
        print("  3. Set up Supabase database with documentation")
