"""Two-layer evidence gate: data sufficiency and knowledge traceability."""

from __future__ import annotations

from pathlib import Path

from app.schemas.analysis import EvidenceReference, GateResult
from app.schemas.rules import Rule
from app.schemas.telemetry import LapPairAnalysis

MIN_COVERAGE = 0.8


def evaluate_data_gate(pair: LapPairAnalysis) -> GateResult:
    missing: list[str] = []
    notes: list[str] = []

    for lap_id, quality in pair.quality.items():
        if not quality.time_monotonic:
            missing.append(f"{lap_id}: time is not monotonic")
        if not quality.distance_monotonic:
            missing.append(f"{lap_id}: distance is not monotonic")
        if quality.missing_channels:
            missing.append(f"{lap_id}: missing channels {', '.join(quality.missing_channels)}")
        if quality.sample_count < 2:
            missing.append(f"{lap_id}: fewer than two samples")
        if quality.gaps:
            notes.append(f"{lap_id}: {len(quality.gaps)} sampling gap(s) excluded or flagged")

    coverage = pair.speed_delta.coverage_ratio if pair.speed_delta is not None else 0.0
    if coverage < MIN_COVERAGE:
        missing.append(f"overlap coverage {coverage:.3f} is below {MIN_COVERAGE}")
    else:
        notes.append(f"overlap coverage {coverage:.3f}")

    for lap_id, provenance in pair.provenance.items():
        if not provenance.provider or not provenance.telemetry_sha256:
            missing.append(f"{lap_id}: provenance is incomplete")

    notes.append("distance is provider-derived; alignment uncertainty applies")
    return GateResult(passed=not missing, notes=notes, missing=missing)


def _normalise(text: str) -> str:
    return " ".join(text.split()).lower()


def evaluate_knowledge_gate(
    pairs: list[tuple[Rule, str]],
    corpus_paths: list[Path | str],
) -> tuple[GateResult, list[EvidenceReference]]:
    corpus = []
    for path in corpus_paths:
        source = Path(path)
        if source.exists():
            corpus.append(_normalise(source.read_text(encoding="utf-8")))
    combined = "\n".join(corpus)

    evidence: list[EvidenceReference] = []
    missing: list[str] = []
    for rule, _goal in pairs:
        quote = _normalise(rule.source.quote)
        found = bool(quote) and quote in combined
        evidence.append(
            EvidenceReference(
                rule_id=rule.rule_id,
                document_id=rule.source.document_id,
                article=rule.source.article,
                quote=rule.source.quote,
                quote_found=found,
                semantic_support_verified=False,
            )
        )
        if not found:
            missing.append(f"{rule.rule_id}: source quote not found in the corpus")

    notes = [
        "quote verification checks string presence only; it does not prove semantic entailment",
        "semantic support has not been manually audited",
    ]
    return GateResult(passed=not missing, notes=notes, missing=missing), evidence
