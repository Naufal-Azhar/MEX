# Rangkuman Proyek — F1 Technical Regulation Expert System

**Tanggal:** 17 November 2026  
**Status:** Prototipe mata kuliah; berjalan; aturan masih `reviewed` (demo), belum `active`.  
**Tujuan dokumen:** bahan brainstorming untuk AI Reasoning lain. Dokumen ini merangkum konteks, arsitektur, hasil, batasan, prior-art, dan pertanyaan terbuka. Jangan menganggap klaim di sini sebagai klaim akademik final.

---

## 1. Konteks

- Proyek dibuat untuk **tugas mata kuliah AI / sistem pakar**, akan dikumpulkan ke dosen sebagai nilai.
- Pembuat proyek adalah **fans F1**, bukan insinyur F1, bukan peneliti regulasi, dan **tidak punya akses ke ahli domain F1**.
- Dosen meminta dua hal:
  1. **“AI-EXPERT di bidangnya”** — validasi dari expert manusia.
  2. **“Teknologi yang belum ada”** — unsur kebaruan.
- Ada ambiguitas yang belum diklarifikasi: “expert di bidangnya” berarti **ahli AI/sistem pakar** atau **ahli F1/regulasi teknis**?
- Dua dokumen acuan di workspace:
  - `PROMPT.md` — brief awal proyek.
  - `project_context.md` — spesifikasi/handover yang lebih ketat, mewajibkan rule lifecycle dan human sign-off (Gate 2).

**Konsekuensi:** semua hasil saat ini harus diperlakukan sebagai **demo/decision-support**, bukan sertifikasi FIA.

---

## 2. Masalah yang diselesaikan

Membangun prototipe **sistem pakar pemeriksaan kepatuhan** untuk subdomain kecil regulasi teknis Formula 1:

- Sumber normatif: `FIA 2026 Formula One Regulations — Section C [Technical]`, **Issue 21, 19 Oktober 2026** (254 halaman).
- Subdomain: **fundamental dimensions dan mass** (C2.3 dan C4).
- Tujuan: menerima fakta teknis, mengambil bukti pasal, menjalankan **Backward Chaining deterministik**, dan menghasilkan keputusan yang bisa dilacak.
- Prinsip: setiap keputusan harus bisa ditelusuri ke fakta, aturan, dan kutipan pasal FIA.

**Bukan tujuan:** memeriksa seluruh mobil F1, menggantikan FIA technical delegate, membaca CAD/gambar, atau mengukur fisik.

---

## 3. Apa yang sudah dibangun

### 3.1 Arsitektur ringkas

```text
PDF FIA
  → document_processing (PyMuPDF, halaman, chunk, SHA-256)
  → knowledge_base (rules.json, facts)
  → RAG (Sentence Transformers + Qdrant; fallback TF-IDF)
  → expert_system (fact validation → backward chaining → three-valued result → trace/explanation)
  → FastAPI (/v1) → Streamlit UI
```

Prinsip pemisahan tugas:

- **RAG** hanya mengambil bukti (teks + artikel + halaman + skor).
- **LLM** hanya boleh mengusulkan fakta (saat ini dinonaktifkan).
- **Backward Chaining** adalah satu-satunya pemutus verdict.
- **Aturan** adalah data JSON; tidak ada eksekusi kode dari LLM.

### 3.2 Modul utama

| Area | File |
|---|---|
| API | `app/api/routes.py`, `app/main.py` |
| Document processing | `app/document_processing/pdf_loader.py`, `text_extractor.py`, `chunker.py` |
| RAG | `app/rag/embeddings.py`, `vector_store.py`, `retriever.py` |
| LLM (disabled) | `app/llm/base.py`, `api_provider.py`, `local_provider.py`, `fact_extractor.py` |
| Expert system | `app/expert_system/knowledge_base.py`, `rule_engine.py`, `backward_chaining.py`, `explanation.py`, `service.py` |
| Schemas | `app/schemas/facts.py`, `fact_specs.py`, `units.py`, `rules.py`, `results.py`, `api.py` |
| Evaluation | `app/evaluation/metrics.py`, `evaluator.py` |
| UI | `frontend/streamlit_app.py` |
| Data | `knowledge_base/`, `datasets/`, `research/` |
| Scripts | `scripts/extract_documents.py`, `build_index.py`, `run_evaluation.py`, `validate_rules.py`, `split_dataset.py` |
| Tests | `tests/` (66 test) |

