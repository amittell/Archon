"""
Archon Workflow Analyzer - Deep Dive Analysis Tool

This script analyzes the Archon agentic workflow architecture,
performs static code analysis, and identifies optimization opportunities.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Set
import json


class WorkflowAnalyzer:
    """Analyze the Archon workflow architecture"""

    def __init__(self, base_path: str = "/home/user/Archon"):
        self.base_path = Path(base_path)
        self.analysis = {
            "nodes": {},
            "edges": [],
            "agents": {},
            "tools": {},
            "dependencies": set(),
            "metrics": {}
        }

    def analyze_graph_structure(self):
        """Analyze the LangGraph structure"""
        graph_file = self.base_path / "archon" / "archon_graph.py"

        with open(graph_file, 'r') as f:
            content = f.read()
            tree = ast.parse(content)

        # Find node definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('__') or node.name == 'main':
                    continue

                self.analysis["nodes"][node.name] = {
                    "name": node.name,
                    "line": node.lineno,
                    "is_async": isinstance(node, ast.AsyncFunctionDef) or \
                               any(isinstance(d, ast.Name) and d.id == 'async' for d in node.decorator_list),
                    "args": [arg.arg for arg in node.args.args],
                    "docstring": ast.get_docstring(node)
                }

        # Extract edge information from content
        edges = []
        for line in content.split('\n'):
            if 'add_edge' in line:
                edges.append(line.strip())

        self.analysis["edges"] = edges

        return self.analysis["nodes"]

    def analyze_agents(self):
        """Analyze agent definitions"""
        graph_file = self.base_path / "archon" / "archon_graph.py"

        with open(graph_file, 'r') as f:
            content = f.read()

        # Find Agent instantiations
        agents = []
        for line in content.split('\n'):
            if 'Agent(' in line and '=' in line:
                agent_name = line.split('=')[0].strip()
                agents.append({
                    "name": agent_name,
                    "definition": line.strip()
                })

        self.analysis["agents"] = agents
        return agents

    def analyze_tools(self):
        """Analyze tools defined in the coder agent"""
        tools_file = self.base_path / "archon" / "pydantic_ai_coder.py"

        with open(tools_file, 'r') as f:
            content = f.read()
            tree = ast.parse(content)

        tools = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for @pydantic_ai_coder.tool decorator
                has_tool_decorator = any(
                    isinstance(d, ast.Attribute) and
                    d.attr == 'tool' for d in node.decorator_list
                )

                if has_tool_decorator:
                    tools[node.name] = {
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args if arg.arg != 'ctx'],
                        "docstring": ast.get_docstring(node),
                        "is_async": isinstance(node, ast.AsyncFunctionDef)
                    }

        self.analysis["tools"] = tools
        return tools

    def analyze_dependencies(self):
        """Analyze package dependencies"""
        req_file = self.base_path / "requirements.txt"

        deps = set()
        with open(req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name (before ==, >=, etc.)
                    pkg = line.split('==')[0].split('>=')[0].split('<=')[0]
                    deps.add(pkg)

        self.analysis["dependencies"] = sorted(list(deps))
        return self.analysis["dependencies"]

    def calculate_metrics(self):
        """Calculate various metrics about the workflow"""
        metrics = {
            "total_nodes": len(self.analysis["nodes"]),
            "total_edges": len(self.analysis["edges"]),
            "total_agents": len(self.analysis["agents"]),
            "total_tools": len(self.analysis["tools"]),
            "total_dependencies": len(self.analysis["dependencies"]),
            "async_nodes": sum(1 for n in self.analysis["nodes"].values() if n["is_async"]),
            "async_tools": sum(1 for t in self.analysis["tools"].values() if t["is_async"])
        }

        self.analysis["metrics"] = metrics
        return metrics

    def identify_bottlenecks(self):
        """Identify potential performance bottlenecks"""
        bottlenecks = []

        # Check for synchronous nodes that might block
        for name, node in self.analysis["nodes"].items():
            if not node["is_async"]:
                bottlenecks.append({
                    "type": "synchronous_node",
                    "location": f"archon_graph.py:{node['line']}",
                    "description": f"Node '{name}' is synchronous and may block async workflow",
                    "severity": "medium"
                })

        # Check for non-streaming operations
        graph_file = self.base_path / "archon" / "archon_graph.py"
        with open(graph_file, 'r') as f:
            content = f.read()

        if 'run_stream' in content:
            # Good - using streaming
            pass

        if 'run(' in content:
            bottlenecks.append({
                "type": "non_streaming",
                "location": "archon_graph.py",
                "description": "Some agent calls use .run() instead of .run_stream()",
                "severity": "low",
                "suggestion": "Convert all agent calls to streaming for better UX"
            })

        # Check for in-memory checkpoint (scalability issue)
        if 'MemorySaver' in content:
            bottlenecks.append({
                "type": "memory_checkpoint",
                "location": "archon_graph.py",
                "description": "Using MemorySaver for checkpointing - doesn't persist across restarts",
                "severity": "high",
                "suggestion": "Use SqliteSaver or PostgresSaver for production"
            })

        return bottlenecks

    def identify_improvements(self):
        """Identify potential improvements"""
        improvements = []

        # Check for error handling
        graph_file = self.base_path / "archon" / "archon_graph.py"
        with open(graph_file, 'r') as f:
            content = f.read()

        try_count = content.count('try:')
        if try_count < len(self.analysis["nodes"]):
            improvements.append({
                "category": "error_handling",
                "description": "Not all nodes have try-except blocks",
                "impact": "medium",
                "effort": "low",
                "suggestion": "Add comprehensive error handling to all nodes"
            })

        # Check for validation
        if 'validate' not in content.lower():
            improvements.append({
                "category": "validation",
                "description": "No code validation step in workflow",
                "impact": "high",
                "effort": "high",
                "suggestion": "Add a validation node to test generated code before delivery (V4 feature)"
            })

        # Check for monitoring
        if 'logfire' in content:
            # Has some monitoring
            pass
        else:
            improvements.append({
                "category": "monitoring",
                "description": "Limited observability and monitoring",
                "impact": "medium",
                "effort": "medium",
                "suggestion": "Add comprehensive logging and metrics tracking"
            })

        # Check for rate limiting
        if 'rate_limit' not in content.lower():
            improvements.append({
                "category": "rate_limiting",
                "description": "No rate limiting for API calls",
                "impact": "medium",
                "effort": "low",
                "suggestion": "Add rate limiting to prevent quota exhaustion"
            })

        # Check for caching
        if 'cache' not in content.lower():
            improvements.append({
                "category": "caching",
                "description": "No caching mechanism for repeated queries",
                "impact": "medium",
                "effort": "medium",
                "suggestion": "Cache RAG results and agent responses for common queries"
            })

        return improvements

    def generate_report(self) -> Dict[str, Any]:
        """Generate complete analysis report"""

        print("Analyzing Archon workflow...")
        print("=" * 80)

        # Run all analyses
        self.analyze_graph_structure()
        self.analyze_agents()
        self.analyze_tools()
        self.analyze_dependencies()
        self.calculate_metrics()

        bottlenecks = self.identify_bottlenecks()
        improvements = self.identify_improvements()

        report = {
            "analysis_timestamp": __import__('datetime').datetime.now().isoformat(),
            "workflow_structure": {
                "nodes": list(self.analysis["nodes"].keys()),
                "edges": self.analysis["edges"],
                "node_details": self.analysis["nodes"]
            },
            "agents": self.analysis["agents"],
            "tools": self.analysis["tools"],
            "dependencies": self.analysis["dependencies"],
            "metrics": self.analysis["metrics"],
            "bottlenecks": bottlenecks,
            "improvements": improvements
        }

        return report


def print_report(report: Dict[str, Any]):
    """Print analysis report in readable format"""

    print("\n" + "=" * 80)
    print("ARCHON WORKFLOW ANALYSIS REPORT")
    print("=" * 80)

    print("\n📊 METRICS:")
    print("-" * 40)
    for key, value in report["metrics"].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")

    print("\n🔧 WORKFLOW NODES:")
    print("-" * 40)
    for node_name in report["workflow_structure"]["nodes"]:
        node = report["workflow_structure"]["node_details"][node_name]
        async_marker = "⚡" if node["is_async"] else "🔄"
        print(f"  {async_marker} {node_name} (line {node['line']})")
        if node["docstring"]:
            print(f"     {node['docstring'][:80]}...")

    print("\n🤖 AGENTS:")
    print("-" * 40)
    for agent in report["agents"]:
        print(f"  • {agent['name']}")

    print("\n🛠️  TOOLS:")
    print("-" * 40)
    for tool_name, tool in report["tools"].items():
        async_marker = "⚡" if tool["is_async"] else "🔄"
        args_str = ", ".join(tool["args"])
        print(f"  {async_marker} {tool_name}({args_str})")
        if tool["docstring"]:
            print(f"     {tool['docstring'][:100]}...")

    print("\n⚠️  BOTTLENECKS:")
    print("-" * 40)
    if report["bottlenecks"]:
        for b in report["bottlenecks"]:
            severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            icon = severity_icon.get(b["severity"], "⚪")
            print(f"  {icon} [{b['severity'].upper()}] {b['type']}")
            print(f"     Location: {b['location']}")
            print(f"     Description: {b['description']}")
            if "suggestion" in b:
                print(f"     💡 Suggestion: {b['suggestion']}")
            print()
    else:
        print("  ✅ No significant bottlenecks identified")

    print("\n💡 IMPROVEMENT OPPORTUNITIES:")
    print("-" * 40)
    if report["improvements"]:
        for imp in report["improvements"]:
            print(f"  • [{imp['category'].upper()}] {imp['description']}")
            print(f"     Impact: {imp['impact']} | Effort: {imp['effort']}")
            print(f"     💡 {imp['suggestion']}")
            print()
    else:
        print("  ✅ Workflow is well-optimized")

    print("\n📦 KEY DEPENDENCIES:")
    print("-" * 40)
    key_deps = ["pydantic-ai", "langgraph", "openai", "supabase", "fastapi", "mcp"]
    for dep in key_deps:
        if dep in report["dependencies"]:
            print(f"  ✓ {dep}")

    print("\n" + "=" * 80)


def save_report(report: Dict[str, Any], filename: str):
    """Save report to JSON file"""
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert sets to lists for JSON serialization
    def convert_sets(obj):
        if isinstance(obj, set):
            return sorted(list(obj))
        elif isinstance(obj, dict):
            return {k: convert_sets(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_sets(item) for item in obj]
        return obj

    report_serializable = convert_sets(report)

    with open(output_path, 'w') as f:
        json.dump(report_serializable, f, indent=2)

    print(f"\n📄 Full report saved to: {filename}")


def main():
    """Main analysis execution"""
    analyzer = WorkflowAnalyzer()
    report = analyzer.generate_report()

    print_report(report)

    # Save detailed report
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_report(report, f"workbench/workflow_analysis_{timestamp}.json")


if __name__ == "__main__":
    main()
