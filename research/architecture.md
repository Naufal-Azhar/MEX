# Architecture

## 1. Tujuan dan batas sistem

Sistem adalah prototipe **pemeriksa kepatuhan regulasi teknis F1** yang menggabungkan:

- Retrieval-Augmented Generation (RAG) sebagai penyedia bukti dari dokumen FIA.
- Knowledge base fakta + aturan JSON.
- Backward Chaining sebagai mesin keputusan.
- Adapter LLM untuk memahami bahasa pengguna (dinonaktifkan pada tahap ini).

Batas eksplisit:

- Hanya 5 ketentuan yang dimodelkan: **C2.3.1, C2.3.3, C2.3.5, C4.1, C4.2** (Section C, Issue 21).
- RAG tidak menentukan kepatuhan. Keputusan selalu berasal dari mesin inferensi deterministik.
- LLM tidak boleh membuat atau mengubah aturan.
- Sistem tidak memverifikasi pengukuran fisik, geometri CAD, atau dokumen homologasi.

## 2. Peta komponen

```
frontend/streamlit_app.py
        │  (langsung atau HTTP)
        ▼
app/api/routes.py ──────────────► app/expert_system/service.py
        │                                   │
        │                                   ├── knowledge_base.py  (rules.json)
        │                                   ├── backward_chaining.py
        │                                   ├── rule_engine.py
        │                                   └── explanation.py
        │
        ├── app/rag/retriever.py ────► embeddings.py (Sentence Transformers / TF-IDF)
        │                        └───► vector_store.py (Qdrant local / TF-IDF / NumPy)
        │
        └── app/llm/fact_extractor.py ► base.py → api_provider.py / local_provider.py

app/document_processing/  pdf_loader → text_extractor → chunker
scripts/                  extract_documents.py, build_index.py, run_evaluation.py
```

### Tanggung jawab modul

| Modul | Tanggung jawab | Tidak melakukan |
|---|---|---|
| `document_processing` | Ekstraksi teks PDF per halaman, metadata, chunking dengan artikel/halaman | Menafsirkan regulasi |
| `rag` | Embedding, indexing, pencarian bukti + metadata | Menentukan TRUE/FALSE |
| `expert_system` | Fakta, aturan, evaluasi kondisi, subgoal, trace, penjelasan | Memanggil LLM |
| `llm` | Provider adapter + ekstraksi fakta tervalidasi | Menyusun aturan |
| `api` | Kontrak HTTP dan validasi input | Logika inferensi |
| `evaluation` | Metrik keputusan, sitasi, missing fact, retrieval | Mengubah aturan |
| `frontend` | Form, tampilan hasil, trace, bukti RAG | Menyimpan state keputusan |

## 3. Alur pemeriksaan kepatuhan

1. Pengguna memilih **goal** (mis. `wheelbase_compliance`) dan mengisi fakta (form atau teks).
2. Fakta dinormalisasi: nama, nilai, satuan, sumber. Fakta duplikat dengan nilai berbeda ditolak.
3. `BackwardChainingEngine.prove(goal)`:
   - mengambil aturan yang runnable (active, atau reviewed dalam demo mode) yang dapat membuktikan goal;
   - mengevaluasi `applies_if` (konteks penerapan);
   - mengevaluasi setiap kondisi; operand dapat berupa fakta, konstanta, ekspresi, atau `value(subgoal)`;
   - subgoal diproses rekursif (contoh: `minimum_mass` dari C4.1 dipakai C4.2);
   - menggabungkan hasil aturan.
4. `ComplianceService` menyusun laporan: status, aturan penentu, kutipan pasal, kondisi, fakta hilang, jejak, keterbatasan.
5. Penjelasan dihasilkan oleh template deterministik (bukan LLM).

## 4. Semantik inferensi

### Status

Internal proof steps: `TRUE`, `FALSE`, `UNKNOWN`.