### 3.3 Rule set

13 rule entry: **5 compliance goal + 8 value subgoal**.

| Rule ID | Artikel | Ketentuan | Halaman |
|---|---|---|---|
| `FIA26-C2.3.1-HALF-WIDTH` | C2.3.1 | Tidak ada bagian non-eksklusi > 950 mm dari plane Y=0 | 10 |
| `FIA26-C2.3.3-WHEELBASE` | C2.3.3 | Wheelbase ≤ 3400 mm | 11 |
| `FIA26-C2.3.5-COCKPIT-POSITION` | C2.3.5 | Jarak XA=0–XC=0 ∈ [1830, 2030] mm | 11 |
| `FIA26-C4.1-MINIMUM-MASS` | C4.1 (+C4.6) | Car Mass ≥ Minimum Mass (726/724 kg + Nominal Tyre Mass + Heat Hazard) | 59–60 |
| `FIA26-C4.2-MASS-DISTRIBUTION` | C4.2 | Front ≥ 0.44 × Minimum Mass; rear ≥ 0.54 × (Q/SQ) | 59 |

Subgoal nilai mencakup:

- `base_minimum_mass` (726/724 kg),
- `heat_hazard_mass_increase` (5/2/0 kg),
- `minimum_mass`,
- `minimum_mass_excluding_heat_hazard`.

Contoh rantai BC nyata:

```text
mass_distribution_compliance
  → minimum_mass_excluding_heat_hazard
      → base_minimum_mass
      → nominal_tyre_mass
```

### 3.4 Status contract

Internal proof: `TRUE`, `FALSE`, `UNKNOWN`.

Eksternal (API/UI):

- `SATISFIED`
- `VIOLATED`
- `INSUFFICIENT_DATA`
- `NOT_APPLICABLE`
- `UNSUPPORTED`
- `ERROR`

Diagnostik:

- `INVALID_INPUT`
- `CONFLICTING_INPUT`
- `SOURCE_MISSING`
- `VERSION_MISMATCH`
- `UNSUPPORTED_GOAL`
- `RULE_NOT_APPROVED`
- `INTERNAL_ERROR`

Aturan: `UNKNOWN` tidak pernah dianggap `FALSE`.

### 3.5 Rule lifecycle

`draft → reviewed → active → deprecated`

- Saat ini: **13/13 `reviewed`**, **0 `active`**, `human_approved: false`.
- `reviewed` hanya berjalan dalam demo mode (`ALLOW_REVIEWED_RULES=true`), dengan warning + diagnostik `RULE_NOT_APPROVED`.
- `active` wajib punya `human_approved`, `reviewer`, `reviewed_at`, verifikasi sumber, dan test case IDs.
- Rule `active` tanpa approval manusia ditolak schema.

### 3.6 Bukti dan validasi sumber

- Manifest menyimpan **SHA-256** dan ukuran setiap file sumber.
- Semua **13/13 kutipan aturan** diverifikasi otomatis ada di halaman yang dirujuk.
- `research/rule_validation_log.md` dibuat; bagian tanda tangan reviewer masih kosong.
- Sitasi yang tidak terverifikasi memicu `SOURCE_MISSING`; verdict `SATISFIED`/`VIOLATED` bisa diturunkan ke `INSUFFICIENT_DATA`.

### 3.7 API

Canonical:

- `GET /health`
- `GET /v1/goals`
- `POST /v1/check`
- `POST /v1/check/all`
- `POST /v1/search`
- `POST /v1/extract-facts`
- `GET /v1/retrieval/status`

Legacy alias: `/goals`, `/check`, `/check/all`, `/retrieve`, `/extract-facts`.

Request `/v1/check`:

```json
{
  "goal_id": "minimum_mass_compliance",
  "document_issue": "21",
  "facts": [
    {"name": "car_mass", "value": 800, "unit": "kg", "origin": "user"}
  ]
}
```

Response memuat: `status`, `internal_status`, `scope`, `missing_facts`, `conflicts`, `diagnostics`, `rules_evaluated`, `citations` (dengan `verified`), `proof_trace`, `explanation`.

Error envelope:

- 422 `INVALID_INPUT`
- 409 `CONFLICTING_INPUT`
- 500 `ERROR`

