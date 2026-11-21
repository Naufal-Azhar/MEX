"""Fact representation, origins, conflicts, and the in-memory fact store."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FactOrigin(str, Enum):
    USER = "user"
    MEASUREMENT = "measurement"
    DERIVED = "derived"
    DOCUMENT = "document"


class Fact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: Any
    unit: str | None = None
    origin: FactOrigin = FactOrigin.USER
    note: str | None = None

    @field_validator("name")
    @classmethod
    def _name_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("fact name must not be empty")
        return value.strip()


class FactInput(BaseModel):
    """Shape accepted from API/UI input."""

    model_config = ConfigDict(extra="forbid")

    name: str
    value: Any
    unit: str | None = None
    origin: FactOrigin = FactOrigin.USER
    note: str | None = None


class FactConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    existing_value: Any
    existing_unit: str | None = None
    existing_origin: FactOrigin | None = None
    new_value: Any
    new_unit: str | None = None
    new_origin: FactOrigin | None = None


class FactConflictError(ValueError):
    code = "CONFLICTING_INPUT"

    def __init__(self, conflicts: list[FactConflict]) -> None:
        self.conflicts = conflicts
        names = ", ".join(sorted({item.name for item in conflicts}))
        super().__init__(f"Conflicting facts for: {names}")


class FactStore:
    """A flat store of facts. Duplicate identical facts are merged; conflicts raise."""

    def __init__(self) -> None:
        self._facts: dict[str, Fact] = {}

    def add(self, fact: Fact) -> None:
        if fact.name in self._facts:
            existing = self._facts[fact.name]
            if existing.value != fact.value or (existing.unit or None) != (fact.unit or None):
                raise FactConflictError(
                    [
                        FactConflict(
                            name=fact.name,
                            existing_value=existing.value,
                            existing_unit=existing.unit,
                            existing_origin=existing.origin,
                            new_value=fact.value,
                            new_unit=fact.unit,
                            new_origin=fact.origin,
                        )
                    ]
                )
            return
        self._facts[fact.name] = fact

    def add_many(self, facts: list[Fact]) -> None:
        for fact in facts:
            self.add(fact)

    def get(self, name: str) -> Fact | None:
        return self._facts.get(name)

    def has(self, name: str) -> bool:
        return name in self._facts

    def all(self) -> dict[str, Fact]:
        return dict(self._facts)

    def names(self) -> list[str]:
        return sorted(self._facts)

    def __len__(self) -> int:
        return len(self._facts)

    def __contains__(self, name: str) -> bool:
        return name in self._facts

    def as_public_dict(self) -> dict[str, dict[str, Any]]:
        return {
            name: {
                "value": fact.value,
                "unit": fact.unit,
                "origin": fact.origin.value,
                "note": fact.note,
            }
            for name, fact in self._facts.items()
        }


class MissingFact(BaseModel):
    fact: str
    expected_unit: str | None = None
    rule_id: str | None = None
    reason: str
    source_article: str | None = None


class ExtractedFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: Any
    unit: str | None = None
    evidence: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facts: list[ExtractedFact] = Field(default_factory=list)
    rejected: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    provider: str = "deterministic"
    raw_output: str | None = None
    requires_confirmation: bool = True