External statuses (API/UI):

- `SATISFIED` — all applicable prerequisites proved true.
- `VIOLATED` — at least one applicable prerequisite proved false.
- `INSUFFICIENT_DATA` — missing/uncertain facts or evidence.
- `NOT_APPLICABLE` — all candidate rules are definitively inapplicable.
- `UNSUPPORTED` — unknown goal or regulation issue mismatch.
- `ERROR` — system failure, never a compliance verdict.

Diagnostics (`INVALID_INPUT`, `CONFLICTING_INPUT`, `SOURCE_MISSING`, `VERSION_MISMATCH`, `UNSUPPORTED_GOAL`, `RULE_NOT_APPROVED`, `INTERNAL_ERROR`) are reported separately.

Aturan penggabungan:

- Pelanggaran bersifat konservatif: jika ada aturan berlaku yang FALSE, hasil goal FALSE.
- Jika TRUE dan FALSE muncul bersamaan, hasil FALSE dan `rule_conflict = true` dicatat.
- `UNKNOWN` tidak pernah diubah menjadi `FALSE`.
- Aturan yang tidak berlaku (mis. C4.2 di sesi Race) menghasilkan `NOT_APPLICABLE`, bukan `SATISFIED`.

### Rule lifecycle

`draft → reviewed → active → deprecated`

- Only `active` rules are authoritative.
- `reviewed` rules run only in demo mode (`ALLOW_REVIEWED_RULES=true`), with a warning and `RULE_NOT_APPROVED` diagnostics.
- `active` requires `human_approved`, `reviewer`, `reviewed_at`, source verification fields, and test case IDs.
- Current rules are `reviewed` and **not human-approved**.

### Satuan dan presisi

- Setiap fakta numerik wajib memiliki satuan; konversi mendukung mm/cm/m dan g/kg/t.
- Satuan yang tidak kompatibel menghasilkan `UNKNOWN` dengan detail `incompatible units`, bukan perbandingan diam-diam.
- Tidak ada pembulatan nilai batas, sesuai **C2.5**.
- Nilai yang tidak ditetapkan regulasi (Nominal Tyre Mass) selalu menjadi fakta input.

### Representasi aturan

`knowledge_base/rules/rules.json` berisi `Rule`:

- `source` wajib: document_id, document, issue, article, page, quote.
- `applies_if` untuk konteks penerapan.
- `conditions` untuk syarat kepatuhan.
- `conclusion` bertipe `boolean` atau `value`.
- `status`: `draft`, `reviewed`, `active`, atau `deprecated`; hanya `active` yang otoritatif, `reviewed` hanya berjalan dalam demo mode.
- `validation`: verified_against, verified_on, method, reviewer, reviewed_at, human_approved, test_case_ids (wajib untuk reviewed/active; active wajib human_approved).

## 5. RAG

- Dokumen diproses menjadi chunk dengan metadata `document_id`, `article`/`subarticle`, `page`, `page_end`, `document_type`.
- Halaman daftar isi (TOC) dan header/footer diabaikan.
- Manifest menyimpan **SHA-256** dan ukuran setiap file sumber.
- Dua backend embedding:
  - **Sentence Transformers** (`all-MiniLM-L6-v2`), model cache di `storage/model_cache/`.
  - **TF-IDF** sebagai fallback offline yang deterministik.
- Vector store:
  - **Qdrant local mode** (`storage/vector_db/qdrant`) untuk embedding dense.
  - **TF-IDF index** (`storage/vector_db/tfidf_index.joblib`) untuk fallback.
- **Jurnal metodologi dikecualikan dari pencarian kepatuhan secara default**; `/v1/search` hanya menyertakannya dengan `include_methodology=true`.
- Setiap sitasi aturan diverifikasi terhadap teks halaman yang disimpan; kegagalan verifikasi menghasilkan `SOURCE_MISSING`.
- RAG hanya mengembalikan teks bukti + skor + metadata; tidak ada klaim kepatuhan dari retrieval.

