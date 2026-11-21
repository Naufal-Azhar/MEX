"""Run the decision and retrieval test suites and produce metrics."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.config import DATASETS_DIR, get_logger
from app.evaluation.metrics import classification_metrics, retrieval_metrics, set_precision_recall_f1
from app.expert_system.service import ComplianceService
from app.schemas.facts import Fact, FactOrigin, FactStore
from app.schemas.results import CheckReport, TraceNode

logger = get_logger("app.evaluation")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _facts_from_case(items: list[dict[str, Any]]) -> FactStore:
    store = FactStore()
    for item in items:
        store.add(
            Fact(
                name=item["name"],
                value=item["value"],
                unit=item.get("unit"),
                origin=FactOrigin.USER,
            )
        )
    return store


def explanation_completeness(report: CheckReport) -> dict[str, Any]:
    checks = {
        "mentions_status_or_verdict": any(
            word in report.explanation.lower()
            for word in (
                "memenuhi",
                "tidak memenuhi",
                "belum dapat ditentukan",
                "tidak berlaku",
                "tidak dapat diputuskan",
                "kesalahan sistem",
            )
        ),
        "mentions_rule_id": bool(report.rule_id and report.rule_id in report.explanation),
        "mentions_article": bool(report.source and f"Article {report.source.article}" in report.explanation),
        "mentions_evidence_or_missing": any(
            marker in report.explanation
            for marker in ("Kutipan regulasi", "Fakta yang masih diperlukan", "Sitasi sumber", "Goal yang didukung")
        ),
        "includes_scope_disclaimer": "seluruh kepatuhan" in report.explanation,
    }
    return {"score": round(sum(checks.values()) / len(checks), 4), "checks": checks}


def trace_consistency(report: CheckReport) -> dict[str, Any]:
    issues: list[str] = []
    trace = report.trace
    if trace is None:
        issues.append("missing trace")
    else:
        if trace.goal != report.goal_id:
            issues.append("trace goal differs from report goal")
        if trace.status != report.internal_status:
            issues.append("trace status differs from report internal status")
        if report.rule_id and trace.rule_id and report.rule_id != trace.rule_id:
            issues.append("trace rule differs from report rule")
        node_ids: set[str] = set()

        def walk(node: TraceNode) -> None:
            if node.node_id in node_ids:
                issues.append(f"duplicate trace node id {node.node_id}")
            node_ids.add(node.node_id)
            for child in node.children:
                if child.kind.endswith("goal") and child.status not in ("TRUE", "FALSE", "UNKNOWN"):
                    issues.append(f"invalid child status at {child.node_id}")
                walk(child)

        walk(trace)
    return {"consistent": not issues, "issues": issues}


def _load_decision_cases(datasets_dir: Path) -> list[dict[str, Any]]:
    development = datasets_dir / "development_cases.json"
    heldout = datasets_dir / "heldout_cases.json"
    if development.exists() and heldout.exists():
        return _load(development)["cases"] + _load(heldout)["cases"]
    return _load(datasets_dir / "test_cases.json")["cases"]


def _aggregate_decisions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    if total == 0:
        return {"case_count": 0}
    y_true = [row["expected_status"] for row in rows]
    y_pred = [row["actual_status"] for row in rows]
    latencies = sorted(row["latency_ms"] for row in rows)
    p95_index = min(total - 1, int(0.95 * total))
    return {
        "classification": classification_metrics(y_true, y_pred, positive="FALSE"),
        "rule_match_accuracy": round(sum(bool(row["rule_match"]) for row in rows) / total, 4),
        "article_match_accuracy": round(sum(bool(row["article_match"]) for row in rows) / total, 4),
        "citation_accuracy": round(sum(bool(row["citation_in_explanation"]) for row in rows) / total, 4),
        "citation_verification_rate": round(sum(bool(row["citation_valid"]) for row in rows) / total, 4),
        "missing_fact_precision": round(
            sum(row["missing_fact_metrics"]["precision"] for row in rows) / total, 4
        ),
        "missing_fact_recall": round(
            sum(row["missing_fact_metrics"]["recall"] for row in rows) / total, 4
        ),
        "explanation_completeness": round(
            sum(row["explanation_completeness"]["score"] for row in rows) / total, 4
        ),
        "trace_consistency": round(
            sum(bool(row["trace_consistency"]["consistent"]) for row in rows) / total, 4
        ),
        "latency_ms_mean": round(sum(latencies) / total, 2),
        "latency_ms_p95": round(latencies[p95_index], 2),
        "failure_rate": round(sum(1 for row in rows if row.get("error")) / total, 4),
        "case_count": total,
    }


class Evaluator:
    def __init__(self, service: ComplianceService, datasets_dir: Path | str = DATASETS_DIR) -> None:
        self.service = service
        self.datasets_dir = Path(datasets_dir)

    def run_decision_suite(self) -> dict[str, Any]:
        cases = _load_decision_cases(self.datasets_dir)
        expected = {item["case_id"]: item for item in _load(self.datasets_dir / "expected_results.json")["results"]}

        rows: list[dict[str, Any]] = []
        for case in cases:
            case_id = case["case_id"]
            expectation = expected[case_id]
            store = _facts_from_case(case["facts"])
            started = time.perf_counter()
            try:
                report = self.service.check(case["goal"], store)
            except Exception as exc:  # noqa: BLE001 - record failure instead of aborting the suite
                latency_ms = round((time.perf_counter() - started) * 1000, 2)
                rows.append(
                    {
                        "case_id": case_id,
                        "goal": case["goal"],
                        "split": case.get("split"),
                        "expected_status": expectation["expected_status"],
                        "actual_status": "ERROR",
                        "external_status": "ERROR",
                        "expected_rule_id": expectation["expected_rule_id"],
                        "actual_rule_id": None,
                        "expected_article": expectation["expected_article"],
                        "actual_article": None,
                        "rule_match": False,
                        "article_match": False,
                        "missing_fact_metrics": {
                            "precision": 0.0,
                            "recall": 0.0,
                            "f1": 0.0,
                            "expected": expectation["expected_missing_facts"],
                            "actual": [],
                        },
                        "explanation_completeness": {"score": 0.0, "checks": {}},
                        "trace_consistency": {"consistent": False, "issues": [str(exc)]},
                        "citation_in_explanation": False,
                        "citation_valid": False,
                        "latency_ms": latency_ms,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            latency_ms = round((time.perf_counter() - started) * 1000, 2)

            internal_status = report.internal_status.value if report.internal_status else "UNSUPPORTED"
            rule_match = report.rule_id == expectation["expected_rule_id"]
            article_match = bool(report.source and report.source.article == expectation["expected_article"])
            actual_missing = [item.fact for item in report.missing_facts]
            missing_metric = set_precision_recall_f1(expectation["expected_missing_facts"], actual_missing)
            completeness = explanation_completeness(report)
            consistency = trace_consistency(report)
            article_in_explanation = bool(
                report.source and f"Article {report.source.article}" in report.explanation
            )
            citation_valid = bool(report.citations) and all(c.verified for c in report.citations)

            rows.append(
                {
                    "case_id": case_id,
                    "goal": case["goal"],
                    "split": case.get("split"),
                    "expected_status": expectation["expected_status"],
                    "actual_status": internal_status,
                    "external_status": report.status.value,
                    "expected_rule_id": expectation["expected_rule_id"],
                    "actual_rule_id": report.rule_id,
                    "expected_article": expectation["expected_article"],
                    "actual_article": report.source.article if report.source else None,
                    "rule_match": rule_match,
                    "article_match": article_match,
                    "missing_fact_metrics": missing_metric,
                    "explanation_completeness": completeness,
                    "trace_consistency": consistency,
                    "citation_in_explanation": article_in_explanation,
                    "citation_valid": citation_valid,
                    "latency_ms": latency_ms,
                }
            )

        by_split = {
            split: _aggregate_decisions([row for row in rows if row["split"] == split])
            for split in sorted({row["split"] or "unspecified" for row in rows})
        }
        return {
            "mode": "rag_disabled",
            "inference": "backward_chaining",
            "validation_status": "reviewed_demo_only" if self.service.kb.demo_mode else "active",
            "cases": rows,
            "aggregate": _aggregate_decisions(rows),
            "by_split": by_split,
        }

    def run_retrieval_suite(self, retriever, k: int = 5) -> dict[str, Any]:
        path = self.datasets_dir / "retrieval_cases.json"
        if not path.exists():
            return {"skipped": True, "reason": "retrieval_cases.json not found"}
        cases = _load(path)["cases"]
        rows = []
        for case in cases:
            started = time.perf_counter()
            hits = retriever.search(case["query"], top_k=k)
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            articles = [hit.article for hit in hits]
            metrics = retrieval_metrics(case["expected_articles"], articles, k)
            rows.append(
                {
                    "case_id": case["case_id"],
                    "query": case["query"],
                    "expected_articles": case["expected_articles"],
                    "retrieved": [
                        {"article": hit.article, "page": hit.page, "score": hit.score} for hit in hits
                    ],
                    "metrics": metrics,
                    "latency_ms": latency_ms,
                }
            )
        count = len(rows)
        latencies = sorted(row["latency_ms"] for row in rows)
        aggregate = {
            "cases": count,
            "k": k,
            "hit_rate": round(sum(row["metrics"]["hit"] for row in rows) / count, 4),
            "precision_at_k": round(sum(row["metrics"]["precision_at_k"] for row in rows) / count, 4),
            "recall_at_k": round(sum(row["metrics"]["recall_at_k"] for row in rows) / count, 4),
            "mrr": round(sum(row["metrics"]["reciprocal_rank"] for row in rows) / count, 4),
            "latency_ms_mean": round(sum(latencies) / count, 2),
            "latency_ms_p95": round(latencies[min(count - 1, int(0.95 * count))], 2),
            "index": retriever.describe(),
        }
        return {"cases": rows, "aggregate": aggregate}

    def run_all(self, retriever=None) -> dict[str, Any]:
        result = {"decisions": self.run_decision_suite()}
        if retriever is not None:
            result["retrieval"] = self.run_retrieval_suite(retriever)
        return result
