# PETA LENGKAP WORKSPACE — AI-Pakar
### F1 Technical Regulation Expert System / AI Pendamping Belajar Teknik F1

**Dibuat:** 20 November 2026
**Tujuan dokumen:** peta menyeluruh workspace ini untuk dibawa ke ChatGPT sebagai bahan brainstorming.
**Cakupan:** seluruh file, folder, kode, data, aturan, dokumen, hasil evaluasi, artefak runtime, riset, dan transkrip percakapan — tanpa terkecuali.
**Sifat:** deskriptif. Dokumen ini memetakan apa yang **benar-benar ada**, bukan apa yang seharusnya ada. Klaim yang belum terbukti ditandai.

---

## 0. Cara pakai dokumen ini

1. Bagian 1–3 memberi konteks cepat (produk, status, lingkungan).
2. Bagian 4 adalah inventaris file lengkap — cocok untuk menjawab "file apa saja yang ada?".
3. Bagian 5–7 menjelaskan arsitektur, kode, dan kontrak data.
4. Bagian 8–10 adalah inti pengetahuan: aturan FIA, korpus dokumen, dataset, dan hasil evaluasi.
5. Bagian 11–15 menjelaskan antarmuka, skrip, test, dan deployment.
6. Bagian 16–17 merangkum riset dan posisi novelty.
7. Bagian 18 berisi temuan/inkonsistensi hasil pemetaan.
8. Bagian 19 adalah brief siap-tempel untuk ChatGPT (pertanyaan brainstorming).
9. Bagian 20 glosarium dan perintah cepat.

> **Penting:** semua aturan masih berstatus `reviewed` (demo), **belum** `active` dan **belum** disetujui manusia. Semua hasil kepatuhan adalah demo/decision-support, bukan sertifikasi FIA.

---

## 1. Identitas proyek & ringkasan eksekutif

| Item | Nilai |
|---|---|
| Nama proyek | AI-Pakar / F1 Technical Regulation Expert System |
| Nama paket Python | `f1-technical-regulation-expert-system` |
| Versi paket | 1.1.0 (`pyproject.toml`), ruleset versi 1.0.0 |
| Jenis | Prototipe akademik sistem pakar (tugas mata kuliah AI) |
| Judul yang disetujui dosen | *Development of an Evidence-Based Motorsport Engineering Expert AI Using Retrieval-Augmented Generation* |
| Domain | Regulasi teknis Formula 1 2026, Section C |
| Sumber normatif | `FIA 2026 Formula One Regulations — Section C [Technical]`, **Issue 21, 19 Oktober 2026**, 254 halaman |
| Subdomain aturan | Fundamental dimensions & mass (C2.3 dan C4) |
| Target pengguna | Penggemar F1, mahasiswa, anggota klub F1 |
| Bukan target | Tim F1, FIA, scrutineer, sertifikasi kepatuhan seluruh mobil |
| Bahasa keluaran | Indonesia (penjelasan), Inggris (kode/istilah teknis) |
| Stack | Python, FastAPI, Streamlit, PyMuPDF, Pydantic, Sentence Transformers, Qdrant, scikit-learn, pytest |
| Metode inti | Backward Chaining deterministik 3-nilai + RAG + verifikasi sitasi; LLM opsional (nonaktif) |

### Angka kunci

| Metrik | Nilai |
|---|---|
| Aturan | **13 rule entry** = 5 compliance goal + 8 value subgoal |
| Status aturan | 13 `reviewed`, 0 `active`, 0 `draft`, 0 `deprecated`, semua `human_approved: false` |
| Fakta input yang didukung | **11 nama fakta** |
| Dokumen sumber terindeks | **4** (2 regulasi FIA + 2 jurnal) |
| Halaman dokumen | 254 + 84 + 17 + 8 = **363 halaman** |
| Chunk retrieval | **1.184** (Section C 987; Section A 160; BC journal 34; RAG journal 3) |
| Dataset keputusan | **18 kasus** (6 TRUE, 7 FALSE, 5 UNKNOWN) → 12 development + 6 held-out |
| Query retrieval | **10** |
| Test | **66** (pytest cache memuat 70 id; 4 id lama sudah tidak ada) |
| Endpoint API | 7 kanonik `/v1` + 5 alias legacy + `/rules`, `/sample-facts`, `/` |
| Akurasi keputusan (dataset sendiri) | 18/18 = 1.0 (internal & eksternal) |
| Retrieval | hit rate 0.9; MRR 0.9; precision@5 0.18; 1 miss (C4.2 vs C10.1) |
| LLM | `LLM_PROVIDER=none`; adapter ada, belum diuji |
| Antarmuka | Streamlit 4 tab, tema gelap ala Command Code |

### Status satu kalimat

Sistem sudah berjalan end-to-end untuk **5 ketentuan FIA 2026** dengan backward chaining deterministik, bukti halaman, dan UI; tetapi belum punya **rule 2025**, belum punya **jawaban generatif RAG**, belum punya **perbandingan lintas issue**, dan belum ada **validasi manusia**.

---

## 2. Snapshot lingkungan & status repo

| Item | Nilai |
|---|---|
| Working directory | `C:\Users\HAR\Documents\SEMESTER 5\SENIN\AI\Project\AI-Pakar` |
| OS | Windows (win32), shell PowerShell 5.1 |
| Python venv | `.venv` → **Python 3.14.10** |
| `requires-python` | `>=3.11` |
| Docker base image | `python:3.12-slim` (berbeda dari venv lokal) |
| Paket terpasang di venv | 86 distribusi |
| Ukuran `.venv` | ±1.407 MB |
| `.env` | **Tidak ada** (hanya `.env.example`) → semua default dipakai |
| Git | **Bukan repository git** (`fatal: not a git repository`) |
| CI | Tidak ada |
| Total file (di luar `.venv`) | **145 file** |
| Total ukuran proyek (di luar `.venv`) | ±133 MB (storage 95,5 MB; folder_dokumen 24,8 MB; knowledge_base 12,3 MB) |

Distribusi ekstensi (di luar `.venv`, `__pycache__`, `.git`):

| Ekstensi | Jumlah |
|---|---|
| `.py` | 50 |
| `.json` | 32 |
| `.md` | 23 |
| `.pdf` | 12 |
| `.jsonl` | 4 |
| tanpa ekstensi | 4 |
| `.TAG` | 2 |
| `.log` | 2 |
| `.gitignore` | 2 |
| `.toml` | 2 |
| `.txt` | 2 |
| `.sqlite`, `.jinja`, `.joblib`, `.lock`, `.safetensors`, `.yml`, `.example`, `.dockerignore`, `.png`, `.css` | masing-masing 1 |

---

## 3. Peta direktori & ukuran

```
AI-Pakar/
├── .commandcode/          2 file     <0,01 MB   preferensi taste
├── .pytest_cache/         5 file      0,01 MB   cache pytest (stale)
├── .streamlit/            1 file     <0,01 MB   tema Streamlit
├── .venv/                (tidak dipetakan) 1.407 MB  virtualenv
├── app/                  68 file      0,43 MB   34 file .py + __pycache__
├── configs/               1 file     <0,01 MB   contoh konfigurasi
├── datasets/              6 file      0,06 MB   dataset & hasil evaluasi
├── folder_dokumen/        9 file     24,76 MB   PDF pembanding + catatan sumber
├── frontend/              4 file      0,07 MB   Streamlit + CSS + referensi UI
├── knowledge_base/       20 file     12,30 MB   PDF sumber, hasil ekstraksi, aturan, fakta
├── research/             10 file      0,14 MB   9 markdown + 1 screenshot
├── scripts/              16 file      0,06 MB   7 skrip + __pycache__
├── storage/              28 file     95,51 MB   model cache, Qdrant, log
├── tests/                23 file      0,23 MB   8 file .py + __pycache__
└── (root)                11 file      0,07 MB   dokumen proyek + Docker + deps
```

---

## 4. Inventaris file lengkap

### 4.1 Root (11 file)

| File | Ukuran | Isi/peran |
|---|---:|---|
| `.dockerignore` | 82 B | Exclude `.venv/`, `storage/`, `__pycache__/`, `.git/`, `.env`, `*.log` |
| `.env.example` | 1.282 B | Template env: LLM, retrieval, API, `ALLOW_REVIEWED_RULES` |
| `.gitignore` | 265 B | Ignore `.env`, `.venv`, cache Python, `storage/`, `*.log` |
| `docker-compose.yml` | 1.127 B | 3 service: `qdrant`, `api`, `ui` |
| `Dockerfile` | 534 B | `python:3.12-slim`, install requirements, expose 8000/8501 |
| `project_context.md` | 26.241 B (251 baris) | Master specification & handover: FR, BR, gate, non-goals, kontrak status, aturan agen |
| `PROMPT.md` | 14.829 B (384 baris) | Brief awal berbahasa Indonesia: audit dokumen, arsitektur, aturan, evaluasi |
| `pyproject.toml` | 328 B | Metadata proyek + konfigurasi pytest |
| `rangkuman_proyek.md` | 16.834 B (329 baris) | Ringkasan proyek untuk brainstorming: arsitektur, hasil, gap, prior art, pertanyaan |
| `README.md` | 11.116 B (183 baris) | Dokumentasi teknis: quick start, endpoint, aturan, evaluasi, limitasi |
| `requirements.txt` | 266 B | 12 dependency utama dengan pin versi |

### 4.2 `app/` — 34 file Python (tanpa `__pycache__`)