### 3.8 UI

Streamlit menyediakan:

- pemilihan goal dan form fakta;
- ekstraksi fakta dari teks (parser deterministik; LLM opsional nanti);
- konfirmasi fakta hasil ekstraksi;
- status eksternal, diagnostik, konflik, sitasi, rules evaluated;
- proof trace;
- pencarian bukti RAG;
- unduh hasil JSON;
- peringatan mode demo.

### 3.9 Data dan evaluasi

- 4 dokumen sumber: Section C (254 hlm), Section A (84 hlm), 2 jurnal metodologi.
- **1.184 chunk** dengan metadata artikel/halaman/tipe dokumen.
- Dataset 18 kasus:
  - 6 TRUE, 7 FALSE, 5 UNKNOWN;
  - split **12 development + 6 held-out**.
- Retrieval suite: 10 query.
- 66 test lulus.

---

## 4. Keputusan desain penting

1. **Document-grounded knowledge acquisition**
   - Aturan diambil dari PDF FIA, bukan dari opini LLM.
   - Setiap rule punya kutipan verbatim + halaman.

2. **Deterministic BC, LLM bukan pemutus**
   - LLM hanya boleh mengusulkan fakta.
   - LLM tidak boleh mengubah aturan, nilai, status, atau verdict.

3. **Three-valued logic + external status**
   - Fakta hilang → `INSUFFICIENT_DATA`, bukan pelanggaran.
   - Rule tidak berlaku → `NOT_APPLICABLE`.
   - Goal di luar cakupan → `UNSUPPORTED`.

4. **Evidence gate**
   - Verdict hanya keluar jika sitasi rule terverifikasi.
   - Ini yang diusulkan sebagai salah satu elemen kebaruan.

5. **Dependensi eksternal eksplisit**
   - Nominal Tyre Mass, jenis sesi, kategori sesi, Heat Hazard adalah fakta input.
   - Tidak ada angka default yang dikarang.

6. **Satuan dan presisi**
   - Konversi mm/cm/m dan g/kg/t.
   - Tidak ada pembulatan batas (sesuai C2.5).

7. **Validasi input**
   - Hanya 11 nama fakta yang didukung.
   - Satuan wajib; nilai negatif ditolak; konflik fakta ditolak.

8. **Pemisahan jurnal**
   - Pencarian kepatuhan default hanya `regulation`.
   - Jurnal hanya ikut dengan `include_methodology=true`.

9. **Rule lifecycle**
   - `reviewed` ≠ `active`.
   - Human sign-off adalah gate, bukan formalitas.

---

## 5. Hasil evaluasi saat ini

### Decision suite

- 18/18 keputusan internal dan eksternal benar.
- F1 (VIOLATED) = 1.0.
- Rule match = 1.0.
- Article match = 1.0.
- Citation accuracy = 1.0.
- Citation verification rate = 1.0.
- Missing-fact precision/recall = 1.0 / 1.0.
- Explanation completeness = 1.0.
- Trace consistency = 1.0.
- Latency mean 7.43 ms; p95 120.62 ms; failure rate 0.0.

### Retrieval suite

- 10 query.
- Hit rate 0.9.
- MRR 0.9.
- Precision@5 0.18.
- Satu miss: query C4.2 tertukar dengan C10.1.
- Latency mean 91.57 ms; p95 351.86 ms.

**Caveat:** dataset kecil, sintetis, label dibuat sendiri; bukan bukti akurasi dunia nyata. Semua hasil masih demo karena rule belum human-approved.

---

## 6. Batasan yang disengaja

- Hanya 5 ketentuan; bukan seluruh Section C.
- Section A tidak dipakai sebagai rule source.
- Tidak membaca CAD, gambar, Reference Volumes, atau tabel kompleks.
- Tidak memverifikasi pengukuran fisik atau Legality Setup.
- Nominal Tyre Mass harus diberikan pengguna.
- LLM dinonaktifkan; A/B/C belum dijalankan.
- Tidak ada autentikasi API.
- Tidak ada klaim “pertama di dunia”.
- Tidak ada validasi ahli F1.

---

## 7. Gap yang belum selesai

