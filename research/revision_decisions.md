# Revision Decisions — MEX-AI

**Dibuat:** 21 November 2026
**Status:** catatan keputusan Phase 0. Hanya berisi hasil yang benar-benar diverifikasi; klaim yang belum diuji ditandai sebagai blocker.
**Sumber arah:** `revisi/pemetaan_public_revisi.md` Bagian 22–34. Bagian 0–21 tetap menjadi snapshot historis dan tidak diubah.

## 1. Precedence dokumen

1. `revisi/pemetaan_public_revisi.md` Bagian 22–34 mengesampingkan rencana lama yang bertentangan (termasuk prioritas wheelbase 2025–2026 di §15.2 dan §18.4).
2. `project_context.md` tetap berlaku untuk batasan integritas, lifecycle rule, pemisahan LLM/inferensi, dan status demo.
3. Dokumen ini mencatat keputusan implementasi aktual dan penyimpangan yang disengaja dari addendum.

## 2. Baseline terverifikasi (21 November 2026)

Perintah yang benar-benar dijalankan dan hasilnya:

| Perintah | Hasil |
|---|---|
| `.venv\Scripts\python.exe -m pytest -q` | 66 test, exit code 0 (setelah dan sebelum perubahan Phase 0) |
| `.venv\Scripts\python.exe scripts\validate_rules.py` | 13/13 kutipan PASS, exit code 0 |
| `.venv\Scripts\python.exe scripts\run_evaluation.py` | decision accuracy 1.0 (18/18), trace consistency 1.0, citation verification 1.0; retrieval hit rate 0.9, MRR 0.9, precision@5 0.18 |

Artefak baseline diarsipkan di `datasets/evaluation/baseline_2026-11-21/` (`evaluation_results.json`, `evaluation_results.md`, `run_log.txt`). Hasil ini tetap angka snapshot dataset sintetis sendiri, bukan bukti akurasi dunia nyata.

Runtime lokal terverifikasi: Python **3.14.10** (venv). Docker CLI tersedia (29.8.2) tetapi **daemon tidak berjalan**, sehingga image `python:3.12-slim` belum dapat dibangun/diuji. Keputusan versi Python final ditunda sampai dependency provider data diuji (Phase 1); ini bukan penyamaan versi yang diklaim sudah terbukti.

## 2.1 Phase 1 — keputusan provider data (21 November 2026)

Hasil pemeriksaan aktual:

| Kandidat | Hasil verifikasi | Keputusan |
|---|---|---|
| OpenF1 | Dokumentasi publik menyatakan data historis 2023+ gratis tanpa autentikasi (3 req/s, 30 req/min). Namun `api.openf1.org` **tidak dapat dihubungi** dari jaringan ini, baik port 80 maupun 443 (connection timeout), dan fetch proxy juga timeout. | **Tidak dipakai** |
| FastF1 + F1 livetiming | FastF1 3.9.2 (MIT, mendukung Python 3.14) berhasil resolve sesi dan daftar driver, tetapi seluruh stream `livetiming.formula1.com` mengembalikan **401**. Rilis FastF1 mencatat Formula 1 mewajibkan autentikasi akun sejak **Oktober 2026**; mirror resmi FastF1 mengembalikan 404. | **Ditunda** sampai kredensial F1TV tersedia |
| TracingInsights (GitHub) | Repositori publik data telemetry F1, lisensi **Apache-2.0**, README menyatakan bebas dipakai untuk penelitian/akademik tanpa API key. Tersedia telemetry per lap (speed, throttle, brake, gear, RPM, DRS, distance, acceleration). | **DIPILIH untuk MVP** |

Fixture nyata yang diunduh ke workspace:

- Sesi: **2025 Abu Dhabi Grand Prix — Qualifying**.
- Lap: **VER lap 14** (Q3, SOFT, 82.295 s) dan **NOR lap 16** (Q3, SOFT, 82.408 s).
- Lokasi: `datasets/telemetry/raw/tracinginsights/2025-abu-dhabi-qualifying/`.
- Manifest + hash: `datasets/telemetry/manifest.json`.

