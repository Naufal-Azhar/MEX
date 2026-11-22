"""Run a small B-vs-C comparison: RAG+LLM vs the gated pipeline."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.learning.ask_service import AskService, _telemetry_query, classify_question  # noqa: E402
from app.llm.base import ChatMessage, get_provider  # noqa: E402
from app.schemas.learning import AskRequest  # noqa: E402

RAW = ROOT / "datasets" / "evaluation" / "answer_accuracy_raw_bm25.json"
RESULTS = ROOT / "datasets" / "evaluation" / "b_vs_c_results.json"
REPORT = ROOT / "research" / "b_vs_c_comparison.md"

CASES = [
    (
        "engineering_relaxation",
        "what is relaxation length in tire lateral dynamics?",
        None,
        None,
    ),
    (
        "telemetry_braking",
        "compare the braking and speed between these two laps",
        "VER-Q-14",
        "NOR-Q-16",
    ),
    (
        "theory_brake_onset",
        "what does brake onset mean and why can it differ?",
        None,
        None,
    ),
    (
        "unsupported_prediction",
        "predict the race winner",
        None,
        None,
    ),
]

EXPECTED_TELEMETRY_FACTS = [
    "max_speed = 331.0 km/h",
    "max_speed = 329.0 km/h",
    "speed_delta_mean = -0.344 km/h",
    "speed_delta_min = -23.13 km/h",
    "speed_delta_max = 14.037 km/h",
]
ABSTENTION_MARKERS = (
    "cannot",
    "can't",
    "can not",
    "unable",
    "insufficient",
    "not enough",
    "no data",
    "not provided",
    "tidak",
    "tidak dapat",
    "maaf",
)


def _b_prompt(question: str, evidence: list) -> list[ChatMessage]:
    block = "\n\n".join(
        f"[E{index}] ({hit.document_id} / {hit.article})\n{hit.text[:1400]}"
        for index, hit in enumerate(evidence, start=1)
    )
    return [
        ChatMessage(
            role="system",
            content=(
                "You are an engineering tutor. Answer using only the supplied evidence. "
                "If the evidence is insufficient, say so explicitly. Do not invent numbers, "
                "citations, or race outcomes. Keep the answer under 180 words."
            ),
        ),
        ChatMessage(
            role="user",
            content=f"Question: {question}\n\nEvidence:\n{block or 'none'}",
        ),
    ]


def _looks_abstained(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ABSTENTION_MARKERS)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    provider = get_provider()
    if provider is None or not provider.is_configured():
        raise SystemExit("LLM provider is not configured")
    service = AskService.default()
    c_answers = json.loads(RAW.read_text(encoding="utf-8"))
    rows = []
    for case_id, question, lap_a, lap_b in CASES:
        request = AskRequest(
            question=question,
            level="beginner",
            lap_a_id=lap_a,
            lap_b_id=lap_b,
        )
        c_answer = c_answers[case_id]
        question_type = classify_question(question, bool(lap_a and lap_b))
        retrieval_query = _telemetry_query(question) if question_type.value == "telemetry_case" else question
        hits = service.corpus.search(retrieval_query, top_k=request.top_k)
        b_text = provider.complete(_b_prompt(question, hits), temperature=0.0, max_tokens=500).strip()
        b_citation_markers = re.findall(r"\[E\d+\]", b_text)
        c_observed = " | ".join(c_answer.get("observed_facts", []))
        rows.append(
            {
                "case_id": case_id,
                "question": question,
                "question_type": question_type.value,
                "B": {
                    "answer": b_text,
                    "citation_markers": len(b_citation_markers),
                    "telemetry_fact_hits": sum(
                        1 for fact in EXPECTED_TELEMETRY_FACTS if fact in b_text
                    ),
                    "looks_abstained": _looks_abstained(b_text),
                },
                "C": {
                    "generation_status": c_answer["generation_status"],
                    "citation_count": len(c_answer.get("citation_refs", [])),
                    "verified_citations": all(
                        item.get("verified") for item in c_answer.get("citation_refs", [])
                    ),
                    "claim_check": c_answer.get("generation_provenance", {}).get(
                        "claim_citation_check"
                    ),
                    "telemetry_fact_hits": sum(
                        1 for fact in EXPECTED_TELEMETRY_FACTS if fact in c_observed
                    ),
                    "abstained": c_answer["question_type"] == "unsupported",
                },
            }
        )
        print(
            f"{case_id}: B markers={len(b_citation_markers)} "
            f"facts={rows[-1]['B']['telemetry_fact_hits']} "
            f"abstain={rows[-1]['B']['looks_abstained']} | "
            f"C cites={rows[-1]['C']['citation_count']} "
            f"facts={rows[-1]['C']['telemetry_fact_hits']} "
            f"abstain={rows[-1]['C']['abstained']}"
        )

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": getattr(provider, "model", ""),
        "retrieval_backend": service.corpus.backend_name,
        "design": {
            "B": "RAG + LLM, free text, no server facts, no rule/evidence gate, no citation validator.",
            "C": "same BM25 retrieval + server facts + rule/evidence gate + schema + [E#] citation validation.",
        },
        "rows": rows,
        "limits": [
            "Four cases, one model snapshot; not a statistically powered benchmark.",
            "B is free text, so citation presence is counted but not validated.",
            "Telemetry fact hits are string checks, not semantic equivalence.",
        ],
    }
    RESULTS.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# B vs C Comparison",
        "",
        f"Generated: {result['generated_at']}",
        f"Model: `{result['model']}`; retrieval: `{result['retrieval_backend']}`",
        "",
        "## Design",
        "",
        f"- **B**: {result['design']['B']}",
        f"- **C**: {result['design']['C']}",
        "",
        "## Results",
        "",
        "| Case | B citations | B telemetry facts | B abstained | C citations | C telemetry facts | C status |",
        "| --- | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['B']['citation_markers']} | "
            f"{row['B']['telemetry_fact_hits']} | {row['B']['looks_abstained']} | "
            f"{row['C']['citation_count']} | {row['C']['telemetry_fact_hits']} | "
            f"{row['C']['generation_status']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- C keeps measured facts server-side and rejects answers whose claim citations do not validate.",
            "- B can produce fluent prose but does not prove that its statements are supported by the retrieved evidence.",
            "- This is a small internal comparison, not a claim of general superiority.",
            "",
            "## Limits",
            "",
        ]
    )
    for limit in result["limits"]:
        lines.append(f"- {limit}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {RESULTS} and {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