## 6. Batas LLM

- `LLM_PROVIDER=none` secara default. Tidak ada panggilan jaringan saat pemeriksaan.
- Adapter tersedia untuk API OpenAI-compatible dan Ollama lokal.
- LLM hanya boleh dipakai untuk **ekstraksi fakta** dari bahasa alami, dengan output JSON yang divalidasi terhadap `FACT_SPECS`; nama fakta tak dikenal atau tipe salah ditolak.
- Aturan, nilai batas, dan status kepatuhan tidak pernah dihasilkan LLM.
- API key hanya dari `.env` (tidak pernah ditulis ke kode atau Git).

## 7. Penyimpanan dan isolasi

Semua artefak runtime berada di workspace:

```
.venv/                        virtual environment lokal
storage/model_cache/          cache Hugging Face / sentence-transformers / torch
storage/vector_db/            Qdrant local + indeks TF-IDF
storage/logs/app.log          log aplikasi
knowledge_base/               dokumen sumber, hasil ekstraksi, aturan, fakta
datasets/                     test cases, expected results, evaluation results
```

Tidak ada dependency global; instalasi dilakukan dengan `.venv\Scripts\python.exe -m pip install ...`.

## 8. API

| Endpoint | Fungsi |
|---|---|
| `GET /health` | Status, lifecycle counts, demo mode, provider LLM |
| `GET /v1/goals` | Daftar goal + artikel + kutipan + fakta yang dibutuhkan |
| `GET /rules` | Aturan + lifecycle + metadata validasi |
| `POST /v1/check` | Pemeriksaan satu goal (`goal_id`, `document_issue`, `facts[]`) |
| `POST /v1/check/all` | Pemeriksaan semua goal kepatuhan |
| `POST /v1/search` | Pencarian bukti; default hanya dokumen regulasi |
| `GET /v1/retrieval/status` | Status indeks |
| `POST /v1/extract-facts` | Ekstraksi fakta deterministik; LLM hanya jika diminta dan aktif |
| `GET /sample-facts` | Fakta contoh |
| legacy | `/goals`, `/check`, `/check/all`, `/retrieve`, `/extract-facts` |

Error envelope: `422 INVALID_INPUT`, `409 CONFLICTING_INPUT`, `503` untuk kegagalan retrieval/provider, `500 ERROR` tanpa stack trace ke klien.

## 9. Keamanan dan kualitas

- Validasi input: nama fakta yang didukung, tipe, satuan, rentang, dan konflik duplikat.
- Tidak ada eksekusi kode dari aturan (aturan adalah data).
- Siklus inferensi dideteksi; kedalaman maksimum 25.
- Setiap hasil membawa sumber, issue, halaman, kutipan, dan status verifikasi sitasi.
- Log aktivitas penting dan error ke `storage/logs/app.log`.
- 66 test mencakup parsing dokumen, unit, aturan, chaining, retrieval, API, lifecycle, sitasi, dan 18 skenario end-to-end.

## 10. Keterbatasan arsitektur

- Chunking berbasis baris/paragraf; tabel kompleks dan gambar tidak menjadi data terstruktur.
- Retrieval dense dapat tertukar dengan pasal lain yang memakai istilah serupa (mis. C10.1 untuk kata "front axle/rear axle"); ini dilaporkan di evaluasi.
- TF-IDF `max_features=4096` didominasi Section C sehingga sebagian istilah jurnal tidak masuk vocabulary; jurnal tetap dipisahkan dari pencarian kepatuhan.
- Perbandingan LLM-only vs RAG+LLM vs RAG+LLM+BC belum dijalankan.
- Rule quotes diverifikasi otomatis, tetapi belum ada human sign-off; semua hasil berstatus demo.
- Belum ada autentikasi API; prototipe diasumsikan berjalan lokal.
