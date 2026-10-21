import json
import re
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable, RunnableLambda
from langgraph.graph import END, START, StateGraph
from src.config import settings
from src.logger import get_logger
from src.models import Extraction, Plan, ResearcherState, Verification
from src.prompts.researcher import (
    MAX_SUB_QUESTIONS,
    PLAN_SYSTEM_PROMPT,
    REPORT_SYSTEM_PROMPT,
    RESEARCH_SYSTEM_PROMPT,
    VERIFY_SYSTEM_PROMPT,
)
from src.tools import duckduckgo_web_search, read_contents_from_webpage
from src.utils.output import message_content_to_text

logger = get_logger(__name__)
_PLAN_LOG_PATH = Path("output/plan_node_log.jsonl")
_URL_LINE = re.compile(r"^URL: (\S+)$", re.MULTILINE)


def _task_description(state: ResearcherState) -> str:
    for message in reversed(state.messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def _extract_urls(search_text: str, limit: int) -> list[str]:
    return _URL_LINE.findall(search_text)[:limit]


def _log_plan(query: str, sub_questions: list[str]) -> None:
    """Append the query and the sub-questions the planner derived from it."""
    _PLAN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "sub_questions": sub_questions,
    }
    with _PLAN_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def build_deep_researcher_graph(model: BaseChatModel) -> Runnable:
    """Compile the researcher as a Plan -> Search -> Research -> Verify -> Report graph."""
    planner = model.with_structured_output(Plan)
    extractor = model.with_structured_output(Extraction)
    verifier = model.with_structured_output(Verification)

    async def plan(state: ResearcherState) -> dict:
        query = _task_description(state)
        result = await planner.ainvoke(
            [("system", PLAN_SYSTEM_PROMPT), ("human", query)]
        )
        sub_questions = result.sub_questions[:MAX_SUB_QUESTIONS] or [query]
        logger.info("Planner questions: %s", json.dumps(sub_questions))
        _log_plan(query, sub_questions)
        return {"sub_questions": sub_questions}

    async def search(state: ResearcherState) -> dict:
        search_results = {
            sub_question: await duckduckgo_web_search.ainvoke(
                {
                    "query": sub_question,
                    "max_results": settings.sources_per_question,
                }
            )
            for sub_question in state.sub_questions
        }
        return {"search_results": search_results}

    async def research(state: ResearcherState) -> dict:
        findings: dict[str, list[dict[str, str]]] = {}
        for sub_question in state.sub_questions:
            urls = _extract_urls(
                state.search_results.get(sub_question, ""),
                settings.sources_per_question,
            )
            pages = [
                await read_contents_from_webpage.ainvoke({"url": url})
                for url in urls
            ]
            for url, page in zip(urls, pages):
                logger.info("Read response for %s: %s", url, page)
            page_text = "\n\n---\n\n".join(pages)
            if not page_text.strip():
                findings[sub_question] = []
                continue

            extraction = await extractor.ainvoke(
                [
                    ("system", RESEARCH_SYSTEM_PROMPT),
                    (
                        "human",
                        f"Sub-question: {sub_question}\n\nPage text:\n{page_text}",
                    ),
                ]
            )
            findings[sub_question] = [
                item.model_dump() for item in extraction.findings
            ]
        return {"findings": findings}

    async def verify(state: ResearcherState) -> dict:
        findings_blob = "\n".join(
            f"Sub-question: {sub_question}\n"
            + "\n".join(
                f"- {item['claim']} (Source: {item['source_url']})"
                for item in items
            )
            for sub_question, items in state.findings.items()
        )
        verification = await verifier.ainvoke(
            [
                ("system", VERIFY_SYSTEM_PROMPT),
                ("human", findings_blob or "No findings were collected."),
            ]
        )
        return {
            "verified_findings": [
                item.model_dump() for item in verification.verified_findings
            ],
            "open_questions": verification.open_questions,
        }

    async def report(state: ResearcherState) -> dict:
        verified_blob = "\n".join(
            f"- [{item['sub_question']}] {item['claim']} "
            f"(Source: {item['source_url']}, Confidence: {item['confidence']})"
            for item in state.verified_findings
        )
        open_blob = (
            "\n".join(f"- {question}" for question in state.open_questions)
            or "None"
        )
        human_prompt = (
            f"Original query: {_task_description(state)}\n\n"
            f"Verified findings:\n{verified_blob or 'None'}\n\n"
            f"Open questions:\n{open_blob}"
        )
        response = await model.ainvoke(
            [("system", REPORT_SYSTEM_PROMPT), ("human", human_prompt)]
        )
        return {
            "messages": [
                AIMessage(content=message_content_to_text(response.content))
            ]
        }

    graph = StateGraph(ResearcherState)
    graph.add_node("plan", plan)
    graph.add_node("search", search)
    graph.add_node("research", research)
    graph.add_node("verify", verify)
    graph.add_node("report", report)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "search")
    graph.add_edge("search", "research")
    graph.add_edge("research", "verify")
    graph.add_edge("verify", "report")
    graph.add_edge("report", END)
    compiled_graph = graph.compile()

    async def _run(state: dict) -> dict:
        result = await compiled_graph.ainvoke({"messages": state["messages"]})
        return {"messages": result["messages"]}

    return RunnableLambda(_run)
