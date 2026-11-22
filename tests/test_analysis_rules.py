"""Tests for the prototype telemetry ruleset, evidence gates and API wiring."""

from __future__ import annotations

import copy

import pytest
from fastapi.testclient import TestClient

from app.expert_system.knowledge_base import KnowledgeBase
from app.learning.evidence_gate import evaluate_data_gate, evaluate_knowledge_gate
from app.learning.service import TELEMETRY_RULES_PATH, TelemetryLearningService, build_facts
from app.main import app
from app.schemas.analysis import AnalysisStatus


@pytest.fixture(scope="module")
def learning() -> TelemetryLearningService:
    return TelemetryLearningService.default()


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_telemetry_ruleset_is_draft_only(learning: TelemetryLearningService) -> None:
    assert len(learning.kb.all_rules()) == 8
    assert all(rule.status.value == "draft" for rule in learning.kb.all_rules())
    assert len(learning.kb.goals()) == 8


def test_draft_rules_are_hidden_by_default() -> None:
    kb = KnowledgeBase.from_file(TELEMETRY_RULES_PATH)
    assert kb.goals() == []


def test_regulation_kb_unchanged() -> None:
    kb = KnowledgeBase.from_file()
    assert len(kb.all_rules()) == 13
    assert len(kb.goals()) == 9
    boolean_goals = {
        rule.goal for rule in kb.all_rules() if rule.conclusion.kind == "boolean"
    }
    assert len(boolean_goals) == 5


def test_real_analysis_observational_findings(learning: TelemetryLearningService) -> None:
    report = learning.analyze("VER-Q-14", "NOR-Q-16")
    by_goal = {finding.goal: finding for finding in report.findings}

    assert by_goal["speed_comparison_available"].status is AnalysisStatus.OBSERVED
    assert by_goal["speed_profile_difference_observed"].status is AnalysisStatus.OBSERVED
    assert by_goal["relative_brake_onset_difference_observed"].status is AnalysisStatus.OBSERVED
    assert by_goal["braking_dynamics_learning_topic_relevant"].status is AnalysisStatus.OBSERVED
    assert by_goal["withhold_supported_engineering_interpretation"].status is AnalysisStatus.INSUFFICIENT_DATA
    assert report.engineering_interpretation_status is AnalysisStatus.INSUFFICIENT_DATA


def test_guardrails_not_applicable_without_question(learning: TelemetryLearningService) -> None:
    report = learning.analyze("VER-Q-14", "NOR-Q-16")
    by_goal = {finding.goal: finding for finding in report.findings}
    assert by_goal["insufficient_evidence_for_understeer_diagnosis"].status is AnalysisStatus.NOT_APPLICABLE
    assert by_goal["insufficient_evidence_for_drag_cause"].status is AnalysisStatus.NOT_APPLICABLE


def test_understeer_question_triggers_guardrail(learning: TelemetryLearningService) -> None:
    report = learning.analyze("VER-Q-14", "NOR-Q-16", question="Why did the car understeer?")
    by_goal = {finding.goal: finding for finding in report.findings}
    assert by_goal["insufficient_evidence_for_understeer_diagnosis"].status is AnalysisStatus.INSUFFICIENT_DATA
    assert any("understeer" in item for item in report.missing_data)


def test_gates_pass_on_real_fixture(learning: TelemetryLearningService) -> None:
    report = learning.analyze("VER-Q-14", "NOR-Q-16")
    assert report.data_gate.passed, report.data_gate.missing
    assert report.knowledge_gate.passed, report.knowledge_gate.missing
    assert report.evidence
    assert all(item.quote_found for item in report.evidence)
    assert all(not item.semantic_support_verified for item in report.evidence)


def test_data_gate_rejects_missing_channel(learning: TelemetryLearningService) -> None:
    pair = learning.telemetry.analyze("VER-Q-14", "NOR-Q-16")
    broken = copy.deepcopy(pair)
    broken.quality["VER-Q-14"].missing_channels = ["speed"]
    gate = evaluate_data_gate(broken)
    assert not gate.passed
    assert any("kanal data tidak tersedia" in item for item in gate.missing)


def test_deleted_lap_withholds_observations(learning: TelemetryLearningService) -> None:
    report = learning.analyze("VER-Q-14", "TSU-Q-16")
    assert not report.data_gate.passed
    assert any("dibatalkan" in item for item in report.data_gate.missing)
    assert all(finding.status is not AnalysisStatus.OBSERVED for finding in report.findings)


