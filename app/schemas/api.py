"""API request models and structured error/diagnostic envelopes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.facts import FactInput


def _non_empty(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be empty")
    return value


class CheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(min_length=1)
    document_issue: str | None = None
    facts: list[FactInput] = Field(default_factory=list)
    question: str | None = None

    @field_validator("goal_id")
    @classmethod
    def _goal_not_empty(cls, value: str) -> str:
        return _non_empty(value)


class LegacyCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str = Field(min_length=1)
    document_issue: str | None = None
    facts: list[FactInput] = Field(default_factory=list)
    question: str | None = None

    @field_validator("goal")
    @classmethod
    def _goal_not_empty(cls, value: str) -> str:
        return _non_empty(value)


class CheckAllRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facts: list[FactInput] = Field(default_factory=list)


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    document_id: str | None = None
    article: str | None = None
    include_methodology: bool = False

    @field_validator("query")
    @classmethod
    def _query_not_empty(cls, value: str) -> str:
        return _non_empty(value)


class ExtractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    use_llm: bool = False
    confirm: bool = False

    @field_validator("text")
    @classmethod
    def _text_not_empty(cls, value: str) -> str:
        return _non_empty(value)


class GoalInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str
    name: str
    rule_id: str
    rule_status: str
    article: str
    page: int | None = None
    document: str
    issue: str
    quote: str
    scope: str
    requirements: list[dict[str, Any]]


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)
    detail: str | None = None