Pemeriksaan kualitas yang benar-benar dijalankan:

- 617 sampel (VER) dan 623 sampel (NOR); median interval sampel 0,136 s; gap maksimum 1,076 s.
- Waktu dan jarak monoton naik; tidak ada nilai hilang pada speed/throttle/brake.
- **`brake` pada dataset ini adalah 0/1, bukan 0/100**; ambang onset harus `> 0.5`.
- Terdeteksi 6 brake onset per lap; contoh perbedaan: T1 VER 312,05 m vs NOR 303,09 m; T5 VER 4.239,81 m vs NOR 4.224,49 m. Ini observasi, bukan klaim kausal.
- `speed_delta` (NOR − VER) pada grid 1 m: rata-rata −0,36 km/h, minimum −23,49, maksimum +14,22.

Konsekuensi dependency yang dicatat jujur:

- `fastf1==3.9.2` terpasang dan memaksa downgrade **pandas 3.1.1 → 2.3.3**. Regression 66 test tetap lulus setelah perubahan ini.
- `matplotlib==3.11.2` ikut terpasang dan akan dipakai untuk plot Phase 3.
- FastF1 tidak dipakai oleh jalur fixture saat ini; ia dipertahankan sebagai adapter opsional jika kredensial F1TV tersedia. Ini dicatat di `requirements.txt`.

## 2.2 Phase 2 — korpus, feature spec, prior art (21 November 2026)

Dibuat:

| File | Isi |
|---|---|
| `knowledge_base/source_documents/telemetry/data_dictionary.md` | Definisi channel, satuan, encoding brake 0/1, kualitas sampel, caveat provenance |
| `knowledge_base/source_documents/telemetry/engineering_fundamentals.md` | Catatan fisika/teknik original: kinematika, pengereman, throttle, grip/load transfer, drag, batas interpretasi |
| `knowledge_base/metadata/telemetry_sources.json` | Manifest hak/akses sumber |
| `research/engineering_sources.md` | Daftar sumber yang diverifikasi, sumber yang tidak diperoleh, aturan penggunaan |
| `research/telemetry_feature_spec.md` | Spesifikasi formal fitur, threshold, sign convention, gap policy, uncertainty, rencana test |
| `research/source_rule_mapping.md` | Pemetaan TEL-R01..R08 ke bukti dan batasan |
| `research/novelty_validation.md` | Matriks prior art dengan tanggal pencarian dan status verifikasi |

Temuan prior art yang membatasi klaim:

- Farooq et al. (Scientific Reports, 2025, DOI 10.1038/s41598-025-89266-9) sudah memakai **forward + backward chaining pada data telemetry** untuk diagnostik/prognostik IoT. Jadi "BC + telemetry" bukan hal baru.
- Thomas et al. (Frontiers in AI, 2026, DOI 10.3389/frai.2026.1922508) sudah membuat **hybrid RAG + rule-based reasoning** untuk dokumen teknis dengan penalaran simbolik deterministik. Jadi "RAG + rule reasoning" bukan hal baru.
- Produk telemetry viewer dan AI race engineer untuk sim racing sudah ada. Tidak ditemukan produk yang menggabungkan seluruh alur; ini gap kandidat, bukan novelty terbukti.

Pilot retrieval yang benar-benar dijalankan pada 2 dokumen baru (13 chunk):

- Chunking per paragraf: 6 query uji, hanya 2 yang menempatkan section yang benar di ranking pertama. Tabel Markdown rusak menjadi chunk tidak koheren.
- Chunking berbasis heading `##`: 5 dari 6 query menempatkan section yang benar di ranking pertama. Query tentang unit/encoding `brake` masih mengambil section "Braking" lebih dulu karena definisi brake berada di tabel.
- **Kesimpulan:** ingestion Markdown untuk RAG harus section-aware, dan tabel perlu perlakuan khusus. Ini menjadi pekerjaan Phase 5. Belum ada klaim kualitas retrieval pada korpus baru.

