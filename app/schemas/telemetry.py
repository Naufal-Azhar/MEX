"""Pydantic models for telemetry fixtures, quality, and derived features."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class FeatureStatus(str, Enum):
    OBSERVED = "OBSERVED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class LapIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lap_id: str
    driver: str
    lap_number: int
    session: str
    lap_time_s: float
    compound: str | None = None
    phase: str | None = None
    deleted: bool = False
    accurate: bool | None = None
    category: str | None = None


class LapProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    repository: str
    license: str
    retrieved_at: str
    telemetry_sha256: str
    source_file: str


class DataGap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_s: float
    end_s: float
    duration_s: float


class DataQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_count: int
    duration_s: float
    distance_m: float
    median_dt_s: float
    max_gap_s: float
    time_monotonic: bool
    distance_monotonic: bool
    missing_channels: list[str] = Field(default_factory=list)
    gaps: list[DataGap] = Field(default_factory=list)
    interpolation_gap_s: float
    uncertainty_flags: list[str] = Field(default_factory=list)


class FeatureValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: float | int | None = None
    unit: str | None = None
    status: FeatureStatus = FeatureStatus.OBSERVED
    detail: str | None = None


class BrakeOnset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    distance_m: float
    time_s: float
    speed_km_h: float
    throttle_pct: float
    estimated: bool = True


class BrakeOnsetComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    onset_a: BrakeOnset
    onset_b: BrakeOnset
    delta_m: float
    within_alignment_uncertainty: bool


class SpeedDeltaSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mean_km_h: float
    min_km_h: float
    max_km_h: float
    max_abs_distance_m: float
    coverage_ratio: float
    point_count: int


class LapPairAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_id: str
    data_kind: str = "recorded_public_fixture"
    lap_a: LapIdentity
    lap_b: LapIdentity
    provenance: dict[str, LapProvenance]
    quality: dict[str, DataQuality]
    observed_facts: list[FeatureValue] = Field(default_factory=list)
    brake_onsets_a: list[BrakeOnset] = Field(default_factory=list)
    brake_onsets_b: list[BrakeOnset] = Field(default_factory=list)
    brake_onset_comparisons: list[BrakeOnsetComparison] = Field(default_factory=list)
    speed_delta: SpeedDeltaSummary | None = None
    limitations: list[str] = Field(default_factory=list)
