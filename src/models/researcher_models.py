from pydantic import BaseModel, Field
from typing import Annotated, Literal
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from src.config import settings


class ResearcherState(BaseModel):
    """
    State model for the Researcher Agent.
    """
    messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list)
    sub_questions: list[str] = Field(default_factory=list)
    search_results: dict[str, str] = Field(default_factory=dict)
    findings: dict[str, list[dict[str, str]]] = Field(default_factory=dict)
    verified_findings: list[dict[str, str]] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)

class Plan(BaseModel):
    sub_questions: list[str] = Field(
        description="Focused, non-overlapping, self-contained search queries",
        max_length=settings.max_sub_questions,
    )

class Finding(BaseModel):
    claim: str
    source_url: str

class Extraction(BaseModel):
    findings: list[Finding]

class VerifiedFinding(BaseModel):
    sub_question: str
    claim: str
    source_url: str
    confidence: Literal["high", "medium", "low"]

class Verification(BaseModel):
    verified_findings: list[VerifiedFinding]
    open_questions: list[str]


__all__ = [
    "ResearcherState",
    "Plan",
    "Finding",
    "Extraction",
    "VerifiedFinding",
    "Verification",
]
