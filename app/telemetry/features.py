"""Deterministic telemetry feature extraction."""

from __future__ import annotations

import numpy as np

from app.race_data.alignment import AlignedLaps
from app.race_data.loader import LapTelemetry
from app.schemas.telemetry import (
    BrakeOnset,
    BrakeOnsetComparison,
    DataGap,
    DataQuality,
    FeatureStatus,
    FeatureValue,
    SpeedDeltaSummary,
)

DEFAULT_DEBOUNCE_SAMPLES = 2
DEFAULT_THROTTLE_LOW_PCT = 10.0
DEFAULT_THROTTLE_HIGH_PCT = 90.0
ALIGNMENT_UNCERTAINTY_M = 10.0
DEFAULT_INTERPOLATION_GAP_S = 0.5


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(mask):
        if value and start is None:
            start = index
        elif not value and start is not None:
            runs.append((start, index))
            start = None
    if start is not None:
        runs.append((start, mask.size))
    return runs


def find_brake_onsets(
    lap: LapTelemetry,
    debounce: int = DEFAULT_DEBOUNCE_SAMPLES,
) -> list[BrakeOnset]:
    if debounce < 1:
        raise ValueError("debounce must be at least one sample")
    onsets: list[BrakeOnset] = []
    for start, end in _runs(lap.brake):
        if end - start < debounce:
            continue
        onsets.append(
            BrakeOnset(
                distance_m=round(float(lap.distance_m[start]), 3),
                time_s=round(float(lap.time_s[start]), 3),
                speed_km_h=round(float(lap.speed_km_h[start]), 3),
                throttle_pct=round(float(lap.throttle_pct[start]), 3),
            )
        )
    return onsets


def find_throttle_onsets(
    lap: LapTelemetry,
    low_pct: float = DEFAULT_THROTTLE_LOW_PCT,
    high_pct: float = DEFAULT_THROTTLE_HIGH_PCT,
    debounce: int = DEFAULT_DEBOUNCE_SAMPLES,
) -> list[BrakeOnset]:
    if low_pct >= high_pct:
        raise ValueError("low_pct must be below high_pct")
    onsets: list[BrakeOnset] = []
    armed = False
    consecutive = 0
    candidate: int | None = None
    for index, throttle in enumerate(lap.throttle_pct):
        if throttle < low_pct:
            armed = True
            consecutive = 0
            candidate = None
            continue
        if not armed:
            continue
        if throttle >= high_pct:
            if consecutive == 0:
                candidate = index
            consecutive += 1
            if consecutive >= debounce and candidate is not None:
                onsets.append(
                    BrakeOnset(
                        distance_m=round(float(lap.distance_m[candidate]), 3),
                        time_s=round(float(lap.time_s[candidate]), 3),
                        speed_km_h=round(float(lap.speed_km_h[candidate]), 3),
                        throttle_pct=round(float(lap.throttle_pct[candidate]), 3),
                    )
                )
                armed = False
                consecutive = 0
                candidate = None
        else:
            consecutive = 0
            candidate = None
    return onsets


def max_speed(
    lap: LapTelemetry,
    start_m: float | None = None,
    end_m: float | None = None,
) -> FeatureValue:
    mask = np.ones(lap.speed_km_h.shape, dtype=bool)
    if start_m is not None:
        mask &= lap.distance_m >= start_m
    if end_m is not None:
        mask &= lap.distance_m <= end_m
    if not np.any(mask):
        return FeatureValue(
            name="max_speed",
            value=None,
            unit="km/h",
            status=FeatureStatus.INSUFFICIENT_DATA,
            detail=f"{lap.identity.lap_id}: tidak ada sampel pada rentang ini",
        )
    return FeatureValue(
        name="max_speed",
        value=round(float(np.max(lap.speed_km_h[mask])), 3),
        unit="km/h",
        status=FeatureStatus.OBSERVED,
        detail=lap.identity.lap_id,
    )


