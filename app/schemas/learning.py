"""Schemas for grounded learning answers."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import TelemetryAnalysisReport


class QuestionType(str, Enum):
    THEORY = "theory"
    TELEMETRY_CASE = "telemetry_case"
    REGULATION = "regulation"
    UNSUPPORTED = "unsupported"


class GenerationStatus(str, Enum):
    GENERATED = "generated"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"
    ERROR = "error"


class CitationRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref_id: str
    document_id: str
    article: str | None = None
    quote: str
    verified: bool
    semantic_support_verified: bool = False


class GroundedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    question_type: QuestionType
    level: str
    observed_facts: list[str] = Field(default_factory=list)
    rule_based_findings: list[str] = Field(default_factory=list)
    potential_explanations: list[str] = Field(default_factory=list)
    theory: list[str] = Field(default_factory=list)
    citation_refs: list[CitationRef] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    suggested_learning_questions: list[str] = Field(default_factory=list)
    generation_status: GenerationStatus
    generation_provenance: dict[str, Any] = Field(default_factory=dict)
    analysis: TelemetryAnalysisReport | None = None


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    level: Literal["beginner", "engineering"] = "beginner"
    lap_a_id: str | None = None
    lap_b_id: str | None = None
    top_k: int = Field(default=3, ge=1, le=10)