| File | Baris | Peran & simbol utama |
|---|---:|---|
| `app/__init__.py` | 0 | Penanda paket |
| `app/config.py` | 91 | `ROOT`, `STORAGE_DIR`, `MODEL_CACHE_DIR`, `VECTOR_DB_DIR`, `LOG_DIR`, `PROCESSED_DIR`, `RULES_PATH`, `SAMPLE_FACTS_PATH`, `MANIFEST_PATH`, `DATASETS_DIR`; `ensure_directories()`, `configure_local_caches()`, `Settings`, `load_settings()`, `get_logger()` |
| `app/main.py` | 113 | `FastAPI` app v1.1.0, CORS `*`, router, exception handler untuk `FactBatchValidationError` (422), `FactConflictError` (409), `RequestValidationError` (422), `Exception` (500); `GET /`; `run()` |
| `app/api/__init__.py` | 0 | — |
| `app/api/routes.py` | 175 | Singleton `service()` dan `retriever()`; payload helper; `health`, `goals`, `rules`, `check_v1`, `check_legacy`, `check_all`, `search_v1`, `retrieve_legacy`, `retrieval_status`, `extract_facts`, `sample_facts` |
| `app/document_processing/__init__.py` | 0 | — |
| `app/document_processing/pdf_loader.py` | 54 | `open_document`, `read_metadata`, `extract_page`, `extract_pages`; `OCR_PAGE_CHAR_THRESHOLD = 40`; ekstraksi teks + block + font size + bold |
| `app/document_processing/text_extractor.py` | 183 | `slugify`, `classify`, `parse_fia_filename`, `load_overrides`, `render_markdown`, `build_document`, `write_document`; SHA-256, halaman, metadata, override manual |
| `app/document_processing/chunker.py` | 132 | `Chunk` dataclass; `ARTICLE_RE`, `SUBARTICLE_RE`, `NOISE_PATTERNS`; `chunk_pages`, `chunks_from_processed_dir`; buang TOC & header/footer |
| `app/rag/__init__.py` | 0 | — |
| `app/rag/embeddings.py` | 132 | `normalize_for_tfidf`, `EmbeddingError`, `EmbeddingBackend`, `TfidfEmbeddingBackend` (max_features 4096), `SentenceTransformerBackend`, `_sentence_transformer_cached`, `get_embedding_backend` (auto/tfidf/ST) |
| `app/rag/vector_store.py` | 184 | `SearchHit`; `TfidfVectorStore` (joblib), `NumpyVectorStore` (cosine in-memory), `QdrantVectorStore` (local/URL, filter article/document/type) |
| `app/rag/retriever.py` | 145 | `Retriever.from_chunks`, `load_or_build`, `search` (default hanya `regulation`), `describe`; `TFIDF_INDEX_PATH`, `DENSE_META_PATH`, `DENSE_COLLECTION="regulation_chunks"` |
| `app/llm/__init__.py` | 0 | — |
| `app/llm/base.py` | 41 | `LLMError`, `ChatMessage`, `LLMProvider` ABC, `get_provider()` |
| `app/llm/api_provider.py` | 42 | `OpenAICompatibleProvider` → `POST /chat/completions`, Bearer key |
| `app/llm/local_provider.py` | 37 | `OllamaProvider` → `POST /api/chat`, stream=False |
| `app/llm/fact_extractor.py` | 258 | `DeterministicFactExtractor` (regex ID/EN), `LLMFactExtractor` (JSON ketat + validasi `FACT_SPECS`), `get_extractor`; `SYSTEM_PROMPT`, `MEASUREMENT_KEYWORDS` |
| `app/expert_system/__init__.py` | 0 | — |
| `app/expert_system/knowledge_base.py` | 120 | `KnowledgeBase` (filter rule runnable, demo mode), `from_file`, `from_dict`, lifecycle counts, `rules_for_goal`, `goals`, `load_facts_from_file`, `load_document_manifest` |
| `app/expert_system/rule_engine.py` | 324 | `RuleEngine`; `render_operand`, `render_expr`; `Resolved`, `ConditionOutcome`; resolusi fact/goal_value/expr; evaluasi kondisi; `evaluate_rule`; konversi satuan; operator `< <= > >= == != in not_in` |
| `app/expert_system/backward_chaining.py` | 199 | `BackwardChainingEngine` (`MAX_DEPTH=25`), `prove()`, `_combine` boolean/value, cycle detection, memoization, `_build_trace`, `check_goal()` |
| `app/expert_system/explanation.py` | 139 | Penjelasan template deterministik (bukan LLM): `format_value`, `condition_text`, `render_trace_text`, `build_explanation` |
| `app/expert_system/service.py` | 400 | `ComplianceService`: validasi fakta, `goal_facts`, `requirements`, `check`, `check_all`, sitasi + verifikasi kutipan, diagnostik, `LIMITATIONS`, `DEMO_WARNING`, `normalize_text` |
| `app/schemas/__init__.py` | 0 | — |
| `app/schemas/units.py` | 29 | `UnitMismatch`, `UNIT_TABLE` (mm/cm/m, kg/g/t, s, deg, %), `convert_unit`, `is_number` |
| `app/schemas/facts.py` | 115 | `FactOrigin`, `Fact`, `FactInput`, `FactConflict`, `FactConflictError`, `FactStore`, `MissingFact`, `ExtractedFact`, `ExtractionResult` |
| `app/schemas/fact_specs.py` | 138 | `FACT_SPECS` (11 fakta), `ALLOWED_FACT_NAMES`, `FactValidationError`, `FactBatchValidationError`, `validate_and_normalize` |
| `app/schemas/rules.py` | 165 | `RuleStatus`, `Operator`, `Expr`, `Operand`, `Condition`, `EvidenceSpan`, `RuleSource`, `RuleValidation`, `Conclusion`, `Rule` (+validator lifecycle), `RuleSet` |
| `app/schemas/results.py` | 136 | `TruthValue`, `ExternalStatus`, `DiagnosticCode`, `Diagnostic`, `ConditionEvaluation`, `RuleEvaluation`, `TraceNode`, `GoalResult`, `Citation`, `CheckReport`, `RetrievalHit` |
| `app/schemas/api.py` | 71 | `CheckRequest`, `LegacyCheckRequest`, `CheckAllRequest`, `SearchRequest`, `ExtractRequest`, `GoalInfo`, `ErrorEnvelope` |
| `app/evaluation/__init__.py` | 0 | — |
| `app/evaluation/metrics.py` | 74 | `classification_metrics`, `set_precision_recall_f1`, `retrieval_metrics` |
| `app/evaluation/evaluator.py` | 244 | `Evaluator.run_decision_suite`, `run_retrieval_suite`, `run_all`; `explanation_completeness`, `trace_consistency`; agregasi dev/held-out |

### 4.3 `frontend/` (3 file sumber)

| File | Ukuran | Peran |
|---|---:|---|
| `streamlit_app.py` | 24.968 B | UI 4 tab: Pemeriksaan, Cari bukti, Aturan & sumber, Tentang; form fakta dinamis; ekstraksi teks; render report; download JSON; switch backend In-process/FastAPI |
| `theme.css` | 4.822 B | Tema gelap `#090a0c`, aksen `#e8eaed`, sudut tajam, tab, tombol, form, tabel, responsif, `prefers-reduced-motion` |
| `UI_REFERENCES.md` | 1.148 B | Catatan referensi komponen gratis 21st.dev (Dashboard Sidebar, Sidebar, Minimal Button, Input) + alasan adaptasi ke Streamlit |
| `__pycache__/` | — | Cache Python |

### 4.4 `scripts/` (7 file Python)

| File | Baris | Fungsi | Output/side effect |
|---|---:|---|---|
| `extract_documents.py` | 118 | Ekstraksi semua PDF di `knowledge_base/source_documents` | 3 file per dokumen (`.json`, `.md`, `.pages.jsonl`) + `document_manifest.json` |
| `build_index.py` | 30 | Bangun ulang indeks retrieval (`force=True`) | Qdrant/TF-IDF di `storage/vector_db` |
| `run_evaluation.py` | 170 | Jalankan decision + retrieval suite | `datasets/evaluation_results.json`, `research/evaluation_results.md` |
| `validate_rules.py` | 105 | Cek kutipan setiap rule ada di halaman yang dirujuk | `research/rule_validation_log.md`; exit 1 jika gagal |
| `split_dataset.py` | 55 | Split deterministik 18 kasus → 12 dev + 6 held-out | `development_cases.json`, `heldout_cases.json`, `test_cases.json` |
| `migrate_rules_v2.py` | 73 | Migrasi status rule ke `reviewed`, isi validation, `human_approved=false` | Menulis ulang `rules.json` (one-off) |
| `add_external_status.py` | 33 | Tambah `expected_external_status` ke expected results | Menulis `expected_results.json` (one-off) |

### 4.5 `tests/` (8 file Python)

| File | Baris | Cakupan |
|---|---:|---|
| `conftest.py` | 31 | Set env `EMBEDDING_BACKEND=tfidf`, `LLM_PROVIDER=none`; fixture `kb` (session), `service`, `facts_factory` |
| `test_backward_chaining.py` | 145 | Batas wheelbase, missing→UNKNOWN, subgoal minimum mass, heat hazard, propagasi missing fact, NOT_APPLICABLE, cycle detection, konflik aturan |
| `test_document_processing.py` | 59 | Manifest 4 dokumen + SHA-256, 254 halaman Section C, output ada, PDF loader, chunk metadata, TOC tidak diindeks, jurnal terindeks |
| `test_end_to_end.py` | 180 | 18 kasus dataset lewat `TestClient`, health, goals, rules lifecycle, unknown goal, version mismatch, konflik 409, invalid 422, check-all 5 goal, ekstraksi deterministik, search exclude methodology, retrieval C2.3.3, legacy endpoint |
| `test_retrieval.py` | 79 | Query wheelbase, metadata & skor, filter artikel, query kosong, exclude journal, NumPy cosine, Qdrant local |
| `test_rule_engine.py` | 88 | Konversi satuan, TRUE/FALSE, missing fact+unit, mismatch→UNKNOWN, `in`, boolean equality, ekspresi aritmetika, tanpa pembulatan, NOT_APPLICABLE |
| `test_rule_sources.py` | 62 | Semua kutipan ada di halaman, semua rule reviewed & tidak approved, active tanpa approval ditolak, reviewed bisa dimatikan |
| `__init__.py` | 0 | — |

### 4.6 `knowledge_base/` (20 file)

| File | Ukuran | Peran |
|---|---:|---|
| `document_manifest.json` | 6.941 B | Manifest 4 dokumen: SHA-256, ukuran, halaman, issue, tanggal, status ekstraksi, path output |
| `metadata/document_overrides.json` | 2.181 B | Metadata hasil verifikasi manual (judul, publisher, penulis, DOI, tanggal) |
| `facts/sample_facts.json` | 1.293 B | 11 fakta contoh untuk mobil fiktif |
| `rules/rules.json` | 28.275 B | Ruleset 2026: 13 rule, sumber, kondisi, validasi |
| `processed_documents/2024-konvens-main-6.json` | 75.274 B | Dokumen jurnal RAG, 8 halaman |
| `processed_documents/2024-konvens-main-6.md` | 30.205 B | Markdown dengan penanda halaman |
| `processed_documents/2024-konvens-main-6.pages.jsonl` | 30.472 B | Satu baris per halaman |
| `processed_documents/backward-chaining-...-knowledge-bases.json` | 106.802 B | Jurnal BC, 17 halaman |
| `processed_documents/backward-chaining-...-knowledge-bases.md` | 47.021 B | Markdown |
| `processed_documents/backward-chaining-...-knowledge-bases.pages.jsonl` | 49.457 B | JSONL |
| `processed_documents/fia-2026-...-section-a-...-iss-03-2026-06-25.json` | 664.757 B | Section A, 84 halaman |
| `processed_documents/fia-2026-...-section-a-....md` | 242.617 B | Markdown |
| `processed_documents/fia-2026-...-section-a-....pages.jsonl` | 254.932 B | JSONL |
| `processed_documents/fia-2026-...-section-c-...-iss-21-2026-10-19.json` | 2.004.412 B | Section C, 254 halaman |
| `processed_documents/fia-2026-...-section-c-....md` | 657.562 B | Markdown |
| `processed_documents/fia-2026-...-section-c-....pages.jsonl` | 691.730 B | JSONL |
| `source_documents/REGULASI FIA/FIA 2026 F1 Regulations - Section A [General Provisions] - Iss 03 - 2026-06-25.pdf` | 972.269 B | PDF sumber (84 hlm) |
| `source_documents/REGULASI FIA/FIA 2026 F1 Regulations - Section C [Technical] - Iss 21 - 2026-10-19.pdf` | 4.617.723 B | PDF sumber utama (254 hlm) |
| `source_documents/Jurnal/2024.konvens-main.6.pdf` | 351.935 B | Jurnal RAG & sitasi (8 hlm) |
| `source_documents/Jurnal/Backward chaining inference as a database stored procedure ... knowledge bases.pdf` | 2.062.096 B | Jurnal backward chaining (17 hlm) |

