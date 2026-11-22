"""Tests for approved reference data and provenance."""

from __future__ import annotations

import csv
import json
from pathlib import Path

REFERENCE = Path("datasets/reference")
RACEDATA = REFERENCE / "racedata"
ZENODO = REFERENCE / "zenodo-2024"
MANIFEST = Path("datasets/telemetry/manifest_2025_british_gp.json")
SOURCES = Path("datasets/telemetry/sources.json")


def _parse_lap_time(value: str) -> float:
    minutes, seconds = value.split(":")
    return int(minutes) * 60 + float(seconds)


def test_sources_registry_lists_three_approved_sources() -> None:
    payload = json.loads(SOURCES.read_text(encoding="utf-8"))
    by_id = {item["source_id"]: item for item in payload["sources"]}
    assert set(by_id) == {
        "tracinginsights-2025-british-gp",
        "zenodo-20061496",
        "tracinginsights-racedata",
    }
    assert by_id["zenodo-20061496"]["security"]["blocked_count"] > 0
    assert by_id["zenodo-20061496"]["license"] == "CC-BY-4.0"


def test_racedata_q3_times_match_telemetry_manifest() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = {lap["driver"]: lap["lap_time_s"] for lap in manifest["laps"]}

    with (RACEDATA / "races.csv").open(encoding="utf-8", newline="") as handle:
        race = next(
            row
            for row in csv.DictReader(handle)
            if row["year"] == "2025" and row["name"] == "British Grand Prix"
        )
    with (RACEDATA / "drivers.csv").open(encoding="utf-8", newline="") as handle:
        drivers = {row["driverId"]: row["code"] for row in csv.DictReader(handle)}
    with (RACEDATA / "qualifying.csv").open(encoding="utf-8", newline="") as handle:
        qualifying = {
            drivers[row["driverId"]]: row
            for row in csv.DictReader(handle)
            if row["raceId"] == race["raceId"] and drivers.get(row["driverId"]) in expected
        }

    assert set(qualifying) == {"VER", "NOR"}
    for driver, lap_time in expected.items():
        assert _parse_lap_time(qualifying[driver]["q3"]) == lap_time


def test_zenodo_extraction_is_data_only() -> None:
    report = json.loads((ZENODO / "extraction_report.json").read_text(encoding="utf-8"))
    assert report["extracted_count"] > 0
    assert report["blocked_count"] > 0
    assert (ZENODO / "gold_csv" / "sector_analysis.csv").exists()
    with (ZENODO / "gold_csv" / "sector_analysis.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert any(row["race_year"] == "2024" for row in rows)


def test_reference_tree_has_no_executable_or_pickle_files() -> None:
    blocked = {".exe", ".dll", ".bat", ".cmd", ".ps1", ".py", ".pyc", ".pkl", ".ff1pkl", ".duckdb", ".db"}
    assert not [
        path
        for path in REFERENCE.rglob("*")
        if path.is_file() and path.suffix.lower() in blocked
    ]
