"""Deterministic plots for aligned telemetry laps."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from app.race_data.alignment import AlignedLaps


def _gap_spans(valid: np.ndarray) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start: int | None = None
    for index, ok in enumerate(valid):
        if not ok and start is None:
            start = index
        elif ok and start is not None:
            spans.append((start, index))
            start = None
    if start is not None:
        spans.append((start, valid.size))
    return spans


def save_comparison_plot(
    aligned: AlignedLaps,
    path: Path | str,
    title: str,
    label_a: str = "A",
    label_b: str = "B",
) -> Path:
    if aligned.valid.size == 0:
        raise ValueError("cannot plot an empty alignment")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    distance = aligned.distance_m

    figure, axes = plt.subplots(3, 1, figsize=(11, 7.5), sharex=True)
    axes[0].plot(distance, aligned.speed_a_km_h, label=label_a, linewidth=1.4)
    axes[0].plot(distance, aligned.speed_b_km_h, label=label_b, linewidth=1.4)
    axes[0].set_ylabel("Speed (km/h)")
    axes[0].legend(loc="upper right")

    axes[1].plot(distance, aligned.throttle_a_pct, label=label_a, linewidth=1.2)
    axes[1].plot(distance, aligned.throttle_b_pct, label=label_b, linewidth=1.2)
    axes[1].set_ylabel("Throttle (%)")
    axes[1].set_ylim(-5, 105)
    axes[1].legend(loc="upper right")

    axes[2].step(distance, np.nan_to_num(aligned.brake_a), where="mid", label=label_a, linewidth=1.2)
    axes[2].step(distance, np.nan_to_num(aligned.brake_b), where="mid", label=label_b, linewidth=1.2)
    axes[2].set_ylabel("Brake (0/1)")
    axes[2].set_xlabel("Distance (m)")
    axes[2].set_ylim(-0.1, 1.2)
    axes[2].legend(loc="upper right")

    for axis in axes:
        for start, end in _gap_spans(aligned.valid):
            axis.axvspan(distance[start], distance[min(end, distance.size - 1)], color="tab:red", alpha=0.08)
        axis.grid(alpha=0.25)

    figure.suptitle(title)
    figure.tight_layout()
    figure.savefig(destination, dpi=140, bbox_inches="tight")
    plt.close(figure)
    return destination