### 4.7 `datasets/` (6 file)

| File | Ukuran | Isi |
|---|---:|---|
| `test_cases.json` | 10.026 B | Gabungan 18 kasus (generated convenience artifact) |
| `development_cases.json` | 6.960 B | 12 kasus development |
| `heldout_cases.json` | 3.442 B | 6 kasus held-out |
| `expected_results.json` | 6.555 B | Expected status internal/eksternal, rule, article, missing facts, alasan |
| `retrieval_cases.json` | 1.647 B | 10 query + artikel gold |
| `evaluation_results.json` | 36.867 B | Hasil run terakhir: 18 baris keputusan + 10 retrieval + agregat + by_split |

### 4.8 `research/` (10 file)

| File | Baris/Ukuran | Isi |
|---|---:|---|
| `architecture.md` | 145 baris | Peta komponen, alur, semantik inferensi, RAG, batas LLM, storage, API, keamanan, limitasi |
| `document_analysis.md` | 116 baris | Analisis 4 dokumen, struktur Section C, kandidat aturan, dependensi silang, kualitas ekstraksi, rekomendasi subdomain |
| `rule_selection.md` | 130 baris | 5 rule card lengkap: pasal, kutipan, fakta, TRUE/FALSE/UNKNOWN, alasan, dependensi; kandidat yang belum diaktifkan |
| `rule_validation_log.md` | 35 baris | Tabel 13 rule: quote check PASS, human_approved False, reviewer `internal_agent_check`, test cases; kolom sign-off kosong |
| `evaluation_plan.md` | 87 baris | Tujuan, dataset, metrik, rencana A/B/C, prosedur, hasil ringkas, ancaman validitas |
| `evaluation_results.md` | 82 baris | Hasil lengkap: agregat, split, per-case, confusion matrix, retrieval, limitasi |
| `rencana_pengembangan_proyek.md` | 53 baris | Rencana 6 tahap: kunci skenario → rule 2025 → compare → RAG answer → UI → evaluasi |
| `pembanding_simulator_regulasi.md` | 73 baris | Riset pembanding produk/publikasi, matriks bukti, revisi klaim novelty, skenario wheelbase 2025 vs 2026 |
| `transkrip_percakapan_ai_pakar.md` | 428 baris | Transkrip 21 giliran percakapan Codex tentang UI, arah produk, judul, novelty, dan rencana |
| `percakapan_assets/tangkapan_layar_tab_navigasi.png` | 11,5 KB | Screenshot tab Streamlit yang berhimpitan (bukti perbaikan CSS) |

### 4.9 Konfigurasi kecil

| File | Isi |
|---|---|
| `configs/settings.example.json` | Dokumentasi default: llm, retrieval, api, inference (`max_depth 25`, `allow_reviewed_rules`, `unknown_is_never_false`, `violation_dominates`) |
| `.streamlit/config.toml` | Tema dark: primary `#e8eaed`, bg `#090a0c`, secondary `#15181c`, text `#e8e9eb`, `toolbarMode="minimal"` |
| `.commandcode/taste/taste.md` | Index taste → link ke file kategori |
| `.commandcode/taste/taste-—-command-code/taste.md` | 7 preferensi kerja (isolasi workspace, user menjalankan server sendiri, perintah PowerShell 5.1, jawab langsung, brief dulu sebelum eksekusi) |
| `.pytest_cache/README.md` | Dokumentasi bawaan pytest |
| `.pytest_cache/CACHEDIR.TAG` | Penanda direktori cache |
| `.pytest_cache/.gitignore` | `*` |
| `.pytest_cache/v/cache/nodeids` | 70 id test (termasuk 4 id lama) |
| `.pytest_cache/v/cache/lastfailed` | 3 kegagalan lama dari versi test sebelumnya |

### 4.10 `storage/` (28 file, 95,51 MB) — artefak runtime, gitignored

| File | Ukuran | Peran |
|---|---:|---|
| `logs/app.log` | 36.030 B | Log aplikasi: build index, setiap `check`, load retriever |
| `model_cache/.agent_harnesses.json` | 9.285 B | Katalog harness agen AI (bukan bagian aplikasi; artefak tooling) |
| `model_cache/sentence-transformers/CACHEDIR.TAG` | 195 B | Penanda cache |
| `model_cache/sentence-transformers/models--sentence-transformers--all-MiniLM-L6-v2/refs/main` | 40 B | Ref model |
| `.../snapshots/1110a243.../config.json` | 612 B | Konfigurasi model |
| `.../config_sentence_transformers.json` | 116 B | Konfigurasi ST |
| `.../model.safetensors` | 90.868.376 B | Bobot model MiniLM |
| `.../modules.json` | 349 B | Pipeline modul |
| `.../README.md` | 10.502 B | Kartu model |
| `.../sentence_bert_config.json` | 53 B | Konfigurasi BERT |
| `.../special_tokens_map.json` | 112 B | Special tokens |
| `.../tokenizer.json` | 466.247 B | Tokenizer |
| `.../tokenizer_config.json` | 350 B | Konfigurasi tokenizer |
| `.../vocab.txt` | 231.508 B | Vocabulary |
| `.../1_Pooling/config.json` | 190 B | Pooling |
| `.../.no_exist/.../adapter_config.json` | 0 B | Placeholder |
| `.../.no_exist/.../added_tokens.json` | 0 B | Placeholder |
| `.../.no_exist/.../chat_template.jinja` | 0 B | Placeholder |
| `.../.no_exist/.../preprocessor_config.json` | 0 B | Placeholder |
| `.../.no_exist/.../processor_config.json` | 0 B | Placeholder |
| `.../.no_exist/.../video_preprocessor_config.json` | 0 B | Placeholder |
| `.../.no_exist/.../2_Normalize/config.json` | 0 B | Placeholder |
| `model_cache/xet/logs/xet_20261117T113334140+0700_14840.log` | 85.651 B | Log unduhan Hugging Face Xet |
| `vector_db/dense_index.json` | 141 B | Metadata indeks: ST, MiniLM, dim 384, 1184 chunk |
| `vector_db/tfidf_index.joblib` | 2.357.696 B | Indeks TF-IDF fallback |
| `vector_db/qdrant/.lock` | 13 B | Lock file Qdrant local |
| `vector_db/qdrant/meta.json` | 590 B | Metadata koleksi `regulation_chunks` (384, Cosine) |
| `vector_db/qdrant/collection/regulation_chunks/storage.sqlite` | 6.086.656 B | Penyimpanan koleksi Qdrant |

### 4.11 `folder_dokumen/` (9 file, 24,76 MB) — bahan riset, belum terintegrasi

| File | Halaman | Ukuran | SHA-256 (16 awal) | Catatan |
|---|---:|---:|---|---|
| `FIA 2025 F1 Technical Regulations - Issue 03 - 2025-04-07.pdf` | 179 | 2.242.504 B | `454b76e2b388e61d` | Pembanding 2025; wheelbase 3.4.2 = 3600 mm |
| `FIA 2026 Section C Technical - Issue 16 - 2026-02-27.pdf` | 259 | 5.454.798 B | `06611459e6eff9c7` | Issue awal 2026 |
| `FIA 2026 Section C Technical - Issue 19 - 2026-06-25.pdf` | 257 | 4.432.143 B | `8751d3d478706753` | Issue 2026 |
| `FIA 2026 Section C Technical - Issue 20 - 2026-08-05.pdf` | 254 | 5.825.714 B | `cf0b919eef5eecc2` | Pembanding langsung Issue 21 |
| `Jurnal/2024.konvens-main.6.pdf` | 8 | 351.935 B | `ec0917dbcd988fcc` | Duplikat byte-identik dari knowledge_base |
| `Jurnal/Backward chaining inference ... knowledge bases.pdf` | 17 | 2.062.096 B | `5c7a85f83a66d329` | Duplikat byte-identik |
| `REGULASI FIA/FIA 2026 F1 Regulations - Section A [General Provisions] - Iss 03 - 2026-06-25.pdf` | 84 | 972.269 B | `6ce8c9420ddb8194` | Duplikat byte-identik |
| `REGULASI FIA/FIA 2026 F1 Regulations - Section C [Technical] - Iss 21 - 2026-10-19.pdf` | 254 | 4.617.723 B | `698d14b6c3b340c3` | Duplikat byte-identik (dokumen utama) |
| `SUMBER_UNDUHAN.md` | — | 1.943 B | — | Tabel sumber resmi FIA + kandidat perbandingan |

### 4.12 `.venv/`

Virtual environment lokal, 86 paket, Python 3.14.10. Tidak dipetakan per file (1.407 MB). Semua cache model diarahkan ke `storage/model_cache` lewat `app/config.py`.

---

## 5. Arsitektur sistem & alur data

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Streamlit UI (8501)                         │
│  Tab 01 Pemeriksaan │ 02 Cari bukti │ 03 Aturan │ 04 Tentang          │
└───────────────┬──────────────────────────────────┬───────────────────┘
                │ in-process                        │ HTTP (FastAPI mode)
                ▼                                   ▼
      ┌───────────────────┐               ┌────────────────────┐
      │ ComplianceService │◄──────────────│  FastAPI (8000)    │
      │  (orchestrator)   │               │  app/api/routes.py │
      └─────────┬─────────┘               └─────────┬──────────┘
                │                                   │
    ┌───────────┼───────────────┬───────────────────┴──────────┐
    ▼           ▼               ▼                              ▼
┌────────┐ ┌──────────────┐ ┌──────────────┐          ┌────────────────┐
│Knowledge│ │Backward      │ │Explanation   │          │ Retriever      │
│Base     │ │Chaining      │ │(template)    │          │ RAG            │
│rules.json│ │Engine        │ │              │          │                │
└────┬────┘ └──────┬───────┘ └──────────────┘          └───────┬────────┘
     │             ▼                                         │
     │      ┌──────────────┐                  ┌──────────────┴───────────┐
     │      │ RuleEngine   │                  │ Embeddings                │
     │      │ (facts/units)│                  │ ST MiniLM  │ TF-IDF       │
     │      └──────────────┘                  └──────┬───────────┬────────┘
     │                                               ▼           ▼
     │                                        Qdrant local   TF-IDF index
     ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Ingestion: PDF → pdf_loader → text_extractor → chunker → index       │