## 2.3 Phase 3 — data adapter, fitur deterministik, plot (21 November 2026)

File baru:

| File | Peran |
|---|---|
| `app/schemas/telemetry.py` | Model provenance, quality, feature, onset, analysis report |
| `app/race_data/loader.py` | Loader fixture + normalisasi brake (0/1 dan 0/100) |
| `app/race_data/validation.py` | Validasi monotonic time/distance, rentang, durasi, channel |
| `app/race_data/alignment.py` | Grid jarak bersama, interpolasi terbatas, channel diskret nearest |
| `app/telemetry/features.py` | max speed, speed delta, brake/throttle onset, rate, segment time, data quality |
| `app/telemetry/service.py` | Orkestrasi analisis dua lap |
| `app/telemetry/plots.py` | Plot speed/throttle/brake vs jarak, gap ditandai |
| `tests/test_telemetry.py` | 18 test baru |

Hasil yang benar-benar dieksekusi:

- `pytest tests/test_telemetry.py` → **18 passed**, exit 0.
- `pytest` penuh → **84 passed**, exit 0 (66 baseline + 18 baru).
- Analisis VER-Q-14 vs NOR-Q-16: 6 brake onset terpasang; delta T1 −8,96 m (dalam uncertainty), T2 +2,55 m, T3 +1,24 m, T4 +0,57 m, T5 **−15,32 m**, T6 **−12,61 m** (di luar uncertainty ±10 m).
- `speed_delta` (B−A): mean −0,344 km/h, min −23,13, max +14,04; 5.031 titik grid valid; coverage 0,99995.
- Artefak: `datasets/telemetry/analysis/ver14_vs_nor16.json` dan `.png`. Plot menandai dua dropout nyata (~3.500 m dan ~5.000 m).

Perubahan threshold yang didokumentasikan:

- Gap interpolasi awal 0,25 s menolak 28% titik grid karena banyak interval normal 0,26–0,33 s. Setelah mengukur distribusi (median 0,136 s; p99 0,323 s; dropout nyata ~1 s), default diubah menjadi **0,5 s**. Interval 0,25–0,5 s tetap diinterpolasi dan ditandai sebagai sampling uncertainty. Ini perubahan berbasis data, bukan pelonggaran diam-diam.
- `brake` dinormalisasi dari 0/1 atau 0/100 ke boolean; onset memakai debounce 2 sampel.
- Semua angka di atas adalah hasil fixture, bukan klaim performa pembalap.

## 2.4 Phase 4 — ruleset analisis, evidence gate, endpoint (21 November 2026)

File baru:

| File | Peran |
|---|---|
| `knowledge_base/rules/telemetry_rules.json` | 8 rule `draft` (TEL-R01..R08) dengan sumber dan kondisi |
| `app/schemas/analysis.py` | Status analisis, gate result, finding, evidence reference, report, request |
| `app/learning/evidence_gate.py` | Data gate dan knowledge gate |
| `app/learning/service.py` | Orkestrasi BC + gate + laporan |
| `tests/test_analysis_rules.py` | 15 test baru |

Perubahan aditif:

- `KnowledgeBase` menerima `include_draft=False` (default). Default perilaku lama tidak berubah; ruleset telemetry dimuat dengan `include_draft=True` khusus mode prototipe.
- Endpoint baru: `GET /v1/races`, `GET /v1/races/{session_id}/laps`, `POST /v1/telemetry/analyze`.
- Handler `RequestValidationError` diperbaiki agar `ctx.error` (ValueError) tidak lagi membuat respons 422 gagal diserialisasi.

Hasil yang benar-benar dieksekusi:

- `pytest tests/test_analysis_rules.py` → **15 passed**, exit 0.
- `pytest` penuh → **99 passed**, exit 0 (66 baseline + 18 telemetry + 15 analysis).
- Analisis nyata: data gate PASS, knowledge gate PASS (6 kutipan ditemukan), 4 finding `OBSERVED` (R01–R04), R05/R06 `NOT_APPLICABLE` tanpa pertanyaan understeer/drag, R07/R08 `INSUFFICIENT_DATA`.
- `engineering_interpretation_status` = `INSUFFICIENT_DATA` karena sumber teknik yang tersedia belum cukup untuk interpretasi tersokong.
- Artefak: `datasets/telemetry/analysis/learning_report.json`.
- Aturan tetap `draft`; tidak ada yang dipromosikan ke `reviewed`/`active`, dan tidak ada klaim FC.

## 2.5 Phase 5 — retrieval ter-scope dan /v1/ask (21 November 2026)

File baru:

| File | Peran |
|---|---|
| `app/rag/corpus.py` | Chunking Markdown berbasis heading section |
| `app/learning/retrieval.py` | Indeks TF-IDF scoped untuk korpus engineering |
| `app/rag/grounded_answer.py` | Jawaban terstruktur, fallback deterministik, validasi sitasi |
| `app/learning/ask_service.py` | Routing pertanyaan dan orkestrasi jawaban |
| `app/schemas/learning.py` | Schema pertanyaan, sitasi, jawaban |
| `tests/test_learning_ask.py` | 13 test baru |

Hasil yang benar-benar dieksekusi:

- `pytest tests/test_learning_ask.py` → **13 passed**, exit 0.
- `pytest` penuh → **112 passed**, exit 0.
- Retrieval section-aware: query "what does throttle percentage mean" → artikel "3. Throttle"; "compare the braking..." memakai query terfokus dan kini mengarah ke "2. Braking" (sebelumnya "5. Provenance caveats").
- `/v1/ask` teori: 200, `generation_status=unavailable`, 3 sitasi terverifikasi (keberadaan string).
- `/v1/ask` telemetry case: 200, 13 observed facts, 6 findings, sitasi "2. Braking" pertama.
- Validasi sitasi menolak ID karangan (`E99`); fake provider test memastikan schema dan jalur generasi bekerja, tetapi **provider LLM nyata tidak diuji**.
- Artefak: `datasets/telemetry/analysis/ask_theory.json`, `ask_telemetry_case.json`.

Blocker yang dinyatakan:

- `LLM_PROVIDER=none`, tidak ada Ollama, tidak ada API key. Karena itu **RAG generatif belum selesai** menurut checklist Bab 33. Jawaban yang keluar adalah deterministik dari fakta + kutipan, bukan generasi LLM.
- Pertanyaan regulasi tidak dicampur ke jalur telemetry; `/v1/ask` mengarahkan ke permukaan Regulation Lab/RAG lama.

## 2.6 Phase 6 — UI tiga modul, evaluasi, acceptance (21 November 2026)

Perubahan:

- `frontend/streamlit_app.py` menambahkan pemilih modul: **Race Analysis**, **Engineering Tutor**, **Regulation Lab**. Kode Regulation Lab lama dipertahankan.
- Race Analysis: pilih dua lap, segmen opsional, jalankan analisis, lihat quality/fakta/temuan/onset/gate/trace, plot speed-throttle-brake, unduh JSON.
- Engineering Tutor: pertanyaan teori atau kontekstual, level beginner/engineering, sitasi, batasan, fallback deterministik.
- Regulation Lab: tab lama tetap utuh; sidebar hanya menampilkan kontrol fakta saat modul ini dipilih.

Verifikasi yang benar-benar dijalankan:

