# F1 Technical Regulation Expert System

Academic prototype for checking selected **Formula 1 technical regulation** provisions using:

- a declarative, versioned knowledge base;
- a deterministic **Backward Chaining** engine with proof trace;
- **RAG** over the supplied FIA documents;
- an optional LLM adapter for fact extraction (disabled at this stage).

Source: `FIA 2026 Formula One Regulations — Section C [Technical]`, **Issue 21, 19 October 2026** (254 pages).

> This is **not FIA certification** and not a whole-car compliance check. It only evaluates the reviewed provisions listed below. Rules are currently `reviewed`, not `active`; results are demo-only until a human reviewer signs off.

> **Revision direction (21 November 2026):** `revisi/pemetaan_public_revisi.md` sections 22–34 reposition this work as MEX-AI (Race Analysis, Engineering Tutor, Regulation Lab). The regulation-lab functionality in this README remains the preserved baseline. Phase 0 decisions, verified test/evaluation baseline, and open blockers are recorded in `research/revision_decisions.md`.

## MEX-AI modules (implemented)

| Module | Status | Surface |
|---|---|---|
| **Race Analysis** | Implemented on one cached public fixture | `GET /v1/races`, `GET /v1/races/{id}/laps`, `POST /v1/telemetry/analyze`; Streamlit module |
| **Engineering Tutor** | Implemented with deterministic fallback | `POST /v1/ask`; Streamlit module |
| **Regulation Lab** | Preserved baseline | Existing `/v1/check`, `/v1/search`, Streamlit tabs |

Telemetry fixtures: 2025 Abu Dhabi Qualifying (**7 cached laps**) and 2025 British GP Qualifying (**VER lap 17, NOR lap 19**) from **TracingInsights** (Apache-2.0, public repository). Hashes and caveats: `datasets/telemetry/manifest.json` and `manifest_2025_british_gp.json`. Evaluation: `research/learning_evaluation.md`; retrieval: `research/engineering_retrieval_report.md`; acceptance: `research/mvp_acceptance.md`.

Screenshots of the running app: `research/screenshots/race_analysis_sessions.png`, `race_analysis_british_results.png`, `engineering_tutor_generated.png`, `regulation_lab.png`. The Engineering Tutor screenshot predates BM25 ranking; retake it before the final presentation.

> **Generation status:** Google AI Studio is configured locally via `.env` with `gemini-3.1-flash-lite`. `/v1/ask` now returns `generated` answers for theory and telemetry questions, while keeping facts and rule findings server-side and validating `[E#]` citations. A B-vs-C comparison is available in `research/b_vs_c_comparison.md`; A-only and full semantic citation audit are not run.
>
> When a provider is enabled, observed facts and rule findings are still rendered server-side; the LLM cannot alter numbers or verdicts. Theory items must carry a valid `[E#]` citation, and retrieved evidence is treated as untrusted data.



## Covered provisions

| Rule ID | Article | Requirement | Page |
|---|---|---|---|
| `FIA26-C2.3.1-HALF-WIDTH` | C2.3.1 | No non-excluded part more than 950 mm from plane Y=0 | 10 |
| `FIA26-C2.3.3-WHEELBASE` | C2.3.3 | Wheelbase ≤ 3400 mm | 11 |
| `FIA26-C2.3.5-COCKPIT-POSITION` | C2.3.5 | XA=0 to XC=0 within [1830, 2030] mm | 11 |
| `FIA26-C4.1-MINIMUM-MASS` | C4.1 (+C4.6) | Car Mass ≥ Minimum Mass (726/724 kg + Nominal Tyre Mass + Heat Hazard increase) | 59–60 |
| `FIA26-C4.2-MASS-DISTRIBUTION` | C4.2 | Front axle ≥ 0.44 × Minimum Mass; rear ≥ 0.54 × (Q/SQ only) | 59 |

The rule set contains **13 rule entries**: 5 compliance goals plus 8 value subgoals (base mass, Heat Hazard increase, minimum mass, minimum mass excluding heat).

## Status contract

External statuses returned by the API and UI:

- `SATISFIED` — all applicable prerequisites proved true.
- `VIOLATED` — at least one applicable prerequisite proved false.
- `INSUFFICIENT_DATA` — missing/uncertain facts or evidence.
- `NOT_APPLICABLE` — the provision is definitively inapplicable.
- `UNSUPPORTED` — goal or regulation issue outside the reviewed rule set.
- `ERROR` — system failure; never a compliance verdict.

Diagnostics are reported separately: `INVALID_INPUT`, `CONFLICTING_INPUT`, `SOURCE_MISSING`, `VERSION_MISMATCH`, `UNSUPPORTED_GOAL`, `RULE_NOT_APPROVED`, `INTERNAL_ERROR`.

Internal proof steps still use `TRUE` / `FALSE` / `UNKNOWN`. **UNKNOWN is never treated as FALSE.**

## Rule lifecycle and demo status

Rules follow `draft → reviewed → active → deprecated`.

- All current rules are **`reviewed`** and `human_approved: false`.
- The engine runs `reviewed` rules only in demo mode (`ALLOW_REVIEWED_RULES=true`, default), and every report carries a validation warning and the `RULE_NOT_APPROVED` diagnostic.
- To activate a rule after human review:
  1. set `validation.human_approved: true`;
  2. fill `validation.reviewer` and `validation.reviewed_at`;
  3. change `status` from `reviewed` to `active`.
- An `active` rule without human approval is rejected by schema validation.

Automated quote verification and the sign-off sheet are in `research/rule_validation_log.md` (generated by `scripts/validate_rules.py`).

## Quick start (Windows, dependencies isolated)

Everything runs from a local `.venv`; model/vector caches stay inside `storage/`.

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
copy .env.example .env
```

### 1. Extract documents (already generated; rerun if sources change)

```bat
.venv\Scripts\python.exe scripts\extract_documents.py
```

Outputs `knowledge_base/document_manifest.json` (including **SHA-256** and file size), processed JSON/Markdown/JSONL.

### 2. Build retrieval index

```bat
.venv\Scripts\python.exe scripts\build_index.py
```

- `EMBEDDING_BACKEND=bm25` (default) uses BM25 with TF-IDF fallback.
- Force TF-IDF only: `set EMBEDDING_BACKEND=tfidf`.
- Optional dense retrieval: `set EMBEDDING_BACKEND=sentence_transformers` and use Qdrant; `auto` uses Sentence Transformers only if the model is cached.

### 3. Run the API

```powershell
Set-Location "C:\Users\HAR\Documents\SEMESTER 5\SENIN\AI\Project\AI-Pakar"; .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

### 4. Run the UI

```powershell
Set-Location "C:\Users\HAR\Documents\SEMESTER 5\SENIN\AI\Project\AI-Pakar"; .venv\Scripts\python.exe -m streamlit run frontend/streamlit_app.py
```

Open `http://localhost:8501`. BM25 avoids the old Qdrant file-lock issue; Qdrant is optional.

## API

Canonical endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Status, rule lifecycle counts, demo mode |
| GET | `/v1/goals` | Supported goals, sources, required facts |
| POST | `/v1/check` | Check one goal |
| POST | `/v1/check/all` | Check all compliance goals |
| POST | `/v1/search` | Retrieve evidence (regulation only by default) |
| POST | `/v1/extract-facts` | Deterministic fact extraction by default |
| GET | `/v1/retrieval/status` | Index description |
| GET | `/v1/races` | Telemetry session catalog from the cached fixture |
| GET | `/v1/races/{session_id}/laps` | Available laps and metadata |
| POST | `/v1/telemetry/analyze` | Deterministic two-lap features, draft rules, evidence gates |
| POST | `/v1/ask` | Routed theory/telemetry answer with citations and limitations |

Legacy aliases remain for compatibility: `/goals`, `/check`, `/check/all`, `/retrieve`, `/extract-facts`.

Request:

```json
{
  "goal_id": "minimum_mass_compliance",
  "document_issue": "21",
  "facts": [
    {"name": "car_mass", "value": 800, "unit": "kg", "origin": "user"},
    {"name": "nominal_tyre_mass", "value": 70, "unit": "kg", "origin": "user"},
    {"name": "session_type", "value": "Q", "origin": "user"},
    {"name": "session_category", "value": "TTCS", "origin": "user"},
    {"name": "heat_hazard_declared", "value": false, "origin": "user"},
    {"name": "competition_heat_hazard_declared", "value": false, "origin": "user"}
  ]
}
```