│ Files: scripts/extract_documents.py, scripts/build_index.py          │
└──────────────────────────────────────────────────────────────────────┘
```

### Alur pemeriksaan kepatuhan

1. Pengguna memilih `goal_id` (5 goal kepatuhan) dan mengisi fakta (form atau teks).
2. `ComplianceService.build_fact_store()` memvalidasi nama, tipe, satuan, nilai minimum; duplikat konflik → `FactConflictError` (409).
3. `check()` memeriksa `document_issue` (harus "21") dan keberadaan goal; jika tidak → `UNSUPPORTED` + diagnostik.
4. `BackwardChainingEngine.prove(goal)`:
   - ambil rule runnable untuk goal;
   - evaluasi `applies_if` (konteks);
   - evaluasi `conditions`; operand bisa `fact`, `const`, `expr`, `goal_value`;
   - `goal_value` memicu subgoal rekursif (contoh C4.2 → C4.1 → C4.6);
   - gabungkan: FALSE menang, lalu TRUE, lalu UNKNOWN; memoization; deteksi siklus; depth maks 25.
5. `ComplianceService` menyusun `CheckReport`: status eksternal, aturan penentu, kutipan, kondisi, fakta hilang, rules evaluated, trace, diagnostik, limitasi.
6. Sitasi diverifikasi: kutipan dinormalisasi dan dicari di teks halaman yang tersimpan; gagal → `SOURCE_MISSING`; jika aturan penentu tidak terverifikasi, `SATISFIED`/`VIOLATED` diturunkan menjadi `INSUFFICIENT_DATA`.
7. Penjelasan dibuat oleh template deterministik, bukan LLM.

### Alur retrieval

```
PDF → PyMuPDF (per halaman, blocks, font size) → JSON/MD/JSONL
    → chunker (buang TOC & header/footer; metadata article/subarticle/page)
    → embedding (MiniLM 384d atau TF-IDF max_features 4096)
    → Qdrant local / TF-IDF joblib
    → search(query, top_k, article?, document_id?, include_methodology?)
    → RetrievalHit (document_id, document_type, article, page, text, score, chunk_id)
```

### Prinsip pemisahan tugas

| Komponen | Boleh | Tidak boleh |
|---|---|---|
| RAG | Mengambil bukti + metadata + skor | Menentukan TRUE/FALSE, menyatakan patuh |
| LLM | Mengusulkan fakta dari teks, menyusun narasi (belum aktif) | Membuat/mengubah aturan, mengubah verdict, mengaktifkan rule |
| Rule engine / BC | Menghitung kondisi, subgoal, verdict deterministik | Mengarang nilai, mengabaikan satuan |
| Explanation | Meringkas trace engine | Menafsirkan ulang hasil |

---

## 6. Model data & kontrak

### 6.1 Fakta yang didukung (11)

| Nama fakta | Tipe | Satuan | Aturan/nilai | Dipakai goal |
|---|---|---|---|---|
| `max_half_width_excluding_tyres_and_rims` | number | mm | min 0 | half_width_compliance |
| `wheelbase` | number | mm | min 0 | wheelbase_compliance |
| `cockpit_position_distance` | number | mm | min 0 | cockpit_position_compliance |
| `car_mass` | number | kg | min 0 | minimum_mass_compliance |
| `nominal_tyre_mass` | number | kg | min 0 | minimum_mass_compliance, mass_distribution_compliance |
| `front_axle_mass` | number | kg | min 0 | mass_distribution_compliance |
| `rear_axle_mass` | number | kg | min 0 | mass_distribution_compliance |
| `session_type` | string | — | `Q`, `SQ`, `R`, `FP`, `SPRINT`, `OTHER` | minimum_mass, mass_distribution |
| `session_category` | string | — | `TTCS`, `LTCS` | minimum_mass |
| `heat_hazard_declared` | boolean | — | — | minimum_mass |
| `competition_heat_hazard_declared` | boolean | — | — | minimum_mass |

### 6.2 Satuan yang didukung (`UNIT_TABLE`)

| Dimensi | Satuan | Faktor ke basis |
|---|---|---|
| length | mm / cm / m | 1 / 10 / 1000 |
| mass | kg / g / t | 1 / 0,001 / 1000 |
| time | s | 1 |
| angle | deg | 1 |
| percent | % | 1 |

Aturan: satuan tidak kompatibel → `UNKNOWN` + detail `incompatible units`, **bukan** FALSE. Tidak ada pembulatan nilai batas (sesuai C2.5).

### 6.3 Skema aturan (`Rule`)

```
rule_id, name, source{document_id, document, issue, article, page, quote, evidence_span},
applies_if[Condition], conditions[Condition],
conclusion{goal, kind: boolean|value, value?, unit?, expr?},
status: draft|reviewed|active|deprecated,
validation{verified_against, verified_on, method, reviewer?, reviewed_at?, human_approved, test_case_ids[], notes?},
notes
```

`Condition` = `left Operand`, `operator`, `right Operand?`, `unit?`, `description?`.
`Operand` = tepat satu dari `const`, `fact`, `goal_value`, `expr`.
`Expr` = `op: add|sub|mul|div`, `args: Operand[]` (min 2).

Validasi lifecycle:
- `reviewed`/`active` wajib punya `validation`;
- `active` wajib `human_approved=true` + `reviewer`, `reviewed_at`, `verified_against`, `verified_on`, `method`;
- `RuleSet` menolak `rule_id` duplikat;
- satu goal tidak boleh mencampur rule boolean dan value.

### 6.4 Status & diagnostik

| Internal (proof) | Eksternal (API/UI) |
|---|---|
| `TRUE` | `SATISFIED` |
| `FALSE` | `VIOLATED` |
| `UNKNOWN` | `INSUFFICIENT_DATA` |
| — | `NOT_APPLICABLE` (semua kandidat rule definitif tidak berlaku) |
| — | `UNSUPPORTED` (goal/issue di luar ruleset) |
| — | `ERROR` (kegagalan sistem, bukan verdict) |

Diagnostik: `INVALID_INPUT`, `CONFLICTING_INPUT`, `SOURCE_MISSING`, `VERSION_MISMATCH`, `UNSUPPORTED_GOAL`, `RULE_NOT_APPROVED`, `INTERNAL_ERROR`.

Aturan penggabungan:
- ada rule FALSE → goal FALSE (konservatif);
- TRUE + FALSE bersamaan → FALSE, `rule_conflict=true`;
- UNKNOWN tidak pernah diubah menjadi FALSE;
- rule tidak berlaku → `NOT_APPLICABLE`, bukan `SATISFIED`.

### 6.5 Bentuk `CheckReport`

Field: `goal_id`, `status`, `internal_status`, `value`, `scope`, `explanation`, `rule_id`, `rule_name`, `rule_status`, `validation_warning`, `source`, `applicability_conditions[]`, `conditions[]`, `missing_facts[]`, `conflicts[]`, `diagnostics[]`, `rules_evaluated[]`, `citations[]`, `facts_used{}`, `proof_trace`, `regulation{}`, `limitations[]`, `rule_conflict`, `generated_at`.

`TraceNode`: `node_id`, `goal`, `kind`, `status`, `value`, `rule_id`, `rule_name`, `expression`, `source`, `conditions[]`, `children[]`, `notes[]`.

---

## 7. Knowledge base aturan — 13 rule entry

### 7.1 Tabel aturan

| # | Rule ID | Goal | Kind | Artikel | Hlm | Ketentuan | Status |
|---|---|---|---|---|---:|---|---|
| 1 | `FIA26-C2.3.1-HALF-WIDTH` | half_width_compliance | boolean | C2.3.1 | 10 | Tidak ada bagian non-eksklusi > 950 mm dari plane Y=0 | reviewed |
| 2 | `FIA26-C2.3.3-WHEELBASE` | wheelbase_compliance | boolean | C2.3.3 | 11 | Wheelbase ≤ 3400 mm | reviewed |
| 3 | `FIA26-C2.3.5-COCKPIT-POSITION` | cockpit_position_compliance | boolean | C2.3.5 | 11 | Jarak XA=0–XC=0 ∈ [1830, 2030] mm | reviewed |
| 4 | `FIA26-C4.1-BASE-MASS-Q` | base_minimum_mass | value 726 kg | C4.1 | 59 | Sesi SQ/Q → base 726 kg | reviewed |
| 5 | `FIA26-C4.1-BASE-MASS-OTHER` | base_minimum_mass | value 724 kg | C4.1 | 59 | Sesi lain → base 724 kg | reviewed |
| 6 | `FIA26-C4.6-HEAT-INCREASE-TTCS-DECLARED` | heat_hazard_mass_increase | value 5 kg | C4.6 | 60 | TTCS + heat hazard sesi + competition | reviewed |
| 7 | `FIA26-C4.6-HEAT-INCREASE-LTCS-COMPETITION` | heat_hazard_mass_increase | value 2 kg | C4.6 | 60 | Competition heat hazard + LTCS | reviewed |
| 8 | `FIA26-C4.6-HEAT-INCREASE-TTCS-NOT-DECLARED` | heat_hazard_mass_increase | value 2 kg | C4.6 | 60 | Competition heat hazard + TTCS tanpa heat sesi | reviewed |
| 9 | `FIA26-C4.6-HEAT-INCREASE-NONE` | heat_hazard_mass_increase | value 0 kg | C4.1 | 59 | Tidak ada heat hazard (sesi & competition) | reviewed |
| 10 | `FIA26-C4.1-MINIMUM-MASS-VALUE` | minimum_mass | value expr | C4.1 | 59 | base + nominal tyre mass + heat increase | reviewed |
| 11 | `FIA26-C4.2-MINIMUM-MASS-NO-HEAT` | minimum_mass_excluding_heat_hazard | value expr | C4.2 | 59 | base + nominal tyre mass | reviewed |
| 12 | `FIA26-C4.1-MINIMUM-MASS` | minimum_mass_compliance | boolean | C4.1 | 59 | car_mass ≥ minimum_mass | reviewed |
| 13 | `FIA26-C4.2-MASS-DISTRIBUTION` | mass_distribution_compliance | boolean | C4.2 | 59 | front ≥ 0,44×; rear ≥ 0,54× | reviewed |

### 7.2 Rantai backward chaining nyata

```
mass_distribution_compliance (C4.2, Q/SQ)
├── minimum_mass_excluding_heat_hazard (C4.2)
│   ├── base_minimum_mass (C4.1: 726 jika Q/SQ, 724 lainnya)
│   └── nominal_tyre_mass (FACT input)
├── front_axle_mass ≥ 0.44 × minimum_mass_excluding_heat_hazard
└── rear_axle_mass  ≥ 0.54 × minimum_mass_excluding_heat_hazard

