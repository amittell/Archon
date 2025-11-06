"""
Archon Agentic Tool - 100+ Iteration Test Harness

This script tests the Archon prompt loop by running multiple iterations
to evaluate performance, consistency, and behavior under stress.
"""

import asyncio
import time
import json
import statistics
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

# Try to import real dependencies, fall back to mock mode if not available
try:
    from archon.archon_graph import agentic_flow
    from supabase import Client, create_client
    from openai import AsyncOpenAI
    from dotenv import load_dotenv
    import os

    load_dotenv()
    MOCK_MODE = False

    # Initialize real clients if possible
    try:
        supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception as e:
        print(f"Warning: Could not initialize clients: {e}")
        print("Falling back to mock mode...")
        MOCK_MODE = True
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Running in MOCK MODE - simulating workflow without real API calls")
    MOCK_MODE = True


class PerformanceMetrics:
    """Track performance metrics across iterations"""

    def __init__(self):
        self.iteration_times: List[float] = []
        self.response_lengths: List[int] = []
        self.errors: List[Dict[str, Any]] = []
        self.start_time: float = 0
        self.end_time: float = 0

    def record_iteration(self, duration: float, response_length: int):
        self.iteration_times.append(duration)
        self.response_lengths.append(response_length)

    def record_error(self, iteration: int, error: str):
        self.errors.append({
            "iteration": iteration,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    def get_statistics(self) -> Dict[str, Any]:
        if not self.iteration_times:
            return {"error": "No iterations completed"}

        return {
            "total_iterations": len(self.iteration_times),
            "total_time": self.end_time - self.start_time,
            "avg_iteration_time": statistics.mean(self.iteration_times),
            "median_iteration_time": statistics.median(self.iteration_times),
            "min_iteration_time": min(self.iteration_times),
            "max_iteration_time": max(self.iteration_times),
            "stddev_iteration_time": statistics.stdev(self.iteration_times) if len(self.iteration_times) > 1 else 0,
            "avg_response_length": statistics.mean(self.response_lengths),
            "total_errors": len(self.errors),
            "error_rate": len(self.errors) / len(self.iteration_times) if self.iteration_times else 0,
            "errors": self.errors
        }


class MockArchonWorkflow:
    """Mock implementation for testing without real API calls"""

    def __init__(self):
        self.state = {"messages": [], "scope": "", "iteration": 0}

    async def simulate_iteration(self, message: str) -> str:
        """Simulate an iteration with realistic timing"""
        # Simulate network and processing delay
        await asyncio.sleep(0.1 + (0.05 * (self.state["iteration"] % 3)))

        self.state["iteration"] += 1

        # Simulate different response types
        if "error" in message.lower():
            raise Exception("Simulated error for testing")
        elif "finish" in message.lower() or "done" in message.lower():
            return "Great! Your agent is complete. Here's how to run it:\n\n1. Install dependencies\n2. Set up .env\n3. Run python agent.py\n\nGoodbye!"
        elif self.state["iteration"] == 1:
            return f"""# Agent Scope

Based on your request: {message}

## Architecture:
- Main agent with tool calling
- RAG system for knowledge retrieval
- Streaming response support

## Components:
- agent.py
- agent_tools.py
- agent_prompts.py
- requirements.txt
- .env.example

## Documentation needed:
- Agent basics
- Tool definitions
- Streaming

I'll now create the initial agent code. Let me know if you need changes!"""
        else:
            return f"""Iteration {self.state["iteration"]}: Updated the agent based on your feedback.

Here's the refined code for `agent.py`:

```python
from pydantic_ai import Agent

agent = Agent(
    'openai:gpt-4o-mini',
    system_prompt='You are a helpful assistant.',
)

# Tool definitions...
```

Does this look good, or do you need further changes?"""


async def run_real_workflow(num_iterations: int, test_prompts: List[str]) -> PerformanceMetrics:
    """Run the actual Archon workflow (requires environment setup)"""
    metrics = PerformanceMetrics()
    metrics.start_time = time.time()

    config = {
        "configurable": {
            "thread_id": f"test_{datetime.now().timestamp()}"
        }
    }

    print(f"Starting REAL workflow test with {num_iterations} iterations...")
    print("=" * 80)

    try:
        # Initial message
        initial_message = test_prompts[0]
        print(f"\n[Iteration 1] User: {initial_message[:100]}...")

        iteration_start = time.time()
        response = ""

        async for msg in agentic_flow.astream(
            {"latest_user_message": initial_message},
            config,
            stream_mode="custom"
        ):
            response += str(msg)

        duration = time.time() - iteration_start
        metrics.record_iteration(duration, len(response))

        print(f"[Iteration 1] Response length: {len(response)} chars, Time: {duration:.2f}s")
        print(f"[Iteration 1] Preview: {response[:200]}...")

        # Subsequent iterations
        for i in range(2, num_iterations + 1):
            try:
                # Use prompts cyclically
                user_message = test_prompts[i % len(test_prompts)]
                print(f"\n[Iteration {i}] User: {user_message[:100]}...")

                iteration_start = time.time()
                response = ""

                from langgraph.types import Command
                async for msg in agentic_flow.astream(
                    Command(resume=user_message),
                    config,
                    stream_mode="custom"
                ):
                    response += str(msg)

                duration = time.time() - iteration_start
                metrics.record_iteration(duration, len(response))

                print(f"[Iteration {i}] Response length: {len(response)} chars, Time: {duration:.2f}s")

                # Progress indicator
                if i % 10 == 0:
                    avg_time = statistics.mean(metrics.iteration_times[-10:])
                    print(f"\n--- Progress: {i}/{num_iterations} iterations ({i/num_iterations*100:.1f}%) ---")
                    print(f"--- Last 10 iterations avg time: {avg_time:.2f}s ---\n")

            except Exception as e:
                print(f"[Iteration {i}] ERROR: {str(e)}")
                metrics.record_error(i, str(e))

    except Exception as e:
        print(f"Fatal error in workflow: {e}")
        metrics.record_error(0, f"Fatal: {str(e)}")

    metrics.end_time = time.time()
    return metrics


async def run_mock_workflow(num_iterations: int, test_prompts: List[str]) -> PerformanceMetrics:
    """Run a simulated workflow for testing (no API calls)"""
    metrics = PerformanceMetrics()
    metrics.start_time = time.time()

    mock_workflow = MockArchonWorkflow()

    print(f"Starting MOCK workflow test with {num_iterations} iterations...")
    print("(No real API calls - simulating workflow behavior)")
    print("=" * 80)

    for i in range(1, num_iterations + 1):
        try:
            # Use prompts cyclically
            user_message = test_prompts[i % len(test_prompts)]
            print(f"\n[Iteration {i}] User: {user_message[:100]}...")

            iteration_start = time.time()
            response = await mock_workflow.simulate_iteration(user_message)
            duration = time.time() - iteration_start

            metrics.record_iteration(duration, len(response))

            print(f"[Iteration {i}] Response length: {len(response)} chars, Time: {duration:.2f}s")
            print(f"[Iteration {i}] Preview: {response[:200]}...")

            # Progress indicator
            if i % 10 == 0:
                avg_time = statistics.mean(metrics.iteration_times[-10:])
                print(f"\n--- Progress: {i}/{num_iterations} iterations ({i/num_iterations*100:.1f}%) ---")
                print(f"--- Last 10 iterations avg time: {avg_time:.2f}s ---\n")

        except Exception as e:
            print(f"[Iteration {i}] ERROR: {str(e)}")
            metrics.record_error(i, str(e))

    metrics.end_time = time.time()
    return metrics


def save_results(metrics: PerformanceMetrics, output_file: str):
    """Save test results to JSON file"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "mode": "MOCK" if MOCK_MODE else "REAL",
        "statistics": metrics.get_statistics()
    }

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")


def print_summary(metrics: PerformanceMetrics):
    """Print a summary of the test results"""
    stats = metrics.get_statistics()

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Mode: {'MOCK' if MOCK_MODE else 'REAL'}")
    print(f"Total Iterations: {stats['total_iterations']}")
    print(f"Total Time: {stats['total_time']:.2f} seconds ({stats['total_time']/60:.2f} minutes)")
    print(f"\nIteration Times:")
    print(f"  Average: {stats['avg_iteration_time']:.3f}s")
    print(f"  Median: {stats['median_iteration_time']:.3f}s")
    print(f"  Min: {stats['min_iteration_time']:.3f}s")
    print(f"  Max: {stats['max_iteration_time']:.3f}s")
    print(f"  Std Dev: {stats['stddev_iteration_time']:.3f}s")
    print(f"\nResponse Lengths:")
    print(f"  Average: {stats['avg_response_length']:.0f} characters")
    print(f"\nErrors:")
    print(f"  Total: {stats['total_errors']}")
    print(f"  Error Rate: {stats['error_rate']*100:.2f}%")

    if stats['errors']:
        print(f"\nError Details:")
        for error in stats['errors'][:5]:  # Show first 5 errors
            print(f"  - Iteration {error['iteration']}: {error['error']}")
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more errors")

    print("=" * 80)


async def main():
    """Main test execution"""

    # Configuration
    NUM_ITERATIONS = 100

    # Diverse test prompts to cycle through
    TEST_PROMPTS = [
        "Create a weather forecasting agent that can get weather data and provide forecasts.",
        "Add error handling to the agent.",
        "Implement a caching mechanism for weather data.",
        "Add support for multiple locations.",
        "Improve the system prompt to be more conversational.",
        "Add unit tests for the tools.",
        "Optimize the agent for faster response times.",
        "Add logging to track API calls.",
        "Implement rate limiting to avoid API quota issues.",
        "Add a help command to explain available features.",
        "Refine the response formatting.",
        "Add support for temperature unit conversion (C/F).",
        "Implement historical weather data retrieval.",
        "Add weather alerts and warnings.",
        "Improve error messages for invalid locations.",
        "Add autocomplete for location names.",
        "Implement a 7-day forecast feature.",
        "Add visualization for temperature trends.",
        "Optimize token usage in the prompts.",
        "That looks good, thanks!",
    ]

    # Run workflow
    if MOCK_MODE:
        metrics = await run_mock_workflow(NUM_ITERATIONS, TEST_PROMPTS)
    else:
        metrics = await run_real_workflow(NUM_ITERATIONS, TEST_PROMPTS)

    # Print and save results
    print_summary(metrics)

    output_file = f"workbench/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results(metrics, output_file)

    # Analysis
    stats = metrics.get_statistics()
    if stats.get('total_iterations', 0) >= 100:
        print("\n✅ Successfully completed 100+ iterations!")
        print(f"   Total completed: {stats['total_iterations']}")
        print(f"   Success rate: {(1 - stats['error_rate']) * 100:.2f}%")
    else:
        print(f"\n⚠️  Completed {stats.get('total_iterations', 0)} iterations (target: 100)")


if __name__ == "__main__":
    asyncio.run(main())
