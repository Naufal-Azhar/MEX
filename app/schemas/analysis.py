"""Schemas for evidence-gated telemetry learning analysis."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.results import TraceNode
from app.schemas.rules import RuleSource
from app.schemas.telemetry import (
    BrakeOnsetComparison,
    DataQuality,
    FeatureValue,
    LapIdentity,
    LapProvenance,
    SpeedDeltaSummary,
)


class AnalysisStatus(str, Enum):
    OBSERVED = "OBSERVED"
    SUPPORTED_INTERPRETATION = "SUPPORTED_INTERPRETATION"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNSUPPORTED = "UNSUPPORTED"
    ERROR = "ERROR"


class GateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    notes: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    document_id: str
    article: str
    quote: str
    quote_found: bool
    semantic_support_verified: bool = False


class AnalysisFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    goal: str
    description: str
    status: AnalysisStatus
    rule_status: str
    fact_refs: list[str] = Field(default_factory=list)
    source: RuleSource | None = None
    notes: list[str] = Field(default_factory=list)


class TelemetryAnalysisReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str
    data_kind: str
    lap_a: LapIdentity
    lap_b: LapIdentity
    provenance: dict[str, LapProvenance]
    quality: dict[str, DataQuality]
    observed_facts: list[FeatureValue] = Field(default_factory=list)
    findings: list[AnalysisFinding] = Field(default_factory=list)
    trace: list[TraceNode] = Field(default_factory=list)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    speed_delta: SpeedDeltaSummary | None = None
    brake_onset_comparisons: list[BrakeOnsetComparison] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    data_gate: GateResult
    knowledge_gate: GateResult
    engineering_interpretation_status: AnalysisStatus
    generation_status: str = "not_run"
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TelemetryAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str | None = Field(default=None, max_length=100)
    lap_a_id: str = Field(min_length=1, max_length=100)
    lap_b_id: str = Field(min_length=1, max_length=100)
    segment_start_m: float | None = None
    segment_end_m: float | None = None
    question: str | None = Field(default=None, max_length=2000)
    level: Literal["beginner", "engineering"] = "beginner"

    @model_validator(mode="after")
    def _segment_pair(self) -> "TelemetryAnalyzeRequest":
        if (self.segment_start_m is None) != (self.segment_end_m is None):
            raise ValueError("segment_start_m and segment_end_m must be provided together")
        if (
            self.segment_start_m is not None
            and self.segment_end_m is not None
            and self.segment_end_m <= self.segment_start_m
        ):
            raise ValueError("segment_end_m must be greater than segment_start_m")
        return self