minimum_mass_compliance (C4.1)
├── minimum_mass
│   ├── base_minimum_mass
│   ├── nominal_tyre_mass (FACT input)
│   └── heat_hazard_mass_increase (C4.6: 5 / 2 / 0 kg)
└── car_mass ≥ minimum_mass
```

### 7.3 Kutipan sumber (verbatim, terverifikasi otomatis)

| Rule | Kutipan |
|---|---|
| C2.3.1 | “Except for the tyres, the Wheel Rims, and parts attached to the Wheel Rims as defined in Article C10.7.6, no part of the car may lie more than 950mm from the plane Y=0 at Legality Setup.” |
| C2.3.3 | “The distance between the planes XF = 0 and XR = 0 must be less than or equal to 3400mm at Legality Setup.” |
| C2.3.5 | “The distance between XA = 0 and XC = 0 must be greater than or equal to 1830mm and less than or equal to 2030mm.” |
| C4.1 (base) | “During the Sprint Qualifying and Qualifying sessions, The Minimum Mass is 726kg plus the Nominal Tyre Mass. In all other sessions, the Minimum Mass is 724kg plus the Nominal Tyre Mass.” |
| C4.1 (compliance) | “At all times during the Competition, Car Mass must not be less than the Minimum Mass.” |
| C4.1 (heat) | “When a Heat Hazard is declared, the Minimum Mass will be increased by the Heat Hazard Mass Increase.” |
| C4.6 (5 kg) | “During a TTCS for which a Heat Hazard has been declared: a. The Heat Hazard Mass Increase is 5kg.” |
| C4.6 (2 kg) | “During a Competition at which a Heat Hazard has been declared for any session; For any LTCS or TTCS for which a Heat Hazard has not been declared: c. A Heat Hazard Mass Increase of 2kg will be applied.” |
| C4.2 (distribution) | “At all times during the Qualifying and Sprint Qualifying Sessions, with the car resting on a horizontal plane: i. …front axle… ≥ Minimum Mass … factored by 0.44. ii. …rear axle… ≥ … factored by 0.54.” |
| C4.2 (heat exclusion) | “If, when required for checking, a Heat Hazard has been declared, the increase in mass will not be considered.” |

### 7.4 Scope ruleset

`scope`: “Selected reviewed provisions only; not a whole-car compliance certification.”
`subdomain`: “Fundamental dimensions and mass (C2.3 and C4)”.

---

## 8. Dokumen sumber, ekstraksi, dan chunking

### 8.1 Manifest (4 dokumen)

| document_id | Judul | Jenis | Penerbit | Tahun | Issue | Hlm | Rata-rata char/hlm | OCR |
|---|---|---|---|---|---:|---:|---:|---|
| `fia-2026-f1-regulations-section-c-technical-iss-21-2026-10-19` | FIA 2026 F1 Regulations — Section C [Technical] | regulation | FIA | 2026 | 21 (2026-10-19) | 254 | 2.500,1 | 0 |
| `fia-2026-f1-regulations-section-a-general-provisions-iss-03-2026-06-25` | FIA 2026 F1 Regulations — Section A [General Provisions] | regulation | FIA | 2026 | 03 (2026-06-25) | 84 | 2.709,5 | 0 |
| `backward-chaining-inference-as-a-database-stored-procedure-the-experiments-on-real-world-knowledge-bases` | Backward chaining inference as a database stored procedure | journal | J. Information & Telecommunication (T&F) | 2018 | Vol.2 No.4 | 17 | 2.661,9 | 0 |
| `2024-konvens-main-6` | Evaluating and Fine-Tuning Retrieval-Augmented Language Models to Generate Text With Accurate Citations | journal | ACL / KONVENS 2024 | 2024 | Proc. KONVENS 2024 | 8 | 3.625,4 | 0 |

Total karakter ±937.000 (Section C 635.021; Section A 227.599; dua jurnal 74.256).

### 8.2 Chunking

| Dokumen | Chunk |
|---|---:|
| Section C (Issue 21) | **987** |
| Section A (Issue 03) | **160** |
| Jurnal backward chaining | **34** |
| Jurnal RAG & sitasi | **3** |
| **Total** | **1.184** |

- Section C menghasilkan **815 label artikel/subartikel** berbeda.
- Halaman TOC (≤6) tidak menghasilkan chunk.
- Header/footer berulang dibuang berdasarkan pola.
- Metadata chunk: `chunk_id`, `document_id`, `text`, `article`, `subarticle`, `page`, `page_end`, `document_type`.
- Chunk ID format: `{document_id}:p{start_page}:{index}`.

### 8.3 Struktur Section C

| Artikel | Judul | Halaman |
|---|---|---:|
| C1 | General Principles | 7 |
| C2 | Conventions and Fundamental Dimensions | 9 |
| C3 | Aerodynamic Components | 12 |
| C4 | Mass | 59 |
| C5 | Power Unit | 61 |
| C6 | Fuel System | 85 |
| C7 | Oil and Coolant Systems / Charge Air Cooling | 89 |
| C8 | Electrical Systems | 90 |
| C9 | Transmission System | 100 |
| C10 | Suspension, Steering, Wheels, Tyres | 106 |
| C11 | Brake System | 116 |
| C12 | Survival Cell | 118 |
| C13 | Safety Structures and Homologation | 129 |
| C14 | Safety Equipment | 148 |
| C15 | Materials | 153 |
| C16 | Fuel and Engine Oil | 164 |
| C17 | Components' Classification | 172 |
| C18 | Power Unit Components' Classification | 182 |
| App. C1 | Definitions | 190 |
| App. C2 | Regulation Volumes | 204 |
| App. C3 | Drawings | 220 |
| App. C4 | PU Systems/Functions/Components | 225 |
| App. C5 | Homologation & Development 2026–2030 | 237 |
| App. C6 | Components' Classification and Perimeter | 244 |

### 8.4 Keterbatasan ekstraksi yang sudah didokumentasikan

1. Gambar, diagram, CAD, Appendix C2/C3 tidak distrukturkan.
2. Tabel kompleks menjadi teks berurutan.
3. Warna amendment (hitam/merah muda/merah/oranye/hijau) hilang.
4. Header/footer harus difilter (sudah dilakukan).
5. Superscript/subscript/simbol sebagian kehilangan format.
6. Tidak ada halaman yang perlu OCR.

---

## 9. Dataset & evaluasi

### 9.1 18 kasus keputusan

| Case | Split | Goal | Fakta ringkas | Expected internal | Expected eksternal | Rule | Artikel |
|---|---|---|---|---|---|---|---|
| TC01 | dev | wheelbase | 3400 mm | TRUE | SATISFIED | C2.3.3 | C2.3.3 |
| TC02 | dev | cockpit | 1830 mm | TRUE | SATISFIED | C2.3.5 | C2.3.5 |
| TC03 | heldout | half width | 950 mm | TRUE | SATISFIED | C2.3.1 | C2.3.1 |
| TC04 | dev | minimum mass | 796 kg, tyre 70, Q, TTCS, no heat | TRUE | SATISFIED | C4.1 | C4.1 |
| TC05 | dev | distribution | Q, tyre 70, front 360, rear 440 | TRUE | SATISFIED | C4.2 | C4.2 |
| TC06 | dev | wheelbase | 3400,5 mm | FALSE | VIOLATED | C2.3.3 | C2.3.3 |
| TC07 | heldout | cockpit | 2031 mm | FALSE | VIOLATED | C2.3.5 | C2.3.5 |
| TC08 | dev | half width | 951 mm | FALSE | VIOLATED | C2.3.1 | C2.3.1 |
| TC09 | dev | minimum mass | 795,5 kg | FALSE | VIOLATED | C4.1 | C4.1 |
| TC10 | dev | distribution | front 350 kg | FALSE | VIOLATED | C4.2 | C4.2 |
| TC11 | dev | wheelbase | kosong | UNKNOWN | INSUFFICIENT_DATA | C2.3.3 | C2.3.3 |
| TC12 | heldout | cockpit | kosong | UNKNOWN | INSUFFICIENT_DATA | C2.3.5 | C2.3.5 |
| TC13 | dev | minimum mass | tanpa nominal tyre mass | UNKNOWN | INSUFFICIENT_DATA | C4.1 | C4.1 |
| TC14 | heldout | minimum mass | tanpa konteks heat hazard | UNKNOWN | INSUFFICIENT_DATA | C4.1 | C4.1 |
| TC15 | dev | distribution | sesi R | UNKNOWN | NOT_APPLICABLE | C4.2 | C4.2 |
| TC16 | dev | minimum mass | heat sesi+competition, 800 kg | FALSE | VIOLATED | C4.1 | C4.1 |
| TC17 | heldout | minimum mass | competition heat, sesi tidak, 800 kg | TRUE | SATISFIED | C4.1 | C4.1 |
| TC18 | heldout | minimum mass | LTCS + competition heat, 797,5 kg | FALSE | VIOLATED | C4.1 | C4.1 |

Komposisi: TRUE 6, FALSE 7, UNKNOWN 5. Split deterministik: `HELDOUT = {TC03, TC07, TC12, TC14, TC17, TC18}`.

### 9.2 10 query retrieval

| Case | Query | Gold article | Hasil (top-5) | Hit |
|---|---|---|---|---|
| RT01 | maximum wheelbase 3400 mm distance between planes XF and XR | C2.3.3 | C2.3.3 ✓, C2.3.4, C2.3.5, C3.18.10, C12.6.1 | 1 |
| RT02 | minimum mass 726 kg qualifying 724 kg other sessions nominal tyre mass | C4.1 | C4.1 ✓, C4.7, C4.2, C1, C4.5.2 | 1 |
| RT03 | front axle mass 0.44 rear axle mass 0.54 mass distribution | C4.2 | **C10.1**, C9.5.2, C10.2.2, C13.7.2, C5.5.6 | **0** |
| RT04 | 950 mm from plane Y=0 tyres wheel rims half width | C2.3.1 | C2.3.1 ✓, C10.6.1, C2.3.4, C13.10, C2.1.2 | 1 |
| RT05 | cockpit position XA XC 1830 mm 2030 mm | C2.3.5 | C2.3.5 ✓, C12.5, C12.6, C2.3.6, C2.3.4 | 1 |
| RT06 | heat hazard mass increase 5 kg TTCS | C4.6 | C4.6 ✓, C4.1, C5.5.2, C4.2, C9.5.2 | 1 |
| RT07 | nominal tyre mass measurement 50 tyres per axle dry weather tyres | C4.7 | C4.7 ✓, C4.2, C1, C4.1, C10.8.2 | 1 |
| RT08 | driver ballast density greater than 7500 kg/m3 | C4.3.2 | C4.3.2 ✓, C4.5.2, C4.5, C4.3, C5.5.8 | 1 |
| RT09 | rear bulkhead position distance XC XPU 360 mm | C2.3.6 | C2.3.6 ✓, C13.6.3, C3.18.2, C12.6.1, C3.18.13 | 1 |
| RT10 | front wheel position plane XF between XA 0 and 150 | C2.3.4 | C2.3.4 ✓, C2.3.3, C2.3.5, C2.1.3, C10.10.1 | 1 |

### 9.3 Hasil agregat (run 17 Nov 2026)

| Metrik | Nilai |
|---|---|
| Decision accuracy | **1,0** (18/18) |
| Per-label P/R/F1 | TRUE 1,0/1,0/1,0; FALSE 1,0/1,0/1,0; UNKNOWN 1,0/1,0/1,0 |
| Confusion | FALSE→FALSE 7; TRUE→TRUE 6; UNKNOWN→UNKNOWN 5 |
| Rule match | 1,0 |
| Article match | 1,0 |
| Citation accuracy | 1,0 |
| Citation verification rate | 1,0 |
| Missing-fact precision/recall | 1,0 / 1,0 |
| Explanation completeness | 1,0 |
| Trace consistency | 1,0 |
| Latency keputusan mean / p95 | 7,43 ms / 120,62 ms |
| Failure rate | 0,0 |
| Development split | 12 kasus, accuracy 1,0 |
| Held-out split | 6 kasus, accuracy 1,0 |
| Retrieval hit / precision@5 / recall@5 / MRR | 0,9 / 0,18 / 0,9 / 0,9 |
| Retrieval latency mean / p95 | 91,57 ms / 351,86 ms |

**Caveat:** dataset kecil, sintetis, label dibuat sendiri, tanpa inter-annotator agreement; bukan bukti akurasi dunia nyata. Semua hasil demo karena rule belum human-approved.

---

## 10. API — permukaan lengkap

| Method | Path | Fungsi |
|---|---|---|
| GET | `/` | Info app, versi, regulasi, provider LLM, status contract |
| GET | `/health` dan `/v1/health` | Status, metadata regulasi, hitungan lifecycle, demo mode, goals, provider, status retriever |
| GET | `/goals` dan `/v1/goals` | Daftar goal kepatuhan + aturan, artikel, halaman, kutipan, requirements |
| GET | `/rules` | Semua rule + lifecycle + source + validation (tanpa filter runnable) |
| POST | `/v1/check` | Periksa satu goal (`goal_id`, `document_issue?`, `facts[]`, `question?`) |
| POST | `/check` | Legacy: `goal` (bukan `goal_id`) |
| POST | `/v1/check/all` dan `/check/all` | Periksa 5 compliance goal dengan fakta yang sama |
| POST | `/v1/search` | Retrieval; default hanya dokumen `regulation` |
| POST | `/retrieve` | Legacy: retrieval termasuk jurnal (`include_methodology=true` paksa) |
| GET | `/v1/retrieval/status` dan `/retrieval/status` | Status indeks (lazy load) |
| POST | `/v1/extract-facts` dan `/extract-facts` | Ekstraksi fakta; deterministik default, LLM jika `use_llm` dan provider aktif |
| GET | `/sample-facts` | 11 fakta contoh |

### Error envelope

| Status | Body |
|---|---|
| 422 | `{status: "INVALID_INPUT", diagnostics: [...], detail: "Input fakta tidak valid."}` |
| 409 | `{status: "CONFLICTING_INPUT", diagnostics: [...], detail: "Fakta yang bertentangan..."}` |
| 503 | Retrieval/embedding error atau LLM provider gagal |
| 502 | Error generik saat ekstraksi fakta |
| 500 | `{status: "ERROR", diagnostics: [{code: "INTERNAL_ERROR"}]}` — tanpa stack trace |

### Contoh request `/v1/check`

```json
{
  "goal_id": "minimum_mass_compliance",
  "document_issue": "21",
  "facts": [
    {"name": "car_mass", "value": 800, "unit": "kg"},
    {"name": "nominal_tyre_mass", "value": 70, "unit": "kg"},
    {"name": "session_type", "value": "Q"},
    {"name": "session_category", "value": "TTCS"},
    {"name": "heat_hazard_declared", "value": false},
    {"name": "competition_heat_hazard_declared", "value": false}
  ]
}
```

Catatan perilaku:
- Goal tak dikenal → HTTP **200** dengan `status: UNSUPPORTED` (bukan 404).
- Issue tidak cocok → 200 `UNSUPPORTED` + `VERSION_MISMATCH`.
- Konflik fakta → **409** (dilempar sebelum inferensi).
- Fakta tidak valid → **422**.

---

## 11. UI Streamlit

| Area | Isi |
|---|---|
| Sidebar | Eyebrow “WORKSPACE / FIA 2026”; info regulasi + issue; radio backend `In-process`/`FastAPI`; input API URL; metrik jumlah rule reviewed, active, goal; tombol **Muat contoh fakta** dan **Kosongkan fakta** |
| Tab 01 Pemeriksaan | Pilih goal; panel kutipan sumber; form fakta dinamis 2 kolom sesuai `requirements(goal)`; textarea ekstraksi + tombol ekstrak; checkbox konfirmasi hasil ekstraksi; tombol periksa; laporan lengkap |
| Tab 02 Cari bukti | Query, slider top_k 1–10, filter artikel, checkbox “Sertakan jurnal metodologi”, daftar hasil expander + skor/chunk |
| Tab 03 Aturan & sumber | Daftar rule runnable, kutipan, kondisi, `applies_if`, validation JSON |
| Tab 04 Tentang | Cakupan 5 ketentuan, status eksternal, penjelasan demo, alur sistem |

Laporan yang dirender: badge status (warna success/error/warning/info), validation warning, explanation markdown, sumber + kutipan, tabel diagnostik, konflik, applicability, conditions, missing facts, citations, rules evaluated, trace teks + JSON, fakta digunakan, limitasi, tombol unduh JSON.

Tema (`theme.css`): background `#090a0c`, sidebar `#0e1013`, border `#22252a`–`#30343a`, aksen `#e8eaed`, tombol primary putih, radius 3 px, tanpa animasi berat, `prefers-reduced-motion`, responsif ≤900 px.

