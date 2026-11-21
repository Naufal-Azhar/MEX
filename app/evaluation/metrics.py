"""Evaluation metrics used by the prototype."""

from __future__ import annotations

from collections import Counter
from typing import Iterable


def classification_metrics(
    y_true: list[str], y_pred: list[str], labels: list[str] | None = None, positive: str = "FALSE"
) -> dict:
    labels = labels or ["TRUE", "FALSE", "UNKNOWN"]
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    total = len(y_true)
    accuracy = sum(t == p for t, p in zip(y_true, y_pred)) / total if total else 0.0

    per_label = {}
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_label[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": sum(1 for t in y_true if t == label),
        }

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p == positive)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != positive and p == positive)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p != positive)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    confusion = Counter(zip(y_true, y_pred))
    return {
        "accuracy": round(accuracy, 4),
        "positive_label": positive,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "per_label": per_label,
        "confusion": {f"{t}->{p}": count for (t, p), count in sorted(confusion.items())},
        "count": total,
    }


def set_precision_recall_f1(expected: Iterable[str], actual: Iterable[str]) -> dict:
    expected_set = set(expected)
    actual_set = set(actual)
    tp = len(expected_set & actual_set)
    precision = tp / len(actual_set) if actual_set else (1.0 if not expected_set else 0.0)
    recall = tp / len(expected_set) if expected_set else (1.0 if not actual_set else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "expected": sorted(expected_set),
        "actual": sorted(actual_set),
    }


def retrieval_metrics(expected_articles: list[str], hit_articles: list[str], k: int) -> dict:
    top = hit_articles[:k]
    expected = set(expected_articles)
    found = [article for article in top if article in expected]
    precision = len(found) / len(top) if top else 0.0
    recall = len(set(found)) / len(expected) if expected else 0.0
    reciprocal_rank = 0.0
    for rank, article in enumerate(top, start=1):
        if article in expected:
            reciprocal_rank = 1.0 / rank
            break
    return {
        "hit": 1.0 if found else 0.0,
        "precision_at_k": round(precision, 4),
        "recall_at_k": round(recall, 4),
        "reciprocal_rank": round(reciprocal_rank, 4),
    }
