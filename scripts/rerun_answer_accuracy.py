"""Rerun the four answer-accuracy cases against the live LLM using BM25."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.learning.ask_service import AskService  # noqa: E402
from app.schemas.learning import AskRequest  # noqa: E402

OUTPUT = ROOT / "datasets" / "evaluation" / "answer_accuracy_raw_bm25.json"

CASES = [
    (
        "engineering_relaxation",
        AskRequest(
            question="what is relaxation length in tire lateral dynamics?",
            level="beginner",
        ),
    ),
    (
        "telemetry_braking",
        AskRequest(
            question="compare the braking and speed between these two laps",
            level="beginner",
            lap_a_id="VER-Q-14",
            lap_b_id="NOR-Q-16",
        ),
    ),
    (
        "theory_brake_onset",
        AskRequest(
            question="what does brake onset mean and why can it differ?",
            level="beginner",
        ),
    ),
    (
        "unsupported_prediction",
        AskRequest(question="predict the race winner", level="beginner"),
    ),
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    service = AskService.default()
    answers: dict[str, dict] = {}
    for case_id, request in CASES:
        answer = service.ask(request)
        answers[case_id] = answer.model_dump(mode="json")
        provenance = answers[case_id].get("generation_provenance", {})
        print(
            f"{case_id}: type={answers[case_id]['question_type']} "
            f"status={answers[case_id]['generation_status']} "
            f"backend={provenance.get('retrieval_backend')} "
            f"citations={len(answers[case_id].get('citation_refs', []))}"
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(answers, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