Referensi UI: 21st.dev — Dashboard Sidebar (Arun J Dass), Sidebar (wensity, MIT), Minimal Button (jay sharma, MIT), Input (ReUI, MIT). Komponen React **tidak** diadopsi; hanya pola visual.

---

## 12. Skrip & perintah operasional

| Perintah | Efek |
|---|---|
| `.venv\Scripts\python.exe scripts\extract_documents.py` | Ekstraksi ulang seluruh PDF sumber → processed + manifest |
| `.venv\Scripts\python.exe scripts\build_index.py` | Rebuild indeks retrieval (`force=True`) |
| `.venv\Scripts\python.exe scripts\run_evaluation.py` | Decision + retrieval suite → JSON + Markdown |
| `.venv\Scripts\python.exe scripts\validate_rules.py` | Cek kutipan rule → log; exit 1 jika gagal |
| `.venv\Scripts\python.exe scripts\split_dataset.py` | Regenerasi split dev/held-out |
| `.venv\Scripts\python.exe scripts\migrate_rules_v2.py` | One-off migrasi status rule (jangan dijalankan tanpa alasan) |
| `.venv\Scripts\python.exe scripts\add_external_status.py` | One-off tambah expected_external_status |
| `.venv\Scripts\python.exe -m pytest` | 66 test |
| `.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000` | API |
| `.venv\Scripts\python.exe -m streamlit run frontend\streamlit_app.py` | UI di 8501 |

Catatan: Streamlit perlu restart setelah perubahan kode modul. Qdrant local memakai file lock → jangan dua proses lokal bersamaan; gunakan `QDRANT_URL` untuk mode server.

---

## 13. Test suite (66 test)

| File | Jumlah/isi | Yang dibuktikan |
|---|---|---|
| `test_backward_chaining.py` | 8 | Batas 3400/3400,5; missing ≠ FALSE; subgoal minimum mass; heat hazard 5 kg/2 kg; propagasi missing `nominal_tyre_mass`; NOT_APPLICABLE sesi R; cycle → UNKNOWN; konflik rule → FALSE + flag |
| `test_document_processing.py` | 7 | Manifest 4 dokumen & SHA-256; Section C 254 hlm tanpa OCR; output JSON/MD/JSONL; PDF loader; chunk >500 dengan metadata; TOC tidak diindeks; jurnal terindeks |
| `test_end_to_end.py` | 31 (18 parametrized + 13) | Semua kasus dataset via API; health; goals; rules; unsupported goal; version mismatch; konflik 409; invalid 422 (3 kasus); check-all 5 goal; ekstraksi deterministik; search exclude/include journal; retrieval C2.3.3; legacy endpoint |
| `test_retrieval.py` | 7 | Query wheelbase; metadata & skor positif; filter artikel; query kosong; exclude journal; NumPy cosine; Qdrant local + filter tipe |
| `test_rule_engine.py` | 8 | Konversi unit; TRUE/FALSE; missing + expected unit; mismatch→UNKNOWN; `in`/boolean equality; ekspresi aritmetika; tanpa pembulatan; NOT_APPLICABLE |
| `test_rule_sources.py` | 4 | Semua kutipan ada di halaman; semua reviewed & tidak approved; active tanpa approval ditolak; mode strict tanpa rule runnable |

Status cache: `lastfailed` masih menyimpan 3 nama test lama (`test_rules_endpoint_exposes_validation`, `test_unknown_goal_returns_404`, `test_conflicting_facts_return_400`) yang sudah tidak ada di kode saat ini. `nodeids` menyimpan 70 id, 4 di antaranya lama. Test aktual = 66.

---

## 14. Konfigurasi & deployment

### 14.1 Environment variable (`app/config.py` → `load_settings`)

| Variabel | Default | Fungsi |
|---|---|---|
| `LLM_PROVIDER` | `none` | `none` / `api` / `ollama` |
| `LLM_API_BASE_URL` | `https://api.openai.com/v1` | Base URL OpenAI-compatible |
| `LLM_API_KEY` | kosong | Kunci API (hanya `.env`) |
| `LLM_API_MODEL` | `gpt-4o-mini` | Model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Server Ollama |
| `OLLAMA_MODEL` | `llama3.1` | Model Ollama |
| `ALLOW_REVIEWED_RULES` | `true` | Demo mode untuk rule `reviewed` |
| `EMBEDDING_BACKEND` | `auto` | `auto` / `sentence_transformers` / `tfidf` |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Model embedding |
| `VECTOR_STORE` | `qdrant` | Dibaca, tetapi alur retriever memilih berdasarkan backend |
| `QDRANT_URL` | kosong | Jika diisi → Qdrant server, bukan local |
| `CHUNK_SIZE` | `1200` | Ukuran chunk |
| `TOP_K` | `5` | Default retrieval |
| `API_HOST` | `127.0.0.1` | Host uvicorn |
| `API_PORT` | `8000` | Port |
| `LOG_LEVEL` | `INFO` | Level log |

Cache diisolasi ke workspace: `HF_HOME`, `HUGGINGFACE_HUB_CACHE`, `TRANSFORMERS_CACHE`, `SENTENCE_TRANSFORMERS_HOME`, `TORCH_HOME` → `storage/model_cache/...`.

