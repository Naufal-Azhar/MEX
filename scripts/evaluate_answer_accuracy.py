"""Evaluate structural answer accuracy from recorded real-LLM runs.

This does not call the model. It evaluates the saved outputs so the check is
reproducible without spending quota. Run the live cases separately when needed.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(
    os.getenv(
        "ANSWER_ACCURACY_RAW",
        str(ROOT / "datasets" / "evaluation" / "answer_accuracy_raw_bm25.json"),
    )
)
THEORY_RERUN = ROOT / "datasets" / "evaluation" / "answer_theory_rerun.json"
RESULTS = ROOT / "datasets" / "evaluation" / "answer_accuracy_results.json"
REPORT = ROOT / "research" / "answer_accuracy_report.md"


def _load() -> dict:
    payload = json.loads(RAW.read_text(encoding="utf-8"))
    if THEORY_RERUN.exists() and "theory_brake_onset" not in payload:
        payload["theory_brake_onset"] = json.loads(THEORY_RERUN.read_text(encoding="utf-8"))
    return payload


def _citation_docs(answer: dict) -> list[str]:
    return [item["document_id"] for item in answer.get("citation_refs", [])]


def _citation_articles(answer: dict) -> list[str]:
    return [item.get("article") or "" for item in answer.get("citation_refs", [])]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    answers = _load()
    checks = []

    engineering = answers["engineering_relaxation"]
    checks.append(
        {
            "case_id": "engineering_relaxation",
            "answerable": True,
            "generated": engineering["generation_status"] == "generated",
            "citations_present": bool(engineering["citation_refs"]),
            "expected_source_hit": "tire-lateral-dynamics-2022" in _citation_docs(engineering),
            "verified_citations": all(c.get("verified") for c in engineering["citation_refs"]),
            "claim_check_passed": engineering.get("generation_provenance", {}).get("claim_citation_check") == "passed",
        }
    )

    telemetry = answers["telemetry_braking"]
    observed = " | ".join(telemetry.get("observed_facts", []))
    expected_facts = [
        "max_speed = 331.0 km/h",
        "max_speed = 329.0 km/h",
        "speed_delta_mean = -0.344 km/h",
        "speed_delta_min = -23.13 km/h",
        "speed_delta_max = 14.037 km/h",
    ]
    checks.append(
        {
            "case_id": "telemetry_braking",
            "answerable": True,
            "generated": telemetry["generation_status"] == "generated",
            "citations_present": bool(telemetry["citation_refs"]),
            "verified_citations": all(c.get("verified") for c in telemetry["citation_refs"]),
            "claim_check_passed": telemetry.get("generation_provenance", {}).get("claim_citation_check") == "passed",
            "expected_facts_found": sum(1 for item in expected_facts if item in observed),
            "expected_facts_total": len(expected_facts),
        }
    )

    theory = answers["theory_brake_onset"]
    checks.append(
        {
            "case_id": "theory_brake_onset",
            "answerable": True,
            "generated": theory["generation_status"] == "generated",
            "citations_present": bool(theory["citation_refs"]),
            "expected_source_hit": "engineering-fundamentals" in _citation_docs(theory),
            "definition_section_hit": any("2.1 Brake onset" in article for article in _citation_articles(theory)),
            "verified_citations": all(c.get("verified") for c in theory["citation_refs"]),
            "claim_check_passed": theory.get("generation_provenance", {}).get("claim_citation_check") == "passed",
        }
    )

    unsupported = answers["unsupported_prediction"]
    checks.append(
        {
            "case_id": "unsupported_prediction",
            "answerable": False,
            "question_type": unsupported["question_type"],
            "no_theory": not unsupported.get("theory"),
            "no_citations": not unsupported.get("citation_refs"),
            "no_observed_facts": not unsupported.get("observed_facts"),
            "abstained": unsupported["question_type"] == "unsupported",
        }
    )

    answerable = [item for item in checks if item["answerable"]]
    structural_pass = sum(
        1
        for item in answerable
        if item["generated"] and item["citations_present"] and item["verified_citations"] and item["claim_check_passed"]
    )
    unsupported_pass = 1 if checks[-1]["abstained"] and checks[-1]["no_theory"] else 0
    backends = sorted(
        {
            answer.get("generation_provenance", {}).get("retrieval_backend", "unknown")
            for answer in answers.values()
        }
    )
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": f"recorded real-LLM outputs under BM25; no new API calls ({RAW.name})",
        "retrieval_backends": backends,
        "checks": checks,
        "summary": {
            "answerable_cases": len(answerable),
            "answerable_structural_pass": structural_pass,
            "telemetry_fact_hits": checks[1]["expected_facts_found"],
            "telemetry_fact_total": checks[1]["expected_facts_total"],
            "unsupported_abstention_pass": unsupported_pass,
        },
        "limits": [
            "Structural and numeric checks, not full semantic entailment.",
            "Small sample: four cases, one model snapshot.",
            "LLM output is non-deterministic; reruns may cite different valid passages.",
        ],
    }
    RESULTS.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Answer Accuracy Evaluation",
        "",
        f"Generated: {result['generated_at']}",
        f"Source: recorded real-LLM outputs under BM25 (no new API calls; `{RAW.name}`).",
        f"Retrieval backend: {', '.join(result['retrieval_backends'])}",
        "",
        "## Summary",
        "",
        f"- Answerable structural pass: {structural_pass}/{len(answerable)}",
        f"- Telemetry expected facts found: {checks[1]['expected_facts_found']}/{checks[1]['expected_facts_total']}",
        f"- Unsupported abstention: {unsupported_pass}/1",
        "",
        "## Cases",
        "",
        "| Case | Generated | Citations | Verified | Claim check | Expected source |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in checks[:3]:
        lines.append(
            f"| {item['case_id']} | {item['generated']} | {item['citations_present']} | "
            f"{item['verified_citations']} | {item['claim_check_passed']} | {item.get('expected_source_hit', 'n/a')} |"
        )
    lines.extend(
        [
            f"| unsupported_prediction | n/a | {not checks[3]['no_citations']} | n/a | n/a | abstained={checks[3]['abstained']} |",
            "",
            "## Telemetry facts checked",
            "",
        ]
    )
    for item in expected_facts:
        lines.append(f"- `{item}`: {'found' if item in observed else 'MISSING'}")
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "- This is structural/numeric verification, not semantic entailment.",
            "- Four cases and one model snapshot are not a benchmark.",
            "- The model can cite a valid but weak passage; human review remains required.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"Wrote {RESULTS} and {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
