"""Allowed input facts, their units, and validation rules.

The LLM may only propose these facts; the validator here is the single source of
truth for names, types, units and allowed values.
"""

from __future__ import annotations

import math
from typing import Any

from app.schemas.units import UnitMismatch, convert_unit


class FactValidationError(ValueError):
    def __init__(self, name: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.name = name
        self.code = "INVALID_INPUT"
        self.details = details or {}


class FactBatchValidationError(ValueError):
    code = "INVALID_INPUT"

    def __init__(self, errors: list[FactValidationError]) -> None:
        self.errors = errors
        super().__init__("; ".join(str(error) for error in errors))


FACT_SPECS: dict[str, dict[str, Any]] = {
    "max_half_width_excluding_tyres_and_rims": {
        "kind": "number",
        "unit": "mm",
        "min_value": 0,
        "description": "Maximum |Y| distance of any car part from plane Y=0, excluding tyres, wheel rims and rim attachments (C2.3.1).",
    },
    "wheelbase": {
        "kind": "number",
        "unit": "mm",
        "min_value": 0,
        "description": "Distance between plane XF=0 and plane XR=0 (C2.3.3).",
    },
    "cockpit_position_distance": {
        "kind": "number",
        "unit": "mm",
        "min_value": 0,
        "description": "Distance between plane XA=0 and plane XC=0 (C2.3.5).",
    },
    "car_mass": {
        "kind": "number",
        "unit": "kg",
        "min_value": 0,
        "description": "Car Mass (C4.1).",
    },
    "nominal_tyre_mass": {
        "kind": "number",
        "unit": "kg",
        "min_value": 0,
        "description": "Nominal Tyre Mass as published by the tyre provider (C4.7, Appendix C1).",
    },
    "front_axle_mass": {
        "kind": "number",
        "unit": "kg",
        "min_value": 0,
        "description": "Mass measured at the front axle (C4.2).",
    },
    "rear_axle_mass": {
        "kind": "number",
        "unit": "kg",
        "min_value": 0,
        "description": "Mass measured at the rear axle (C4.2).",
    },
    "session_type": {
        "kind": "string",
        "allowed": ["Q", "SQ", "R", "FP", "SPRINT", "OTHER"],
        "description": "Q = Qualifying, SQ = Sprint Qualifying, R = Race, etc.",
    },
    "session_category": {
        "kind": "string",
        "allowed": ["TTCS", "LTCS"],
        "description": "Session category used by the Heat Hazard provisions (C4.6).",
    },
    "heat_hazard_declared": {
        "kind": "boolean",
        "description": "Whether a Heat Hazard has been declared for the session.",
    },
    "competition_heat_hazard_declared": {
        "kind": "boolean",
        "description": "Whether a Heat Hazard has been declared for any session of the Competition.",
    },
}

ALLOWED_FACT_NAMES = frozenset(FACT_SPECS)


def validate_and_normalize(name: str, value: Any, unit: str | None) -> tuple[Any, str | None]:
    """Validate one fact and convert it to the canonical unit used by the rules."""
    spec = FACT_SPECS.get(name)
    if spec is None:
        raise FactValidationError(
            name,
            f"Unsupported fact '{name}'.",
            {"allowed_facts": sorted(ALLOWED_FACT_NAMES)},
        )

    kind = spec["kind"]
    if kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise FactValidationError(name, f"Fact '{name}' must be numeric.", {"value": value})
        number = float(value)
        if not math.isfinite(number):
            raise FactValidationError(name, f"Fact '{name}' must be finite.", {"value": value})
        minimum = spec.get("min_value")
        if minimum is not None and number < minimum:
            raise FactValidationError(
                name,
                f"Fact '{name}' must be >= {minimum} {spec.get('unit', '')}.".strip(),
                {"value": value, "min_value": minimum},
            )
        expected_unit = spec.get("unit")
        if not unit:
            raise FactValidationError(
                name,
                f"Fact '{name}' requires a unit.",
                {"expected_unit": expected_unit},
            )
        try:
            converted = convert_unit(number, unit, expected_unit)
        except UnitMismatch as exc:
            raise FactValidationError(
                name,
                str(exc),
                {"unit": unit, "expected_unit": expected_unit},
            ) from exc
        return converted, expected_unit

    if kind == "boolean":
        if not isinstance(value, bool):
            raise FactValidationError(name, f"Fact '{name}' must be boolean.", {"value": value})
        return value, None

    if kind == "string":
        if not isinstance(value, str):
            raise FactValidationError(name, f"Fact '{name}' must be a string.", {"value": value})
        normalized = value.strip().upper() if spec.get("allowed") else value
        allowed = spec.get("allowed")
        if allowed and normalized not in allowed:
            raise FactValidationError(
                name,
                f"Fact '{name}' must be one of {allowed}.",
                {"value": value},
            )
        return normalized, None

    raise FactValidationError(name, f"Fact '{name}' has an unsupported specification.")