### 14.2 Docker

| Service | Image/build | Port | Env penting | Volume | Depends |
|---|---|---|---|---|---|
| `qdrant` | `qdrant/qdrant:latest` | 6333 | — | `qdrant_data` | — |
| `api` | build `.` | 8000 | `QDRANT_URL`, `EMBEDDING_BACKEND=auto`, `LLM_PROVIDER=none`, `ALLOW_REVIEWED_RULES=true` | `./storage`, `./knowledge_base`, `./datasets` | qdrant |
| `ui` | build `.` | 8501 | `UI_BACKEND=api`, `API_URL=http://api:8000`, `LLM_PROVIDER=none` | sama | api |

Dockerfile: `python:3.12-slim`, `PYTHONPATH=/app`, `HF_HOME=/app/storage/model_cache`, install build-essential + requirements, expose 8000/8501, CMD uvicorn.

**Belum diverifikasi:** Docker/compose belum diuji; tidak ada CI.

---

## 15. Dokumen riset — ringkasan isi

| Dokumen | Poin inti |
|---|---|
| `architecture.md` | Peta komponen & tanggung jawab; alur check; semantik 3-nilai; lifecycle; satuan; RAG; batas LLM; storage; API; keamanan; 10 limitasi arsitektur |
| `document_analysis.md` | 4 dokumen berhasil dibaca tanpa OCR; Section C punya 18 artikel + 6 lampiran; kandidat aturan dinilai determinisme tinggi/sedang/rendah; C2.3 & C4 dipilih; dependensi silang dicatat; rekomendasi 5 aturan |
| `rule_selection.md` | Rule card lengkap 5 ketentuan: persyaratan, fakta, TRUE/FALSE/UNKNOWN, alasan, dependensi; kandidat yang sengaja belum diaktifkan (C2.3.4, C2.3.6, C4.5.2, C4.3.x, C3, C5, C12/13) |
| `rule_validation_log.md` | 13/13 quote check PASS; semua `reviewed`, `human_approved=False`; reviewer `internal_agent_check`; test case ids; kolom tanda tangan kosong |
| `evaluation_plan.md` | Metrik keputusan & retrieval; rencana A (LLM-only), B (RAG+LLM), C (RAG+LLM+BC); syarat perbandingan adil; ancaman validitas |
| `evaluation_results.md` | Hasil 18/18, split dev/held-out, per-case, confusion, retrieval 10 query, limitasi |
| `rencana_pengembangan_proyek.md` | Rencana 6 tahap menuju alur wheelbase 2025 vs 2026: kunci sumber, rule 2025, `/v1/compare`, `/v1/ask`, UI, evaluasi; batas rilis pertama |
| `pembanding_simulator_regulasi.md` | Riset pembanding (Your Tech Director, Interactive F1, Ignara, TechReg Analyst, Rules Delta, Formula Rules RAG, F1 Garage, QuickSim, FSUK, paper); matriks bukti; revisi klaim novelty; skenario 3399–3601 mm |
| `transkrip_percakapan_ai_pakar.md` | 21 giliran percakapan: perbaikan UI, koreksi arah produk, judul vs implementasi, wawancara ahli, ide simulator regulasi, pencarian prior art, keputusan fokus wheelbase, permintaan breakdown |

### 15.1 Transkrip 21 giliran — kronologi ringkas

| # | Topik | Hasil |
|---|---|---|
| 1 | Perbaiki UI agar terasa produk, nuansa Command Code, tombol berfungsi | UI dark workbench, perbaikan state fakta & hasil pencarian, 20 test terarah lulus |
| 2 | Tab navigasi berhimpitan | CSS tab diperbaiki |
| 3 | Apakah proyek masih worth it vs judul dosen? | Worth, tetapi arah bergeser: sekarang compliance checker, judul menjanjikan asisten RAG |
| 4 | Tidak ada ahli untuk diwawancara; cari “teknologi yang belum ada” | Jurnal bisa jadi basis pengetahuan, tetapi bukan pengganti wawancara; pembanding AI regulasi F1 sudah ada |
| 5 | Stuck karena kode sudah ada pembandingnya | Ide **Regulation Impact Explorer** (bandingkan dua versi + input pengguna) |
| 6 | Unduh dokumen pembanding | 4 PDF FIA diunduh ke `folder_dokumen`: 2025 Issue 3, 2026 Issue 16/19/20 |
| 7 | Target pengguna | Penggemar F1, mahasiswa, klub — bukan tim/FIA |
| 8 | Cari pembanding | Banyak komponen ide sudah ada; kombinasi belum terkonfirmasi |
| 9 | Lakukan riset lanjutan | RC4PC (analisis dampak perubahan regulasi) sudah ada; 2025 3.4.2 = 3600 mm vs 2026 C2.3.3 = 3400 mm |
| 10 | Buka simulator & cek relevansi judul | Ignara berhasil dibuka; panel simulasi tidak menunjukkan input wheelbase; judul perlu dipersempit atau sistem dua fungsi |
| 11 | Dosen: judul tetap, isi bebas | Arah: AI pendamping belajar teknik F1 |
| 12 | Apa lagi yang harus dilakukan | Kunci masalah, siapkan sumber teknik, satu alur demo, pertanyaan uji |
| 13 | Ringkas produk | Tanya jawab bersumber + coba skenario + bandingkan versi |
| 14 | Modul tugas | Modul membolehkan jurnal/pedoman; novelty boleh pada domain/fitur/pengguna/penyajian |
| 15 | Apakah selaras modul? | Inti selaras; gap: novelty, laporan, jawaban RAG |
| 16 | Selaraskan novelty sekarang | Pembeda: tanya bersumber + banding dua versi + coba spesifikasi + alasan |
| 17 | Tanggapan sistem & pembeda | Fondasi bagus, produk belum sesuai pengalaman belajar; pembeda kandidat, belum terbukti |
| 18 | Cari pembeda lebih luas | Formula Rules RAG sudah punya compare antar tahun; pembeda tersisa: input spesifikasi → dua putusan → perubahan minimum |
| 19 | Rekomendasi | Fokus wheelbase 2025–2026 dulu; jangan perluas cakupan |
| 20 | Breakdown lengkap | Rencana 6 tahap ditulis ke `rencana_pengembangan_proyek.md` |
| 21 | Buat transkrip | `transkrip_percakapan_ai_pakar.md` |

### 15.2 Kesepakatan yang sudah terbentuk

- Judul dosen tetap; isi sistem boleh dirancang berbeda tetapi relevan.
- Target: pembelajar F1 (penggemar/mahasiswa), bukan alat resmi.
- Mesin pakar (fakta, IF–THEN, backward chaining, trace, uji) adalah inti yang dipertahankan.
- RAG untuk bukti & penjelasan; rule engine untuk verdict.
- Rilis pertama: **wheelbase 2025 Issue 3 vs 2026 Issue 21**, contoh 3500 mm.
- Klaim novelty: penerapan/alur pembelajaran, bukan algoritma baru atau “pertama di dunia”.
- Tidak boleh mengarang reviewer atau menandai `human_approved` tanpa review nyata.

---

## 16. Prior art & framing novelty (dari riset yang ada)

| Pembanding | Kontribusi | Implikasi |
|---|---|---|
| **PercepLog-0** (EMNLP 2026 Findings) | LLM-augmented backward chaining untuk legal reasoning | BC+LLM bukan hal baru |
| **ARCCS** (arXiv 2610.01345) | Regulatory compliance checking, evidence-grounded, agentic | Compliance + bukti sudah ada |
| **LegalGraphRAG** (ACL 2026) | GraphRAG multi-agent + auditor verifikasi evidence | Verifikasi evidence sudah ada |
| **Formula Rules RAG** (GitHub) | RAG F1 2024–2026 + tool perbandingan pasal antar tahun | RAG + compare antar tahun sudah ada |
| **TechReg Analyst** (GitHub) | Q&A RAG regulasi F1 2026 dengan sitasi | Q&A bersumber sudah ada |
| **Your Tech Director** (F1 resmi) | AI menjelaskan regulasi 2026 untuk penggemar | Target penggemar sudah dilayani |
| **Interactive F1** (GitHub) | Mobil 3D, pemilih aturan 2022/2026, panel komponen & sumber | Pembelajaran interaktif sudah ada |
| **Ignara F1 Analytics** | Regulation Changes + simulator performa | Perbandingan regulasi & simulasi sudah ada |
| **QuickSim** | 178 pemeriksaan aturan FSAE/Formula Student 2027 | Rule checking motorsport sudah ada |
| **FSUK 2027 EV Design Study** | Dimensi JSON → cek numerik → laporan | Alur desain → cek numerik sudah ada |
| **RC4PC** (Inf. & Software Technology 2026) | LLM + algoritma analisis dampak perubahan requirement | Analisis dampak regulasi sudah ada |
| **F1-2026-Regulations-RAG** | RAG regulasi F1 2026 tanpa BC/verdict | RAG F1 ada, verdict tidak |

**Kandidat pembeda yang masih layak diuji (belum terimplementasi):**

> Satu alur belajar: pengguna memasukkan spesifikasi → sistem mengevaluasi terhadap **dua issue FIA yang disebut eksplisit** → menampilkan putusan, pasal, halaman, kondisi pengukuran, jejak aturan, dan **perubahan minimum** agar memenuhi batas issue tujuan.

Kalimat aman:
> “Berdasarkan pembanding publik yang diperiksa sampai 19 November 2026, kombinasi alur tersebut belum terdokumentasi pada satu produk yang sama.”

Yang **bukan** klaim: algoritma baru, “pertama di dunia”, pengganti FIA delegate, full Section C.

---

## 17. Gap, inkonsistensi, dan risiko (temuan pemetaan)

### 17.1 Gap yang diakui dokumen proyek

1. Baru 5 ketentuan; bukan seluruh Section C.
2. Section A tidak dipakai sebagai rule source (hanya korpus retrieval).
3. Tidak membaca CAD, gambar, Reference Volumes, tabel kompleks.
4. `Nominal Tyre Mass` harus diberikan pengguna.
5. LLM nonaktif; ekstraksi LLM belum diuji; A/B/C belum dijalankan.
6. Tidak ada autentikasi API.
7. Belum ada validasi ahli F1 / reviewer manusia.
8. Evidence span offset ada field tetapi belum diisi.
9. Docker/CI belum diverifikasi.
10. Satu retrieval miss: C4.2 tertukar C10.1.
11. Human evaluation penjelasan belum ada; label belum independen.
12. Performa skala besar belum diukur.

### 17.2 Temuan tambahan dari pemetaan ini

