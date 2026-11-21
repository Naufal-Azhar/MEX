"""Tests for section-aware retrieval, grounded answers and /v1/ask."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.learning.ask_service import AskService, classify_question
from app.learning.retrieval import LearningCorpusIndex
from app.learning.service import TelemetryLearningService
from app.main import app
from app.rag.corpus import chunk_markdown
from app.rag.grounded_answer import (
    build_llm_answer,
    citations_from_hits,
    validate_citation_ids,
)
from app.schemas.learning import AskRequest, GenerationStatus, QuestionType


@pytest.fixture(scope="module")
def corpus() -> LearningCorpusIndex:
    return LearningCorpusIndex.from_paths()


@pytest.fixture(scope="module")
def ask_service() -> AskService:
    return AskService.default()


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls = 0

    def is_configured(self) -> bool:
        return True

    def complete(self, messages, temperature: float = 0.0, max_tokens: int = 800) -> str:
        self.calls += 1
        return json.dumps(self.payload)


def test_markdown_chunks_are_section_aware() -> None:
    chunks = chunk_markdown(
        "knowledge_base/source_documents/telemetry/data_dictionary.md",
        "telemetry-data-dictionary",
        "data_dictionary",
    )
    assert chunks
    articles = {chunk.article for chunk in chunks}
    assert any("Channels" in article for article in articles)
    assert all(chunk.document_id == "telemetry-data-dictionary" for chunk in chunks)


def test_markdown_table_rows_keep_header_context() -> None:
    chunks = chunk_markdown(
        "knowledge_base/source_documents/telemetry/data_dictionary.md",
        "telemetry-data-dictionary",
        "data_dictionary",
    )
    brake_rows = [chunk for chunk in chunks if "`brake`" in chunk.text and "0 or 1" in chunk.text]
    assert brake_rows
    assert all("Channel" in chunk.text for chunk in brake_rows)
    assert all("Channels" in chunk.article for chunk in brake_rows)


def test_corpus_finds_brake_channel_definition(corpus: LearningCorpusIndex) -> None:
    hits = corpus.search("what unit is the brake channel", top_k=5)
    assert any(
        "Channels" in (hit.article or "") and "brake" in hit.text.lower()
        for hit in hits
    )


def test_corpus_retrieves_throttle_section(corpus: LearningCorpusIndex) -> None:
    hits = corpus.search("what does throttle percentage mean", top_k=2)
    assert hits
    assert any("Throttle" in (hit.article or "") for hit in hits)


def test_question_classification() -> None:
    assert classify_question("what does brake onset mean", False) is QuestionType.THEORY
    assert classify_question("compare the braking of these laps", True) is QuestionType.TELEMETRY_CASE
    assert classify_question("what is the FIA wheelbase limit", False) is QuestionType.REGULATION
    assert classify_question("predict the race winner", False) is QuestionType.UNSUPPORTED


def test_citation_validation_rejects_fabricated_ids(corpus: LearningCorpusIndex) -> None:
    hits = corpus.search("braking distance", top_k=2)
    citations = citations_from_hits(hits)
    accepted, rejected = validate_citation_ids(["E1", "E99"], citations)
    assert accepted == ["E1"]
    assert rejected == ["E99"]


def test_fake_provider_generates_valid_answer(corpus: LearningCorpusIndex) -> None:
    hits = corpus.search("braking distance", top_k=2)
    provider = FakeProvider(
        {
            "observed_facts": ["999 km/h fabricated"],
            "rule_based_findings": ["TEL-R03: OBSERVED"],
            "potential_explanations": ["entry speed may differ"],
            "theory": ["braking distance grows with speed [E1]"],
            "citation_refs": ["E1"],
            "missing_data": ["tyre state"],
            "limitations": ["descriptive only"],
            "suggested_learning_questions": ["what is load transfer?"],
        }
    )
    answer = build_llm_answer(provider, "why brake earlier?", "beginner", QuestionType.THEORY, hits, None)
    assert answer.generation_status is GenerationStatus.GENERATED
    assert [citation.ref_id for citation in answer.citation_refs] == ["E1"]
    assert answer.observed_facts == []
    assert all("999" not in item for item in answer.observed_facts)
    assert answer.generation_provenance["facts_source"] == "server"
    assert provider.calls == 1


def test_llm_cannot_override_server_facts(
    corpus: LearningCorpusIndex,
    ask_service: AskService,
) -> None:
    hits = corpus.search("braking distance", top_k=2)
    analysis = ask_service.learning.analyze("VER-Q-14", "NOR-Q-16")
    provider = FakeProvider(
        {
            "observed_facts": ["999 km/h fabricated"],
            "rule_based_findings": ["FAKE-RULE: OBSERVED"],
            "potential_explanations": [],
            "theory": ["braking distance grows with speed [E1]"],
            "citation_refs": ["E1"],
            "missing_data": [],
            "limitations": [],
            "suggested_learning_questions": [],
        }
    )
    answer = build_llm_answer(provider, "compare braking", "beginner", QuestionType.TELEMETRY_CASE, hits, analysis)
    assert answer.generation_status is GenerationStatus.GENERATED
    assert answer.observed_facts
    assert all("999" not in item for item in answer.observed_facts)
    assert all("FAKE-RULE" not in item for item in answer.rule_based_findings)
    assert any("max_speed" in item for item in answer.observed_facts)


def test_llm_theory_without_claim_citation_is_rejected(corpus: LearningCorpusIndex) -> None:
    hits = corpus.search("braking distance", top_k=2)
    provider = FakeProvider(
        {
            "observed_facts": [],
            "rule_based_findings": [],
            "potential_explanations": [],
            "theory": ["braking distance grows with speed"],
            "citation_refs": ["E1"],
            "missing_data": [],
            "limitations": [],
            "suggested_learning_questions": [],
        }
    )
    answer = build_llm_answer(provider, "why brake earlier?", "beginner", QuestionType.THEORY, hits, None)
    assert answer.generation_status is GenerationStatus.REJECTED
    assert answer.generation_provenance["claims_without_citation"] == 1


def test_prompt_isolates_untrusted_evidence(corpus: LearningCorpusIndex) -> None:
    from app.rag.grounded_answer import _prompt

    hits = corpus.search("braking distance", top_k=1)
    messages = _prompt("what is braking?", "beginner", hits, None)
    assert "<evidence>" in messages[1].content
    assert "</evidence>" in messages[1].content
    assert "untrusted data" in messages[0].content


def test_fake_provider_with_unknown_citation_is_rejected(corpus: LearningCorpusIndex) -> None:
    hits = corpus.search("braking distance", top_k=2)
    provider = FakeProvider(
        {
            "observed_facts": [],
            "rule_based_findings": [],
            "potential_explanations": [],
            "theory": ["text"],
            "citation_refs": ["E99"],
            "missing_data": [],
            "limitations": [],
            "suggested_learning_questions": [],
        }
    )
    answer = build_llm_answer(provider, "why brake earlier?", "beginner", QuestionType.THEORY, hits, None)
    assert answer.generation_status is GenerationStatus.REJECTED
    assert answer.generation_provenance["rejected_citation_ids"] == ["E99"]


def test_ask_theory_returns_citations(ask_service: AskService) -> None:
    answer = ask_service.ask(AskRequest(question="what does throttle percentage mean"))
    assert answer.question_type is QuestionType.THEORY
    assert answer.generation_status is GenerationStatus.UNAVAILABLE
    assert answer.citation_refs
    assert all(citation.verified for citation in answer.citation_refs)


def test_ask_telemetry_case_includes_analysis(ask_service: AskService) -> None:
    answer = ask_service.ask(
        AskRequest(
            question="compare the braking between these two laps",
            lap_a_id="VER-Q-14",
            lap_b_id="NOR-Q-16",
        )
    )
    assert answer.question_type is QuestionType.TELEMETRY_CASE
    assert answer.analysis is not None
    assert answer.observed_facts
    assert answer.rule_based_findings
    assert answer.generation_status is GenerationStatus.UNAVAILABLE
    assert any("Braking" in (citation.article or "") for citation in answer.citation_refs)


def test_ask_telemetry_case_requires_laps(ask_service: AskService) -> None:
    with pytest.raises(ValueError):
        ask_service.ask(AskRequest(question="compare the braking between these laps"))


def test_api_ask_theory(client: TestClient) -> None:
    response = client.post("/v1/ask", json={"question": "how does braking distance relate to speed"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["question_type"] == "theory"
    assert payload["generation_status"] == "unavailable"
    assert payload["citation_refs"]


def test_api_ask_telemetry(client: TestClient) -> None:
    response = client.post(
        "/v1/ask",
        json={
            "question": "compare braking between the two laps",
            "lap_a_id": "VER-Q-14",
            "lap_b_id": "NOR-Q-16",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["question_type"] == "telemetry_case"
    assert payload["analysis"]["findings"]
    assert payload["observed_facts"]


def test_api_ask_regulation_is_routed(client: TestClient) -> None:
    response = client.post("/v1/ask", json={"question": "what is the FIA wheelbase limit"})
    assert response.status_code == 200
    assert response.json()["question_type"] == "regulation"


def test_api_ask_unsupported(client: TestClient) -> None:
    response = client.post("/v1/ask", json={"question": "predict the race winner"})
    assert response.status_code == 200
    assert response.json()["question_type"] == "unsupported"
