"""
Framework Configuration for Archon V6

Defines supported frameworks, their documentation sources,
and framework-specific generation templates.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class FrameworkInfo:
    """Information about a supported AI agent framework"""
    name: str
    display_name: str
    docs_base_url: str
    sitemap_url: Optional[str]
    package_name: str
    default_model: str
    file_structure: Dict[str, str]  # filename -> description
    example_imports: List[str]


# Framework definitions
FRAMEWORKS = {
    'pydantic_ai': FrameworkInfo(
        name='pydantic_ai',
        display_name='Pydantic AI',
        docs_base_url='https://ai.pydantic.dev',
        sitemap_url='https://ai.pydantic.dev/sitemap.xml',
        package_name='pydantic-ai',
        default_model='openai:gpt-4o-mini',
        file_structure={
            'agent.py': 'Main agent definition',
            'agent_tools.py': 'Tool functions',
            'agent_prompts.py': 'System prompts',
            '.env.example': 'Environment variables',
            'requirements.txt': 'Dependencies'
        },
        example_imports=[
            'from pydantic_ai import Agent, RunContext',
            'from pydantic_ai.models.openai import OpenAIModel',
        ]
    ),

    'langgraph': FrameworkInfo(
        name='langgraph',
        display_name='LangGraph',
        docs_base_url='https://langchain-ai.github.io/langgraph',
        sitemap_url='https://langchain-ai.github.io/langgraph/sitemap.xml',
        package_name='langgraph',
        default_model='gpt-4o-mini',
        file_structure={
            'graph.py': 'LangGraph state machine',
            'nodes.py': 'Graph node functions',
            'state.py': 'State schema',
            'tools.py': 'Tool definitions',
            '.env.example': 'Environment variables',
            'requirements.txt': 'Dependencies'
        },
        example_imports=[
            'from langgraph.graph import StateGraph, START, END',
            'from langgraph.checkpoint.sqlite import SqliteSaver',
            'from langchain_openai import ChatOpenAI',
        ]
    ),

    'crewai': FrameworkInfo(
        name='crewai',
        display_name='CrewAI',
        docs_base_url='https://docs.crewai.com',
        sitemap_url='https://docs.crewai.com/sitemap.xml',
        package_name='crewai',
        default_model='gpt-4o-mini',
        file_structure={
            'crew.py': 'Crew definition',
            'agents.py': 'Agent definitions',
            'tasks.py': 'Task definitions',
            'tools.py': 'Tool definitions',
            '.env.example': 'Environment variables',
            'requirements.txt': 'Dependencies'
        },
        example_imports=[
            'from crewai import Agent, Task, Crew, Process',
            'from crewai_tools import tool',
        ]
    ),

    'autogen': FrameworkInfo(
        name='autogen',
        display_name='AutoGen',
        docs_base_url='https://microsoft.github.io/autogen',
        sitemap_url='https://microsoft.github.io/autogen/sitemap.xml',
        package_name='pyautogen',
        default_model='gpt-4o-mini',
        file_structure={
            'agents.py': 'Agent definitions',
            'group_chat.py': 'Group chat configuration',
            'tools.py': 'Tool definitions',
            '.env.example': 'Environment variables',
            'requirements.txt': 'Dependencies'
        },
        example_imports=[
            'from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager',
            'from autogen import config_list_from_json',
        ]
    ),
}


def get_framework(name: str) -> Optional[FrameworkInfo]:
    """Get framework info by name"""
    return FRAMEWORKS.get(name.lower().replace('-', '_').replace(' ', '_'))


def list_frameworks() -> List[str]:
    """List all supported framework names"""
    return list(FRAMEWORKS.keys())


def detect_framework(user_message: str) -> str:
    """
    Detect framework from user message

    Args:
        user_message: User's request

    Returns:
        Framework name (defaults to 'pydantic_ai')
    """
    message_lower = user_message.lower()

    for framework_name, framework_info in FRAMEWORKS.items():
        # Check for framework name or display name
        if framework_name in message_lower or framework_info.display_name.lower() in message_lower:
            return framework_name

        # Check for package name
        if framework_info.package_name in message_lower:
            return framework_name

    # Default to pydantic_ai
    return 'pydantic_ai'


# Framework-specific system prompts
FRAMEWORK_SYSTEM_PROMPTS = {
    'pydantic_ai': """
You are an expert at Pydantic AI - a Python AI agent framework.

When building agents:
- Use Agent class with appropriate model
- Define system prompts clearly
- Use @agent.tool decorators for tools
- Implement proper RunContext and dependencies
- Follow Pydantic AI best practices
- Always include proper type hints

Structure code into:
- agent.py: Main agent definition
- agent_tools.py: Tool functions
- agent_prompts.py: System prompts
- .env.example: Environment template
- requirements.txt: Dependencies
""",

    'langgraph': """
You are an expert at LangGraph - a framework for building stateful, multi-actor applications with LLMs.

When building graphs:
- Define clear StateGraph with TypedDict state
- Create nodes as functions that take state and return updates
- Use conditional edges for routing
- Implement proper checkpointing (SqliteSaver recommended)
- Handle interrupts for human-in-the-loop
- Follow LangGraph best practices

Structure code into:
- graph.py: StateGraph definition
- nodes.py: Node functions
- state.py: State schema (TypedDict)
- tools.py: Tool definitions
- .env.example: Environment template
- requirements.txt: Dependencies
""",

    'crewai': """
