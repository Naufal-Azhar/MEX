# MVP Acceptance Checklist — Bab 33

**Date:** 21 November 2026
**Legend:** PASS = demonstrated by executed command/artifact; PARTIAL = implemented but a condition is unmet; BLOCKED = dependency unavailable.

| # | Requirement | Status | Evidence / reason |
|---|---|---|---|
| 1 | Pilih sesi dan lap nyata dari provider/cache terverifikasi tanpa upload manual | **PASS (cached fixture)** | 2025 Abu Dhabi Qualifying, VER lap 14 and NOR lap 16 from TracingInsights; manifest with SHA-256. Live provider acquisition is blocked (see row 8). |
| 2 | Dua lap ditampilkan dengan metadata sumber, channel availability, kualitas alignment; tidak ada data karangan | **PASS** | `datasets/telemetry/manifest.json`, quality tables, data gate; sample counts and gaps measured. |
| 3 | Hitung minimal speed difference dan brake-onset difference dengan unit/sign benar; data kurang menghasilkan status yang sesuai | **PASS** | `speed_delta` and six matched onsets; sign convention documented and tested; invalid/gap tests pass. |
| 4 | Tampilkan aturan aktif dan trace; bedakan fakta/inferensi/hipotesis/keterbatasan | **PARTIAL** | Trace, facts, findings and limitations are shown. The rules are `draft`, so they are not "active"; this is intentional and must not be misrepresented. |
| 5 | Satu pertanyaan teori dan satu pertanyaan kontekstual dijawab via RAG generatif aktif, sitasi valid, pertanyaan tanpa bukti ditahan | **BLOCKED** | `/v1/ask` returns structured deterministic answers with citation validation, but `LLM_PROVIDER=none`. No generative RAG claim is possible. |
| 6 | Legacy compliance regression lulus, lifecycle tidak dilonggarkan, scope demo terlihat | **PASS** | 112 tests pass; 66 legacy cases unchanged; all 13 regulation rules remain `reviewed`/unapproved; UI warning visible. |
| 7 | Test cases, data manifest, source/rule mapping, evaluation report, screenshot aktual, batasan terdokumentasi | **PARTIAL** | Tests, manifest, `source_rule_mapping.md`, `learning_evaluation.md`, and limitations exist. An actual UI screenshot was not produced; headless AppTest was used instead. |
| 8 | Jika data/provider/model/reviewer tidak tersedia, laporkan blocker dan partial implementation secara jujur | **PASS** | Blockers recorded in `revision_decisions.md` and `learning_evaluation.md`; no synthetic data was passed off as real. |

## Blockers

1. **LLM provider**: none installed/configured. Real generative RAG, A/B/C comparison, and semantic citation audit are not done.
2. **Live F1 data**: `livetiming.formula1.com` returns 401 without an F1 account; OpenF1 is unreachable from this network. The MVP uses a cached public fixture.
3. **Human reviewer**: unavailable; no rule was promoted beyond `draft`.
4. **Docker**: daemon not running; Compose stack unverified.
5. **Screenshot**: no real browser screenshot artifact; UI was executed and interacted with via Streamlit `AppTest`.

## Next three tasks

1. Configure an LLM provider in `.env` and run one theory question plus one telemetry-case question through `/v1/ask`; record actual outputs and citation validation.
2. Add table-aware Markdown chunking for the brake/throttle data dictionary, then re-run the retrieval pilot on a larger query set.
3. Run the B-vs-C comparison with the same questions, facts and output schema; report the actual denominator and limitations, whether or not C wins.
