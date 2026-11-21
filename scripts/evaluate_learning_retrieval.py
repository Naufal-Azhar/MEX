"""Evaluate retrieval over the engineering learning corpus (no LLM required)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.learning.retrieval import LearningCorpusIndex  # noqa: E402

CASES_PATH = ROOT / "datasets" / "evaluation" / "retrieval_learning_cases.json"
RESULTS_JSON = ROOT / "datasets" / "evaluation" / "learning_retrieval_results.json"
REPORT_MD = ROOT / "research" / "learning_retrieval_report.md"
NO_ANSWER_THRESHOLD = 0.20


def _rank(articles: list[str], expected: list[str]) -> int | None:
    for index, article in enumerate(articles, start=1):
        if article in expected:
            return index
    return None


def main() -> int:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    index = LearningCorpusIndex.from_paths(root=ROOT)
    rows = []
    for case in data["cases"]:
        hits = index.search(case["query"], top_k=5)
        articles = [hit.article or "" for hit in hits]
        expected = case["expected_articles"]
        rank = _rank(articles, expected) if expected else None
        top_score = hits[0].score if hits else 0.0
        rows.append(
            {
                "case_id": case["case_id"],
                "query": case["query"],
                "category": case["category"],
                "answerable": case["answerable"],
                "expected_articles": expected,
                "top_articles": articles,
                "hit_at_1": bool(expected and rank == 1),
                "hit_at_3": bool(expected and rank is not None and rank <= 3),
                "reciprocal_rank": round(1 / rank, 6) if rank else 0.0,
                "top_score": round(top_score, 6),
                "abstained": (not case["answerable"] and top_score < NO_ANSWER_THRESHOLD),
            }
        )

    answerable = [row for row in rows if row["answerable"]]
    no_answer = [row for row in rows if not row["answerable"]]
    count = len(answerable)
    aggregate = {
        "cases": len(rows),
        "answerable_cases": count,
        "no_answer_cases": len(no_answer),
        "hit_at_1": round(sum(row["hit_at_1"] for row in answerable) / count, 4) if count else 0.0,
        "hit_at_3": round(sum(row["hit_at_3"] for row in answerable) / count, 4) if count else 0.0,
        "mrr": round(sum(row["reciprocal_rank"] for row in answerable) / count, 4) if count else 0.0,
        "no_answer_abstention": round(
            sum(row["abstained"] for row in no_answer) / len(no_answer), 4
        ) if no_answer else None,
        "no_answer_threshold": NO_ANSWER_THRESHOLD,
    }

    by_category: dict[str, dict] = {}
    for category in sorted({row["category"] for row in answerable}):
        subset = [row for row in answerable if row["category"] == category]
        by_category[category] = {
            "cases": len(subset),
            "hit_at_1": round(sum(row["hit_at_1"] for row in subset) / len(subset), 4),
            "hit_at_3": round(sum(row["hit_at_3"] for row in subset) / len(subset), 4),
            "mrr": round(sum(row["reciprocal_rank"] for row in subset) / len(subset), 4),
        }

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus": "data_dictionary.md + engineering_fundamentals.md",
        "retrieval_backend": "tfidf",
        "aggregate": aggregate,
        "by_category": by_category,
        "cases": rows,
    }
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Learning Retrieval Evaluation",
        "",
        f"Generated: {results['generated_at']}",
        "",
        "Corpus: `knowledge_base/source_documents/telemetry/` (data dictionary + engineering notes).",
        "Backend: TF-IDF with table-row chunks and intent-aware scoring.",
        "",
        "## Aggregate",
        "",
        f"- Answerable cases: {aggregate['answerable_cases']}",
        f"- Hit@1: {aggregate['hit_at_1']}",
        f"- Hit@3: {aggregate['hit_at_3']}",
        f"- MRR: {aggregate['mrr']}",
        f"- No-answer cases: {aggregate['no_answer_cases']}",
        f"- No-answer abstention (top score < {NO_ANSWER_THRESHOLD}): {aggregate['no_answer_abstention']}",
        "",
        "## By category",
        "",
        "| Category | Cases | Hit@1 | Hit@3 | MRR |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for category, values in by_category.items():
        lines.append(
            f"| {category} | {values['cases']} | {values['hit_at_1']} | "
            f"{values['hit_at_3']} | {values['mrr']} |"
        )
    lines.extend(
        [
            "",
            "## Per case",
            "",
            "| Case | Category | Expected | Top article | Hit@1 | RR |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        expected = ", ".join(row["expected_articles"]) or "(no answer)"
        top = row["top_articles"][0] if row["top_articles"] else "-"
        lines.append(
            f"| {row['case_id']} | {row['category']} | {expected} | {top} | "
            f"{row['hit_at_1']} | {row['reciprocal_rank']} |"
        )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Small corpus and small query set; not a general benchmark.",
            "- The no-answer check uses a fixed score threshold, not semantic entailment.",
            "- Indonesian queries depend on the prototype term-expansion map.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(aggregate, indent=2))
    print(f"Wrote {RESULTS_JSON} and {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