- `pytest` penuh → **112 passed**, exit 0.
- `py_compile frontend/streamlit_app.py` → exit 0.
- Streamlit `AppTest` untuk ketiga modul → tidak ada exception.
- AppTest klik "Analisis lap" → tidak ada exception; 3 tabel hasil.
- AppTest submit pertanyaan teori → tidak ada exception; warning fallback deterministik muncul.
- Dokumen: `research/learning_evaluation.md`, `research/mvp_acceptance.md`; README diperbarui.

Tidak dilakukan (jujur):

- Screenshot UI nyata tidak dibuat; verifikasi memakai AppTest headless.
- Eksperimen A/B/C tidak dijalankan karena provider LLM tidak tersedia.
- Evaluasi pendidikan tidak dijalankan; tidak ada klaim peningkatan belajar.
- Docker/Compose belum diverifikasi.

## 2.7 Pasca-audit: hardening integritas LLM dan retrieval tabel (21 November 2026)

Perubahan:

- `app/rag/grounded_answer.py`: `observed_facts` dan `rule_based_findings` selalu berasal dari server, bukan output LLM. LLM tidak bisa mengubah angka atau mengarang temuan aturan.
- Setiap item `theory` wajib menyertakan penanda sitasi `[E#]` yang valid; jika tidak, jawaban LLM ditolak dan fallback deterministik dipakai.
- Evidence dibungkus `<evidence>...</evidence>` dan system prompt menyatakan evidence adalah data tidak tepercaya; instruksi di dalamnya tidak boleh diikuti.
- `app/rag/corpus.py`: chunk tabel Markdown per baris dengan header diulang, ditandai `subarticle="table_row"`.
- `app/learning/retrieval.py`: policy skor deterministik — baris tabel diredam untuk pertanyaan how/why/should, dikuatkan untuk pertanyaan definisi/unit channel.

Hasil yang benar-benar dieksekusi:

- `pytest` penuh → **117 passed**, exit 0.
- Test baru: fakta `999 km/h` dari fake provider diabaikan; temuan aturan palsu diabaikan; teori tanpa sitasi ditolak; prompt mengisolasi evidence; baris tabel brake mempertahankan header.
- Pilot retrieval 6 query → **6/6 rank-1** (sebelumnya 5/6). Query brake kini mengambil baris tabel `2. Channels`.
- Tidak ada provider LLM nyata yang diuji; status RAG generatif tetap **BLOCKED**.















## 3. Perubahan Phase 0

| File | Perubahan | Alasan | Verifikasi |
|---|---|---|---|
| `.gitignore` | Tambah `.env.*` dan pengecualian `!.env.example` | Cegah variasi env lokal ikut ter-commit | `git status` bersih setelah commit |
| `app/evaluation/evaluator.py` | `explanation_completeness` memakai kriteria struktur (`has_explanation_text`, `has_verdict_status`, `has_rule_reference`, `has_source_reference`, `has_evidence_or_missing_facts`, `has_declared_limitations`) | Addendum §31.3 meminta kriteria struktur eksplisit, bukan pencocokan string | Skor tetap 1.0; 66 test lulus |
| `app/rag/retriever.py` | `describe()` menormalkan `target` absolut di dalam workspace menjadi path relatif POSIX | Temuan §17.2 #11 (path Windows tidak portabel) | `evaluation_results.json` kini berisi `"target": "storage/vector_db/qdrant"` |
| `.pytest_cache/` | Dihapus | Temuan §17.2 #10 (3 id test lama/stale) | Direktori tidak ada lagi |

Catatan koreksi temuan: klaim §17.2 #15 ("`explanation_completeness` mencari string `Kutipan regulasi` yang tidak pernah dipancarkan") **tidak lagi sesuai kode aktual**. Kode sebelum perubahan sudah menyertakan `"Sitasi sumber"` di daftar marker, dan seluruh 18 kasus mendapat skor 1.0. Perubahan ke kriteria struktur dilakukan untuk memenuhi §31.3, bukan karena ada sub-check yang selalu false. Tidak ada angka yang dinaikkan secara artifisial.

## 4. Keputusan yang berbeda dari addendum (dengan alasan)

