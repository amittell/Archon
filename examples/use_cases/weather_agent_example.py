"""
Use Case: Weather Forecasting Agent

This example shows how to use Archon to create a complete weather forecasting agent
with real API integration, error handling, and multiple features.
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from archon.archon_graph_v6 import agentic_flow
from langgraph.types import Command


async def main():
    """Create a production-ready weather agent"""

    config = {
        "configurable": {
            "thread_id": "weather_agent_example"
        }
    }

    print("=" * 80)
    print("USE CASE: WEATHER FORECASTING AGENT")
    print("=" * 80)
    print("\nThis example creates a production-ready weather agent with:")
    print("  • Current weather lookup")
    print("  • 7-day forecast")
    print("  • Temperature unit conversion")
    print("  • Weather alerts")
    print("  • Error handling and retries")
    print("  • Rate limiting")
    print("=" * 80)

    # Step 1: Define comprehensive requirements
    print("\n[Step 1] Defining agent requirements...\n")

    requirements = """
    Create a comprehensive weather forecasting agent using Pydantic AI with the following features:

    CORE FEATURES:
    1. Current Weather Lookup
       - Get current weather for any city
       - Return temperature, conditions, humidity, wind speed
       - Handle invalid city names gracefully

    2. Multi-Day Forecast
       - Provide 7-day forecast
       - Include high/low temperatures
       - Show precipitation probability
       - Display weather conditions per day

    3. Temperature Conversion
       - Convert between Celsius and Fahrenheit
       - Support both directions
       - Show formulas in responses

    4. Weather Alerts
       - Check for severe weather alerts
       - Categorize by severity (warning, watch, advisory)
       - Include alert details and timing

    TECHNICAL REQUIREMENTS:
    - Use OpenWeatherMap API (or similar)
    - Implement proper error handling
    - Add request rate limiting
    - Cache results for 10 minutes
    - Include comprehensive logging
    - Use environment variables for API keys

    CODE STRUCTURE:
    - agent.py: Main agent with tools
    - weather_api.py: API client wrapper
    - utils.py: Helper functions (conversion, caching)
    - .env.example: Configuration template
    - requirements.txt: Dependencies

    Make the code production-ready with:
    - Type hints throughout
    - Docstrings for all functions
    - Error handling with specific exceptions
    - Retry logic for API failures
    - Input validation
    """

    response_text = ""
    async for msg in agentic_flow.astream(
        {"latest_user_message": requirements},
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 1 Complete] Generated initial implementation ({len(response_text)} chars)")

    # Step 2: Add testing
    print("\n" + "=" * 80)
    print("[Step 2] Adding tests...\n")

    test_request = """
    Add comprehensive unit tests for the weather agent:
    - Test each tool independently
    - Test error cases (invalid city, API failures, rate limiting)
    - Test caching behavior
    - Test temperature conversion edge cases
    - Use pytest with async support
    - Include fixtures for mock API responses
    """

    response_text = ""
    async for msg in agentic_flow.astream(
        Command(resume=test_request),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 2 Complete] Added tests ({len(response_text)} chars)")

    # Step 3: Add CLI interface
    print("\n" + "=" * 80)
    print("[Step 3] Adding CLI interface...\n")

    cli_request = """
    Add a CLI interface (cli.py) that:
    - Uses argparse for command-line arguments
    - Supports commands: current, forecast, alerts, convert
    - Has a conversational mode for natural language queries
    - Shows results in a nice formatted table
    - Has --json flag for JSON output
    - Includes help text and examples
    """

    response_text = ""
    async for msg in agentic_flow.astream(
        Command(resume=cli_request),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 3 Complete] Added CLI ({len(response_text)} chars)")

    # Step 4: Finalize
    print("\n" + "=" * 80)
    print("[Step 4] Finalizing...\n")

    final_request = "Perfect! Add a README.md with setup instructions and usage examples."

    response_text = ""
    async for msg in agentic_flow.astream(
        Command(resume=final_request),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print("\n\n" + "=" * 80)
    print("WEATHER AGENT COMPLETE!")
    print("=" * 80)
    print("\nGenerated Files:")
    print("  ✓ agent.py - Main agent with tools")
    print("  ✓ weather_api.py - API client")
    print("  ✓ utils.py - Helper functions")
    print("  ✓ cli.py - Command-line interface")
    print("  ✓ test_weather_agent.py - Unit tests")
    print("  ✓ requirements.txt - Dependencies")
    print("  ✓ .env.example - Configuration template")
    print("  ✓ README.md - Documentation")
    print("\nNext Steps:")
    print("  1. Copy the generated code to a new directory")
    print("  2. Set up .env with your OpenWeatherMap API key")
    print("  3. Run: pip install -r requirements.txt")
    print("  4. Run tests: pytest test_weather_agent.py")
    print("  5. Try CLI: python cli.py current 'San Francisco'")
    print("  6. Try conversational: python cli.py --interactive")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("\nMake sure your environment is set up correctly.")
