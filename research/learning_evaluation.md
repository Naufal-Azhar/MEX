# Learning Evaluation — Phase 6 Report

**Date:** 21 November 2026
**Scope:** the implemented MEX-AI vertical slice on one cached public fixture.
**Rule:** every number below comes from a command or artifact produced in this workspace. Anything not run is marked **not run**.

## 1. What was executed

| Check | Command | Result |
|---|---|---|
| Baseline + new regression | `.venv\Scripts\python.exe -m pytest -q` | **140 passed**, exit 0 |
| Baseline legacy suite | same suite, original 66 cases | all passed, no expected values changed |
| Telemetry feature tests | `pytest tests/test_telemetry.py` | all passed |
| Independent gold checks | `pytest tests/test_telemetry_gold.py` | **9 passed** |
| Rule/evidence-gate tests | `pytest tests/test_analysis_rules.py` | all passed |
| LTCS rule audit | `pytest tests/test_rule_audit.py` | **2 passed** |
| Retrieval/ask tests | `pytest tests/test_learning_ask.py` | all passed |
| Security hardening | `pytest tests/test_security_hardening.py` | **5 passed** |
| Retrieval evaluation | `python scripts/evaluate_learning_retrieval.py` | 10 cases, report written |
| Streamlit screenshots | headless Chrome via CDP | 4 screenshots in `research/screenshots/` |

## 2. Fixture and features

Session: 2025 Abu Dhabi Grand Prix, Qualifying.
Seven cached laps:

| Lap | Category | Compound | Context |
|---|---|---|---|
| VER-Q-14 | clean_fast | SOFT | Q3 |
| NOR-Q-16 | clean_fast | SOFT | Q3 |
| PIA-Q-16 | clean_fast | SOFT | Q3 |
| LEC-Q-17 | clean_fast | SOFT | Q3 |
| HAM-Q-2 | clean_medium | MEDIUM | Q1 |
| TSU-Q-16 | deleted | SOFT | Q3; steward-deleted, data gate withheld |
| GAS-Q-4 | invalid_distance | SOFT | Q1; non-monotonic distance, validation rejects |

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

## 4. Retrieval pilot and evaluation

Corpus: `data_dictionary.md` and `engineering_fundamentals.md`.

| Chunking | Queries with correct section at rank 1 |
|---|---|
| Paragraph chunks | 2 / 6 |
| Section-aware (`##`) chunks | 5 / 6 |
| Section-aware + table-row chunks + intent score policy | **6 / 6** |

The brake-unit query now retrieves the `2. Channels` table row instead of the `2. Braking` prose section. Table rows are marked `table_row`; they are damped for how/why/should questions and boosted when the query asks for a channel definition. This is a deterministic prototype policy on a two-document corpus, not a general retrieval benchmark.

Ten-case evaluation (`scripts/evaluate_learning_retrieval.py`, including bilingual and no-answer cases):

| Metric | Result |
|---|---:|
| Answerable cases | 9 |
| Hit@1 | 0.8889 |
| Hit@3 | 1.0 |
| MRR | 0.9259 |
| No-answer abstention (score < 0.20) | 0.0 |

Known failures: `LR08` (Indonesian “menangani nilai channel yang hilang”) ranks `2. Braking` first, with the expected `4. Interpretation rules` at rank 3. `LR10` (brake pressure in bar) retrieves a channel caveat instead of abstaining; score-threshold abstention is not reliable without semantic checking. Full per-case results: `research/learning_retrieval_report.md`.

## 4.1 LLM integrity hardening (tested with a fake provider)

- `observed_facts` and `rule_based_findings` are now rendered from the server-side analysis; the LLM cannot change numbers or invent rule findings.
- Every theory item must carry a valid `[E#]` citation from the retrieved evidence, otherwise the answer is rejected and the deterministic fallback is returned.
- Evidence is wrapped in `<evidence>` delimiters and explicitly labelled untrusted data in the system prompt.
- Added tests: fabricated `999 km/h` facts are ignored, fake rule findings are ignored, uncited theory is rejected, and the prompt isolates evidence.
- These tests use a fake provider. A real LLM provider is still **not configured or tested**.

## 4.2 Independent gold checks