| Topik | Keputusan | Alasan | Acceptance test |
|---|---|---|---|
| Forward Chaining | **Ditunda** (P1); MVP memakai Backward Chaining untuk goal observasional dan evidence insufficiency | Modul menerima BC; belum ada bukti FC memberi manfaat terukur; menghindari klaim FC palsu | Trace BC baru konsisten; tidak ada rule yang diklaim sebagai FC |
| `/v1/compare` + registry lintas issue | **Ditunda** sampai MVP selesai | Bab 24 menetapkan DEFER; fokus vertical slice telemetry lebih dulu | Checklist MVP Bab 33 |
| CSV upload | **Ditunda** (P1) | Bukan syarat MVP; risiko validasi/keamanan file | Endpoint upload tidak diklaim ada |
| Frontend | Pertahankan satu `frontend/streamlit_app.py`, tambah navigasi bertahap; multipage hanya jika struktur aktual mendukung | Menghindari rewrite total dan import break | Aplikasi Streamlit berjalan, tab lama tetap berfungsi |
| Python target | Belum dikunci; runtime terverifikasi 3.14.10, Docker 3.12 belum diuji | Daemon Docker mati; dependency provider belum diuji | Phase 1 mencatat hasil uji dependency nyata |
| Dependensi baru | Hanya diinstal jika benar-benar diperlukan, ke dalam workspace | Preferensi pengguna: pakai yang sudah terpasang; unduhan di dalam workspace | `pip list`/`requirements.txt` mencatat versi aktual |

## 5. Temuan yang masih terbuka (belum diperbaiki)

1. **Rule LTCS 2 kg** (`FIA26-C4.6-HEAT-INCREASE-LTCS-COMPETITION`) belum diaudit terhadap teks asli untuk kasus `heat_hazard_declared=false` (§17.2 #9). Jangan diputuskan dari ringkasan; audit saat menyentuh ruleset di Phase 4.
2. **Duplikasi PDF byte-identik** di `folder_dokumen/` dan `knowledge_base/source_documents/` dibiarkan. Tidak ada file dihapus tanpa izin.
3. **`CheckReport.conflicts` vs HTTP 409** belum didokumentasikan ulang; perilaku lama dipertahankan.
4. **`evidence_span` offset** masih kosong; verifikasi berbasis keberadaan string, bukan entailment.
5. **TF-IDF vocabulary** masih didominasi Section C.
6. **Docker/Compose** belum diverifikasi karena daemon tidak aktif.
7. **LLM provider** belum diuji; `LLM_PROVIDER=none` valid untuk mode offline, tetapi bukan RAG generatif penuh.
8. **Reviewer manusia** belum ada; tidak ada `human_approved` yang dibuat.

## 6. Blocker yang harus diselesaikan di Phase 1

- Ketersediaan, lisensi, dan cakupan data provider (FastF1/OpenF1) untuk sesi contoh — harus diverifikasi dari dokumentasi resmi.
- Identitas sesi + dua lap nyata yang benar-benar dapat diunduh; jika gagal, fixture sintetis wajib diberi label jelas.
- Kebutuhan API key LLM (atau Ollama) untuk menguji `/v1/ask`; tanpa itu, gate RAG generatif belum boleh dinyatakan selesai.
- Hak akses sumber engineering (buku/paper). Jika tidak ada izin indexing, gunakan catatan faktual bersumber, bukan PDF tidak sah.

## 7. Change-control

- Setiap fase: jalankan `pytest` dan catat hasil nyata; jangan mengubah expected agar lulus.
- Jangan menaikkan status rule atau `human_approved` tanpa review manusia nyata.
- Jangan menambah endpoint yang merusak kontrak legacy.
- Semua unduhan/dependency baru disimpan di dalam workspace ini.
- Laporan penutup fase wajib memuat: file diubah, perintah dijalankan, output nyata, keterbatasan, langkah berikut.
