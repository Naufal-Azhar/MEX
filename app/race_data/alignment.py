"""Distance-grid alignment for two telemetry laps with bounded interpolation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.race_data.loader import LapTelemetry

DEFAULT_STEP_M = 1.0
DEFAULT_MAX_GAP_S = 0.5


@dataclass
class AlignedLaps:
    distance_m: np.ndarray
    valid: np.ndarray
    speed_a_km_h: np.ndarray
    speed_b_km_h: np.ndarray
    throttle_a_pct: np.ndarray
    throttle_b_pct: np.ndarray
    brake_a: np.ndarray
    brake_b: np.ndarray
    time_a_s: np.ndarray
    time_b_s: np.ndarray
    coverage_ratio: float
    step_m: float
    max_gap_s: float

    def speed_delta_km_h(self) -> np.ndarray:
        return self.speed_b_km_h - self.speed_a_km_h


def _interpolate(
    lap: LapTelemetry,
    grid: np.ndarray,
    channel: np.ndarray,
    discrete: bool,
    max_gap_s: float,
) -> tuple[np.ndarray, np.ndarray]:
    distance = lap.distance_m
    if distance.size < 2:
        return np.full(grid.shape, np.nan), np.zeros(grid.shape, dtype=bool)

    valid = (grid >= distance[0]) & (grid <= distance[-1])
    indices = np.clip(np.searchsorted(distance, grid, side="right") - 1, 0, distance.size - 2)
    d0 = distance[indices]
    d1 = distance[indices + 1]
    span = d1 - d0
    time_gap = lap.time_s[indices + 1] - lap.time_s[indices]

    with np.errstate(divide="ignore", invalid="ignore"):
        weight = np.where(span > 0, (grid - d0) / span, 0.0)

    valid &= (span > 0) & np.isfinite(weight) & (time_gap <= max_gap_s)

    if discrete:
        values = np.where(weight < 0.5, channel[indices], channel[indices + 1])
    else:
        values = channel[indices] + weight * (channel[indices + 1] - channel[indices])

    values = np.where(valid, values, np.nan)
    return values, valid


def align_laps(
    lap_a: LapTelemetry,
    lap_b: LapTelemetry,
    step_m: float = DEFAULT_STEP_M,
    max_gap_s: float = DEFAULT_MAX_GAP_S,
) -> AlignedLaps:
    if step_m <= 0:
        raise ValueError("step_m must be positive")
    if max_gap_s <= 0:
        raise ValueError("max_gap_s must be positive")

    start = max(float(lap_a.distance_m[0]), float(lap_b.distance_m[0]))
    end = min(float(lap_a.distance_m[-1]), float(lap_b.distance_m[-1]))
    if end <= start:
        raise ValueError("the two laps have no overlapping distance coverage")

    grid = np.arange(start, end + step_m, step_m)

    speed_a, valid_a = _interpolate(lap_a, grid, lap_a.speed_km_h, False, max_gap_s)
    speed_b, valid_b = _interpolate(lap_b, grid, lap_b.speed_km_h, False, max_gap_s)
    throttle_a, _ = _interpolate(lap_a, grid, lap_a.throttle_pct, False, max_gap_s)
    throttle_b, _ = _interpolate(lap_b, grid, lap_b.throttle_pct, False, max_gap_s)
    brake_a, _ = _interpolate(lap_a, grid, lap_a.brake.astype(float), True, max_gap_s)
    brake_b, _ = _interpolate(lap_b, grid, lap_b.brake.astype(float), True, max_gap_s)
    time_a, _ = _interpolate(lap_a, grid, lap_a.time_s, False, max_gap_s)
    time_b, _ = _interpolate(lap_b, grid, lap_b.time_s, False, max_gap_s)

    valid = valid_a & valid_b
    span_a = float(lap_a.distance_m[-1] - lap_a.distance_m[0])
    span_b = float(lap_b.distance_m[-1] - lap_b.distance_m[0])
    shorter = min(span_a, span_b)
    overlap = float(end - start)
    coverage_ratio = round(overlap / shorter, 6) if shorter > 0 else 0.0

    return AlignedLaps(
        distance_m=grid,
        valid=valid,
        speed_a_km_h=speed_a,
        speed_b_km_h=speed_b,
        throttle_a_pct=throttle_a,
        throttle_b_pct=throttle_b,
        brake_a=brake_a,
        brake_b=brake_b,
        time_a_s=time_a,
        time_b_s=time_b,
        coverage_ratio=coverage_ratio,
        step_m=step_m,
        max_gap_s=max_gap_s,
    )
