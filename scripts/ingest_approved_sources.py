"""Ingest the three approved sources without executing any downloaded code."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.race_data.loader import load_manifest_laps  # noqa: E402
from app.race_data.validation import validate_lap  # noqa: E402

QUARANTINE = ROOT / "storage" / "quarantine"
RAW = ROOT / "datasets" / "telemetry" / "raw" / "tracinginsights" / "2025-british-gp-qualifying"
TELEMETRY_DIR = ROOT / "datasets" / "telemetry"
REFERENCE = ROOT / "datasets" / "reference"
SOURCES = TELEMETRY_DIR / "sources.json"
SESSIONS = TELEMETRY_DIR / "sessions.json"

BRITISH_QUARANTINE = QUARANTINE / "tracinginsights-2025-british-gp"
ZENODO_ZIP = QUARANTINE / "zenodo-20061496" / "F1-telemetry-DE-v1.0.0-is547-final.zip"
RACEDATA_ZIP = QUARANTINE / "tracinginsights-racedata" / "data.zip"

BRITISH_FILES = {
    "VER_17_tel.json": "British Grand Prix__Qualifying__VER__17_tel.json",
    "NOR_19_tel.json": "British Grand Prix__Qualifying__NOR__19_tel.json",
    "VER_laptimes.json": "British Grand Prix__Qualifying__VER__laptimes.json",
    "NOR_laptimes.json": "British Grand Prix__Qualifying__NOR__laptimes.json",
}
ZENODO_ALLOWED_SUFFIXES = {".csv", ".md", ".json"}
ZENODO_ALLOWED_PREFIXES = (
    "anandm84-F1-telemetry-DE-592e162/docs/curation/",
)
ZENODO_ALLOWED_DATA_PREFIX = "anandm84-F1-telemetry-DE-592e162/docs/curation/sample_output/gold_csv/"
ZENODO_BLOCKED_SUFFIXES = {".exe", ".dll", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".py", ".pyc", ".pkl", ".ff1pkl", ".joblib", ".duckdb", ".db", ".msi", ".scr"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_sums(directory: Path) -> None:
    lines = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            lines.append(f"{sha256(path)}  {path.relative_to(directory).as_posix()}")
    (directory / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def ingest_british_session() -> dict:
    RAW.mkdir(parents=True, exist_ok=True)
    for target, source_name in BRITISH_FILES.items():
        source = BRITISH_QUARANTINE / source_name
        if not source.exists():
            raise FileNotFoundError(source)
        shutil.copy2(source, RAW / target)
    verdict = json.loads((BRITISH_QUARANTINE / "British Grand Prix__Qualifying__VER__laptimes.json").read_text(encoding="utf-8"))
    nor_verdict = json.loads((BRITISH_QUARANTINE / "British Grand Prix__Qualifying__NOR__laptimes.json").read_text(encoding="utf-8"))
    assert verdict["del"][17 - 1] is False
    assert nor_verdict["del"][19 - 1] is False

    laps = []
    telemetry_path = RAW / "VER_17_tel.json"
    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))["tel"]
    nor_path = RAW / "NOR_19_tel.json"
    nor = json.loads(nor_path.read_text(encoding="utf-8"))["tel"]
    for lap_id, driver, number, path, tel, lap_time, samples in [
        ("VER-GBR-Q-17", "VER", 17, telemetry_path, telemetry, 84.892, len(telemetry["time"])),
        ("NOR-GBR-Q-19", "NOR", 19, nor_path, nor, 85.01, len(nor["time"])),
    ]:
        laps.append(
            {
                "lap_id": lap_id,
                "driver": driver,
                "category": "clean_fast",
                "team": "Red Bull Racing" if driver == "VER" else "McLaren",
                "lap_number": number,
                "qualifying_phase": "Q3",
                "compound": "SOFT",
                "tyre_life_laps": 2,
                "lap_time_s": lap_time,
                "accurate": True,
                "deleted": False,
                "telemetry_file": f"raw/tracinginsights/2025-british-gp-qualifying/{path.name}",
                "telemetry_sha256": sha256(path).lower(),
                "lap_metadata_file": f"raw/tracinginsights/2025-british-gp-qualifying/{driver}_laptimes.json",
                "lap_metadata_sha256": sha256(RAW / f"{driver}_laptimes.json").lower(),
                "samples": samples,
                "duration_s": float(tel["time"][-1] - tel["time"][0]),
                "distance_m": float(tel["distance"][-1]),
                "channels": list(tel.keys()),
            }
        )

    manifest = {
        "dataset_id": "tracinginsights-2025-british-gp-qualifying-ver17-nor19",
        "session_id": "2025-british-gp-qualifying",
        "data_kind": "recorded_public_fixture",
        "provider": "TracingInsights",
        "provider_repository": "https://github.com/TracingInsights-Archive/2025",
        "provider_site": "https://tracinginsights.com/data",
        "license": "Apache-2.0",
        "license_url": "https://github.com/TracingInsights-Archive/2025/blob/main/LICENSE",
        "usage_note": "Provider README permits free use for data analysis, research, academic work and personal applications; attribution appreciated but not required.",
        "retrieved_at_utc": "2026-11-21",
        "retrieval_method": "raw.githubusercontent.com HTTPS download (no authentication)",
        "session": {
            "season": 2025,
            "event": "British Grand Prix",
            "session_type": "Qualifying",
            "source_path": "British Grand Prix/Qualifying",
        },
        "laps": laps,
        "data_dictionary": {
            "time": "seconds from lap sample start; verified strictly increasing",
            "speed": "km/h",
            "throttle": "percent 0-100",
            "brake": "0/1 indicator",
            "gear": "discrete gear number",
            "drs": "provider-specific DRS indicator; not used in MVP features",
            "distance": "meters, provider-derived",
            "DriverAhead": "string 'None' used as missing marker",
            "acc_x/acc_y/acc_z": "provider-computed acceleration channels; not used in MVP features",
        },
        "caveats": [
            "Telemetry is redistributed by a third party and was originally collected via FastF1; provenance beyond the repository is not independently verifiable.",
            "Distance is derived from telemetry integration; cross-lap alignment remains approximate.",
            "Brake is a boolean indicator, not brake pressure.",
            "Both laps are Q3 and SOFT, but track evolution, fuel load, tyre state and driver intent still differ.",
            "This comparison is descriptive; it does not establish a cause or a better driver.",
        ],
    }
    (TELEMETRY_DIR / "manifest_2025_british_gp.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    loaded = load_manifest_laps(TELEMETRY_DIR / "manifest_2025_british_gp.json")
    reports = {lap_id: validate_lap(lap) for lap_id, lap in loaded.items()}
    for lap_id, report in reports.items():
        if not report.ok:
            raise ValueError(f"{lap_id} validation failed: {report.errors}")
    write_sums(RAW)
    return {
        "session_id": manifest["session_id"],
        "laps": list(loaded),
        "samples": {lap_id: len(lap) for lap_id, lap in loaded.items()},
        "validation": {lap_id: report.ok for lap_id, report in reports.items()},
        "warnings": {lap_id: report.warnings for lap_id, report in reports.items()},
    }


def ingest_zenodo() -> dict:
    destination = REFERENCE / "zenodo-2024"
    destination.mkdir(parents=True, exist_ok=True)
    extracted = []
    skipped_blocked = []
    with zipfile.ZipFile(ZENODO_ZIP) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            member = PurePosixPath(info.filename)
            if ".." in member.parts:
                raise ValueError(f"path traversal in ZIP: {info.filename}")
            suffix = member.suffix.lower()
            if suffix in ZENODO_BLOCKED_SUFFIXES:
                skipped_blocked.append(info.filename)
                continue
            allowed = info.filename.startswith(ZENODO_ALLOWED_PREFIXES) and suffix in ZENODO_ALLOWED_SUFFIXES
            if not allowed:
                continue
            if info.filename.startswith(ZENODO_ALLOWED_DATA_PREFIX):
                relative = Path("gold_csv") / member.name
            else:
                relative = Path("metadata") / member.name
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
            extracted.append({"archive_path": info.filename, "path": str(target.relative_to(destination)), "size": info.file_size})
    (destination / "extraction_report.json").write_text(
        json.dumps(
            {
                "source_archive": str(ZENODO_ZIP.relative_to(ROOT)),
                "archive_sha256": sha256(ZENODO_ZIP).lower(),
                "extracted": extracted,
                "extracted_count": len(extracted),
                "blocked_count": len(skipped_blocked),
                "blocked_examples": skipped_blocked[:20],
                "policy": "Only CSV/Markdown/JSON from docs/curation; no executable, Python, pickle, venv or DuckDB content extracted.",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    write_sums(destination)
    return {
        "destination": str(destination.relative_to(ROOT)),
        "extracted_count": len(extracted),
        "blocked_count": len(skipped_blocked),
        "archive_sha256": sha256(ZENODO_ZIP).lower(),
    }


def ingest_racedata() -> dict:
    destination = REFERENCE / "racedata"
    destination.mkdir(parents=True, exist_ok=True)
    extracted = []
    with zipfile.ZipFile(RACEDATA_ZIP) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            member = PurePosixPath(info.filename)
            if ".." in member.parts:
                raise ValueError(f"path traversal in ZIP: {info.filename}")
            if member.suffix.lower() not in {".csv", ".json"}:
                continue
            target = destination / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
            extracted.append({"name": member.name, "size": info.file_size})
    (destination / "extraction_report.json").write_text(
        json.dumps(
            {
                "source_archive": str(RACEDATA_ZIP.relative_to(ROOT)),
                "archive_sha256": sha256(RACEDATA_ZIP).lower(),
                "extracted": extracted,
                "policy": "CSV and JSON only; no executable content.",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    write_sums(destination)
    return {
        "destination": str(destination.relative_to(ROOT)),
        "extracted_count": len(extracted),
        "archive_sha256": sha256(RACEDATA_ZIP).lower(),
    }


def write_registry(british: dict, zenodo: dict, racedata: dict) -> None:
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {
                "source_id": "tracinginsights-2025-british-gp",
                "provider": "TracingInsights",
                "kind": "telemetry",
                "repository": "https://github.com/TracingInsights-Archive/2025",
                "license": "Apache-2.0",
                "auth_required": False,
                "retrieved_at_utc": "2026-11-21",
                "manifest": "manifest_2025_british_gp.json",
                "telemetry_sha256": {
                    item["lap_id"]: item["telemetry_sha256"]
                    for item in json.loads((TELEMETRY_DIR / "manifest_2025_british_gp.json").read_text(encoding="utf-8"))["laps"]
                },
                "security": {"status": "data_only", "blocked_content": [], "notes": "JSON telemetry only; no repository code executed."},
            },
            {
                "source_id": "zenodo-20061496",
                "provider": "Zenodo / Anand Marepalli",
                "kind": "curated_session_sample",
                "repository": "https://zenodo.org/records/20061496",
                "doi": "10.5281/zenodo.20061496",
                "license": "CC-BY-4.0",
                "auth_required": False,
                "retrieved_at_utc": "2026-11-21",
                "archive_sha256": zenodo["archive_sha256"],
                "extracted_count": zenodo["extracted_count"],
                "blocked_count": zenodo["blocked_count"],
                "security": {
                    "status": "quarantined_then_data_only_extract",
                    "blocked_count": zenodo["blocked_count"],
                    "blocked_content": ["venv", "exe", "dll", "py", "pyc", "pkl", "ff1pkl", "bat"],
                    "notes": "ZIP contains a full Windows venv and executable files; only CSV/Markdown/JSON under docs/curation were extracted.",
                },
            },
            {
                "source_id": "tracinginsights-racedata",
                "provider": "TracingInsights",
                "kind": "metadata",
                "repository": "https://github.com/TracingInsights/RaceData",
                "license": "CC0-1.0",
                "auth_required": False,
                "retrieved_at_utc": "2026-11-21",
                "archive_sha256": racedata["archive_sha256"],
                "extracted_count": racedata["extracted_count"],
                "security": {"status": "data_only", "blocked_content": [], "notes": "CSV/JSON only; no executable content."},
            },
        ],
    }
    SOURCES.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_sessions() -> None:
    payload = {
        "schema_version": 1,
        "default_session_id": "2025-abu-dhabi-qualifying",
        "sessions": [
            {
                "session_id": "2025-abu-dhabi-qualifying",
                "manifest": "manifest.json",
                "label": "2025 Abu Dhabi Grand Prix — Qualifying",
                "provider": "TracingInsights",
            },
            {
                "session_id": "2025-british-gp-qualifying",
                "manifest": "manifest_2025_british_gp.json",
                "label": "2025 British Grand Prix — Qualifying",
                "provider": "TracingInsights",
            },
        ],
    }
    SESSIONS.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    british = ingest_british_session()
    zenodo = ingest_zenodo()
    racedata = ingest_racedata()
    write_registry(british, zenodo, racedata)
    write_sessions()
    print(json.dumps({"british": british, "zenodo": zenodo, "racedata": racedata}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
