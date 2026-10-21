from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from fastapi import Request
from langgraph.checkpoint.memory import MemorySaver
from src.models.chat import ChatRequestModel
from src.prompts import (
    Code_Review_And_Enhancement_AGENT_PROMPT,
    DEEP_AGENT_PROMPT,
    System_DESIGN_AGENT_PROMPT,
)
from src.tools import duckduckgo_web_search, read_contents_from_webpage

from .researcher_graph_agent import build_deep_researcher_graph


@dataclass
class AgentSetup:
    agent: Any
    subagent_names: frozenset[str]
    subagent_tools: dict[str, list[str]]


@dataclass
class ChatRequestContext:
    request: ChatRequestModel
    agent_setup: AgentSetup


def create_agent_setup(llm_model: Any) -> AgentSetup:
    """Set up the deep agent."""
    skills_sources = ["/skills/code-reviewer"]

    subagents = [
        {
            "name": "deep_researcher_agent",
            "description": (
                "Plans research, finds sources, scrapes web pages, and creates "
                "detailed reports"
            ),
            "runnable": build_deep_researcher_graph(llm_model),
        },
        {
            "name": "system_design_agent",
            "description": (
                "Lays out different approaches and tech stacks for solving a "
                "problem, with pros and cons for each approach"
            ),
            "system_prompt": System_DESIGN_AGENT_PROMPT,
            "tools": [duckduckgo_web_search, read_contents_from_webpage],
        },
        {
            "name": "code_review_and_enhancement_agent",
            "description": (
                "Reviews and enhances code, providing feedback and suggestions "
                "for improvement"
            ),
            "system_prompt": Code_Review_And_Enhancement_AGENT_PROMPT,
            "tools": [duckduckgo_web_search, read_contents_from_webpage],
            "skills": skills_sources,
        },
    ]
    project_root = Path(__file__).resolve().parents[2]

    agent = create_deep_agent(
        model=llm_model,
        tools=[],
        subagents=subagents,
        system_prompt=DEEP_AGENT_PROMPT,
        checkpointer=MemorySaver(),
        backend=FilesystemBackend(root_dir=project_root, virtual_mode=True),
    )
    subagent_tools = {
        item["name"]: [tool.name for tool in item.get("tools", [])]
        for item in subagents
    }
    return AgentSetup(
        agent=agent,
        subagent_names=frozenset(subagent_tools),
        subagent_tools=subagent_tools,
    )


def get_chat_request_context(
    chat_request: ChatRequestModel,
    http_request: Request,
) -> ChatRequestContext:
    setups: dict[str, AgentSetup] = http_request.app.state.agent_setups
    setup = setups.get(chat_request.provider)
    if setup is None:
        setup = setups.get("gemini")
    return ChatRequestContext(request=chat_request, agent_setup=setup)
