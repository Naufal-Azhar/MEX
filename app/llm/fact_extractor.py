"""Turn free text into structured facts.

Two extractors:
- ``DeterministicFactExtractor``: regex/keyword based, offline, no LLM.
- ``LLMFactExtractor``: asks the configured provider for strict JSON, then validates
  every field against the allowed fact specification. The LLM can never create or
  modify rules, and anything that fails validation is rejected and reported.
"""

from __future__ import annotations

import json
import re
from typing import Any

from app.config import Settings, load_settings
from app.llm.base import ChatMessage, LLMError, LLMProvider, get_provider
from app.schemas.fact_specs import FACT_SPECS
from app.schemas.facts import ExtractedFact, ExtractionResult

NUMBER = r"(\d+(?:[.,]\d+)?)"

UNIT_FACTORS = {
    "mm": ("length", 1.0),
    "cm": ("length", 10.0),
    "m": ("length", 1000.0),
    "kg": ("mass", 1.0),
    "g": ("mass", 0.001),
}

MEASUREMENT_KEYWORDS: dict[str, list[str]] = {
    "max_half_width_excluding_tyres_and_rims": [
        r"half[\s-]?width",
        r"setengah lebar",
        r"lebar maksimum",
        r"jarak maksimum[^.\n]{0,30}(bidang|plane)\s*y",
    ],
    "wheelbase": [r"wheelbase", r"jarak sumbu roda", r"jarak antar sumbu"],
    "cockpit_position_distance": [
        r"cockpit position",
        r"posisi kokpit",
        r"jarak[^.\n]{0,30}xa[^.\n]{0,30}xc",
    ],
    "car_mass": [r"car mass", r"massa mobil", r"berat mobil", r"massa total"],
    "nominal_tyre_mass": [r"nominal tyre mass", r"massa ban nominal", r"massa ban"],
    "front_axle_mass": [r"front axle mass", r"massa axle depan", r"massa poros depan"],
    "rear_axle_mass": [r"rear axle mass", r"massa axle belakang", r"massa poros belakang"],
}


def _to_float(value: str) -> float:
    return float(value.replace(",", "."))


def _convert_unit(value: float, from_unit: str, to_unit: str) -> float:
    from_dim, from_factor = UNIT_FACTORS[from_unit]
    to_dim, to_factor = UNIT_FACTORS[to_unit]
    if from_dim != to_dim:
        raise ValueError(f"unit {from_unit} cannot be converted to {to_unit}")
    return value * from_factor / to_factor


def _find_measurement(text: str, keywords: list[str]) -> tuple[float, str | None, str] | None:
    for keyword in keywords:
        for match in re.finditer(keyword, text, re.IGNORECASE):
            tail = text[match.end() : match.end() + 60]
            tail_match = re.search(NUMBER + r"\s*(mm|cm|m|kg|g)?", tail, re.IGNORECASE)
            if tail_match:
                value = _to_float(tail_match.group(1))
                unit = (tail_match.group(2) or "").lower() or None
                return value, unit, text[match.start() : match.end() + len(tail_match.group(0))]
            head = text[max(0, match.start() - 40) : match.start()]
            head_matches = list(re.finditer(NUMBER + r"\s*(mm|cm|m|kg|g)?", head, re.IGNORECASE))
            if head_matches:
                found = head_matches[-1]
                value = _to_float(found.group(1))
                unit = (found.group(2) or "").lower() or None
                return value, unit, text[max(0, match.start() - 40) : match.end()]
    return None


def _detect_session_type(text: str) -> tuple[str, str] | None:
    lowered = text.lower()
    ordered = [
        (r"sprint\s+qualifying|sq\b", "SQ"),
        (r"\bqualifying\b|\bkualifikasi\b", "Q"),
        (r"\bsprint\b", "SPRINT"),
        (r"\brace\b|\bbalapan\b|\blomba\b", "R"),
        (r"free\s+practice|latihan\s+bebas|\bfp[123]\b", "FP"),
    ]
    for pattern, label in ordered:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if match:
            return label, match.group(0)
    return None


def _detect_category(text: str) -> tuple[str, str] | None:
    match = re.search(r"\b(TTCS|LTCS)\b", text, re.IGNORECASE)
    if match:
        return match.group(1).upper(), match.group(0)
    return None


def _detect_boolean(text: str, subject_pattern: str) -> tuple[bool, str] | None:
    true_pattern = rf"{subject_pattern}[^.\n]{{0,50}}?(declared|dinyatakan|active|aktif)"
    false_pattern = rf"(no|tidak ada|tanpa)\s+{subject_pattern}"
    not_declared_pattern = rf"{subject_pattern}[^.\n]{{0,40}}?(not declared|tidak dinyatakan|not active|tidak aktif)"
    match = re.search(false_pattern, text, re.IGNORECASE)
    if match:
        return False, match.group(0)
    match = re.search(not_declared_pattern, text, re.IGNORECASE)
    if match:
        return False, match.group(0)
    match = re.search(true_pattern, text, re.IGNORECASE)
    if match:
        return True, match.group(0)
    return None


