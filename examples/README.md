# Archon Examples

Welcome to the Archon examples! This directory contains practical, runnable examples to help you get started with Archon's AI agent generation capabilities.

## 📁 Directory Structure

```
examples/
├── README.md (this file)
├── basic/
│   ├── v3_basic_usage.py        # Simple Archon V3 workflow
│   ├── v4_with_validation.py    # V4 with code validation
│   └── v6_multi_framework.py    # V6 with multi-framework support
├── use_cases/
│   ├── weather_agent_example.py           # Weather forecasting agent
│   ├── data_analysis_agent_example.py     # Data analysis with AutoGen
│   └── code_review_agent_example.py       # Code review with LangGraph
└── .env.example                  # Environment configuration
```

## 🚀 Quick Start

### Prerequisites

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Set Up Supabase** (for RAG documentation)
   ```bash
   # Initialize database
   python archon/init_supabase.py

   # Crawl documentation
   python archon/crawl_site.py  # For V3 (Pydantic AI only)
   python archon/crawl_multi_framework_docs.py --all  # For V6 (all frameworks)
   ```

### Running Examples

#### Basic Examples

**V3 - Basic Usage** (Pydantic AI only)
```bash
python examples/basic/v3_basic_usage.py
```
- Demonstrates simple agent creation
- Shows multi-turn conversation flow
- Uses RAG over Pydantic AI docs

**V4 - With Validation** (Adds code validation)
```bash
python examples/basic/v4_with_validation.py
```
- Shows automatic code validation
- Demonstrates validation feedback loop
- Includes validation examples

**V6 - Multi-Framework** (Supports 4 frameworks)
```bash
python examples/basic/v6_multi_framework.py
```
- Creates agents for all 4 frameworks
- Shows framework auto-detection
- Demonstrates framework-specific features

#### Use Case Examples

**Weather Forecasting Agent**
```bash
python examples/use_cases/weather_agent_example.py
```
Creates a production-ready weather agent with:
- Current weather & 7-day forecast
- Temperature conversion
- Weather alerts
- CLI interface
- Comprehensive tests

**Data Analysis Agent** (AutoGen)
```bash
python examples/use_cases/data_analysis_agent_example.py
```
Creates a data analysis system with:
- Natural language queries
- Code execution
- Automatic visualizations
- Jupyter notebook interface

**Code Review Agent** (LangGraph)
```bash
python examples/use_cases/code_review_agent_example.py
```
Creates a multi-agent code review system with:
- Specialized review agents
- Parallel execution
- GitHub integration
- Auto-fix capabilities

## 📚 Archon Versions

### V3 - Basic Agent Generation
**Features:**
- Pydantic AI support only
- RAG over documentation
- Streaming responses
- Multi-turn conversations
- Reasoner LLM for scope

**Best For:**
- Simple agent creation
- Pydantic AI projects
- Quick prototyping

### V4 - With Validation Loop
**Features:**
- All V3 features
- Automatic code validation (5 checks)
- Validation feedback loop (max 3 retries)
- SQLite checkpointing
- Persistent conversations

**Best For:**
- Production agents
- Quality assurance
- Safety-critical applications

**Validation Checks:**
1. **Syntax** - AST parsing
2. **Imports** - Availability checking
3. **Security** - Dangerous pattern scanning
4. **Structure** - Agent structure validation
5. **Execution** - Sandbox testing (optional)

### V6 - Multi-Framework Support
**Features:**
- All V4 features
- 4 framework support (Pydantic AI, LangGraph, CrewAI, AutoGen)
- Framework auto-detection
- Framework-specific RAG
- Framework-specific templates

**Best For:**
- Multi-framework projects
- Framework comparison
- Team with diverse preferences

**Supported Frameworks:**

| Framework | Best For | Key Features |
|-----------|----------|--------------|
| **Pydantic AI** | Simple, type-safe agents | Built-in validation, streaming, simple tools |
| **LangGraph** | Complex workflows | StateGraph, checkpointing, conditional routing |
| **CrewAI** | Role-based collaboration | Agent roles, task delegation, processes |
| **AutoGen** | Code execution agents | AssistantAgent, code execution, GroupChat |

## 🎯 Choosing the Right Framework

### Use Pydantic AI when:
- You need simple, straightforward agents
- Type safety is important
- You want built-in Pydantic validation
- Quick prototyping

### Use LangGraph when:
- You need complex multi-agent workflows
- State management is critical
- You need persistent checkpointing
- Human-in-the-loop interactions

### Use CrewAI when:
- You have role-based agent teams
- Task delegation is important
- You need agent collaboration
- Simulating organizational structures

### Use AutoGen when:
- Code execution is required
- You need conversational agents
- Interactive problem-solving
- Multi-agent conversations

## 💡 Common Patterns

