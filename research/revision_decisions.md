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
