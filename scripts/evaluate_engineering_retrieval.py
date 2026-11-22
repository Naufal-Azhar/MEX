"""Evaluate retrieval and citation checks over the local engineering corpus."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.learning.retrieval import LearningCorpusIndex  # noqa: E402

CASES = ROOT / "datasets" / "evaluation" / "engineering_retrieval_cases.json"
RESULTS = ROOT / "datasets" / "evaluation" / "engineering_retrieval_results.json"
REPORT = ROOT / "research" / "engineering_retrieval_report.md"
LLM_ANSWER = ROOT / "datasets" / "evaluation" / "llm_smoke_engineering.json"
MANIFEST = ROOT / "knowledge_base" / "metadata" / "engineering_sources.json"


def _normalise(text: str) -> str:
    return " ".join(text.split()).lower()


def _strip_page_heading(text: str) -> str:
    return re.sub(r"^#+\s*Page\s+\d+\s*", "", text, flags=re.IGNORECASE).strip()


def _rank(ids: list[str], expected: list[str]) -> int | None:
    for index, value in enumerate(ids, start=1):
        if value in expected:
            return index
    return None


def _verify_citations() -> list[dict]:
    if not LLM_ANSWER.exists() or not MANIFEST.exists():
        return []
    answer = json.loads(LLM_ANSWER.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_id = {item["document_id"]: item for item in manifest.get("documents", [])}
    checks = []
    for citation in answer.get("citation_refs", []):
        document_id = citation.get("document_id")
        article = citation.get("article") or ""
        quote = _strip_page_heading(citation.get("quote") or "")
        entry = by_id.get(document_id)
        found = False
        page = None
        if entry and article.startswith("Page "):
            page = int(article.split()[1])
            processed = ROOT / entry["processed_json"]
            if processed.exists():
                payload = json.loads(processed.read_text(encoding="utf-8"))
                page_text = next(
                    (item.get("text", "") for item in payload.get("pages", []) if item.get("page") == page),
                    "",
                )
                found = bool(quote) and _normalise(quote) in _normalise(page_text)
        checks.append(
            {
                "ref_id": citation.get("ref_id"),
                "document_id": document_id,
                "article": article,
                "page": page,
                "quote_found": found,
            }
        )
    return checks


def main() -> int:
    data = json.loads(CASES.read_text(encoding="utf-8"))
    index = LearningCorpusIndex.from_paths(root=ROOT, include_engineering=True)
    rows = []
    for case in data["cases"]:
        hits = index.search(
            case["query"],
            top_k=5,
            exclude_methodology=not case.get("methodology", False),
        )
        ids = [hit.document_id for hit in hits]
        rank = _rank(ids, case["expected_document_ids"])
        rows.append(
            {
                "case_id": case["case_id"],
                "query": case["query"],
                "expected": case["expected_document_ids"],
                "top_document_ids": ids,
                "hit_at_1": bool(rank == 1),
                "hit_at_3": bool(rank is not None and rank <= 3),
                "reciprocal_rank": round(1 / rank, 6) if rank else 0.0,
            }
        )

    count = len(rows)
    aggregate = {
        "cases": count,
        "hit_at_1": round(sum(row["hit_at_1"] for row in rows) / count, 4),
        "hit_at_3": round(sum(row["hit_at_3"] for row in rows) / count, 4),
        "mrr": round(sum(row["reciprocal_rank"] for row in rows) / count, 4),
    }
    citations = _verify_citations()
    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "retrieval_backend": index.backend_name,
        "corpus_chunks": len(index.chunks),
        "aggregate": aggregate,
        "cases": rows,
        "citation_checks": citations,
    }
    RESULTS.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Engineering Retrieval Evaluation",
        "",
        f"Generated: {results['generated_at']}",
        f"Retrieval backend: {results['retrieval_backend']}",
        f"Indexed chunks: {results['corpus_chunks']}",
        "",
        "## Aggregate",
        "",
        f"- Cases: {count}",
        f"- Hit@1: {aggregate['hit_at_1']}",
        f"- Hit@3: {aggregate['hit_at_3']}",
        f"- MRR: {aggregate['mrr']}",
        "",
        "## Per case",
        "",
        "| Case | Query | Expected | Top document | Hit@1 | RR |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['query']} | {', '.join(row['expected'])} | "
            f"{row['top_document_ids'][0] if row['top_document_ids'] else '-'} | "
            f"{row['hit_at_1']} | {row['reciprocal_rank']} |"
        )
    lines.extend(["", "## Citation checks", "", "| Ref | Document | Page | Quote found |", "| --- | --- | ---: | --- |"])
    for check in citations:
        lines.append(
            f"| {check['ref_id']} | {check['document_id']} | {check['page']} | {check['quote_found']} |"
        )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Engineering retrieval uses page-level TF-IDF chunks, not semantic embeddings.",
            "- The book and arXiv paper are indexed locally only; processed text is under `storage/engineering`.",
            "- Citation checks verify quote presence on the recorded page, not semantic entailment.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(aggregate, indent=2))
    print(f"Wrote {RESULTS} and {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