Response includes `status`, `internal_status`, `scope`, `missing_facts`, `conflicts`, `diagnostics`, `rules_evaluated`, `citations` (with `verified`), `proof_trace`, and `explanation`.

Example:

```bat
curl -X POST http://127.0.0.1:8000/v1/check ^
  -H "Content-Type: application/json" ^
  -d "{\"goal_id\":\"wheelbase_compliance\",\"facts\":[{\"name\":\"wheelbase\",\"value\":3400,\"unit\":\"mm\"}]}"
```

Error envelopes:

- `422 INVALID_INPUT` — unknown fact, missing/incompatible unit, impossible value, bad schema.
- `409 CONFLICTING_INPUT` — same fact with different value/unit.
- `503` — retrieval/index or optional LLM provider failure.

## Validation rules for input facts

- Only the 11 supported fact names are accepted.
- Numeric facts require a unit; compatible units are normalized (mm/cm/m, g/kg/t).
- Negative values are rejected for the current dimensions/masses.
- Unknown facts, wrong types, and conflicting duplicates block evaluation before inference.
- Missing facts are reported as `INSUFFICIENT_DATA`, never as violations.

## RAG and evidence

- Chunks carry `document_id`, `article`/`subarticle`, `page`, `page_end`, `document_type`.
- Table-of-contents pages and repeated headers/footers are excluded.
- **BM25 is the primary lexical retriever**, with **TF-IDF fallback** when BM25 returns no positive hit.
- Qdrant + Sentence Transformers `all-MiniLM-L6-v2` remain available as an optional dense backend (`EMBEDDING_BACKEND=sentence_transformers`, `docker compose --profile qdrant up -d`).
- **Journal/methodology chunks are excluded from compliance search by default.** `/v1/search` only includes them when `include_methodology=true`.
- Each rule citation is checked against the stored page text; unverified evidence adds `SOURCE_MISSING`.
- BM25 builds in memory over 1,184 chunks; no model download is needed.

Known limitation: the TF-IDF vocabulary is dominated by Section C, so some methodology terms fall outside `max_features=4096`.

## Evaluation

```bat
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe scripts\run_evaluation.py
.venv\Scripts\python.exe scripts\validate_rules.py
```

Current state:

- **151 tests pass**.
- Decision suite: **18/18** internal outcomes, all external statuses correct, F1 (VIOLATED) = 1.0.
- Citation verification rate: **1.0**; trace consistency: **1.0**; explanation completeness: **1.0**.
- Engineering retrieval with BM25: **8/8 Hit@1**, Hit@3 **1.0**, MRR **1.0**.
- Legacy regulation retrieval (MiniLM + Qdrant, k=5): hit rate **0.9**, MRR **0.9**, precision@5 **0.18** (one C4.2/C10.1 confusion).
- Decision latency mean **7.43 ms**, p95 **120.62 ms** (includes first-case lazy source loading); failure rate **0.0**.
- Retrieval latency mean **91.57 ms**, p95 **351.86 ms** on the local machine (not a production benchmark).
- Dataset split: **12 development** + **6 held-out** cases (`datasets/development_cases.json`, `heldout_cases.json`).

MEX-AI telemetry slices:

- 2025 Abu Dhabi Q3: 617 / 623 samples; coverage 0.99995; 6 matched brake onsets.
- 2025 British GP Q3: 639 / 626 samples; VER 84.892 s vs NOR 85.010 s; Q3 times cross-checked against RaceData.
- Brake-onset deltas (Abu Dhabi): −8.96, +2.55, +1.24, +0.57, −15.32, −12.61 m; the last two exceed the ±10 m alignment-uncertainty flag.
- Speed delta (NOR − VER, Abu Dhabi): mean −0.344 km/h, min −23.13, max +14.037.
- Data gate PASS; knowledge gate PASS on quote presence only; `engineering_interpretation_status = INSUFFICIENT_DATA`.
- All 8 telemetry rules remain `draft`. No human review was performed.
- A/B/C LLM comparison: A-only not run; B vs C is in `research/b_vs_c_comparison.md`.

These results are on small, synthetic or public fixtures. They are not evidence of real-world accuracy.

