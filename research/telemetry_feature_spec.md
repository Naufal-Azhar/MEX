# Telemetry Feature Specification v1

**Status:** specification for Phase 3 implementation. Thresholds are prototype configuration, not validated engineering constants.
**Fixture:** `datasets/telemetry/raw/tracinginsights/2025-abu-dhabi-qualifying/` (VER lap 14, NOR lap 16).
**Canonical units:** time s; distance m; speed m/s internally, km/h for display; throttle %; brake boolean.

## 1. Input and validation

Each lap record contains parallel channel arrays from `{"tel": {...}}`.

Validation, in order:

1. Required channels present: `time`, `speed`, `throttle`, `brake`, `distance`.
2. Arrays have equal length and length >= 2.
3. `time` strictly increasing; reject duplicate or decreasing timestamps.
4. `distance` non-decreasing; reject a non-monotonic series.
5. No NaN in required channels; `'None'` strings are missing values.
6. `speed` within [0, 400] km/h; `throttle` within [0, 100]; `brake` accepted as boolean-like (`0/1` or `0/100`) and normalised with `brake_on = value > 0.5` for 0/1 data or `> 50` for 0/100 data.
7. Lap duration > 0 and within [20, 300] s for a qualifying-style lap.
8. Channel availability is reported; unavailable channels are `unknown`, never `0` or `false`.

Failure produces `INVALID_INPUT` / `INSUFFICIENT_DATA`; it never produces a performance verdict.

## 2. Alignment

Default: common distance grid with step 1.0 m over the overlapping distance range.

- No extrapolation outside either lap's coverage.
- Continuous channels (`speed`, `throttle`, `time`): linear interpolation only inside a valid interval.
- Discrete channels (`gear`, `drs`, `brake`): nearest sample, never linear interpolation.
- Maximum interpolation gap: **0.25 s** (prototype default). A longer gap marks the interval as missing and excludes it from derived statistics.
- Coverage is reported as `overlap_distance_m / min(total_distance_a, total_distance_b)`.
- Alignment uncertainty flag: differences smaller than **±10 m** in distance positions are treated as within alignment uncertainty, following the FastF1 overlap caveat. This is a prototype threshold and must be documented as such.

## 3. Features

### 3.1 `max_speed`

- Definition: maximum valid `speed` sample within the lap or selected segment.
- Unit: km/h.
- Not the official speed trap (`st_speed`); must never be labelled as a speed trap.
- Segment variant uses samples whose `distance` lies inside the segment.

### 3.2 `speed_delta`

- Definition: `speed_B(d) - speed_A(d)` on the common distance grid.
- Unit: km/h. Sign convention: positive means B is faster at that distance.
- Reported with mean, min, max, and the distance of maximum absolute difference.
- Requires coverage >= 0.8 of the shorter lap; otherwise `INSUFFICIENT_DATA`.

### 3.3 `brake_onset_distance`

- Definition: distance of the first valid transition from `brake_on = false` to `brake_on = true`.
- Debounce: require **2 consecutive** `true` samples to reject single-sample noise.
- Threshold: `brake_on = raw > 0.5` for 0/1 data.
- Unit: m from the lap start reference.
- Reported as an estimate with uncertainty: half the local sample spacing in distance, plus the alignment uncertainty flag.
- Not brake pressure, not brake force.

### 3.4 `brake_onset_delta`

- Definition: `onset_B - onset_A` for matched braking zones.
- Sign convention: **positive** means B brakes at a larger distance, i.e. later on the lap.
- Matching: pair onsets whose distances differ by no more than **150 m** (prototype default); unmatched onsets are reported separately.
- A delta whose absolute value is within ±10 m must be reported as within alignment uncertainty, not as a real difference.
- Requires comparable entering conditions to support interpretation; without them, report observation only.

### 3.5 `longitudinal_speed_change_rate`

- Definition: `(v2_m_s - v1_m_s) / (t2 - t1)` over a specified window.
- Unit: m/s².
- This is an approximation from speed samples, not an accelerometer measurement.
- Default window: 0.5 s; report the window and sample count.

### 3.6 `throttle_onset_distance`

- Definition: distance of the first valid transition from `throttle < 10%` to `throttle >= 90%`.
- Debounce: 2 consecutive samples above the upper threshold.
- Thresholds are configurable prototype values, not universal constants.
- Not engine power and not a traction-limited launch indicator.

### 3.7 `segment_elapsed_time`

- Definition: time between two segment boundaries, obtained by interpolating `time` against `distance` at each boundary.
- Unit: s.
- Only valid when both boundaries lie inside the overlapping coverage; otherwise `INSUFFICIENT_DATA`.
- Not a replacement for official sector times.

### 3.8 `data_quality`

Always reported:

- coverage ratio and overlap distance;
- number and total duration of gaps;
- missing channels;
- known/unknown session context;
- units and canonical conversions;
- uncertainty flags (`alignment`, `sampling`, `brake_encoding`, `derived_distance`).

## 4. Learning findings derived from features

Rules TEL-R01..TEL-R08 may consume these features. They must distinguish:

- `OBSERVED`: a measured fact, e.g. `brake_onset_delta = -9 m`.
- `SUPPORTED_INTERPRETATION`: an interpretation backed by cited engineering sources, with caveats.
- `INSUFFICIENT_DATA`: required channel, coverage or evidence is missing.
- `NOT_APPLICABLE`, `UNSUPPORTED`, `ERROR`: as defined in the existing status contract.

The engine must never convert `INSUFFICIENT_DATA` into a negative finding.

## 5. Planned unit tests (Phase 3)

1. `speed_delta` sign and unit on a hand-built two-lap fixture.
2. `brake_onset` debounce: one-sample spike is rejected; two-sample transition is accepted.
3. Brake encoding: 0/1 and 0/100 inputs produce the same onset.
4. Interpolation gap: a 1.0 s gap is excluded, not bridged.
5. Discrete channel alignment uses nearest, not linear.
6. Segment with disjoint coverage returns `INSUFFICIENT_DATA`.
7. Invalid lap: duplicate timestamp, negative speed, non-monotonic distance.
8. Boundary: onset exactly at the first sample; onset at the last sample.
9. `throttle_onset` threshold behaviour.
10. `data_quality` reports missing channels and gaps.

## 6. Known limitations

- Distance is provider-derived; racing-line differences make cross-lap alignment approximate.
- Sampling is about 7.4 Hz in this fixture; onset precision cannot exceed the local sample spacing.
- Brake is a boolean indicator.
- Tyre state, fuel load, wind, traffic and driver intent are not in the fixture.
- The thresholds in this document are prototype defaults and require sensitivity analysis before any claim of robustness.
