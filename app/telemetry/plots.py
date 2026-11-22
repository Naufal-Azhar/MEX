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

    background = "#0b131b"
    foreground = "#b8c6d4"
    grid_color = "#223444"
    color_a = "#43e3cf"
    color_b = "#ffb75e"

    figure, axes = plt.subplots(3, 1, figsize=(11, 7.5), sharex=True)
    figure.patch.set_facecolor(background)
    figure.suptitle(title, color="#e9f1f8", fontsize=12)

    axes[0].plot(distance, aligned.speed_a_km_h, label=label_a, linewidth=1.4, color=color_a)
    axes[0].plot(distance, aligned.speed_b_km_h, label=label_b, linewidth=1.4, color=color_b)
    axes[0].set_ylabel("Kecepatan (km/jam)")

    axes[1].plot(distance, aligned.throttle_a_pct, label=label_a, linewidth=1.2, color=color_a)
    axes[1].plot(distance, aligned.throttle_b_pct, label=label_b, linewidth=1.2, color=color_b)
    axes[1].set_ylabel("Gas (%)")
    axes[1].set_ylim(-5, 105)

    axes[2].step(
        distance,
        np.nan_to_num(aligned.brake_a),
        where="mid",
        label=label_a,
        linewidth=1.2,
        color=color_a,
    )
    axes[2].step(
        distance,
        np.nan_to_num(aligned.brake_b),
        where="mid",
        label=label_b,
        linewidth=1.2,
        color=color_b,
    )
    axes[2].set_ylabel("Rem (0/1)")
    axes[2].set_xlabel("Jarak (m)")
    axes[2].set_ylim(-0.1, 1.2)

    for axis in axes:
        axis.set_facecolor(background)
        for side, spine in axis.spines.items():
            spine.set_color(grid_color)
            if side in ("top", "right"):
                spine.set_visible(False)
        axis.tick_params(colors=foreground, labelsize=9)
        axis.yaxis.label.set_color(foreground)
        axis.xaxis.label.set_color(foreground)
        axis.grid(alpha=0.18, color=grid_color)
        for start, end in _gap_spans(aligned.valid):
            axis.axvspan(
                distance[start],
                distance[min(end, distance.size - 1)],
                color="#ff8f8f",
                alpha=0.10,
                linewidth=0,
            )
        legend = axis.legend(loc="upper right", facecolor=background, edgecolor=grid_color)
        for text in legend.get_texts():
            text.set_color(foreground)

    figure.tight_layout()
    figure.savefig(destination, dpi=140, bbox_inches="tight", facecolor=background)
    plt.close(figure)
    return destination
