# Telemetry Data Dictionary — TracingInsights Fixture

**Status:** self-authored reference note for the MEX-AI MVP. Not a copy of provider documentation.
**Scope:** the cached 2025 Abu Dhabi Qualifying fixture in `datasets/telemetry/`.
**Dataset license:** Apache-2.0. Source repository: <https://github.com/TracingInsights-Archive/2025>. Provider README permits research, academic work, visualization and personal applications; attribution appreciated, not required.
**Retrieved:** 2026-11-21 from `raw.githubusercontent.com` without authentication.
**Related manifest:** `datasets/telemetry/manifest.json`.

## 1. Files

| File | Content |
|---|---|
| `VER_14_tel.json` | Lap telemetry for VER, lap 14, Q3 |
| `NOR_16_tel.json` | Lap telemetry for NOR, lap 16, Q3 |
| `VER_laptimes.json` / `NOR_laptimes.json` | Session lap metadata for each driver |

Telemetry file shape: `{"tel": {channel: [values...]}}`. Each channel is a column of equal length. `dataKey` identifies the lap, e.g. `2025-Abu Dhabi Grand Prix-Qualifying-VER-14`.

## 2. Channels (as observed in the cached files)

| Channel | Observed type | Unit / values | Use in MVP |
|---|---|---|---|
| `time` | float list | seconds from the first sample of the lap; verified strictly increasing | x-axis for rate calculations |
| `speed` | float list | km/h; verified range 65–331 km/h in VER lap 14 | speed features |
| `throttle` | float list | percent, 0–100 | throttle onset |
| `brake` | numeric list | **0 or 1** in this dataset; not 0/100 | brake onset with threshold `> 0.5` |
| `gear` | numeric list | discrete gear number | context only |
| `drs` | numeric list | provider-specific DRS indicator | not used in MVP features |
| `distance` | float list | metres; provider-derived; verified monotonic | alignment axis |
| `rel_distance` | float list | 0.0–1.0 relative lap distance | alignment helper |
| `rpm` | float list | engine RPM | context only |
| `x`, `y`, `z` | float lists | provider position coordinates; origin arbitrary | not used in MVP features |
| `acc_x`, `acc_y`, `acc_z` | float lists | provider-computed acceleration; units not documented in the files | not used in MVP features |
| `DriverAhead` | string list | `'None'` used as a missing marker | must be parsed as missing |
| `DistanceToDriverAhead` | float list | metres, provider-computed | context only |

## 3. Sampling and quality observations (2026-11-21)

| Check | VER lap 14 | NOR lap 16 |
|---|---|---|
| Samples | 617 | 623 |
| Duration (s) | 82.295 | 82.408 |
| Median sample interval (s) | 0.136 | 0.137 |
| Maximum gap (s) | 1.076 | 1.000 |
| Time monotonic | yes | yes |
| Distance monotonic | yes | yes |
| Missing speed/throttle/brake | 0 | 0 |
| Detected brake onsets | 6 | 6 |

## 4. Interpretation rules

1. `brake` is an indicator, not brake pressure. Never describe it as pressure or pedal force.
2. `throttle` is pedal input percentage, not engine power or torque.
3. `speed` is vehicle speed in km/h. Canonical calculation unit is m/s; convert with `v_m_s = v_km_h / 3.6`.
4. `distance` is derived by the provider, not measured. Cross-lap alignment is approximate because racing lines differ.
5. Missing values must be handled explicitly. The string `'None'` is a missing marker, not a number or a driver.
6. Sampling gaps up to about one second exist. Interpolation across a long gap is not allowed; the interval must be marked as a gap.
7. FastF1 documentation notes roughly ±10 m error when overlapping telemetry of different laps. Treat onset differences of that order as within alignment uncertainty unless the observed difference is larger.

## 5. Provenance caveats

- The dataset is redistributed by a third party. It was originally collected through FastF1; independent verification against the official F1 feed is not possible here.
- The two laps are from the same session and compound, which supports a descriptive comparison. They are not a controlled experiment: entering speed, tyre history, fuel, wind, traffic and driver intent can all differ.
- No claim about driver skill, car damage, setup or causal mechanism is supported by this fixture alone.
