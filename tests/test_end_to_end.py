import json

import pytest
from fastapi.testclient import TestClient

from app.config import DATASETS_DIR
from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def _cases():
    cases = []
    for name in ("development_cases.json", "heldout_cases.json"):
        cases.extend(json.loads((DATASETS_DIR / name).read_text(encoding="utf-8"))["cases"])
    expected = {
        item["case_id"]: item
        for item in json.loads((DATASETS_DIR / "expected_results.json").read_text(encoding="utf-8"))["results"]
    }
    return [(case, expected[case["case_id"]]) for case in cases]


@pytest.mark.parametrize("case,expectation", _cases(), ids=[case["case_id"] for case, _ in _cases()])
def test_dataset_case(client, case, expectation):
    response = client.post(
        "/v1/check",
        json={"goal_id": case["goal"], "facts": case["facts"], "document_issue": "21"},
    )
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["status"] == expectation["expected_external_status"]
    assert report["internal_status"] == expectation["expected_status"]
    assert report["rule_id"] == expectation["expected_rule_id"]
    assert report["source"]["article"] == expectation["expected_article"]
    if expectation["expected_status"] == "UNKNOWN":
        actual_missing = {item["fact"] for item in report["missing_facts"]}
        assert set(expectation["expected_missing_facts"]).issubset(actual_missing)
    assert report["proof_trace"] is not None
    assert report["proof_trace"]["status"] == report["internal_status"]
    assert expectation["expected_article"] in report["explanation"]
    if report["citations"]:
        assert all(citation["verified"] for citation in report["citations"])
    assert report["rule_status"] == "reviewed"
    assert any(diag["code"] == "RULE_NOT_APPROVED" for diag in report["diagnostics"])


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["rules"]["reviewed"] == 13
    assert body["rules"]["active"] == 0
    assert body["demo_mode"] is True
    assert "wheelbase_compliance" in body["goals"]


def test_goals_include_sources_and_requirements(client):
    response = client.get("/v1/goals")
    assert response.status_code == 200
    goals = {item["goal_id"]: item for item in response.json()}
    assert goals["wheelbase_compliance"]["article"] == "C2.3.3"
    assert goals["wheelbase_compliance"]["rule_status"] == "reviewed"
    assert any(req["name"] == "wheelbase" for req in goals["wheelbase_compliance"]["requirements"])
    assert "quote" in goals["minimum_mass_compliance"]

    mass_distribution = {req["name"] for req in goals["mass_distribution_compliance"]["requirements"]}
    assert {"front_axle_mass", "rear_axle_mass", "nominal_tyre_mass", "session_type"} <= mass_distribution

    minimum_mass = {req["name"]: req["unit"] for req in goals["minimum_mass_compliance"]["requirements"]}
    assert {"car_mass", "nominal_tyre_mass", "session_type"} <= set(minimum_mass)
    assert {"session_category", "heat_hazard_declared", "competition_heat_hazard_declared"} <= set(minimum_mass)
    assert minimum_mass["nominal_tyre_mass"] == "kg"


def test_rules_endpoint_exposes_lifecycle(client):
    response = client.get("/rules")
    assert response.status_code == 200
    rules = response.json()
    assert len(rules) == 13
    assert all(rule["status"] == "reviewed" for rule in rules)
    assert all(rule["validation"]["verified_on"] for rule in rules)
    assert all(rule["validation"]["human_approved"] is False for rule in rules)


def test_unknown_goal_is_unsupported(client):
    response = client.post("/v1/check", json={"goal_id": "does_not_exist", "facts": []})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "UNSUPPORTED"
    assert body["internal_status"] is None
    assert body["diagnostics"][0]["code"] == "UNSUPPORTED_GOAL"


def test_version_mismatch_is_unsupported(client):
    response = client.post(
        "/v1/check",
        json={"goal_id": "wheelbase_compliance", "document_issue": "20", "facts": [{"name": "wheelbase", "value": 3400, "unit": "mm"}]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "UNSUPPORTED"
    assert body["diagnostics"][0]["code"] == "VERSION_MISMATCH"


def test_conflicting_facts_return_conflicting_input(client):
    response = client.post(
        "/v1/check",
        json={
            "goal_id": "wheelbase_compliance",
            "facts": [
                {"name": "wheelbase", "value": 3300, "unit": "mm"},
                {"name": "wheelbase", "value": 3500, "unit": "mm"},
            ],
        },
    )
    assert response.status_code == 409
    body = response.json()
    assert body["status"] == "CONFLICTING_INPUT"
    assert body["diagnostics"][0]["code"] == "CONFLICTING_INPUT"


@pytest.mark.parametrize(
    "fact",
    [
        {"name": "wheelbase", "value": 3400},
        {"name": "car_mass", "value": -1, "unit": "kg"},
        {"name": "unknown_fact", "value": 1, "unit": "mm"},
    ],
)
def test_invalid_fact_input_returns_422(client, fact):
    response = client.post("/v1/check", json={"goal_id": "wheelbase_compliance", "facts": [fact]})
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "INVALID_INPUT"
    assert body["diagnostics"][0]["code"] == "INVALID_INPUT"


def test_check_all_returns_every_compliance_goal(client):
    response = client.get("/sample-facts")
    assert response.status_code == 200
    facts = response.json()["facts"]
    response = client.post("/check/all", json={"facts": facts})
    assert response.status_code == 200
    reports = response.json()
    assert len(reports) == 5
    assert {report["goal_id"] for report in reports} == {
        "wheelbase_compliance",
        "cockpit_position_compliance",
        "half_width_compliance",
        "minimum_mass_compliance",
        "mass_distribution_compliance",
    }
    assert all(report["status"] != "ERROR" for report in reports)


def test_extract_facts_deterministic(client):
    response = client.post(
        "/v1/extract-facts",
        json={
            "text": "Wheelbase 3350 mm, massa mobil 810 kg, sesi qualifying, no heat hazard.",
            "use_llm": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    facts = {item["name"]: item["value"] for item in body["facts"]}
    assert facts["wheelbase"] == 3350
    assert facts["car_mass"] == 810
    assert facts["session_type"] == "Q"
    assert facts["heat_hazard_declared"] is False
    assert body["requires_confirmation"] is True
    assert all(item["confidence"] is not None for item in body["facts"])


def test_search_excludes_methodology_by_default(client):
    query = "backward chaining inference database stored procedure"
    response = client.post("/v1/search", json={"query": query, "top_k": 10})
    assert response.status_code == 200, response.text
    hits = response.json()
    assert all(hit["document_type"] == "regulation" for hit in hits)

    response = client.post(
        "/v1/search", json={"query": query, "top_k": 10, "include_methodology": True}
    )
    assert response.status_code == 200
    types = {hit["document_type"] for hit in response.json()}
    assert "journal" in types


def test_retrieval_endpoint_returns_wheelbase_clause(client):
    response = client.post(
        "/v1/search",
        json={"query": "maximum wheelbase 3400 mm distance between planes XF and XR", "top_k": 3},
    )
    assert response.status_code == 200, response.text
    hits = response.json()
    assert hits
    assert hits[0]["article"] == "C2.3.3"
    assert hits[0]["page"] == 11


def test_legacy_endpoints_still_work(client):
    response = client.post(
        "/check",
        json={"goal": "wheelbase_compliance", "facts": [{"name": "wheelbase", "value": 3400, "unit": "mm"}]},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "SATISFIED"

    response = client.post("/retrieve", json={"query": "maximum wheelbase", "top_k": 3})
    assert response.status_code == 200
    assert response.json()
