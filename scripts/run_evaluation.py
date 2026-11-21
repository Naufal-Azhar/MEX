"""Run the evaluation suites and write machine- and human-readable results."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import DATASETS_DIR, ROOT as PROJECT_ROOT, configure_local_caches, get_logger  # noqa: E402
from app.evaluation.evaluator import Evaluator  # noqa: E402
from app.expert_system.service import ComplianceService  # noqa: E402
from app.rag.retriever import Retriever  # noqa: E402

RESULTS_JSON = DATASETS_DIR / "evaluation_results.json"
RESULTS_MD = PROJECT_ROOT / "research" / "evaluation_results.md"


def render_markdown(results: dict) -> str:
    decisions = results["decisions"]
    aggregate = decisions["aggregate"]
    classification = aggregate["classification"]
    generated = datetime.now(timezone.utc).isoformat()

    lines = [
        "# Evaluation Results",
        "",
        f"Generated: {generated}",
        "",
        "Mode: `RAG + LLM extraction disabled + Backward Chaining`. "
        "LLM-only (A) and RAG+LLM (B) configurations have not been run yet; see `research/evaluation_plan.md`.",
        f"Rule validation status: `{decisions.get('validation_status', 'unknown')}`. "
        "Reviewed rules are demo-only until a human reviewer signs them off.",
        "",
        "## Decision suite (backward chaining)",
        "",
        f"- Cases: {aggregate['case_count']}",
        f"- Decision accuracy: {classification['accuracy']}",
        f"- Violation (FALSE) precision: {classification['precision']}",
        f"- Violation (FALSE) recall: {classification['recall']}",
        f"- Violation (FALSE) F1: {classification['f1']}",
        f"- Rule match accuracy: {aggregate['rule_match_accuracy']}",
        f"- Article match accuracy: {aggregate['article_match_accuracy']}",
        f"- Citation accuracy: {aggregate['citation_accuracy']}",
        f"- Citation verification rate: {aggregate['citation_verification_rate']}",
        f"- Missing-fact precision: {aggregate['missing_fact_precision']}",
        f"- Missing-fact recall: {aggregate['missing_fact_recall']}",
        f"- Explanation completeness: {aggregate['explanation_completeness']}",
        f"- Backward-chaining trace consistency: {aggregate['trace_consistency']}",
        f"- Decision latency mean / p95 (ms): {aggregate['latency_ms_mean']} / {aggregate['latency_ms_p95']}",
        f"- Failure rate: {aggregate['failure_rate']}",
        "",
        "### Split summary",
        "",
        "| Split | Cases | Accuracy | F1 (VIOLATED) | Article match | Citation verified | Trace |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for split, split_agg in decisions.get("by_split", {}).items():
        split_class = split_agg["classification"]
        lines.append(
            f"| {split} | {split_agg['case_count']} | {split_class['accuracy']} | {split_class['f1']} | "
            f"{split_agg['article_match_accuracy']} | {split_agg['citation_verification_rate']} | "
            f"{split_agg['trace_consistency']} |"
        )

    lines.extend(
        [
            "",
            "### Per-case results",
            "",
            "| Case | Split | Goal | Expected | Actual | External | Expected rule | Actual rule | Article | Trace |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in decisions["cases"]:
        trace = "ok" if row["trace_consistency"]["consistent"] else "; ".join(row["trace_consistency"]["issues"])
        lines.append(
            f"| {row['case_id']} | {row.get('split')} | {row['goal']} | {row['expected_status']} | "
            f"{row['actual_status']} | {row['external_status']} | {row['expected_rule_id']} | "
            f"{row['actual_rule_id']} | {row['actual_article']} | {trace} |"
        )

    lines.extend(["", "### Confusion matrix", "", "| Transition | Count |", "| --- | --- |"])
    for transition, count in classification["confusion"].items():
        lines.append(f"| {transition} | {count} |")

    retrieval = results.get("retrieval")
    lines.extend(["", "## Retrieval suite", ""])
    if not retrieval or retrieval.get("skipped"):
        lines.append("Retrieval suite was not run.")
    else:
        index = retrieval["aggregate"]["index"]
        lines.extend(
            [
                f"- Cases: {retrieval['aggregate']['cases']}",
                f"- k: {retrieval['aggregate']['k']}",
                f"- Hit rate: {retrieval['aggregate']['hit_rate']}",
                f"- Precision@k: {retrieval['aggregate']['precision_at_k']}",
                f"- Recall@k: {retrieval['aggregate']['recall_at_k']}",
                f"- MRR: {retrieval['aggregate']['mrr']}",
                f"- Latency mean / p95 (ms): {retrieval['aggregate']['latency_ms_mean']} / {retrieval['aggregate']['latency_ms_p95']}",
                f"- Index: {json.dumps(index.get('embedding', index), ensure_ascii=False)}",
                "",
                "| Case | Query | Expected | Top retrieved | Hit | RR |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in retrieval["cases"]:
            top = ", ".join(f"{item['article']} (p{item['page']})" for item in row["retrieved"])
            lines.append(
                f"| {row['case_id']} | {row['query']} | {', '.join(row['expected_articles'])} | {top} | "
                f"{row['metrics']['hit']} | {row['metrics']['reciprocal_rank']} |"
            )

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- The decision suite covers 5 modelled provisions only (C2.3.1, C2.3.3, C2.3.5, C4.1, C4.2).",
            "- All rules are `reviewed`, not `active`; results are demo-only until human sign-off.",
            "- The dataset is split into development (12) and held-out (6) cases; labels are synthetic and self-authored.",
            "- Test inputs are fictional and derived from the regulation limits; they are not real team data.",
            "- Latency includes lazy loading of processed source pages on the first case; it is not a production benchmark.",
            "- Journal/methodology chunks are excluded from compliance search by default, but share the lexical index vocabulary.",
            "- LLM-based fact extraction was not exercised because the LLM stage is intentionally deferred.",
            "- No claim is made that Backward Chaining improves accuracy over an LLM-only baseline until that experiment is run.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    configure_local_caches()
    logger = get_logger("scripts.run_evaluation")
    service = ComplianceService()
    evaluator = Evaluator(service)
    retriever = None
    try:
        retriever = Retriever.load_or_build()
    except Exception as exc:  # noqa: BLE001 - evaluation can still run decisions
        logger.warning("Retrieval index unavailable: %s", exc)

    results = evaluator.run_all(retriever)
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    RESULTS_MD.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_MD.write_text(render_markdown(results), encoding="utf-8")

    aggregate = results["decisions"]["aggregate"]
    print(json.dumps(aggregate, indent=2, ensure_ascii=False))
    if retriever is not None and "retrieval" in results:
        print(json.dumps(results["retrieval"]["aggregate"], indent=2, ensure_ascii=False))
    print(f"Wrote {RESULTS_JSON} and {RESULTS_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