1. **Validasi manusia / AI expert** — belum ada reviewer.
2. **Validasi domain F1** — tidak ada ahli F1.
3. **LLM stage** — adapter ada, belum diuji; ekstraksi fakta LLM belum diuji.
4. **A/B/C comparison** — belum dijalankan.
5. **OR/disjunction dan negasi umum** — rule schema masih conjunction + alternatif rule.
6. **Evidence span offset** — field ada, belum diisi.
7. **Docker/CI** — Dockerfile/compose ada, belum diuji; CI belum ada.
8. **Tabel/gambar** — belum terstruktur.
9. **Retrieval C4.2 vs C10.1** — masih miss.
10. **Human evaluation penjelasan** — belum ada.
11. **Label independen / inter-annotator agreement** — belum ada.
12. **Performa skala besar** — belum diukur.

---

## 8. Prior-art yang ditemukan (penting untuk novelty)

Pencarian terbatas pada November 2026 menemukan sistem yang sangat dekat:

| Sistem | Kontribusi | Implikasi |
|---|---|---|
| **PercepLog-0** (EMNLP 2026 Findings) | LLM-augmented **backward chaining** untuk legal reasoning | RAG/LLM+BC untuk hukum sudah ada |
| **ARCCS** (arXiv 2610.01345, EMNLP 2026 demo) | Regulatory compliance checking, evidence-grounded, agentic | Compliance + bukti sudah ada |
| **LegalGraphRAG** (ACL 2026, arXiv 2605.28120) | Multi-agent GraphRAG + Auditor verifikasi evidence | Evidence verification sudah ada |
| **F1-2026-Regulations-RAG** (GitHub) | RAG atas regulasi F1 2026 | RAG F1 ada, tetapi tanpa BC/verdict |
| **Internal Regulation Expert System** (IEEE) | RAG untuk regulasi internal | RAG + expert system sudah ada |

**Konsekuensi:** klaim “teknologi ini belum ada” secara umum **tidak aman**. Yang mungkin masih menjadi celah adalah **artefak/arsitektur spesifik untuk FIA Section C**, bukan paradigma baru.

### Kandidat novelty yang lebih defensible

> **Evidence-Gated Three-Valued Backward Chaining (EG-3VBC) untuk regulasi teknis FIA Section C.**

Elemen:

- BC deterministik, bukan LLM reasoning;
- verdict hanya keluar jika kutipan rule terverifikasi;
- three-valued logic + external status;
- fakta teknis dengan satuan dan batas numerik;
- dependensi eksternal eksplisit;
- subgoal nyata (C4.2 → C4.1);
- pemisahan RAG/LLM/BC;
- rule lifecycle dengan human sign-off.

Yang **bukan** klaim:

- bukan algoritma baru;
- bukan “pertama di dunia”;
- bukan pengganti FIA delegate;
- bukan full Section C.

Kalimat aman:

> “Berdasarkan pencarian prior-art terbatas, belum ditemukan artefak publik yang menggabungkan BC deterministik, three-valued logic, evidence gate, dan unit-aware facts untuk FIA 2026 Section C. Klaim ini bukan klaim ‘pertama di dunia’.”

---

## 9. Permintaan dosen dan ambiguitas

Dosen meminta:

1. **AI-EXPERT di bidangnya** — validasi expert manusia.
2. **Teknologi yang belum ada** — kebaruan.

Dua kemungkinan arti “expert di bidangnya”:

### A. Ahli AI / sistem pakar
- Realistis: dosen AI, asisten dosen, mahasiswa S2/S3, praktisi.
- Bisa menilai: knowledge representation, BC, uncertainty, trace, evaluation.
- **Tidak** bisa menilai interpretasi pasal F1.

### B. Ahli F1 / regulasi teknis
- Sulit: perlu dosen teknik mesin/otomotif, praktisi motorsport, atau technical scrutineer.
- Bisa menilai: pasal, angka, satuan, pengecualian, applicability.
- Tidak tersedia saat ini.

**Pertanyaan klarifikasi yang harus diajukan ke dosen:**

> “Pak/Bu, ‘AI-expert di bidangnya’ yang dimaksud apakah ahli AI/sistem pakar yang memvalidasi metodologi, atau ahli domain Formula 1 yang memvalidasi interpretasi pasal? Jika yang diminta ahli F1, apakah validasi dokumen FIA + review AI expert dapat diterima sebagai pengganti, dengan keterbatasan dinyatakan eksplisit?”

