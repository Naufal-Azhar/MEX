"""Deterministic validation for loaded telemetry laps."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.race_data.loader import LapTelemetry


class LapValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_lap(
    lap: LapTelemetry,
    speed_range: tuple[float, float] = (0.0, 400.0),
    duration_range: tuple[float, float] = (20.0, 300.0),
) -> ValidationReport:
    report = ValidationReport()
    arrays = {
        "time": lap.time_s,
        "speed": lap.speed_km_h,
        "throttle": lap.throttle_pct,
        "distance": lap.distance_m,
    }
    lengths = {name: values.size for name, values in arrays.items()}
    if len(set(lengths.values())) != 1:
        report.errors.append(f"channel lengths differ: {lengths}")
        return report
    if lap.time_s.size < 2:
        report.errors.append("at least two samples are required")
        return report

    for name, values in arrays.items():
        if not np.all(np.isfinite(values)):
            report.errors.append(f"channel '{name}' contains non-finite values")

    dt = np.diff(lap.time_s)
    if np.any(dt <= 0):
        report.errors.append("time is not strictly increasing")

    dd = np.diff(lap.distance_m)
    if np.any(dd < -1e-9):
        report.errors.append("distance is not non-decreasing")

    if np.any(lap.speed_km_h < speed_range[0]) or np.any(lap.speed_km_h > speed_range[1]):
        report.errors.append(f"speed outside [{speed_range[0]}, {speed_range[1]}] km/h")
    if np.any(lap.throttle_pct < 0) or np.any(lap.throttle_pct > 100):
        report.errors.append("throttle outside [0, 100] percent")

    duration = float(lap.time_s[-1] - lap.time_s[0])
    if not duration_range[0] <= duration <= duration_range[1]:
        report.errors.append(f"lap duration {duration:.3f}s outside {duration_range}")

    if lap.brake.dtype != bool:
        report.errors.append("brake channel was not normalised to boolean")

    if dt.size and float(np.max(dt)) > 5 * float(np.median(dt)):
        report.warnings.append("maximum sample gap exceeds five times the median interval")

    return report


def ensure_valid_lap(lap: LapTelemetry) -> ValidationReport:
    report = validate_lap(lap)
    if not report.ok:
        raise LapValidationError(report.errors)
    return report
