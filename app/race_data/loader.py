"""Internal telemetry data objects and deterministic fixture loader."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from app.schemas.telemetry import LapIdentity, LapProvenance


class TelemetryLoadError(ValueError):
    """Raised when a telemetry fixture cannot be parsed."""


@dataclass
class LapTelemetry:
    identity: LapIdentity
    provenance: LapProvenance
    time_s: np.ndarray
    speed_km_h: np.ndarray
    throttle_pct: np.ndarray
    brake: np.ndarray
    distance_m: np.ndarray
    gear: np.ndarray | None = None
    drs: np.ndarray | None = None
    raw_channel_names: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        return int(self.time_s.size)


REQUIRED_CHANNELS = ("time", "speed", "throttle", "brake", "distance")


def _as_float_array(values: Any, name: str) -> np.ndarray:
    if not isinstance(values, list):
        raise TelemetryLoadError(f"channel '{name}' is not a list")
    converted: list[float] = []
    for item in values:
        if item is None or item == "None" or item == "":
            converted.append(float("nan"))
            continue
        try:
            converted.append(float(item))
        except (TypeError, ValueError) as exc:
            raise TelemetryLoadError(f"channel '{name}' contains a non-numeric value: {item!r}") from exc
    return np.asarray(converted, dtype=float)


def normalize_brake(raw: np.ndarray) -> np.ndarray:
    """Normalise 0/1 and 0/100 brake encodings to a boolean indicator."""
    finite = raw[np.isfinite(raw)]
    if finite.size and float(np.nanmax(finite)) > 1.5:
        return raw > 50.0
    return raw > 0.5


def load_lap(
    path: Path | str,
    identity: LapIdentity,
    provenance: LapProvenance,
) -> LapTelemetry:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TelemetryLoadError(f"cannot read telemetry file {source}: {exc}") from exc

    tel = payload.get("tel") if isinstance(payload, dict) else None
    if not isinstance(tel, dict):
        raise TelemetryLoadError(f"{source} has no 'tel' object")

    missing = [name for name in REQUIRED_CHANNELS if name not in tel]
    if missing:
        raise TelemetryLoadError(f"{source} is missing required channels: {', '.join(missing)}")

    arrays = {name: _as_float_array(tel[name], name) for name in REQUIRED_CHANNELS}
    lengths = {name: values.size for name, values in arrays.items()}
    if len(set(lengths.values())) != 1:
        raise TelemetryLoadError(f"channel lengths differ: {lengths}")

    return LapTelemetry(
        identity=identity,
        provenance=provenance,
        time_s=arrays["time"],
        speed_km_h=arrays["speed"],
        throttle_pct=arrays["throttle"],
        brake=normalize_brake(arrays["brake"]),
        distance_m=arrays["distance"],
        gear=_as_float_array(tel["gear"], "gear") if "gear" in tel else None,
        drs=_as_float_array(tel["drs"], "drs") if "drs" in tel else None,
        raw_channel_names=list(tel.keys()),
    )


def load_manifest(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_manifest_laps(manifest_path: Path | str) -> dict[str, LapTelemetry]:
    manifest = load_manifest(manifest_path)
    base = Path(manifest_path).resolve().parent
    session = manifest["session"]
    session_label = f"{session['season']} {session['event']} {session['session_type']}"

    laps: dict[str, LapTelemetry] = {}
    for item in manifest["laps"]:
        identity = LapIdentity(
            lap_id=item["lap_id"],
            driver=item["driver"],
            lap_number=int(item["lap_number"]),
            session=session_label,
            lap_time_s=float(item["lap_time_s"]),
            compound=item.get("compound"),
            phase=item.get("qualifying_phase"),
            deleted=bool(item.get("deleted", False)),
            accurate=item.get("accurate"),
            category=item.get("category"),
        )
        provenance = LapProvenance(
            provider=manifest["provider"],
            repository=manifest["provider_repository"],
            license=manifest["license"],
            retrieved_at=manifest["retrieved_at_utc"],
            telemetry_sha256=item["telemetry_sha256"],
            source_file=item["telemetry_file"],
        )
        laps[item["lap_id"]] = load_lap(base / item["telemetry_file"], identity, provenance)
    return laps