---

## 10. Rekomendasi strategi (belum dieksekusi)

1. **Jangan tambah fitur/aturan** sebelum validasi selesai.
2. Buat dokumen:
   - `research/prior_art.md`
   - `research/novelty_statement.md`
   - `research/expert_review_protocol.md`
   - `research/rule_review_form.md`
   - `research/limitations_and_assumptions.md`
3. Cari **AI expert** lebih dulu; F1 expert menyusul jika memungkinkan.
4. Gunakan model **dua lapis validasi**:
   - AI expert: metodologi dan sistem;
   - dokumen FIA: kebenaran normatif;
   - F1 expert: opsional/limitasi.
5. Siapkan paket review 2 halaman + rule cards + demo 3 menit + formulir sign-off.
6. Setelah sign-off, ubah rule `reviewed` → `active`.
7. Siapkan demo 5–10 menit dan 15 pertanyaan dosen + jawaban.
8. Jangan klaim “pertama di dunia”; klaim “celah implementasi pada domain FIA Section C”.

---

## 11. Pertanyaan untuk AI Reasoning (brainstorming)

Tolong bantu jawab/eksplorasi:

1. Apakah **EG-3VBC** cukup defensible sebagai novelty, atau perlu framing lain? Bandingkan dengan PercepLog-0, ARCCS, dan LegalGraphRAG.
2. Apa **bukti minimum** yang bisa diterima dosen sebagai “AI-expert validation” jika ahli F1 tidak tersedia?
3. Bagaimana cara menemukan dan mendekati **AI expert** dalam waktu terbatas? Paket review seperti apa yang paling mungkin disetujui?
4. Bagaimana menjawab tuntutan **“teknologi yang belum ada”** tanpa overclaim?
5. Apa **deliverable minimum** yang harus dikumpulkan agar nilai aman?
6. Bagaimana struktur laporan dan demo yang paling meyakinkan?
7. Jika LLM nanti diaktifkan, bagaimana desain **A/B/C** yang adil dan tidak membingungkan?
8. Apa risiko akademik terbesar proyek ini, dan bagaimana mitigasinya?
9. Apakah proyek perlu **ganti domain** jika dosen tetap menuntut ahli F1? Apa alternatif yang lebih realistis?
10. Pertanyaan apa yang paling mungkin diajukan dosen, dan jawaban terbaiknya?
11. Bagaimana menangani **rule lifecycle dan sign-off** tanpa mengarang reviewer?
12. Perbaikan teknis apa yang **layak** dilakukan, dan mana yang scope creep?

**Jangan sarankan:**

- menambah puluhan aturan;
- mengarang reviewer/sign-off;
- mengklaim “pertama di dunia”;
- mengganti BC dengan LLM-only;
- menghapus batasan/limitasi dari laporan.

---

## 12. Cara menjalankan proyek

Dari root proyek:

```bat
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe scripts\validate_rules.py
.venv\Scripts\python.exe scripts\run_evaluation.py
```

API:

```powershell
Set-Location "C:\Users\HAR\Documents\SEMESTER 5\SENIN\AI\Project\AI-Pakar"
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

UI:

```powershell
Set-Location "C:\Users\HAR\Documents\SEMESTER 5\SENIN\AI\Project\AI-Pakar"
.venv\Scripts\python.exe -m streamlit run frontend\streamlit_app.py
```

Catatan: Streamlit harus di-restart setelah perubahan kode agar modul Python baru termuat.

---

## 13. Ringkasan satu paragraf

Proyek ini adalah prototipe sistem pakar hibrida untuk memeriksa 5 ketentuan FIA 2026 Section C menggunakan RAG (MiniLM + Qdrant), Backward Chaining deterministik tiga nilai, verifikasi sitasi, dan rule lifecycle. Sistem sudah berjalan, memiliki 66 test, API, UI, dan evaluasi dev/held-out. Semua aturan masih `reviewed`/demo, belum divalidasi manusia. Prior-art menunjukkan LLM+BC untuk legal dan regulatory compliance sudah ada, sehingga klaim kebaruan harus dipersempit menjadi artefak/arsitektur EG-3VBC untuk FIA Section C, bukan “teknologi pertama di dunia”. Tantangan utama bukan teknis, melainkan validasi expert manusia dan framing novelty yang jujur.
