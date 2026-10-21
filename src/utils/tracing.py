import json
from src.logger import get_logger

logger = get_logger(__name__)

def _current_turn_messages(messages: list) -> list:
    """Return messages produced since the most recent user message."""
    for index in range(len(messages) -1, -1, -1):
        if getattr(messages [index], "type", "") == "human":
            return messages [index:]
    return messages

def build_execution_info(
    result: dict,
    thread_id: str,
    subagent_names: frozenset[str],
    subagent_tools: dict[str, list[str]] | None = None,
) -> dict:
    """Build execution metadata for the current turn."""
    subagent_tools = subagent_tools or {}
    subagents_used: set [str] = set()
    tools_called: set[str] = set()
    for message in _current_turn_messages(result["messages"]):
        for tool_call in getattr(message, "tool_calls", []):
            name = tool_call.get("name", "")
            arguments = tool_call.get("args", {})
            if name == "task":
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                if not isinstance(arguments, dict):
                    arguments = {}

            subagent_name = arguments.get("subagent_type")
            if subagent_name:
                subagents_used.add(subagent_name)
            elif name in subagent_names:
                subagents_used.add(name)
            elif name:
                tools_called.add(name)
    return {
        "thread_id": thread_id,
        "tools_called": sorted(tools_called),
        "sub_agents_called": [
            {"subagent_name": name, "subagent_tools": subagent_tools.get(name, [])}
            for name in sorted(subagents_used)
        ],
    }


def print_execution_trace(
    result: dict,
    thread_id: str,
    subagent_names: frozenset[str],
    subagent_tools: dict[str, list[str]] | None = None,
) -> dict:
    """Print, log, and return execution metadata for the current turn."""
    info = build_execution_info(result, thread_id, subagent_names, subagent_tools)
    logger.info("Execution Tace:")
    logger.info(
        "Sub-Agents Invoked: %s",
        info["sub_agents_called"] or ["None (answered directly)"],
    )
    logger.info("Tools Called: %s", info["tools_called"] or ["None"])
    logger.info("info: %s", json.dumps(info))
    return info