| # | Temuan | Dampak |
|---|---|---|
| 1 | **Bukan git repository** | Tidak ada riwayat/rollback; `.gitignore` tidak berlaku |
| 2 | **`.env` tidak ada** | Semua default; LLM pasti `none`; konfigurasi tidak eksplisit |
| 3 | **Python venv 3.14.10 vs Docker 3.12** | Perbedaan versi runtime; Docker belum diuji |
| 4 | **Ruleset 1.0.0 vs paket 1.1.0** | Versi tidak seragam |
| 5 | **Tidak ada `/v1/ask` dan `/v1/compare`** | Gap utama terhadap judul dan rencana produk |
| 6 | **Tidak ada rule 2025** | PDF 2025 hanya di `folder_dokumen`, belum masuk knowledge_base |
| 7 | **Tidak ada pemilihan ruleset berdasarkan tahun+issue** | `KnowledgeBase` hanya memuat satu file rules.json |
| 8 | **`CheckReport.conflicts` selalu kosong dari service** | Konflik fakta muncul sebagai 409 sebelum inferensi; field konflik tidak terpakai |
| 9 | **Rule LTCS 2 kg tidak memeriksa `heat_hazard_declared=false`** | Perlu verifikasi apakah LTCS dengan heat hazard sesi tetap 2 kg; berpotensi tumpang tindih/gap |
| 10 | **`.pytest_cache/lastfailed` stale** | 3 nama test lama; bukan kegagalan saat ini |
| 11 | **`evaluation_results.json` menyimpan path absolut Windows** | Tidak portabel |
| 12 | **PDF duplikat byte-identik** di `folder_dokumen` dan `knowledge_base` | 12,3 MB duplikasi; risiko dua sumber kebenaran |
| 13 | **TF-IDF `max_features=4096`** didominasi Section C | Istilah jurnal bisa keluar vocabulary |
| 14 | **Tabel/gambar/warna amendment hilang** | Batas interpretasi visual |
| 15 | **`explanation_completeness` mencari string “Kutipan regulasi”** yang tidak pernah dipancarkan (yang dipakai “Sitasi sumber”) | Satu sub-check selalu false, tetapi skor total tetap 1,0 karena 4/5 check lain lolos |
| 16 | **Belum ada provenance LLM** (prompt version, temperature log) | Belum relevan karena LLM nonaktif |
| 17 | **`storage/` 95,5 MB** termasuk bobot model 90,9 MB | Repo/portabilitas berat jika tidak di-ignore |
| 18 | **Tidak ada CI/lint/type-check** | Kualitas bergantung pada pytest manual |
| 19 | **Tidak ada batas ukuran upload/endpoint file** | Belum ada fitur upload, jadi belum risiko aktif |
| 20 | **CORS `allow_origins=["*"]`** | Wajar untuk prototipe lokal, bukan produksi |

---

## 18. Brief siap-tempel untuk ChatGPT (brainstorming)

### 18.1 Konteks yang harus dipegang

- Ini tugas mata kuliah **sistem pakar**, bukan produk komersial.
- Judul dosen: *Development of an Evidence-Based Motorsport Engineering Expert AI Using Retrieval-Augmented Generation*.
- Yang sudah ada: rule engine BC deterministik, 13 rule, 5 goal, RAG 1.184 chunk, API, UI, 66 test, evaluasi 18/18 pada data sendiri.
- Yang belum ada: rule 2025, perbandingan lintas issue, perubahan minimum, jawaban generatif RAG, literatur teknik motorsport, validasi manusia.
- Semua rule `reviewed`, demo-only.
- Target pengguna: penggemar/mahasiswa.
- Klaim novelty harus jujur dan terbatas.

### 18.2 Pertanyaan brainstorming

**A. Positioning & novelty**
1. Apakah pembeda “input spesifikasi → dua issue → jejak aturan → perubahan minimum” cukup kuat dan cukup jelas untuk tugas sistem pakar?
2. Bagaimana merumuskannya agar tidak overclaim, tetapi tetap terasa “teknologi yang belum ada” di mata dosen?
3. Apakah perlu menambah pembeda lain (misalnya penjelasan asumsi pengukuran, atau perbandingan kondisi ukur antar issue)?

**B. Arsitektur produk**
4. Bagaimana desain `ruleset registry` yang bersih untuk `(year, issue, section)` tanpa merusak API sekarang?
5. Bentuk kontrak `/v1/compare` dan `/v1/ask` yang minimal tetapi lengkap?
6. Apakah `minimum change` sebaiknya dihitung di service baru, di rule engine, atau di lapisan terpisah?
7. Bagaimana menangani perbedaan **kondisi pengukuran** 2025 (Legality Ride Height) vs 2026 (Legality Setup) secara jujur di UI dan API?

**C. RAG & LLM**
8. Bagaimana membuat `/v1/ask` yang benar-benar “evidence-based” tanpa membiarkan LLM mengubah verdict?
9. Literatur teknik motorsport seperti apa yang realistis dikumpulkan dan dievaluasi dalam waktu terbatas?
10. Bagaimana mengukur kualitas jawaban RAG (faithfulness, citation precision) dengan sumber daya terbatas?
11. Apakah perlu menjalankan A/B/C sekarang, atau cukup baseline RAG-only vs sistem gabungan?

**D. Evaluasi & validasi**
12. Berapa ukuran dataset minimum yang bisa dipertanggungjawabkan untuk demo wheelbase lintas issue?
13. Bagaimana mengganti “validasi ahli” yang tidak tersedia tanpa mengarang reviewer?
14. Metrik apa yang paling meyakinkan dosen: akurasi verdict, citation validity, trace consistency, atau pemahaman pengguna?

**E. Scope & risiko**
15. Fitur mana yang harus ditolak agar proyek selesai (scope creep)?
16. Risiko akademik terbesar apa, dan mitigasinya?
17. Jika dosen tetap menuntut “belum pernah ada”, bagaimana menjawab tanpa berbohong?

### 18.3 Batasan yang tidak boleh dilanggar

- Jangan menambah puluhan aturan sebelum alur pertama terbukti.
- Jangan mengarang reviewer, tanda tangan, atau `human_approved`.
- Jangan mengklaim “pertama di dunia”.
- Jangan mengganti backward chaining dengan LLM-only.
- Jangan menghapus bagian limitasi dari laporan.
- Jangan membiarkan LLM menetapkan nilai batas atau verdict.
- Jangan mencampur issue regulasi tanpa penanda versi.

### 18.4 Arah yang paling masuk akal (dari dokumen proyek)

1. Kunci skenario wheelbase 2025 Issue 3 (≤3600 mm) vs 2026 Issue 21 (≤3400 mm).
2. Masukkan PDF 2025 ke knowledge base + satu rule 2025.
3. Buat registry ruleset per `(tahun, issue)`.
4. Tambah `/v1/compare` + hitung perubahan minimum.
5. Tambah literatur teknik + `/v1/ask`.
6. Satukan alur di UI: Tanya → Isi contoh → Bandingkan → Baca alasan & sumber.
7. Uji batas 3399/3400/3401/3500/3600/3601, 3,5 m, kosong, satuan salah, versi tidak ada.
8. Evaluasi baseline RAG vs sistem gabungan.

---

## 19. Glosarium

| Istilah | Arti |
|---|---|
| **Backward chaining** | Inferensi goal-driven: mulai dari goal, cari rule yang membuktikannya, lalu buktikan subgoal/fakta |
| **Forward chaining** | Inferensi data-driven: mulai dari fakta, terapkan rule, tambah fakta baru |
| **Three-valued logic** | TRUE/FALSE/UNKNOWN; UNKNOWN tidak pernah dianggap FALSE |
| **Evidence gate** | Verdict hanya keluar jika kutipan rule terverifikasi di halaman sumber |
| **Rule lifecycle** | `draft → reviewed → active → deprecated`; hanya `active` otoritatif |
| **Demo mode** | `ALLOW_REVIEWED_RULES=true`; rule reviewed boleh jalan dengan warning |
| **Subgoal** | Goal turunan yang nilainya dipakai rule lain (mis. `minimum_mass`) |
| **Nominal Tyre Mass** | Massa ban nominal dari penyedia ban; bukan angka tetap di regulasi |
| **TTCS/LTCS** | Kategori sesi yang dipakai aturan Heat Hazard |
| **Legality Setup** | Kondisi pengukuran resmi di C10.1 (2026) |
| **Legality Ride Height** | Kondisi pengukuran pada regulasi 2025 |
| **RAG** | Retrieval-Augmented Generation: ambil bukti lalu susun jawaban |
| **Chunk** | Potongan teks dengan metadata artikel/halaman |
| **Held-out** | Kasus uji yang tidak dipakai untuk tuning |
| **MRR** | Mean Reciprocal Rank |
| **Precision@k / Recall@k** | Proporsi hasil relevan di top-k / proporsi gold yang ditemukan |
| **EG-3VBC** | Usulan nama novelty: Evidence-Gated Three-Valued Backward Chaining |

---

## 20. Perintah cepat

```powershell
Set-Location "C:\Users\HAR\Documents\SEMESTER 5\SENIN\AI\Project\AI-Pakar"

# Test
.venv\Scripts\python.exe -m pytest

# Validasi kutipan aturan
.venv\Scripts\python.exe scripts\validate_rules.py

# Evaluasi lengkap
.venv\Scripts\python.exe scripts\run_evaluation.py

# API
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000

# UI
.venv\Scripts\python.exe -m streamlit run frontend\streamlit_app.py

# Rebuild indeks
.venv\Scripts\python.exe scripts\build_index.py

# Ekstraksi ulang dokumen
.venv\Scripts\python.exe scripts\extract_documents.py
```

Endpoint cepat:

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/v1/goals
curl -X POST http://127.0.0.1:8000/v1/check -H "Content-Type: application/json" -d "{\"goal_id\":\"wheelbase_compliance\",\"facts\":[{\"name\":\"wheelbase\",\"value\":3400,\"unit\":\"mm\"}]}"
```

---

## 21. Ringkasan satu paragraf

Workspace ini berisi prototipe sistem pakar hibrida untuk memeriksa **5 ketentuan teknis FIA 2026 Section C Issue 21** (C2.3.1, C2.3.3, C2.3.5, C4.1, C4.2) menggunakan **13 rule JSON**, **backward chaining deterministik tiga nilai**, **RAG 1.184 chunk** (MiniLM 384d + Qdrant, fallback TF-IDF), verifikasi sitasi, FastAPI, Streamlit bertema gelap, 66 test, dan evaluasi 18/18 pada dataset sintetis sendiri. Semua aturan masih `reviewed`/demo dan belum disetujui manusia. Dokumen dan percakapan menunjukkan arah produk telah bergeser dari “pemeriksa kepatuhan” menuju “**AI pendamping belajar teknik F1**” dengan alur yang diusulkan: tanya jawab bersumber → coba spesifikasi → bandingkan dua issue → lihat jejak dan perubahan minimum. Bagian yang belum ada: rule 2025, registry ruleset per issue, endpoint compare/ask, literatur teknik motorsport, jawaban generatif RAG, dan validasi ahli. Klaim novelty yang paling jujur adalah **penerapan dan alur pembelajaran**, bukan algoritma baru atau “teknologi pertama di dunia”.
