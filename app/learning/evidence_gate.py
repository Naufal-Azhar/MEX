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
            missing.append(f"{lap_id}: urutan waktu tidak naik")
        if not quality.distance_monotonic:
            missing.append(f"{lap_id}: urutan jarak tidak naik")
        if quality.missing_channels:
            missing.append(f"{lap_id}: kanal data tidak tersedia: {', '.join(quality.missing_channels)}")
        if quality.sample_count < 2:
            missing.append(f"{lap_id}: sampel kurang dari dua")
        if quality.gaps:
            notes.append(f"{lap_id}: {len(quality.gaps)} celah sampel tidak diikutkan")

    coverage = pair.speed_delta.coverage_ratio if pair.speed_delta is not None else 0.0
    if coverage < MIN_COVERAGE:
        missing.append(f"Cakupan tumpang tindih {coverage:.3f} di bawah {MIN_COVERAGE}")
    else:
        notes.append(f"Cakupan tumpang tindih {coverage:.3f}")

    for lap in (pair.lap_a, pair.lap_b):
        if lap.deleted:
            missing.append(f"{lap.lap_id}: lap dibatalkan pengawas")
        if lap.accurate is False:
            notes.append(f"{lap.lap_id}: penyedia menandai lap kurang akurat")

    for lap_id, provenance in pair.provenance.items():
        if not provenance.provider or not provenance.telemetry_sha256:
            missing.append(f"{lap_id}: keterangan sumber tidak lengkap")

    notes.append("jarak berasal dari penyedia data; penyelarasan bersifat perkiraan")
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
            missing.append(f"{rule.rule_id}: kutipan sumber tidak ditemukan pada dokumen")

    notes = [
        "pemeriksaan kutipan hanya mencocokkan teks, bukan makna",
        "kesesuaian makna kutipan belum diaudit manual",
    ]
    return GateResult(passed=not missing, notes=notes, missing=missing), evidence
