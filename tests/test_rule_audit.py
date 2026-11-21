"""Regression checks for the LTCS 2 kg Heat Hazard rule audit."""

from __future__ import annotations

import pytest

from app.expert_system.backward_chaining import BackwardChainingEngine
from app.expert_system.knowledge_base import KnowledgeBase
from app.schemas.facts import Fact, FactOrigin, FactStore
from app.schemas.results import TruthValue


def _store(heat_hazard_declared: bool) -> FactStore:
    store = FactStore()
    for name, value in (
        ("session_type", "Q"),
        ("session_category", "LTCS"),
        ("heat_hazard_declared", heat_hazard_declared),
        ("competition_heat_hazard_declared", True),
    ):
        store.add(Fact(name=name, value=value, origin=FactOrigin.USER))
    return store


def test_ltcs_without_session_heat_hazard_gets_2kg() -> None:
    result = BackwardChainingEngine(KnowledgeBase.from_file(), _store(False)).prove(
        "heat_hazard_mass_increase"
    )
    assert result.status is TruthValue.TRUE
    assert result.value == pytest.approx(2.0)


def test_ltcs_with_session_heat_hazard_is_not_assumed_2kg() -> None:
    result = BackwardChainingEngine(KnowledgeBase.from_file(), _store(True)).prove(
        "heat_hazard_mass_increase"
    )
    assert result.status is TruthValue.UNKNOWN