You are an expert at CrewAI - a framework for orchestrating role-playing, autonomous AI agents.

When building crews:
- Define Agents with clear roles and goals
- Create Tasks with specific descriptions and expected outputs
- Configure Crew with appropriate process (sequential/hierarchical)
- Use @tool decorator for custom tools
- Follow CrewAI best practices
- Implement proper agent collaboration

Structure code into:
- crew.py: Crew definition and execution
- agents.py: Agent definitions
- tasks.py: Task definitions
- tools.py: Custom tools
- .env.example: Environment template
- requirements.txt: Dependencies
""",

    'autogen': """
You are an expert at AutoGen - a framework for building LLM applications using multiple agents.

When building systems:
- Define AssistantAgent and UserProxyAgent appropriately
- Configure GroupChat for multi-agent conversations
- Set up proper LLM configuration
- Implement code execution when needed
- Use human_input_mode appropriately
- Follow AutoGen best practices

Structure code into:
- agents.py: Agent definitions
- group_chat.py: GroupChat configuration (if multi-agent)
- tools.py: Custom functions/tools
- .env.example: Environment template
- requirements.txt: Dependencies
""",
}


def get_framework_system_prompt(framework: str) -> str:
    """Get framework-specific system prompt"""
    return FRAMEWORK_SYSTEM_PROMPTS.get(framework, FRAMEWORK_SYSTEM_PROMPTS['pydantic_ai'])


# Framework-specific code templates
FRAMEWORK_TEMPLATES = {
    'pydantic_ai': {
        'agent.py': '''"""
{description}
"""
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize the agent
agent = Agent(
    OpenAIModel(os.getenv('MODEL', '{default_model}')),
    system_prompt="""{system_prompt}""",
)

# Add tools here using @agent.tool decorator

if __name__ == "__main__":
    # Run the agent
    result = agent.run_sync("Your query here")
    print(result.output)
''',
        'requirements.txt': '''pydantic-ai==1.11.1
python-dotenv
''',
        '.env.example': '''# Model configuration
MODEL={default_model}

# API Keys
OPENAI_API_KEY=your_api_key_here
'''
    },

    'langgraph': {
        'graph.py': '''"""
{description}
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from state import GraphState
from nodes import *

load_dotenv()

# Build the graph
builder = StateGraph(GraphState)

# Add nodes
builder.add_node("example_node", example_node)

# Set edges
builder.add_edge(START, "example_node")
builder.add_edge("example_node", END)

# Compile with checkpointing
memory = SqliteSaver.from_conn_string("checkpoints.db")
graph = builder.compile(checkpointer=memory)
''',
        'state.py': '''"""
Graph state schema
"""
from typing import TypedDict, Annotated, List

class GraphState(TypedDict):
    """State for the graph"""
    messages: Annotated[List[str], lambda x, y: x + y]
    # Add more state fields as needed
''',
        'nodes.py': '''"""
Graph node functions
"""
from state import GraphState

async def example_node(state: GraphState):
    """Example node function"""
    return {"messages": ["Node executed"]}
''',
        'requirements.txt': '''langgraph
langchain-openai
python-dotenv
''',
        '.env.example': '''# Model configuration
MODEL={default_model}

# API Keys
OPENAI_API_KEY=your_api_key_here
'''
    },

    'crewai': {
        'crew.py': '''"""
{description}
"""
from crewai import Crew, Process
from dotenv import load_dotenv
from agents import *
from tasks import *

load_dotenv()

# Create the crew
crew = Crew(
    agents=[example_agent],
    tasks=[example_task],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff()
    print(result)
''',
        'agents.py': '''"""
Agent definitions
"""
from crewai import Agent
import os

example_agent = Agent(
    role="Expert Assistant",
    goal="Help users with their tasks",
    backstory="""{system_prompt}""",
    verbose=True,
    allow_delegation=False
)
''',
        'tasks.py': '''"""
Task definitions
"""
from crewai import Task
from agents import example_agent

example_task = Task(
    description="Complete the user's request",
    agent=example_agent,
    expected_output="A helpful response"
)
''',
        'requirements.txt': '''crewai
python-dotenv
''',
        '.env.example': '''# Model configuration
MODEL={default_model}

# API Keys
OPENAI_API_KEY=your_api_key_here
'''
    },

    'autogen': {
        'agents.py': '''"""
{description}
"""
from autogen import AssistantAgent, UserProxyAgent
from dotenv import load_dotenv
import os

load_dotenv()

# LLM configuration
config_list = [{{
    "model": os.getenv("MODEL", "{default_model}"),
    "api_key": os.getenv("OPENAI_API_KEY")
}}]

# Create assistant agent
assistant = AssistantAgent(
    name="assistant",
    system_message="""{system_prompt}""",
    llm_config={{"config_list": config_list}}
)

# Create user proxy agent
user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={{"work_dir": "coding"}}
)

if __name__ == "__main__":
    user_proxy.initiate_chat(
        assistant,
        message="Your task here"
    )
''',
        'requirements.txt': '''pyautogen
python-dotenv
''',
        '.env.example': '''# Model configuration
MODEL={default_model}

# API Keys
OPENAI_API_KEY=your_api_key_here
'''
    }
}


def get_framework_templates(framework: str) -> Dict[str, str]:
    """Get code templates for a framework"""
    return FRAMEWORK_TEMPLATES.get(framework, FRAMEWORK_TEMPLATES['pydantic_ai'])
