# MVP Acceptance Checklist — Bab 33

**Date:** 21 November 2026
**Legend:** PASS = demonstrated by executed command/artifact; PARTIAL = implemented but a condition is unmet; BLOCKED = dependency unavailable.

| # | Requirement | Status | Evidence / reason |
|---|---|---|---|
| 1 | Pilih sesi dan lap nyata dari provider/cache terverifikasi tanpa upload manual | **PASS (cached fixture)** | 2025 Abu Dhabi Qualifying, 7 laps (clean, medium, deleted, invalid-distance) from TracingInsights; manifest with SHA-256. |
| 2 | Dua lap ditampilkan dengan metadata sumber, channel availability, kualitas alignment; tidak ada data karangan | **PASS** | `datasets/telemetry/manifest.json`, quality tables, data gate; sample counts, gaps, deleted/accurate flags measured. |
| 3 | Hitung minimal speed difference dan brake-onset difference dengan unit/sign benar; data kurang menghasilkan status yang sesuai | **PASS** | `speed_delta` and matched onsets across pairs; deleted lap withholds observations; non-monotonic distance is rejected; 9 independent gold checks pass. |
| 4 | Tampilkan aturan aktif dan trace; bedakan fakta/inferensi/hipotesis/keterbatasan | **PARTIAL** | Trace, facts, findings and limitations are shown. The rules are `draft`, so they are not "active"; this is intentional and must not be misrepresented. |
| 5 | Satu pertanyaan teori dan satu pertanyaan kontekstual dijawab via RAG generatif aktif, sitasi valid, pertanyaan tanpa bukti ditahan | **PASS (smoke)** | Gemini `gemini-3.1-flash-lite` via `.env`: theory and telemetry answers `generated`; server facts preserved; citations `[E1]`/`[E1, E3]`; no-answer query returned `unsupported` with missing data/limitations. Full A/B/C and semantic audit still not run. |
| 6 | Legacy compliance regression lulus, lifecycle tidak dilonggarkan, scope demo terlihat | **PASS** | 140 tests pass; 66 legacy cases unchanged; LTCS audit adds a condition without changing TC18; all 13 regulation rules remain `reviewed`/unapproved; UI warning visible. |
| 7 | Test cases, data manifest, source/rule mapping, evaluation report, screenshot aktual, batasan terdokumentasi | **PASS** | Tests, manifest, mappings, evaluation reports, and 4 actual screenshots in `research/screenshots/` exist. CI workflow is added but unexecuted. |
| 8 | Jika data/provider/model/reviewer tidak tersedia, laporkan blocker dan partial implementation secara jujur | **PASS** | Blockers recorded in `revision_decisions.md`, `learning_evaluation.md`, and `security_audit.md`; no synthetic data was passed off as real. |

## Blockers

1. **LLM evaluation**: smoke test works, but A/B/C, B-vs-C, and semantic citation audit are not run.
2. **Live F1 data**: `livetiming.formula1.com` returns 401 without an F1 account; OpenF1 is unreachable from this network. The MVP uses cached public fixtures from one session.
3. **Human reviewer**: unavailable; no rule was promoted beyond `draft`/`reviewed`.
4. **Docker**: daemon not running; `docker compose config` parses, but build/run is unverified.
5. **CI**: workflow added, but no GitHub remote run exists yet.

## Next three tasks

1. Configure an LLM provider in `.env` and run one theory question plus one telemetry-case question through `/v1/ask`; record actual outputs and citation validation.
2. Add a second session and evaluate retrieval no-answer behavior with a semantic check, not only a score threshold.
3. Prepare and run the human rule review, then execute the B-vs-C comparison with the same questions, facts and output schema.
