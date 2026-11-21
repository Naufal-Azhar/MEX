"""Result, diagnostic, citation, and reasoning-trace models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.facts import FactConflict, MissingFact
from app.schemas.rules import EvidenceSpan, RuleSource, RuleStatus


class TruthValue(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class ExternalStatus(str, Enum):
    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class DiagnosticCode(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    CONFLICTING_INPUT = "CONFLICTING_INPUT"
    SOURCE_MISSING = "SOURCE_MISSING"
    VERSION_MISMATCH = "VERSION_MISMATCH"
    UNSUPPORTED_GOAL = "UNSUPPORTED_GOAL"
    RULE_NOT_APPROVED = "RULE_NOT_APPROVED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class Diagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: DiagnosticCode
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    rule_id: str | None = None


class ConditionEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expression: str
    status: TruthValue
    left_value: Any = None
    right_value: Any = None
    unit: str | None = None
    detail: str | None = None


class RuleEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    rule_name: str
    goal: str
    status: TruthValue
    rule_status: RuleStatus | None = None
    applicability: TruthValue = TruthValue.TRUE
    applicable: bool = True
    conclusion_value: Any = None
    applicability_conditions: list[ConditionEvaluation] = Field(default_factory=list)
    conditions: list[ConditionEvaluation] = Field(default_factory=list)
    missing_facts: list[MissingFact] = Field(default_factory=list)
    source: RuleSource | None = None
    notes: list[str] = Field(default_factory=list)
    subgoal_results: list["GoalResult"] = Field(default_factory=list)


class TraceNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    goal: str
    kind: str = "goal"
    status: TruthValue
    value: Any = None
    rule_id: str | None = None
    rule_name: str | None = None
    expression: str | None = None
    source: RuleSource | None = None
    conditions: list[ConditionEvaluation] = Field(default_factory=list)
    children: list["TraceNode"] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class GoalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str
    status: TruthValue
    value: Any = None
    rule_id: str | None = None
    trace: TraceNode | None = None
    missing_facts: list[MissingFact] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    evaluations: list[RuleEvaluation] = Field(default_factory=list)
    not_applicable: bool = False


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    document: str
    issue: str
    article: str
    page: int | None = None
    quote: str
    verified: bool = False
    evidence_span: EvidenceSpan | None = None


class CheckReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str
    status: ExternalStatus
    internal_status: TruthValue | None = None
    value: Any = None
    scope: str
    explanation: str
    rule_id: str | None = None
    rule_name: str | None = None
    rule_status: RuleStatus | None = None
    validation_warning: str | None = None
    source: RuleSource | None = None
    applicability_conditions: list[ConditionEvaluation] = Field(default_factory=list)
    conditions: list[ConditionEvaluation] = Field(default_factory=list)
    missing_facts: list[MissingFact] = Field(default_factory=list)
    conflicts: list[FactConflict] = Field(default_factory=list)
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    rules_evaluated: list[RuleEvaluation] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    facts_used: dict[str, dict[str, Any]] = Field(default_factory=dict)
    proof_trace: TraceNode | None = None
    regulation: dict[str, str] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    rule_conflict: bool = False
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def goal(self) -> str:
        return self.goal_id

    @property
    def trace(self) -> TraceNode | None:
        return self.proof_trace

    @property
    def conflict(self) -> bool:
        return self.rule_conflict


class RetrievalHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    document_type: str | None = None
    article: str | None = None
    page: int | None = None
    text: str
    score: float
    chunk_id: str