### Pattern 1: Simple Q&A Agent (Pydantic AI)
```python
from archon.archon_graph_v6 import agentic_flow

request = """
Using Pydantic AI, create a customer support agent that can:
- Answer FAQs about products
- Look up order status
- Escalate to human support when needed
"""
```

### Pattern 2: Multi-Agent Workflow (LangGraph)
```python
request = """
Using LangGraph, create a research workflow with:
- Researcher agent (finds information)
- Analyst agent (analyzes findings)
- Writer agent (creates report)
Use StateGraph with sequential execution.
"""
```

### Pattern 3: Role-Based Team (CrewAI)
```python
request = """
Using CrewAI, create a content creation crew with:
- Writer (creates draft)
- Editor (reviews and edits)
- SEO Expert (optimizes for search)
- Publisher (final review)
Use Process.sequential for workflow.
"""
```

### Pattern 4: Code Execution (AutoGen)
```python
request = """
Using AutoGen, create a data analysis agent that can:
- Write Python code for analysis
- Execute code safely
- Generate visualizations
- Explain results
Use AssistantAgent + UserProxyAgent pattern.
"""
```

## 🛠️ Customization

### Changing Models

Edit your `.env` file:
```bash
# Reasoner model (for scope definition)
REASONER_MODEL=o3-mini

# Primary model (for code generation)
PRIMARY_MODEL=gpt-4o-mini

# Or use local models with Ollama
BASE_URL=http://localhost:11434/v1
PRIMARY_MODEL=codellama
```

### Adjusting Validation

In V4/V6, you can customize validation:
```python
from archon.code_validator import CodeValidator

# Adjust timeout
validator = CodeValidator(timeout=10)

# Skip execution validation
is_valid, results = await validator.validate_all(
    code,
    skip_execution=True
)
```

### Framework Selection

V6 auto-detects frameworks, but you can be explicit:
```python
# These keywords trigger framework detection:
"Using Pydantic AI..."  # → Pydantic AI
"Build a LangGraph..."  # → LangGraph
"Create a CrewAI..."    # → CrewAI
"With AutoGen..."       # → AutoGen
```

## 🔍 Troubleshooting

### Issue: "No documentation found"
**Solution:** Run the documentation crawler:
```bash
# For V3
python archon/crawl_site.py

# For V6 (all frameworks)
python archon/crawl_multi_framework_docs.py --all
```

### Issue: "ModuleNotFoundError"
**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "Validation failing unexpectedly"
**Solution:** Check validation details:
```python
# The validation errors show exactly what's wrong
# Look for:
# - Import errors → Install missing packages
# - Syntax errors → Check code generation
# - Security issues → Review dangerous patterns
```

### Issue: "Slow response times"
**Solutions:**
- Use faster models (gpt-4o-mini vs gpt-4)
- Use local models with Ollama
- Skip execution validation
- Reduce number of iterations

## 📖 Additional Resources

- **Main Documentation:** [ARCHON_V6_COMPLETE.md](../ARCHON_V6_COMPLETE.md)
- **Implementation Details:** [IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md)
- **API Reference:** See individual framework docs
  - [Pydantic AI](https://ai.pydantic.dev)
  - [LangGraph](https://langchain-ai.github.io/langgraph/)
  - [CrewAI](https://docs.crewai.com)
  - [AutoGen](https://microsoft.github.io/autogen/)

## 🤝 Contributing Examples

Have a great example? We'd love to include it!

1. Create your example in `use_cases/`
2. Follow the existing format
3. Include comprehensive comments
4. Add to this README
5. Submit a PR

Good example topics:
- Customer service agents
- Research assistants
- Game NPCs
- Educational tutors
- DevOps automation
- Testing assistants

## 📝 Example Template

```python
"""
Use Case: [Name]

Brief description of what this example demonstrates.
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from archon.archon_graph_v6 import agentic_flow
from langgraph.types import Command


async def main():
    config = {"configurable": {"thread_id": "your_example"}}

    # Your example implementation

    requirements = """
    [Detailed requirements for the agent]
    """

    async for msg in agentic_flow.astream(
        {"latest_user_message": requirements},
        config,
        stream_mode="custom"
    ):
        print(msg, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
```

## 🎓 Learning Path

**For Beginners:**
1. Start with `v3_basic_usage.py`
2. Try `weather_agent_example.py`
3. Experiment with your own simple agents

**For Intermediate Users:**
4. Explore `v4_with_validation.py`
5. Try `data_analysis_agent_example.py`
6. Create agents with multiple tools

**For Advanced Users:**
7. Study `v6_multi_framework.py`
8. Explore `code_review_agent_example.py`
9. Build complex multi-agent systems
10. Contribute your own examples!

## 🚀 Next Steps

After running these examples:

1. **Customize** - Modify examples for your use case
2. **Integrate** - Add Archon to your projects
3. **Experiment** - Try different frameworks
4. **Build** - Create your own production agents
5. **Share** - Contribute back to the community

Happy agent building! 🤖✨
