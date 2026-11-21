"""Tests for telemetry loading, validation, alignment and deterministic features."""

from __future__ import annotations

import numpy as np
import pytest

from app.race_data.alignment import align_laps
from app.race_data.loader import LapTelemetry, normalize_brake, load_session_registry
from app.race_data.validation import validate_lap
from app.schemas.telemetry import LapIdentity, LapProvenance
from app.telemetry.features import (
    compare_brake_onsets,
    data_quality,
    find_brake_onsets,
    find_throttle_onsets,
    longitudinal_speed_change_rate,
    max_speed,
    segment_elapsed_time,
    speed_delta_summary,
)
from app.telemetry.plots import save_comparison_plot
from app.telemetry.service import TelemetryAnalysisService

MANIFEST = "datasets/telemetry/manifest.json"
BRITISH_MANIFEST = "datasets/telemetry/manifest_2025_british_gp.json"


def make_lap(
    *,
    driver: str = "TST",
    distances: np.ndarray | None = None,
    times: np.ndarray | None = None,
    speeds: np.ndarray | None = None,
    throttles: np.ndarray | None = None,
    brakes: np.ndarray | None = None,
) -> LapTelemetry:
    distance = np.asarray(distances if distances is not None else np.arange(0, 101, 1.0), dtype=float)
    time = np.asarray(times if times is not None else distance / 10.0, dtype=float)
    speed = np.asarray(speeds if speeds is not None else np.full(distance.shape, 100.0), dtype=float)
    throttle = np.asarray(
        throttles if throttles is not None else np.full(distance.shape, 50.0), dtype=float
    )
    brake_raw = np.asarray(brakes if brakes is not None else np.zeros(distance.shape), dtype=float)
    return LapTelemetry(
        identity=LapIdentity(
            lap_id=f"{driver}-test",
            driver=driver,
            lap_number=1,
            session="test",
            lap_time_s=float(time[-1] - time[0]),
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
        speed_km_h=speed,
        throttle_pct=throttle,
        brake=normalize_brake(brake_raw),
        distance_m=distance,
        gear=None,
        drs=None,
        raw_channel_names=["time", "speed", "throttle", "brake", "distance"],
    )


@pytest.fixture(scope="module")
def service() -> TelemetryAnalysisService:
    return TelemetryAnalysisService.from_manifest(MANIFEST)


def test_manifest_loads_multiple_real_laps(service: TelemetryAnalysisService) -> None:
    laps = service.available_laps()
    assert len(laps) == 7
    assert {lap["lap_id"] for lap in laps} == {
        "VER-Q-14",
        "NOR-Q-16",
        "PIA-Q-16",
        "LEC-Q-17",
        "HAM-Q-2",
        "GAS-Q-4",
        "TSU-Q-16",
    }


def test_manifest_lap_categories(service: TelemetryAnalysisService) -> None:
    by_id = {lap["lap_id"]: lap for lap in service.available_laps()}
    assert by_id["HAM-Q-2"]["compound"] == "MEDIUM"
    assert by_id["TSU-Q-16"]["deleted"] is True
    assert by_id["GAS-Q-4"]["accurate"] is False
    assert by_id["GAS-Q-4"]["category"] == "invalid_distance"
    assert by_id["PIA-Q-16"]["category"] == "clean_fast"


def test_real_laps_pass_validation_or_are_known_invalid(service: TelemetryAnalysisService) -> None:
    for lap in service.laps.values():
        report = validate_lap(lap)
        if lap.identity.category == "invalid_distance":
            assert not report.ok
            assert any("distance" in error for error in report.errors)
        else:
            assert report.ok, report.errors


def test_real_lap_sample_counts(service: TelemetryAnalysisService) -> None:
    assert len(service.laps["VER-Q-14"]) == 617
    assert len(service.laps["NOR-Q-16"]) == 623


def test_real_brake_onsets(service: TelemetryAnalysisService) -> None:
    assert len(find_brake_onsets(service.laps["VER-Q-14"])) == 6
    assert len(find_brake_onsets(service.laps["NOR-Q-16"])) == 6


def test_brake_debounce_rejects_single_sample_spike() -> None:
    brakes = np.zeros(21)
    brakes[10] = 1
    lap = make_lap(brakes=brakes)
    assert find_brake_onsets(lap, debounce=2) == []
    assert len(find_brake_onsets(lap, debounce=1)) == 1


def test_brake_encoding_equivalence() -> None:
    raw_boolean = np.array([0, 0, 1, 1, 0, 1, 1], dtype=float)
    raw_percent = raw_boolean * 100
    assert np.array_equal(normalize_brake(raw_boolean), normalize_brake(raw_percent))


def test_max_speed_real_values(service: TelemetryAnalysisService) -> None:
    assert max_speed(service.laps["VER-Q-14"]).value == pytest.approx(331.0)
    assert max_speed(service.laps["NOR-Q-16"]).value == pytest.approx(329.0)


def test_speed_delta_sign_and_unit() -> None:
    lap_a = make_lap(driver="A", speeds=np.full(101, 100.0))
    lap_b = make_lap(driver="B", speeds=np.full(101, 110.0))
    aligned = align_laps(lap_a, lap_b)
    summary = speed_delta_summary(aligned)
    assert summary is not None
    assert summary.mean_km_h == pytest.approx(10.0)
    assert summary.min_km_h == pytest.approx(10.0)
    assert summary.max_km_h == pytest.approx(10.0)


def test_alignment_excludes_long_gap() -> None:
    time = np.arange(0, 101, 1.0) / 10.0
    time[51:] += 5.0
    lap = make_lap(times=time)
    aligned = align_laps(lap, lap, max_gap_s=0.25)
    assert not np.all(aligned.valid)
    invalid = np.where(~aligned.valid)[0]
    assert invalid.size > 0
    assert 40 <= invalid[0] <= 60


def test_segment_elapsed_time_linear_fixture() -> None:
    lap = make_lap()
    assert segment_elapsed_time(lap, 10.0, 60.0, max_gap_s=0.25) == pytest.approx(5.0)


def test_segment_elapsed_time_outside_coverage() -> None:
    lap = make_lap()
    assert segment_elapsed_time(lap, 90.0, 150.0, max_gap_s=0.25) is None


def test_throttle_onsets_detected(service: TelemetryAnalysisService) -> None:
    assert len(find_throttle_onsets(service.laps["VER-Q-14"])) >= 1
    assert len(find_throttle_onsets(service.laps["NOR-Q-16"])) >= 1


def test_longitudinal_rate_shape(service: TelemetryAnalysisService) -> None:
    rate = longitudinal_speed_change_rate(service.laps["VER-Q-14"])
    assert rate.shape == service.laps["VER-Q-14"].time_s.shape
    assert np.isfinite(rate).any()


def test_quality_reports_gaps() -> None:
    time = np.arange(0, 101, 1.0) / 10.0
    time[51:] += 5.0
    lap = make_lap(times=time)
    quality = data_quality(lap, interpolation_gap_s=0.25)
    assert quality.sample_count == 101
    assert quality.gaps
    assert "sampling_gaps" in quality.uncertainty_flags


def test_brake_onset_comparison_uncertainty() -> None:
    lap_a = make_lap(driver="A", brakes=np.r_[np.zeros(10), np.ones(3), np.zeros(88)])
    lap_b = make_lap(driver="B", brakes=np.r_[np.zeros(15), np.ones(3), np.zeros(83)])
    comparisons = compare_brake_onsets(find_brake_onsets(lap_a), find_brake_onsets(lap_b))
    assert len(comparisons) == 1
    assert comparisons[0].delta_m == pytest.approx(5.0)
    assert comparisons[0].within_alignment_uncertainty is True


def test_unknown_lap_raises(service: TelemetryAnalysisService) -> None:
    with pytest.raises(KeyError):
        service.analyze("missing", "VER-Q-14")


def test_analysis_report_contains_provenance_and_quality(service: TelemetryAnalysisService) -> None:
    report = service.analyze("VER-Q-14", "NOR-Q-16")
    assert report.data_kind == "recorded_public_fixture"
    assert set(report.provenance) == {"VER-Q-14", "NOR-Q-16"}
    assert report.quality["VER-Q-14"].sample_count == 617
    assert report.speed_delta is not None
    assert report.speed_delta.coverage_ratio > 0.8
    assert report.brake_onset_comparisons


def test_comparison_plot_written(service: TelemetryAnalysisService, tmp_path) -> None:
    aligned = align_laps(service.laps["VER-Q-14"], service.laps["NOR-Q-16"])
    destination = save_comparison_plot(aligned, tmp_path / "comparison.png", "test")
    assert destination.exists()
    assert destination.stat().st_size > 1000


def test_session_registry_has_two_sessions() -> None:
    registry = load_session_registry()
    assert registry["default_session_id"] == "2025-abu-dhabi-qualifying"
    assert [entry["session_id"] for entry in registry["sessions"]] == [
        "2025-abu-dhabi-qualifying",
        "2025-british-gp-qualifying",
    ]


def test_british_session_loads_and_validates() -> None:
    british = TelemetryAnalysisService.from_manifest(BRITISH_MANIFEST)
    assert british.session_id == "2025-british-gp-qualifying"
    assert set(british.laps) == {"VER-GBR-Q-17", "NOR-GBR-Q-19"}
    assert len(british.laps["VER-GBR-Q-17"]) == 639
    assert len(british.laps["NOR-GBR-Q-19"]) == 626
    for lap in british.laps.values():
        assert validate_lap(lap).ok
    assert max_speed(british.laps["VER-GBR-Q-17"]).value == pytest.approx(324.0)
    assert max_speed(british.laps["NOR-GBR-Q-19"]).value == pytest.approx(319.0)
