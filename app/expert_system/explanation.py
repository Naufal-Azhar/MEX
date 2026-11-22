"""Deterministic, template-based explanations (no LLM involved)."""

from __future__ import annotations

from typing import Any

from app.schemas.results import (
    CheckReport,
    ConditionEvaluation,
    ExternalStatus,
    TraceNode,
    TruthValue,
)


def format_value(value: Any, unit: str | None = None) -> str:
    if value is None:
        return "tidak tersedia"
    if isinstance(value, bool):
        return "ya" if value else "tidak"
    if isinstance(value, float):
        text = f"{value:.4f}".rstrip("0").rstrip(".")
    else:
        text = str(value)
    return f"{text} {unit}".strip() if unit else text


def condition_text(condition: ConditionEvaluation) -> str:
    actual = format_value(condition.left_value, condition.unit)
    base = f"{condition.expression} (nilai: {actual}"
    if condition.right_value is not None:
        base += f", batas/nilai pembanding: {format_value(condition.right_value, condition.unit)}"
    base += ")"
    if condition.detail:
        base += f" — {condition.detail}"
    return base


def render_trace_text(trace: TraceNode, indent: int = 0) -> str:
    pad = "  " * indent
    lines = [
        f"{pad}- [{trace.status.value}] {trace.goal}"
        + (f" via {trace.rule_id}" if trace.rule_id else "")
        + (f" = {format_value(trace.value)}" if trace.value is not None else "")
    ]
    if trace.expression:
        lines.append(f"{pad}  hitung: {trace.expression}")
    for condition in trace.conditions:
        lines.append(f"{pad}  syarat: [{condition.status.value}] {condition_text(condition)}")
    for note in trace.notes:
        lines.append(f"{pad}  catatan: {note}")
    for child in trace.children:
        lines.append(render_trace_text(child, indent + 1))
    return "\n".join(lines)


def _source_text(report: CheckReport) -> str:
    if not report.source:
        return ""
    return (
        f"Pasal {report.source.article} "
        f"(halaman {report.source.page}) dari {report.source.document}, Issue {report.source.issue}"
    )


def build_explanation(report: CheckReport) -> str:
    source_text = _source_text(report)
    parts: list[str] = []

    if report.status is ExternalStatus.SATISFIED:
        parts.append(
            f"Spesifikasi memenuhi ketentuan {source_text}: syarat pada aturan "
            f"'{report.rule_name}' ({report.rule_id}) terbukti terpenuhi."
        )
    elif report.status is ExternalStatus.VIOLATED:
        parts.append(
            f"Spesifikasi TIDAK memenuhi ketentuan {source_text}: syarat pada aturan "
            f"'{report.rule_name}' ({report.rule_id}) terbukti dilanggar."
        )
    elif report.status is ExternalStatus.NOT_APPLICABLE:
        rule_text = f" Aturan: '{report.rule_name}' ({report.rule_id})." if report.rule_id else ""
        parts.append(
            f"Ketentuan {source_text} tidak berlaku untuk konteks yang diberikan.{rule_text} "
            "Sistem tidak menyatakan kepatuhan maupun pelanggaran."
        )
    elif report.status is ExternalStatus.UNSUPPORTED:
        diagnostic = report.diagnostics[0] if report.diagnostics else None
        message = diagnostic.message if diagnostic else "Permintaan berada di luar cakupan aturan tervalidasi."
        parts.append(f"Permintaan tidak dapat diputuskan: {message}")
        supported = diagnostic.details.get("supported_goals") if diagnostic else None
        if supported:
            parts.append("Goal yang didukung: " + ", ".join(supported) + ".")
    elif report.status is ExternalStatus.ERROR:
        parts.append("Terjadi kesalahan sistem. Tidak ada keputusan kepatuhan yang dibuat.")
    else:
        parts.append(
            f"Hasil pemeriksaan belum dapat ditentukan. Sistem tidak memiliki fakta atau bukti yang cukup "
            f"untuk membuktikan maupun menggagalkan aturan '{report.rule_name or '-'}'"
            + (f" ({report.rule_id})" if report.rule_id else "")
            + "."
        )
        if source_text:
            parts.append(f"Aturan yang dirujuk: {source_text}.")

    if report.validation_warning:
        parts.append(f"Peringatan validasi: {report.validation_warning}")

    if report.applicability_conditions:
        verdict = {
            TruthValue.TRUE: "terpenuhi",
            TruthValue.FALSE: "tidak terpenuhi",
            TruthValue.UNKNOWN: "belum dapat diperiksa",
        }
        items = [
            f"- {verdict[c.status]}: {condition_text(c)}"
            for c in report.applicability_conditions
        ]
        parts.append("Konteks penerapan aturan:\n" + "\n".join(items))

    if report.conditions:
        verdict = {
            TruthValue.TRUE: "terpenuhi",
            TruthValue.FALSE: "dilanggar",
            TruthValue.UNKNOWN: "belum dapat diperiksa",
        }
        items = [f"- {verdict[c.status]}: {condition_text(c)}" for c in report.conditions]
        parts.append("Kondisi yang diperiksa:\n" + "\n".join(items))

    if report.missing_facts:
        seen: set[str] = set()
        lines = []
        for missing in report.missing_facts:
            if missing.fact in seen:
                continue
            seen.add(missing.fact)
            unit = f" (satuan: {missing.expected_unit})" if missing.expected_unit else ""
            article = f", Pasal {missing.source_article}" if missing.source_article else ""
            lines.append(f"- {missing.fact}{unit}: {missing.reason}{article}")
        parts.append("Data yang masih diperlukan:\n" + "\n".join(lines))

    if report.citations:
        lines = []
        for citation in report.citations:
            status = "terverifikasi" if citation.verified else "TIDAK terverifikasi"
            lines.append(
                f"- Pasal {citation.article} (hlm. {citation.page}), {status}: \"{citation.quote}\""
            )
        parts.append("Kutipan pasal:\n" + "\n".join(lines))

    if report.rule_conflict:
        parts.append(
            "Peringatan: terdapat aturan berbeda yang menghasilkan kesimpulan berbeda. "
            "Sistem melaporkan hasil yang paling konservatif (pelanggaran)."
        )

    parts.append(
        "Cakupan: hasil ini hanya berlaku untuk ketentuan yang telah dimodelkan, "
        "bukan untuk seluruh kepatuhan teknis mobil F1."
    )
    return "\n\n".join(parts)