## LLM stage (Gemini free tier)

The workspace `.env` is configured for an OpenAI-compatible Google AI Studio endpoint:

```bat
LLM_PROVIDER=api
LLM_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_MODEL=gemini-3.1-flash-lite
LLM_API_KEY=...local only...
```

`/v1/ask` now returns `generation_status=generated` for smoke-tested theory and telemetry questions. The key stays in `.env` (gitignored); tests force `LLM_PROVIDER=none` and an empty key so pytest does not consume API quota. A/B/C comparison and semantic citation audit are still pending.

Optional Ollama configuration remains available:

```bat
set LLM_PROVIDER=ollama
set OLLAMA_BASE_URL=http://localhost:11434
set OLLAMA_MODEL=llama3.1
```

The LLM may only propose facts and phrasing; it cannot create/activate rules or override the engine verdict.

## Project layout

```
app/
  api/routes.py                 /v1 API + legacy aliases + telemetry/ask endpoints
  document_processing/          PDF loader, extractor (SHA-256), chunker
  rag/                          BM25/TF-IDF/Qdrant stores, retriever, Markdown corpus, grounded answers
  llm/                          provider adapters + validated fact extraction
  expert_system/                KB, rule engine, backward chaining, explanation, service
  race_data/                    telemetry fixture loader, validation, alignment
  telemetry/                    deterministic features, analysis service, plots
  learning/                     evidence gates, scoped retrieval, question routing, analysis service
  schemas/                      facts, fact specs/units, rules, results, API, telemetry, analysis, learning
  evaluation/                   metrics and evaluator (dev/held-out split)
  config.py                     env settings + local cache isolation
  main.py                       FastAPI app + structured error handlers
knowledge_base/                 source PDFs, processed text, manifest, rules, facts, telemetry notes
datasets/                       development/held-out cases, expected results, retrieval cases, telemetry fixtures
research/                       document analysis, rule selection, validation log, architecture, evaluation, revision decisions
frontend/streamlit_app.py       Race Analysis / Engineering Tutor / Regulation Lab
tests/                          151 tests
scripts/                        extract, index, evaluate, validate, migrate, split
storage/                        model cache, optional Qdrant, BM25/TF-IDF indexes, plots, logs (gitignored)
```

## Security and isolation

- `.venv`, model cache, optional Qdrant, and logs stay inside the workspace.
- Secrets only via `.env`; `.env` is gitignored and excluded from Docker build context.
- No arbitrary code execution from rules or LLM output.
- Input paths and fact names are validated; no upload feature.
- BM25 needs no external service. Qdrant is optional (`docker compose --profile qdrant up -d`) and uses a file lock in local mode.

## Limitations

- Five provisions only; Section A is not a rule source.
- No CAD/geometry, drawings, Reference Volumes, or homologation documents.
- Nominal Tyre Mass must be supplied externally.
- Tables/figures are not structured data; amendment colours are lost.
- Rules are demo-reviewed, not human-approved.
- A/B/C LLM comparison is partially done: B vs C completed on four cases; A-only not run.
- Docker build/run and CI-equivalent tests were verified locally; no GitHub remote run exists.
- One legacy retrieval confusion remains (C4.2 vs C10.1).
- Telemetry covers two sessions and three lap pairs; results are descriptive only.
- The 8 telemetry rules are `draft`; no human review was performed.
- Distance is provider-derived, so cross-lap alignment is approximate; brake is an indicator, not pressure.
- The knowledge gate checks quote presence, not semantic entailment.
- LLM smoke/accuracy cases are generated, but full semantic citation audit remains pending.
- Screenshots are in `research/screenshots/`; they were captured from the running app.

## Troubleshooting

- Console mojibake: `set PYTHONIOENCODING=utf-8`.
- `No module named app`: run from the project root (pytest config adds the path automatically).
- Qdrant lock error: use BM25 (default) or stop the other process.
- `/v1/retrieval/status` shows `tfidf`/`qdrant` unexpectedly: check `$env:EMBEDDING_BACKEND`; a shell value overrides `.env`. Unset it or set `bm25`.
- Model download unavailable: BM25/TF-IDF need no model; use `set EMBEDDING_BACKEND=tfidf` if needed.
