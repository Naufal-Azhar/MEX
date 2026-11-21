"""Orchestration for deterministic telemetry lap-pair analysis."""

from __future__ import annotations

from pathlib import Path

from app.race_data.alignment import DEFAULT_MAX_GAP_S, DEFAULT_STEP_M, align_laps
from app.race_data.loader import LapTelemetry, load_manifest_laps
from app.race_data.validation import ensure_valid_lap
from app.schemas.telemetry import FeatureStatus, FeatureValue, LapPairAnalysis
from app.telemetry.features import (
    compare_brake_onsets,
    data_quality,
    find_brake_onsets,
    find_throttle_onsets,
    max_speed,
    segment_elapsed_time,
    speed_delta_summary,
)


class TelemetryAnalysisService:
    def __init__(
        self,
        laps: dict[str, LapTelemetry],
        step_m: float = DEFAULT_STEP_M,
        max_gap_s: float = DEFAULT_MAX_GAP_S,
    ) -> None:
        self.laps = laps
        self.step_m = step_m
        self.max_gap_s = max_gap_s

    @classmethod
    def from_manifest(
        cls,
        manifest_path: Path | str,
        step_m: float = DEFAULT_STEP_M,
        max_gap_s: float = DEFAULT_MAX_GAP_S,
    ) -> "TelemetryAnalysisService":
        return cls(load_manifest_laps(manifest_path), step_m=step_m, max_gap_s=max_gap_s)

    def available_laps(self) -> list[dict]:
        return [
            {
                "lap_id": lap.identity.lap_id,
                "driver": lap.identity.driver,
                "lap_number": lap.identity.lap_number,
                "session": lap.identity.session,
                "lap_time_s": lap.identity.lap_time_s,
                "compound": lap.identity.compound,
                "deleted": lap.identity.deleted,
                "accurate": lap.identity.accurate,
                "category": lap.identity.category,
            }
            for lap in self.laps.values()
        ]

    def analyze(
        self,
        lap_a_id: str,
        lap_b_id: str,
        segment: tuple[float, float] | None = None,
    ) -> LapPairAnalysis:
        lap_a = self._get_lap(lap_a_id)
        lap_b = self._get_lap(lap_b_id)
        ensure_valid_lap(lap_a)
        ensure_valid_lap(lap_b)

        aligned = align_laps(lap_a, lap_b, step_m=self.step_m, max_gap_s=self.max_gap_s)
        quality_a = data_quality(lap_a, self.max_gap_s)
        quality_b = data_quality(lap_b, self.max_gap_s)

        onsets_a = find_brake_onsets(lap_a)
        onsets_b = find_brake_onsets(lap_b)
        comparisons = compare_brake_onsets(onsets_a, onsets_b)
        speed_delta = speed_delta_summary(aligned)

        facts: list[FeatureValue] = []
        if segment is not None:
            start_m, end_m = segment
            facts.append(max_speed(lap_a, start_m, end_m))
            facts.append(max_speed(lap_b, start_m, end_m))
            elapsed_a = segment_elapsed_time(lap_a, start_m, end_m, self.max_gap_s)
            elapsed_b = segment_elapsed_time(lap_b, start_m, end_m, self.max_gap_s)
            for lap_id, elapsed in ((lap_a_id, elapsed_a), (lap_b_id, elapsed_b)):
                facts.append(
                    FeatureValue(
                        name="segment_elapsed_time",
                        value=elapsed,
                        unit="s",
                        status=FeatureStatus.OBSERVED if elapsed is not None else FeatureStatus.INSUFFICIENT_DATA,
                        detail=f"{lap_id} segment {start_m}-{end_m} m",
                    )
                )
        else:
            facts.append(max_speed(lap_a))
            facts.append(max_speed(lap_b))

        if speed_delta is not None:
            facts.append(
                FeatureValue(
                    name="speed_delta_mean",
                    value=speed_delta.mean_km_h,
                    unit="km/h",
                    detail="B minus A on the common distance grid",
                )
            )
            facts.append(
                FeatureValue(
                    name="speed_delta_min",
                    value=speed_delta.min_km_h,
                    unit="km/h",
                )
            )
            facts.append(
                FeatureValue(
                    name="speed_delta_max",
                    value=speed_delta.max_km_h,
                    unit="km/h",
                )
            )
        else:
            facts.append(
                FeatureValue(
                    name="speed_delta_mean",
                    value=None,
                    unit="km/h",
                    status=FeatureStatus.INSUFFICIENT_DATA,
                    detail="no valid overlapping samples",
                )
            )

        facts.append(
            FeatureValue(
                name="brake_onset_count",
                value=len(onsets_a),
                detail=f"{lap_a_id}",
            )
        )
        facts.append(
            FeatureValue(
                name="brake_onset_count",
                value=len(onsets_b),
                detail=f"{lap_b_id}",
            )
        )
        for index, comparison in enumerate(comparisons, start=1):
            note = "within alignment uncertainty" if comparison.within_alignment_uncertainty else "outside alignment uncertainty"
            facts.append(
                FeatureValue(
                    name=f"brake_onset_delta_{index}",
                    value=comparison.delta_m,
                    unit="m",
                    detail=f"{lap_b_id} minus {lap_a_id}; positive means B brakes later; {note}",
                )
            )

        limitations = [
            "Distance is provider-derived; cross-lap alignment is approximate.",
            "Brake is an indicator, not brake pressure.",
            "The comparison is descriptive; it does not establish a cause or a better driver.",
            "Tyre state, fuel load, wind, traffic and driver intent are not in this fixture.",
        ]
        if speed_delta is None or speed_delta.coverage_ratio < 0.8:
            limitations.append("Overlap coverage is below 0.8; treat the comparison as partial.")
        if quality_a.gaps or quality_b.gaps:
            limitations.append("Sampling gaps longer than the interpolation limit were excluded.")

        return LapPairAnalysis(
            analysis_id=f"{lap_a_id}__{lap_b_id}__step{self.step_m:g}",
            lap_a=lap_a.identity,
            lap_b=lap_b.identity,
            provenance={lap_a_id: lap_a.provenance, lap_b_id: lap_b.provenance},
            quality={lap_a_id: quality_a, lap_b_id: quality_b},
            observed_facts=facts,
            brake_onsets_a=onsets_a,
            brake_onsets_b=onsets_b,
            brake_onset_comparisons=comparisons,
            speed_delta=speed_delta,
            limitations=limitations,
        )

    def _get_lap(self, lap_id: str) -> LapTelemetry:
        if lap_id not in self.laps:
            known = ", ".join(sorted(self.laps))
            raise KeyError(f"unknown lap_id '{lap_id}'; available: {known}")
        return self.laps[lap_id]
