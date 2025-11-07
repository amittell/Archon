"""
Use Case: Data Analysis Agent with AutoGen

This example demonstrates creating a data analysis agent that can execute code,
analyze datasets, and generate visualizations.
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from archon.archon_graph_v6 import agentic_flow
from langgraph.types import Command


async def main():
    """Create a data analysis agent using AutoGen"""

    config = {
        "configurable": {
            "thread_id": "data_analysis_agent"
        }
    }

    print("=" * 80)
    print("USE CASE: DATA ANALYSIS AGENT (AutoGen)")
    print("=" * 80)
    print("\nThis example creates a data analysis agent with:")
    print("  • CSV/Excel data loading")
    print("  • Statistical analysis")
    print("  • Data visualization")
    print("  • Code execution capabilities")
    print("  • Natural language queries")
    print("=" * 80)

    # Step 1: Define the agent
    print("\n[Step 1] Creating AutoGen data analysis agent...\n")

    requirements = """
    Using AutoGen, create a data analysis agent system with the following:

    AGENT SETUP:
    1. Assistant Agent (Analyst)
       - Role: Expert data analyst
       - Capabilities: pandas, numpy, matplotlib, seaborn
       - Can write and explain Python code for analysis
       - Provides insights and recommendations

    2. User Proxy Agent (Executor)
       - Executes Python code in safe environment
       - Returns results and any outputs
       - Can display plots and visualizations
       - Has access to work directory

    ANALYSIS CAPABILITIES:
    1. Data Loading
       - Read CSV, Excel, JSON files
       - Handle missing data
       - Show data summary (head, info, describe)

    2. Statistical Analysis
       - Descriptive statistics
       - Correlation analysis
       - Distribution analysis
       - Trend identification

    3. Visualization
       - Histograms and distributions
       - Scatter plots and correlations
       - Time series plots
       - Bar charts and comparisons
       - Heatmaps

    4. Advanced Analysis
       - Outlier detection
       - Feature importance
       - Simple predictions (linear regression)
       - Clustering (k-means)

    FEATURES:
    - Natural language queries: "Show me the correlation between X and Y"
    - Automatic visualization: "Plot sales trends over time"
    - Safety: Code execution with timeout and resource limits
    - Interactive: User can approve code before execution
    - Export: Save plots and results

    CODE STRUCTURE:
    - agents.py: Agent definitions
    - analysis_tools.py: Helper functions
    - config.py: Configuration
    - example_usage.py: Demo queries
    - requirements.txt: Dependencies

    Use AutoGen's code execution features and GroupChat for multi-turn analysis.
    """

    response_text = ""
    async for msg in agentic_flow.astream(
        {"latest_user_message": requirements},
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 1 Complete] Generated AutoGen agent ({len(response_text)} chars)")

    # Step 2: Add example dataset and queries
    print("\n" + "=" * 80)
    print("[Step 2] Adding example dataset and queries...\n")

    example_request = """
    Add:
    1. A sample CSV dataset (sales_data.csv) with:
       - Date, Product, Quantity, Price, Customer, Region columns
       - 100+ rows of realistic data
       - Some missing values to demonstrate handling

    2. Example analysis queries (queries.py):
       - "What are the total sales by region?"
       - "Show me the top 5 products by revenue"
       - "Plot sales trends over the last 6 months"
       - "Find any correlation between price and quantity"
       - "Identify outliers in the sales data"
       - "Create a heatmap of regional performance"

    3. Include code to run these queries and save outputs
    """

    response_text = ""
    async for msg in agentic_flow.astream(
        Command(resume=example_request),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 2 Complete] Added examples ({len(response_text)} chars)")

    # Step 3: Add Jupyter notebook
    print("\n" + "=" * 80)
    print("[Step 3] Adding Jupyter notebook interface...\n")

    notebook_request = """
    Create a Jupyter notebook (analysis_demo.ipynb) that:
    - Sets up the AutoGen agents
    - Loads the sample dataset
    - Demonstrates each analysis capability
    - Shows the conversation flow between agents
    - Includes markdown explanations
    - Displays all visualizations inline
    - Has a "try your own query" section at the end
    """

    response_text = ""
    async for msg in agentic_flow.astream(
        Command(resume=notebook_request),
        config,
        stream_mode="custom"
    ):
        response_text += str(msg)
        print(msg, end="", flush=True)

    print(f"\n\n[Step 3 Complete] Added notebook ({len(response_text)} chars)")

    # Step 4: Finalize
    print("\n" + "=" * 80)
    print("[Step 4] Finalizing...\n")

    final_request = """
    That's excellent! Add:
    1. README.md with setup and usage instructions
    2. Safety guidelines for code execution
    3. Tips for writing effective analysis queries
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
    print("DATA ANALYSIS AGENT COMPLETE!")
    print("=" * 80)
    print("\nGenerated Files:")
    print("  ✓ agents.py - AutoGen agent setup")
    print("  ✓ analysis_tools.py - Helper functions")
    print("  ✓ config.py - Configuration")
    print("  ✓ sales_data.csv - Sample dataset")
    print("  ✓ queries.py - Example queries")
    print("  ✓ example_usage.py - Demo script")
    print("  ✓ analysis_demo.ipynb - Jupyter notebook")
    print("  ✓ requirements.txt - Dependencies")
    print("  ✓ README.md - Documentation")
    print("\nKey Features:")
    print("  • Natural language → Python code → Execution → Results")
    print("  • Safe code execution with AutoGen's UserProxyAgent")
    print("  • Automatic visualization generation")
    print("  • Interactive analysis workflow")
    print("  • Works with any tabular dataset")
    print("\nExample Usage:")
    print('  user: "What are the top selling products?"')
    print("  analyst: [writes pandas code to analyze]")
    print("  executor: [runs code, returns results]")
    print("  analyst: [explains findings]")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("\nMake sure your environment is set up correctly.")
