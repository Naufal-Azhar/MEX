# Learning Evaluation — Phase 6 Report

**Date:** 21 November 2026
**Scope:** the implemented MEX-AI vertical slice on one cached public fixture.
**Rule:** every number below comes from a command or artifact produced in this workspace. Anything not run is marked **not run**.

## 1. What was executed

| Check | Command | Result |
|---|---|---|
| Baseline + new regression | `.venv\Scripts\python.exe -m pytest -q` | **112 passed**, exit 0 |
| Baseline legacy suite | same suite, original 66 cases | all passed, no expected values changed |
| Telemetry feature tests | `pytest tests/test_telemetry.py` | **18 passed** |
| Rule/evidence-gate tests | `pytest tests/test_analysis_rules.py` | **15 passed** |
| Retrieval/ask/UI-adjacent tests | `pytest tests/test_learning_ask.py` | **13 passed** |
| Streamlit module smoke | Streamlit `AppTest` on all three modules | no exception |
| Streamlit analysis interaction | AppTest click "Analisis lap" | no exception; 3 result tables |
| Streamlit tutor interaction | AppTest submit theory question | no exception; deterministic fallback warning shown |

## 2. Fixture and features

Session: 2025 Abu Dhabi Grand Prix, Qualifying.
Laps: VER lap 14 (82.295 s) and NOR lap 16 (82.408 s).
Source: TracingInsights, Apache-2.0; hashes in `datasets/telemetry/manifest.json`.

| Measurement | VER | NOR |
|---|---|---|
| Samples | 617 | 623 |
| Median sample interval | 0.136 s | 0.137 s |
| Maximum gap | 1.076 s | 1.000 s |
| Detected brake onsets | 6 | 6 |
| Max speed | 331 km/h | 329 km/h |

Cross-lap comparison on a 1 m distance grid:

- Coverage ratio: 0.99995; valid grid points: 5,031.
- `speed_delta` (NOR − VER): mean −0.344 km/h, min −23.13 km/h, max +14.037 km/h.
- Brake-onset deltas: −8.96 m, +2.55 m, +1.24 m, +0.57 m, **−15.32 m**, **−12.61 m**.
- The first four are inside the ±10 m alignment-uncertainty flag; the last two are outside it. This is an observation, not a causal finding.

Artifacts: `datasets/telemetry/analysis/ver14_vs_nor16.json`, `.png`, `learning_report.json`, `ask_*.json`.

## 3. Rule and evidence-gate results

| Goal | Rule | Result |
|---|---|---|
| `speed_comparison_available` | TEL-R01 | OBSERVED |
| `speed_profile_difference_observed` | TEL-R02 | OBSERVED |
| `relative_brake_onset_difference_observed` | TEL-R03 | OBSERVED |
| `braking_dynamics_learning_topic_relevant` | TEL-R04 | OBSERVED |
| `insufficient_evidence_for_understeer_diagnosis` | TEL-R05 | NOT_APPLICABLE without an understeer question; INSUFFICIENT_DATA when asked |
| `insufficient_evidence_for_drag_cause` | TEL-R06 | NOT_APPLICABLE without a drag question; INSUFFICIENT_DATA when asked |
| `flag_comparison_context_limitation` | TEL-R07 | INSUFFICIENT_DATA (context channels absent) |
| `withhold_supported_engineering_interpretation` | TEL-R08 | INSUFFICIENT_DATA |

- Data gate: PASS.
- Knowledge gate: PASS on quote presence (6 evidence items); semantic entailment is **not** verified.
- `engineering_interpretation_status`: INSUFFICIENT_DATA by design.
- All 8 telemetry rules remain `draft`; no rule was promoted to `reviewed` or `active`.

## 4. Retrieval pilot

Corpus: `data_dictionary.md` and `engineering_fundamentals.md`.

| Chunking | Queries with correct section at rank 1 |
|---|---|
| Paragraph chunks | 2 / 6 |
| Section-aware (`##`) chunks | 5 / 6 |

The remaining miss is the brake-unit query, because the channel definition lives in a Markdown table. Table-aware chunking remains a Phase 5/7 task. No claim of retrieval quality on a larger corpus is made.

## 5. Not run

| Required experiment | Status | Reason |
|---|---|---|
| LLM-only baseline (A) | **not run** | No LLM provider configured |
| RAG+LLM baseline (B) | **not run** | No LLM provider configured |
| RAG+LLM+rules (C) | **not run** | No LLM provider configured |
| Real-provider citation/semantic audit | **not run** | Fake-provider tests validate schema and citation rejection only |
| Human expert review | **not run** | No reviewer available; no approval was fabricated |
| Educational pre/post evaluation | **not run** | No participants; no learning gain is claimed |
| Docker/Compose verification | **not run** | Docker daemon is not running |
| Real-data ingestion via provider API | **not run** | F1 livetiming requires account authentication; OpenF1 unreachable |

## 6. Threats to validity

- One session and two laps only; no statistical generalization.
- Self-selected lap pair from a qualifying session; conditions are not controlled.
- Distance is provider-derived; cross-lap alignment is approximate.
- Brake is an indicator, not pressure.
- The telemetry rules are draft and written for this prototype.
- The knowledge gate checks string presence, not whether the quote entails the claim.
- The fixture is a third-party redistribution; independent verification against the official feed is not possible here.

## 7. Honest status

**Implemented and demonstrated:** fixture ingestion, validation, alignment, deterministic features, plots, draft rules with Backward Chaining, two-layer evidence gates, additive API endpoints, scoped retrieval, structured deterministic answers with citation validation, and a three-module Streamlit UI.

**Not complete per the MVP checklist:** real generative RAG with an active LLM provider, real-data acquisition from an authenticated F1 source, human review, B-vs-C evaluation, and educational outcome measurement.
