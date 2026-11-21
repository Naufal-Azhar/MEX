"""Unit handling shared by the fact validator and the rule engine."""

from __future__ import annotations

from typing import Any


class UnitMismatch(ValueError):
    pass


UNIT_TABLE: dict[str, tuple[str, float]] = {
    # unit -> (dimension, factor to the dimension's base unit)
    "mm": ("length", 1.0),
    "cm": ("length", 10.0),
    "m": ("length", 1000.0),
    "kg": ("mass", 1.0),
    "g": ("mass", 0.001),
    "t": ("mass", 1000.0),
    "s": ("time", 1.0),
    "deg": ("angle", 1.0),
    "%": ("percent", 1.0),
}


def convert_unit(value: int | float, from_unit: str, to_unit: str) -> float:
    if from_unit == to_unit:
        return float(value)
    if from_unit not in UNIT_TABLE or to_unit not in UNIT_TABLE:
        raise UnitMismatch(f"unknown unit: {from_unit!r} -> {to_unit!r}")
    from_dim, from_factor = UNIT_TABLE[from_unit]
    to_dim, to_factor = UNIT_TABLE[to_unit]
    if from_dim != to_dim:
        raise UnitMismatch(f"incompatible units: {from_unit!r} ({from_dim}) vs {to_unit!r} ({to_dim})")
    return float(value) * from_factor / to_factor


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