def test_invalid_distance_lap_is_rejected(learning: TelemetryLearningService) -> None:
    from app.race_data.validation import LapValidationError

    with pytest.raises(LapValidationError):
        learning.analyze("VER-Q-14", "GAS-Q-4")


def test_medium_compound_lap_is_available(learning: TelemetryLearningService) -> None:
    report = learning.analyze("VER-Q-14", "HAM-Q-2")
    assert report.lap_b.compound == "MEDIUM"


def test_knowledge_gate_rejects_missing_quote() -> None:
    kb = KnowledgeBase.from_file(TELEMETRY_RULES_PATH, include_draft=True)
    rule = kb.all_rules()[0]
    gate, evidence = evaluate_knowledge_gate([(rule, rule.goal)], ["does-not-exist.md"])
    assert not gate.passed
    assert evidence[0].quote_found is False


def test_facts_include_uncertainty_flag(learning: TelemetryLearningService) -> None:
    pair = learning.telemetry.analyze("VER-Q-14", "NOR-Q-16")
    facts = build_facts(pair)
    assert facts["laps_aligned"] is True
    assert facts["onset_delta_exceeds_uncertainty"] is True
    assert facts["scientific_evidence_missing_or_unverified"] is True


def test_report_trace_covers_all_goals(learning: TelemetryLearningService) -> None:
    report = learning.analyze("VER-Q-14", "NOR-Q-16")
    assert len(report.trace) == len(report.findings) == 8


def test_api_races_and_laps(client: TestClient) -> None:
    races = client.get("/v1/races")
    assert races.status_code == 200
    payload = races.json()
    assert payload[0]["session_id"] == "2025-abu-dhabi-qualifying"
    assert payload[0]["lap_count"] == 7
    assert payload[1]["session_id"] == "2025-british-gp-qualifying"
    assert payload[1]["lap_count"] == 2

    laps = client.get("/v1/races/2025-abu-dhabi-qualifying/laps")
    assert laps.status_code == 200
    assert {item["lap_id"] for item in laps.json()} == {
        "VER-Q-14",
        "NOR-Q-16",
        "PIA-Q-16",
        "LEC-Q-17",
        "HAM-Q-2",
        "GAS-Q-4",
        "TSU-Q-16",
    }

    british_laps = client.get("/v1/races/2025-british-gp-qualifying/laps")
    assert british_laps.status_code == 200
    assert {item["lap_id"] for item in british_laps.json()} == {
        "VER-GBR-Q-17",
        "NOR-GBR-Q-19",
    }

    missing = client.get("/v1/races/unknown/laps")
    assert missing.status_code == 404


def test_api_telemetry_analyze_second_session(client: TestClient) -> None:
    response = client.post(
        "/v1/telemetry/analyze",
        json={
            "session_id": "2025-british-gp-qualifying",
            "lap_a_id": "VER-GBR-Q-17",
            "lap_b_id": "NOR-GBR-Q-19",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_gate"]["passed"] is True
    assert len(payload["findings"]) == 8
    assert payload["lap_a"]["session"] == "2025 British Grand Prix Qualifying"


def test_api_telemetry_analyze(client: TestClient) -> None:
    response = client.post(
        "/v1/telemetry/analyze",
        json={"lap_a_id": "VER-Q-14", "lap_b_id": "NOR-Q-16"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_kind"] == "recorded_public_fixture"
    assert len(payload["findings"]) == 8
    assert payload["generation_status"] == "not_run"
    assert payload["data_gate"]["passed"] is True


def test_api_telemetry_analyze_unknown_lap(client: TestClient) -> None:
    response = client.post(
        "/v1/telemetry/analyze",
        json={"lap_a_id": "missing", "lap_b_id": "NOR-Q-16"},
    )
    assert response.status_code == 422


def test_api_telemetry_analyze_invalid_segment(client: TestClient) -> None:
    response = client.post(
        "/v1/telemetry/analyze",
        json={
            "lap_a_id": "VER-Q-14",
            "lap_b_id": "NOR-Q-16",
            "segment_start_m": 500,
            "segment_end_m": 100,
        },
    )
    assert response.status_code == 422