`tests/test_telemetry_gold.py` contains 9 checks with expected values computed directly from the raw JSON using NumPy, not from the production feature functions. Covered: max speed, brake-onset count and first onset for six laps, segment elapsed time, constant-acceleration rate, and throttle-onset pattern. All pass.

## 4.3 LTCS 2 kg rule audit

Article C4.6 page 60 conditions the 2 kg increase on “any LTCS or TTCS for which a Heat Hazard has not been declared”. The rule now requires `heat_hazard_declared == false`. `TC18` still produces 2 kg and remains VIOLATED at 797.5 kg. A new test confirms that an LTCS with a session heat hazard returns `UNKNOWN` rather than silently assuming 2 kg. Details: `research/rule_audit_ltcs.md`.

## 4.4 Security hardening

- TF-IDF index now writes and verifies a SHA-256 sidecar before `joblib.load`; a missing or mismatched checksum forces a rebuild.
- CORS is an explicit allowlist (`CORS_ORIGINS`), not `*`.
- Request bodies over `MAX_REQUEST_BYTES` (default 1,000,000) return HTTP 413.
- API string/list fields have explicit max lengths.
- `qdrant/qdrant` pinned to `v1.20.2`.
- GitHub Actions workflow added at `.github/workflows/tests.yml`; it has **not been executed** because there is no remote CI run yet.

## 4.5 Real LLM smoke test

Provider: Google AI Studio, model `gemini-3.1-flash-lite`, key stored only in `.env`.

| Test | Result |
|---|---|
| Theory: braking distance vs entering speed | `generated`; citation `[E1]`; quadratic relationship stated |
| Telemetry: VER-Q-14 vs NOR-Q-16 braking | `generated`; 13 server facts; 6 findings; 3 citations |
| HTTP `/v1/ask`: throttle percentage | `generated`; theory `[E1, E3]`; `facts_source=server` |
| No-answer: brake pressure in bar | `unsupported`; missing data/limitations, no fabricated number |

Fixes required during integration: bounded retry for 429/5xx, multi-ID citation parsing `[E1, E3]`, dropping only uncited theory items, and test isolation (`LLM_PROVIDER=none`, empty key in `tests/conftest.py`).

This is a smoke test, not the full A/B/C comparison. Semantic citation entailment remains unaudited.

## 5. Not run

| Required experiment | Status | Reason |
|---|---|---|
| LLM-only baseline (A) | **not run** | Provider exists, but the A/B/C experiment harness is not implemented |
| RAG+LLM baseline (B) | **not run** | Same; only C-style `/v1/ask` smoke was run |
| RAG+LLM+rules (C) | **not run** | Same; smoke test is not a comparative run |
| Real-provider citation/semantic audit | **smoke only** | Generative smoke test passes; semantic entailment is not audited |
| Human expert review | **not run** | No reviewer available; no approval was fabricated |
| Educational pre/post evaluation | **not run** | No participants; no learning gain is claimed |
| Docker/Compose verification | **partial** | `docker compose config` parses; build/run not tested because the daemon is not running |
| CI workflow execution | **not run** | Workflow added; no GitHub remote/CI run exists |
| Real-data ingestion via provider API | **not run** | F1 livetiming requires account authentication; OpenF1 unreachable |

## 6. Threats to validity

- One session and seven laps only; no statistical generalization.
- Self-selected lap pair from a qualifying session; conditions are not controlled.
- Distance is provider-derived; cross-lap alignment is approximate.
- Brake is an indicator, not pressure.
- The telemetry rules are draft and written for this prototype.
- The knowledge gate checks string presence, not whether the quote entails the claim.
- The fixture is a third-party redistribution; independent verification against the official feed is not possible here.

## 7. Honest status

**Implemented and demonstrated:** fixture ingestion, validation, alignment, deterministic features, plots, draft rules with Backward Chaining, two-layer evidence gates, additive API endpoints, scoped retrieval, structured deterministic answers with citation validation, and a three-module Streamlit UI.

**Not complete per the MVP checklist:** real generative RAG with an active LLM provider, real-data acquisition from an authenticated F1 source, human review, B-vs-C evaluation, and educational outcome measurement.
