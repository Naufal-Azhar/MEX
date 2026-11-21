"""Independent gold checks for telemetry features.

Expected values below were computed directly from the raw JSON with NumPy,
not with the production feature functions.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.race_data.loader import LapTelemetry, normalize_brake
from app.schemas.telemetry import LapIdentity, LapProvenance
from app.telemetry.features import (
    find_brake_onsets,
    find_throttle_onsets,
    longitudinal_speed_change_rate,
    max_speed,
    segment_elapsed_time,
)
from app.telemetry.service import TelemetryAnalysisService

MANIFEST = "datasets/telemetry/manifest.json"

GOLD = {
    "VER-Q-14": (331.0, 6, 312.05),
    "NOR-Q-16": (329.0, 6, 303.09),
    "PIA-Q-16": (328.0, 6, 310.56),
    "LEC-Q-17": (328.0, 6, 304.03),
    "HAM-Q-2": (326.0, 9, 308.14),
    "TSU-Q-16": (330.0, 7, 303.43),
}


@pytest.fixture(scope="module")
def service() -> TelemetryAnalysisService:
    return TelemetryAnalysisService.from_manifest(MANIFEST)


@pytest.mark.parametrize("lap_id,expected", GOLD.items())
def test_gold_max_speed_and_brake_onsets(service: TelemetryAnalysisService, lap_id: str, expected) -> None:
    lap = service.laps[lap_id]
    expected_speed, expected_count, first_onset = expected
    assert max_speed(lap).value == pytest.approx(expected_speed)
    onsets = find_brake_onsets(lap)
    assert len(onsets) == expected_count
    assert onsets[0].distance_m == pytest.approx(first_onset, abs=0.01)


def test_gold_segment_elapsed_time(service: TelemetryAnalysisService) -> None:
    assert segment_elapsed_time(service.laps["VER-Q-14"], 300, 600, max_gap_s=0.5) == pytest.approx(5.144, abs=0.001)
    assert segment_elapsed_time(service.laps["NOR-Q-16"], 300, 600, max_gap_s=0.5) == pytest.approx(5.132, abs=0.001)
    assert segment_elapsed_time(service.laps["VER-Q-14"], 1000, 1500, max_gap_s=0.5) == pytest.approx(8.537, abs=0.001)


def _synthetic_lap(time: np.ndarray, speed_kmh: np.ndarray, throttle: np.ndarray) -> LapTelemetry:
    distance = np.cumsum(np.r_[0.0, np.diff(time) * (speed_kmh[1:] / 3.6)])
    return LapTelemetry(
        identity=LapIdentity(
            lap_id="SYN-1",
            driver="SYN",
            lap_number=1,
            session="test",
            lap_time_s=float(time[-1]),
        ),
        provenance=LapProvenance(
            provider="test",
            repository="test",
            license="test",
            retrieved_at="2026-11-21",
            telemetry_sha256="0" * 64,
            source_file="test.json",
        ),
        time_s=time,
        speed_km_h=speed_kmh,
        throttle_pct=throttle,
        brake=normalize_brake(np.zeros(time.shape)),
        distance_m=distance,
        raw_channel_names=["time", "speed", "throttle", "brake", "distance"],
    )


def test_gold_longitudinal_rate_constant_acceleration() -> None:
    time = np.arange(0, 10.0, 0.1)
    speed_m_s = 10.0 + time
    lap = _synthetic_lap(time, speed_m_s * 3.6, np.full(time.shape, 50.0))
    rate = longitudinal_speed_change_rate(lap, window_s=0.5)
    assert rate[0] == pytest.approx(1.0, abs=0.01)


def test_gold_throttle_onset_pattern() -> None:
    time = np.arange(0, 1.3, 0.1)
    throttle = np.array([0, 0, 0, 0, 0, 95, 96, 0, 0, 95, 96, 97, 98], dtype=float)
    lap = _synthetic_lap(time, np.full(time.shape, 100.0), throttle)
    onsets = find_throttle_onsets(lap, low_pct=10, high_pct=90, debounce=2)
    assert len(onsets) == 2
