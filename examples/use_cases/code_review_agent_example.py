"""
Use Case: Code Review Agent with LangGraph

This example demonstrates creating a multi-agent code review system with
specialized agents for different aspects of code review.
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from archon.archon_graph_v6 import agentic_flow
from langgraph.types import Command


async def main():
    """Create a code review agent using LangGraph"""

    config = {
        "configurable": {
            "thread_id": "code_review_agent"
        }
    }

    print("=" * 80)
    print("USE CASE: CODE REVIEW AGENT (LangGraph)")
    print("=" * 80)
    print("\nThis example creates a multi-agent code review system with:")
    print("  • Style & formatting review")
    print("  • Security vulnerability scanning")
    print("  • Performance optimization suggestions")
    print("  • Best practices validation")
    print("  • Comprehensive report generation")
    print("=" * 80)

    # Step 1: Define the multi-agent workflow
    print("\n[Step 1] Creating LangGraph code review workflow...\n")

    requirements = """
    Using LangGraph, create a comprehensive code review system with multiple specialized agents:

    AGENT WORKFLOW:
    1. Coordinator Agent
       - Receives code submission
       - Routes to specialized reviewers
       - Aggregates feedback
       - Generates final report

    2. Style Reviewer Agent
       - Checks code formatting
       - Validates naming conventions
       - Ensures consistent style
       - Suggests improvements

    3. Security Reviewer Agent
       - Scans for vulnerabilities
       - Checks for unsafe patterns
       - Validates input handling
       - Reviews authentication/authorization

    4. Performance Reviewer Agent
       - Identifies bottlenecks
       - Suggests optimizations
       - Reviews algorithm complexity
       - Checks resource usage

    5. Best Practices Agent
       - Validates design patterns
       - Checks error handling
       - Reviews testing coverage
       - Ensures maintainability

    STATE GRAPH STRUCTURE:
    - START → coordinator
    - coordinator → [style_review, security_review, performance_review, best_practices]
    - All reviews → aggregator
    - aggregator → report_generator
    - report_generator → END

    STATE SCHEMA:
    - code: str (code to review)
    - language: str (programming language)
    - style_feedback: List[dict]
    - security_issues: List[dict]
    - performance_suggestions: List[dict]
    - best_practice_violations: List[dict]
    - final_report: str
    - severity_score: int (0-100)

    FEATURES:
    - Parallel review execution (all agents run simultaneously)
    - SQLite checkpointing for long reviews
    - Severity scoring (critical, high, medium, low)
    - GitHub/GitLab integration ready
    - Supports multiple languages (Python, JavaScript, TypeScript, etc.)
    - Generates markdown reports
    - Can auto-fix simple issues

    CODE STRUCTURE:
    - graph.py: Main workflow definition
    - state.py: State schema
    - agents/: Individual agent modules
      - coordinator.py
      - style_reviewer.py
      - security_reviewer.py
      - performance_reviewer.py
      - best_practices.py
    - reporters.py: Report generation
    - integrations/: GitHub/GitLab hooks
    - requirements.txt: Dependencies

    Use LangGraph's parallel execution and conditional routing features.
    """

    response_text = ""
    async for msg in agentic_flow.astream(
        {"latest_user_message": requirements},
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 1 Complete] Generated LangGraph workflow ({len(response_text)} chars)")

    # Step 2: Add example code samples
    print("\n" + "=" * 80)
    print("[Step 2] Adding test cases and examples...\n")

    examples_request = """
    Add example code samples for testing (examples/ directory):

    1. good_example.py - Well-written code that passes all checks
    2. style_issues.py - Code with formatting and style problems
    3. security_issues.py - Code with security vulnerabilities (SQL injection, XSS, etc.)
    4. performance_issues.py - Code with performance problems (N+1 queries, etc.)
    5. best_practice_issues.py - Code violating best practices

    For each example, include:
    - The problematic code
    - Expected review feedback
    - Fixed version
    - Explanation of issues

    Also add a test suite (test_reviews.py) that:
    - Tests each reviewer independently
    - Validates severity scoring
    - Checks report generation
    - Ensures all issues are caught
    """

    response_text = ""
    async for msg in agentic_flow.astream(
        Command(resume=examples_request),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 2 Complete] Added examples ({len(response_text)} chars)")

    # Step 3: Add CLI and GitHub Action
    print("\n" + "=" * 80)
    print("[Step 3] Adding CLI and CI/CD integration...\n")

    integration_request = """
    Add:
    1. CLI interface (review_cli.py):
       - Accept file path or directory
       - Support glob patterns (*.py)
       - Output format options (text, json, markdown)
       - Watch mode for continuous review
       - Fix mode to auto-fix simple issues

    2. GitHub Action (action.yml + github_action.py):
       - Runs on pull requests
       - Posts review as PR comments
       - Blocks merge if critical issues found
       - Tracks issues with line numbers
       - Integrates with GitHub Checks API

    3. Pre-commit hook (pre_commit_hook.py):
       - Quick review before commit
       - Blocks commit if critical issues
       - Auto-fixes if possible
       - Configuration file (.reviewrc)

    Include setup instructions for each integration.
    """

    response_text = ""
    async for msg in agentic_flow.astream(
        Command(resume=integration_request),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 3 Complete] Added integrations ({len(response_text)} chars)")

    # Step 4: Finalize
    print("\n" + "=" * 80)
    print("[Step 4] Finalizing...\n")

    final_request = """
    Perfect! Add:
    1. Comprehensive README.md with:
       - Architecture diagram
       - Setup instructions
       - Usage examples
       - Integration guides
    2. Configuration documentation
    3. Contributing guidelines
    """

    response_text = ""
    async for msg in agentic_flow.astream(
        Command(resume=final_request),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print("\n\n" + "=" * 80)
    print("CODE REVIEW AGENT COMPLETE!")
    print("=" * 80)
    print("\nGenerated Files:")
    print("  ✓ graph.py - LangGraph workflow")
    print("  ✓ state.py - State schema")
    print("  ✓ agents/ - Specialized reviewers")
    print("  ✓ reporters.py - Report generation")
    print("  ✓ review_cli.py - CLI interface")
    print("  ✓ github_action.py - GitHub integration")
    print("  ✓ action.yml - GitHub Action config")
    print("  ✓ pre_commit_hook.py - Pre-commit hook")
    print("  ✓ examples/ - Test cases")
    print("  ✓ test_reviews.py - Test suite")
    print("  ✓ requirements.txt - Dependencies")
    print("  ✓ README.md - Documentation")
    print("\nKey Features:")
    print("  • Parallel review by specialized agents")
    print("  • Comprehensive issue detection")
    print("  • Multi-language support")
    print("  • CI/CD integration (GitHub Actions)")
    print("  • Auto-fix capabilities")
    print("  • Detailed severity scoring")
    print("\nUsage Examples:")
    print("  CLI: python review_cli.py src/")
    print("  Pre-commit: pre-commit install")
    print("  GitHub: Add action.yml to .github/workflows/")
    print("\nLangGraph Features Used:")
    print("  • StateGraph for workflow orchestration")
    print("  • Parallel execution for multiple reviewers")
    print("  • SQLite checkpointing for state persistence")
    print("  • Conditional routing based on severity")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("\nMake sure your environment is set up correctly.")
