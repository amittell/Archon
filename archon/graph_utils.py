"""
Common utilities for Archon graph workflows (V4 and V6).

This module provides shared helper functions to eliminate code duplication
between archon_graph_v4.py and archon_graph_v6.py.
"""

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from langgraph.config import get_stream_writer
from typing import List
from archon.config import ArchonConfig


def create_standard_agents(config: ArchonConfig):
    """
    Create standard agents used across all workflow versions.

    Args:
        config: ArchonConfig instance with all configuration

    Returns:
        Tuple of (reasoner, primary_model, router_agent, end_conversation_agent)
    """
    reasoner = Agent(
        OpenAIModel(config.reasoner_model, base_url=config.base_url, api_key=config.api_key),
        system_prompt='You are an expert at coding AI agents and defining the scope for doing so. '
                      'You support multiple frameworks including Pydantic AI, LangGraph, CrewAI, and AutoGen.',
    )

    primary_model = OpenAIModel(config.primary_model, base_url=config.base_url, api_key=config.api_key)

    router_agent = Agent(
        primary_model,
        system_prompt='Your job is to route the user message either to the end of the conversation '
                      'or to continue coding the AI agent.',
    )

    end_conversation_agent = Agent(
        primary_model,
        system_prompt='Your job is to end a conversation for creating an AI agent by giving instructions '
                      'for how to execute the agent and then saying a nice goodbye to the user.',
    )

    return reasoner, primary_model, router_agent, end_conversation_agent


def load_message_history(messages: List[bytes]) -> List[ModelMessage]:
    """
    Load and deserialize message history from state.

    Args:
        messages: List of serialized message bytes from state

    Returns:
        List of deserialized ModelMessage objects
    """
    message_history: List[ModelMessage] = []
    for message_row in messages:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))
    return message_history


async def run_agent_with_streaming(agent, user_message, is_ollama: bool, **kwargs):
    """
    Run an agent with streaming support, handling Ollama vs OpenAI differences.

    Args:
        agent: The Pydantic AI agent to run
        user_message: The user message to process
        is_ollama: Whether using Ollama (local models)
        **kwargs: Additional arguments to pass to agent.run() or agent.run_stream()

    Returns:
        Agent result with output and new messages
    """
    if is_ollama:
        writer = get_stream_writer()
        result = await agent.run(user_message, **kwargs)
        writer(result.output)
    else:
        async with agent.run_stream(user_message, **kwargs) as result:
            async for chunk in result.stream_text(delta=True):
                writer = get_stream_writer()
                writer(chunk)

    return result
