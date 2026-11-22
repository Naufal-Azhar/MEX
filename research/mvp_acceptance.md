# MVP Acceptance Checklist — Bab 33

**Date:** 21 November 2026
**Legend:** PASS = demonstrated by executed command/artifact; PARTIAL = implemented but a condition is unmet; BLOCKED = dependency unavailable.

| # | Requirement | Status | Evidence / reason |
|---|---|---|---|
| 1 | Pilih sesi dan lap nyata dari provider/cache terverifikasi tanpa upload manual | **PASS (two cached sessions)** | 2025 Abu Dhabi Q3 (7 laps) and 2025 British GP Q3 (VER lap 17, NOR lap 19); both from TracingInsights with SHA-256. |
| 2 | Dua lap ditampilkan dengan metadata sumber, channel availability, kualitas alignment; tidak ada data karangan | **PASS** | `manifest.json` + `manifest_2025_british_gp.json`; quality tables, data gate, sample counts, gaps, deleted/accurate flags measured. |
| 3 | Hitung minimal speed difference dan brake-onset difference dengan unit/sign benar; data kurang menghasilkan status yang sesuai | **PASS** | `speed_delta` and matched onsets across pairs; deleted lap withholds observations; non-monotonic distance is rejected; 9 independent gold checks pass; British Q3 times cross-checked to RaceData. |
| 4 | Tampilkan aturan aktif dan trace; bedakan fakta/inferensi/hipotesis/keterbatasan | **PARTIAL** | Trace, facts, findings and limitations are shown. The rules are `draft`, so they are not "active"; this is intentional and must not be misrepresented. |
| 5 | Satu pertanyaan teori dan satu pertanyaan kontekstual dijawab via RAG generatif aktif, sitasi valid, pertanyaan tanpa bukti ditahan | **PASS (smoke + accuracy check)** | Gemini `gemini-3.1-flash-lite`: engineering, telemetry and theory answers `generated`; server facts preserved; citations verified; unsupported query abstained. Answer accuracy: 3/3 structural, 5/5 telemetry facts. Full A/B/C and semantic audit still not run. |
| 6 | Legacy compliance regression lulus, lifecycle tidak dilonggarkan, scope demo terlihat | **PASS** | **151 tests pass**; 66 legacy cases unchanged; LTCS audit adds a condition without changing TC18; all 13 regulation rules remain `reviewed`/unapproved; UI warning visible. |
| 7 | Test cases, data manifest, source/rule mapping, evaluation report, screenshot aktual, batasan terdokumentasi | **PASS** | Tests, manifests, mappings, evaluation reports, and 7 actual screenshots in `research/screenshots/`; CI workflow validated locally. |
| 8 | Jika data/provider/model/reviewer tidak tersedia, laporkan blocker dan partial implementation secara jujur | **PASS** | Blockers recorded in `revision_decisions.md`, `learning_evaluation.md`, `source_security_review.md`, and `phase_execution_plan.md`; no synthetic data was passed off as real. |
| 9 | Multi-session selection and provenance | **PASS** | `sessions.json`, `/v1/races`, session-specific `/laps`, optional `session_id` in analyze, Streamlit selector and source attribution. |
| 10 | Lightweight retrieval without Qdrant | **PASS** | BM25 primary + TF-IDF fallback; `/v1/retrieval/status` reports `bm25_tfidf`; Qdrant optional Compose profile. |

## Blockers

1. **A/B/C evaluation**: answer accuracy smoke + four-case checks pass, but B-vs-C and full semantic citation audit are not run.
2. **Live F1 data**: `livetiming.formula1.com` returns 401 without an F1 account; OpenF1 is unreachable from this network. The MVP uses cached public fixtures.
3. **Human reviewer**: unavailable; candidate rules are internet-checked only, not human-approved. No rule was promoted.
4. **Rights**: Chalmers book permission and arXiv redistribution terms are not resolved; repo is private and both source documents are gitignored.
5. **CI**: workflow validated locally; no GitHub remote run exists yet.
6. **Docker**: build and run verified; stack stopped after testing, Qdrant volume retained.

## Next three tasks

1. Run B-vs-C with the same questions, facts and output schema.
2. Untrack files already committed before `.gitignore` was added (user git action).
3. Run the stack again for the demo and capture the final walkthrough.