class DeterministicFactExtractor:
    name = "deterministic"

    def extract(self, text: str) -> ExtractionResult:
        result = ExtractionResult(provider=self.name)
        if not text.strip():
            result.notes.append("Empty input text.")
            return result

        for fact_name, keywords in MEASUREMENT_KEYWORDS.items():
            found = _find_measurement(text, keywords)
            if found is None:
                continue
            value, unit, evidence = found
            expected_unit = FACT_SPECS[fact_name]["unit"]
            if unit and unit != expected_unit:
                try:
                    value = _convert_unit(value, unit, expected_unit)
                except ValueError:
                    result.rejected.append(
                        {"name": fact_name, "value": value, "unit": unit, "reason": "incompatible unit"}
                    )
                    continue
                result.notes.append(f"Converted {fact_name} from {unit} to {expected_unit}.")
            elif unit is None:
                result.notes.append(f"No unit stated for {fact_name}; assumed {expected_unit}.")
            result.facts.append(
                ExtractedFact(
                    name=fact_name,
                    value=round(value, 4),
                    unit=expected_unit,
                    evidence=evidence.strip(),
                    confidence=0.9 if unit else 0.7,
                )
            )

        session = _detect_session_type(text)
        if session:
            result.facts.append(
                ExtractedFact(name="session_type", value=session[0], evidence=session[1], confidence=0.85)
            )

        category = _detect_category(text)
        if category:
            result.facts.append(
                ExtractedFact(name="session_category", value=category[0], evidence=category[1], confidence=0.9)
            )

        competition_heat = _detect_boolean(text, r"competition\s+heat\s+hazard")
        if competition_heat:
            result.facts.append(
                ExtractedFact(
                    name="competition_heat_hazard_declared",
                    value=competition_heat[0],
                    evidence=competition_heat[1],
                    confidence=0.8,
                )
            )

        session_heat = _detect_boolean(text, r"(?<!competition\s)heat\s+hazard")
        if session_heat:
            result.facts.append(
                ExtractedFact(
                    name="heat_hazard_declared",
                    value=session_heat[0],
                    evidence=session_heat[1],
                    confidence=0.8,
                )
            )

        if not result.facts:
            result.notes.append("Tidak ada data yang bisa dikenali dari teks itu.")
        result.notes.append(
            "Pembacaan teks bersifat perkiraan; periksa kembali data sebelum menjalankan pemeriksaan."
        )
        return result


SYSTEM_PROMPT = """You are a strict information extraction component.
Extract ONLY facts explicitly stated in the user text. Do not infer, calculate, or invent values.
Return a single JSON object and nothing else, with this shape:
{"facts": [{"name": "<allowed name>", "value": <number|string|boolean>, "unit": "<unit or null>", "evidence": "<short quote>"}],
 "unknown": ["<facts that are relevant but not stated>"]}
Use only the allowed fact names listed by the user. If a value is not stated, do not output it."""


class LLMFactExtractor:
    name = "llm"

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    @property
    def provider_name(self) -> str:
        return f"{self.provider.name}:{self.provider.model}"

    def extract(self, text: str) -> ExtractionResult:
        if not self.provider.is_configured():
            raise LLMError("LLM provider is not configured.")
        specs = json.dumps(FACT_SPECS, indent=2, ensure_ascii=False)
        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=f"Allowed fact specification:\n{specs}\n\nText:\n{text}"),
        ]
        raw = self.provider.complete(messages, temperature=0.0, max_tokens=800)
        result = ExtractionResult(provider=self.provider_name, raw_output=raw)
        payload = self._parse_json(raw)
        if payload is None:
            result.notes.append("LLM output was not valid JSON; no facts accepted.")
            return result

        for item in payload.get("facts", []):
            if not isinstance(item, dict):
                result.rejected.append({"item": item, "reason": "not an object"})
                continue
            name = item.get("name")
            spec = FACT_SPECS.get(name)
            if spec is None:
                result.rejected.append({"name": name, "reason": "unknown fact name"})
                continue
            value = item.get("value")
            if spec["kind"] == "number":
                if isinstance(value, bool) or not isinstance(value, (int, float, str)):
                    result.rejected.append({"name": name, "value": value, "reason": "not numeric"})
                    continue
                try:
                    value = float(str(value).replace(",", "."))
                except ValueError:
                    result.rejected.append({"name": name, "value": value, "reason": "not numeric"})
                    continue
            elif spec["kind"] == "boolean":
                if isinstance(value, str):
                    value = value.strip().lower() in ("true", "yes", "ya", "1")
                value = bool(value)
            elif spec["kind"] == "string":
                value = str(value)
                allowed = spec.get("allowed")
                if allowed and value not in allowed:
                    result.rejected.append({"name": name, "value": value, "reason": f"not in {allowed}"})
                    continue
            confidence = item.get("confidence")
            if not isinstance(confidence, (int, float)) or not (0 <= float(confidence) <= 1):
                confidence = None
            result.facts.append(
                ExtractedFact(
                    name=name,
                    value=value,
                    unit=item.get("unit") or spec.get("unit"),
                    evidence=item.get("evidence"),
                    confidence=confidence,
                )
            )
        unknown = payload.get("unknown")
        if isinstance(unknown, list) and unknown:
            result.notes.append("LLM reported relevant but unstated facts: " + ", ".join(map(str, unknown)))
        result.notes.append("LLM extraction validated against the allowed fact specification; verify before use.")
        return result

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any] | None:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None


def get_extractor(settings: Settings | None = None) -> DeterministicFactExtractor | LLMFactExtractor:
    settings = settings or load_settings()
    provider = get_provider(settings)
    if provider is not None and provider.is_configured():
        return LLMFactExtractor(provider)
    return DeterministicFactExtractor()