def data_quality(lap: LapTelemetry, interpolation_gap_s: float = DEFAULT_INTERPOLATION_GAP_S) -> DataQuality:
    dt = np.diff(lap.time_s)
    gaps: list[DataGap] = []
    if dt.size:
        gap_indices = np.where(dt > interpolation_gap_s)[0]
        for index in gap_indices:
            gaps.append(
                DataGap(
                    start_s=round(float(lap.time_s[index]), 3),
                    end_s=round(float(lap.time_s[index + 1]), 3),
                    duration_s=round(float(dt[index]), 3),
                )
            )
    required = {"time", "speed", "throttle", "brake", "distance"}
    missing = sorted(required.difference(lap.raw_channel_names)) if lap.raw_channel_names else []
    flags = ["derived_distance", "brake_indicator", "sampling"]
    if gaps:
        flags.append("sampling_gaps")
    return DataQuality(
        sample_count=len(lap),
        duration_s=round(float(lap.time_s[-1] - lap.time_s[0]), 3),
        distance_m=round(float(lap.distance_m[-1] - lap.distance_m[0]), 3),
        median_dt_s=round(float(np.median(dt)), 6) if dt.size else 0.0,
        max_gap_s=round(float(np.max(dt)), 6) if dt.size else 0.0,
        time_monotonic=bool(np.all(dt > 0)),
        distance_monotonic=bool(np.all(np.diff(lap.distance_m) >= -1e-9)),
        missing_channels=missing,
        gaps=gaps,
        interpolation_gap_s=interpolation_gap_s,
        uncertainty_flags=flags,
    )


def speed_delta_summary(aligned: AlignedLaps) -> SpeedDeltaSummary | None:
    mask = aligned.valid & np.isfinite(aligned.speed_a_km_h) & np.isfinite(aligned.speed_b_km_h)
    if not np.any(mask):
        return None
    delta = aligned.speed_b_km_h[mask] - aligned.speed_a_km_h[mask]
    distances = aligned.distance_m[mask]
    max_index = int(np.argmax(np.abs(delta)))
    return SpeedDeltaSummary(
        mean_km_h=round(float(np.mean(delta)), 3),
        min_km_h=round(float(np.min(delta)), 3),
        max_km_h=round(float(np.max(delta)), 3),
        max_abs_distance_m=round(float(distances[max_index]), 3),
        coverage_ratio=aligned.coverage_ratio,
        point_count=int(np.count_nonzero(mask)),
    )


def compare_brake_onsets(
    onsets_a: list[BrakeOnset],
    onsets_b: list[BrakeOnset],
    match_tolerance_m: float = 150.0,
    uncertainty_m: float = ALIGNMENT_UNCERTAINTY_M,
) -> list[BrakeOnsetComparison]:
    used_b: set[int] = set()
    comparisons: list[BrakeOnsetComparison] = []
    for onset_a in onsets_a:
        candidates = [
            (abs(onset_b.distance_m - onset_a.distance_m), index, onset_b)
            for index, onset_b in enumerate(onsets_b)
            if index not in used_b and abs(onset_b.distance_m - onset_a.distance_m) <= match_tolerance_m
        ]
        if not candidates:
            continue
        _, index, onset_b = min(candidates)
        used_b.add(index)
        delta = onset_b.distance_m - onset_a.distance_m
        comparisons.append(
            BrakeOnsetComparison(
                onset_a=onset_a,
                onset_b=onset_b,
                delta_m=round(delta, 3),
                within_alignment_uncertainty=abs(delta) <= uncertainty_m,
            )
        )
    return comparisons


def longitudinal_speed_change_rate(
    lap: LapTelemetry,
    window_s: float = 0.5,
) -> np.ndarray:
    if window_s <= 0:
        raise ValueError("window_s must be positive")
    speed_m_s = lap.speed_km_h / 3.6
    target_time = lap.time_s + window_s
    next_index = np.searchsorted(lap.time_s, target_time, side="left")
    valid = next_index < lap.time_s.size
    rate = np.full(lap.time_s.shape, np.nan)
    if np.any(valid):
        dt = lap.time_s[next_index[valid]] - lap.time_s[valid]
        dv = speed_m_s[next_index[valid]] - speed_m_s[valid]
        with np.errstate(divide="ignore", invalid="ignore"):
            rate[valid] = np.where(dt > 0, dv / dt, np.nan)
    return rate


def segment_elapsed_time(
    lap: LapTelemetry,
    start_m: float,
    end_m: float,
    max_gap_s: float,
) -> float | None:
    if end_m <= start_m:
        raise ValueError("end_m must be greater than start_m")
    if start_m < lap.distance_m[0] or end_m > lap.distance_m[-1]:
        return None
    for boundary in (start_m, end_m):
        index = int(np.searchsorted(lap.distance_m, boundary, side="right") - 1)
        index = min(max(index, 0), lap.distance_m.size - 2)
        if lap.time_s[index + 1] - lap.time_s[index] > max_gap_s:
            return None
    start_time = float(np.interp(start_m, lap.distance_m, lap.time_s))
    end_time = float(np.interp(end_m, lap.distance_m, lap.time_s))
    elapsed = end_time - start_time
    return round(elapsed, 3) if elapsed > 0 else None
