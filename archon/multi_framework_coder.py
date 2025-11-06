"""
Multi-Framework AI Agent Coder for Archon V6

Generates AI agents for multiple frameworks: Pydantic AI, LangGraph, CrewAI, AutoGen
"""

from __future__ import annotations as _annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import logfire
import asyncio
import os

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
from supabase import Client
from typing import List, Optional

from framework_config import (
    get_framework,
    get_framework_system_prompt,
    get_framework_templates,
    detect_framework,
    FRAMEWORKS
)

load_dotenv()

llm = os.getenv('PRIMARY_MODEL', 'gpt-4o-mini')
base_url = os.getenv('BASE_URL', 'https://api.openai.com/v1')
api_key = os.getenv('LLM_API_KEY', 'no-llm-api-key-provided')
model = OpenAIModel(llm, base_url=base_url, api_key=api_key)


@dataclass
class MultiFrameworkDeps:
    """Dependencies for multi-framework coder"""
    supabase: Client
    openai_client: AsyncOpenAI
    reasoner_output: str
    framework: str = 'pydantic_ai'


async def get_embedding(text: str, openai_client: AsyncOpenAI) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536


def create_multi_framework_coder(framework: str = 'pydantic_ai') -> Agent:
    """
    Create a framework-specific coder agent

    Args:
        framework: The target framework name

    Returns:
        Configured Agent instance
    """
    framework_info = get_framework(framework)
    if not framework_info:
        framework = 'pydantic_ai'
        framework_info = get_framework(framework)

    # Get framework-specific system prompt
    base_system_prompt = get_framework_system_prompt(framework)

    system_prompt = f"""
~~ CONTEXT: ~~

You are an expert at {framework_info.display_name} - an AI agent framework.
You have access to all the documentation for {framework_info.display_name}.

{base_system_prompt}

~~ GOAL: ~~

Your only job is to help the user create an AI agent with {framework_info.display_name}.
The user will describe the AI agent they want to build, or if they don't, guide them towards doing so.
You will take their requirements, and then search through the {framework_info.display_name} documentation with the tools provided
to find all the necessary information to create the AI agent with correct code.

It's important for you to search through multiple documentation pages to get all the information you need.
Almost never stick to just one page - use RAG and the other documentation tools multiple times when you are creating
an AI agent from scratch for the user.

~~ STRUCTURE: ~~

When you build an AI agent from scratch, split the agent into these files:
{chr(10).join(f"- `{filename}`: {desc}" for filename, desc in framework_info.file_structure.items())}

~~ INSTRUCTIONS: ~~

- Don't ask the user before taking an action, just do it. Always make sure you look at the documentation with the provided tools before writing any code.
- When you first look at the documentation, always start with RAG.
  Then also always check the list of available documentation pages and retrieve the content of page(s) if it'll help.
- Always let the user know when you didn't find the answer in the documentation or the right URL - be honest.
- When starting a new AI agent build, always produce the full code for the AI agent - never tell the user to finish a tool/function.
- When refining an existing AI agent build in a conversation, just share the code changes necessary.
- Each time you respond to the user, ask them to let you know either if they need changes or the code looks good.
- Always use framework-specific best practices and patterns from the documentation.
"""

    agent = Agent(
        model,
        system_prompt=system_prompt,
        deps_type=MultiFrameworkDeps,
        retries=2
    )

    @agent.system_prompt
    def add_reasoner_output(ctx: RunContext[MultiFrameworkDeps]) -> str:
        return f"""
        \n\nAdditional thoughts/instructions from the reasoner LLM.
        This scope includes documentation pages for you to search as well:
        {ctx.deps.reasoner_output}

        Target Framework: {ctx.deps.framework}
        """

    @agent.tool
    async def retrieve_relevant_documentation(ctx: RunContext[MultiFrameworkDeps], user_query: str) -> str:
        """
        Retrieve relevant documentation chunks based on the query with RAG.
        Automatically filters for the target framework.

        Args:
            ctx: The context including the Supabase client and framework
            user_query: The user's question or query

        Returns:
            A formatted string containing the top 5 most relevant documentation chunks
        """
        try:
            # Get the embedding for the query
            query_embedding = await get_embedding(user_query, ctx.deps.openai_client)

            # Query Supabase for relevant documents (filtered by framework)
            result = ctx.deps.supabase.rpc(
                'match_site_pages',
                {
                    'query_embedding': query_embedding,
                    'match_count': 5,
                    'filter': {'source': f'{ctx.deps.framework}_docs'}
                }
            ).execute()

            if not result.data:
                return f"No relevant documentation found for {ctx.deps.framework}."

            # Format the results
            formatted_chunks = []
            for doc in result.data:
                chunk_text = f"""
# {doc['title']}

{doc['content']}
"""
                formatted_chunks.append(chunk_text)

            # Join all chunks with a separator
            return "\n\n---\n\n".join(formatted_chunks)

        except Exception as e:
            print(f"Error retrieving documentation: {e}")
            return f"Error retrieving documentation: {str(e)}"

    @agent.tool
    async def list_documentation_pages(ctx: RunContext[MultiFrameworkDeps]) -> List[str]:
        """
        Retrieve a list of all available documentation pages for the target framework.

        Returns:
            List[str]: List of unique URLs for all documentation pages
        """
        try:
            # Query Supabase for unique URLs where source matches framework
            result = ctx.deps.supabase.from_('site_pages') \
                .select('url') \
                .eq('metadata->>source', f'{ctx.deps.framework}_docs') \
                .execute()

            if not result.data:
                return []

            # Extract unique URLs
            urls = sorted(set(doc['url'] for doc in result.data))
            return urls

        except Exception as e:
            print(f"Error retrieving documentation pages: {e}")
            return []

    @agent.tool
    async def get_page_content(ctx: RunContext[MultiFrameworkDeps], url: str) -> str:
        """
        Retrieve the full content of a specific documentation page by combining all its chunks.

        Args:
            ctx: The context including the Supabase client
            url: The URL of the page to retrieve

        Returns:
            str: The complete page content with all chunks combined in order
        """
        try:
            # Query Supabase for all chunks of this URL, ordered by chunk_number
            result = ctx.deps.supabase.from_('site_pages') \
                .select('title, content, chunk_number') \
                .eq('url', url) \
                .eq('metadata->>source', f'{ctx.deps.framework}_docs') \
                .order('chunk_number') \
                .execute()

            if not result.data:
                return f"No content found for URL: {url}"

            # Format the page with its title and all chunks
            page_title = result.data[0]['title'].split(' - ')[0]  # Get the main title
            formatted_content = [f"# {page_title}\n"]

            # Add each chunk's content
            for chunk in result.data:
                formatted_content.append(chunk['content'])

            # Join everything together
            return "\n\n".join(formatted_content)

        except Exception as e:
            print(f"Error retrieving page content: {e}")
            return f"Error retrieving page content: {str(e)}"

    @agent.tool
    async def get_framework_template(ctx: RunContext[MultiFrameworkDeps], file_name: str) -> str:
        """
        Get a code template for a specific file in the target framework.

        Args:
            ctx: The context
            file_name: Name of the file (e.g., 'agent.py', 'requirements.txt')

        Returns:
            str: The template code or empty string if not available
        """
        templates = get_framework_templates(ctx.deps.framework)
        return templates.get(file_name, f"No template available for {file_name}")

    @agent.tool
    async def list_available_templates(ctx: RunContext[MultiFrameworkDeps]) -> List[str]:
        """
        List all available code templates for the target framework.

        Returns:
            List[str]: List of template file names
        """
        templates = get_framework_templates(ctx.deps.framework)
        return list(templates.keys())

    return agent


# Helper function to create appropriate coder based on framework
def get_coder_for_framework(framework: str) -> Agent:
    """
    Get a coder agent configured for a specific framework

    Args:
        framework: Framework name (pydantic_ai, langgraph, crewai, autogen)

    Returns:
        Configured Agent instance
    """
    return create_multi_framework_coder(framework)


# Helper to list available frameworks
async def list_documentation_pages_helper(supabase: Client, framework: str = 'pydantic_ai') -> List[str]:
    """
    Helper function to retrieve documentation pages for a framework.
    Used by the graph to list available pages.

    Args:
        supabase: Supabase client
        framework: Framework name

    Returns:
        List of documentation page URLs
    """
    try:
        result = supabase.from_('site_pages') \
            .select('url') \
            .eq('metadata->>source', f'{framework}_docs') \
            .execute()

        if not result.data:
            return []

        urls = sorted(set(doc['url'] for doc in result.data))
        return urls

    except Exception as e:
        print(f"Error retrieving documentation pages: {e}")
        return []
