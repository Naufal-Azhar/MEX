# Evaluation Plan

## 1. Tujuan evaluasi

Mengukur kualitas sistem secara terpisah untuk:

1. Keputusan aturan (TRUE/FALSE/UNKNOWN).
2. Deteksi informasi yang tidak tersedia.
3. Ketepatan sitasi pasal dan halaman.
4. Kualitas penjelasan.
5. Konsistensi jejak Backward Chaining.
6. Ketepatan retrieval.

Evaluasi tidak boleh mengklaim lebih dari cakupan 5 aturan yang dimodelkan.

## 2. Dataset

### 2.1 Decision suite — `datasets/development_cases.json` + `datasets/heldout_cases.json`

18 skenario, dipisah deterministik:

- 12 development cases (TC01, TC02, TC04, TC05, TC06, TC08, TC09, TC10, TC11, TC13, TC15, TC16).
- 6 held-out cases (TC03, TC07, TC12, TC14, TC17, TC18).

Komposisi kelas tetap seimbang: 6 TRUE, 7 FALSE, 5 UNKNOWN. Setiap skenario memiliki fakta, goal, hasil internal yang diharapkan, hasil eksternal yang diharapkan, aturan, artikel FIA, dan alasan (`datasets/expected_results.json`).

Status internal (`TRUE`/`FALSE`/`UNKNOWN`) dipakai untuk evaluasi proof; status eksternal (`SATISFIED`/`VIOLATED`/`INSUFFICIENT_DATA`/`NOT_APPLICABLE`/`UNSUPPORTED`/`ERROR`) diverifikasi terpisah.

### 2.2 Retrieval suite — `datasets/retrieval_cases.json`

10 query yang dipetakan ke subartikel Section C yang benar. Metrik dihitung pada k = 5.

## 3. Metrik

### Keputusan

- **Accuracy**: proporsi status internal yang sama dengan expected.
- **External status accuracy**: status eksternal (SATISFIED/VIOLATED/INSUFFICIENT_DATA/NOT_APPLICABLE) sesuai expected.
- **Precision / Recall / F1 untuk FALSE**: kemampuan mendeteksi pelanggaran (kelas positif = FALSE).
- **Per-label precision/recall/F1** untuk TRUE, FALSE, UNKNOWN.
- **Confusion matrix** TRUE/FALSE/UNKNOWN.
- **Rule match accuracy**: aturan penentu sama dengan expected.
- **Article match accuracy**: artikel sumber sama dengan expected.
- **Citation accuracy**: kutipan sumber ada dan artikel muncul di penjelasan.
- **Citation verification rate**: semua sitasi yang dipakai terverifikasi pada teks halaman.
- **Missing-fact precision/recall/F1**: himpunan fakta yang dilaporkan vs expected.
- **Explanation completeness**: 5 komponen (verdict, rule id, article, bukti/fakta hilang, disclaimer).
- **Trace consistency**: goal/status internal/rule pada trace sama dengan laporan; tidak ada node duplikat.

### Retrieval

- **Hit@k**: minimal satu artikel yang diharapkan muncul di top-k.
- **Precision@k**: proporsi hasil top-k yang relevan (dengan satu gold artikel, nilai maksimum praktis adalah 1/k).
- **Recall@k**: proporsi gold artikel yang ditemukan.
- **MRR**: reciprocal rank hasil relevan pertama.

## 4. Tiga konfigurasi pembanding (rencana)

| Konfigurasi | Deskripsi | Status |
|---|---|---|
| A | LLM tanpa RAG dan tanpa Backward Chaining | Belum dijalankan |
| B | RAG + LLM | Belum dijalankan |
| C | RAG + LLM + Backward Chaining | Sebagian: mesin BC dan RAG sudah diuji; komponen LLM dinonaktifkan; aturan masih reviewed/demo |

Agar perbandingan adil:

- Model LLM, prompt sistem, temperature (0.0), dan `max_tokens` harus sama.
- Dataset dan urutan kasus sama.
- RAG memakai indeks dan `top_k` yang sama.
- Penilaian status untuk A/B dilakukan oleh anotator yang sama dengan C.
- Hasil LLM tidak boleh mengubah aturan; hanya fakta yang diekstrak.

**Klaim yang dilarang sebelum eksperimen:** "Backward Chaining meningkatkan akurasi". Saat ini belum ada bukti eksperimental untuk klaim tersebut.

## 5. Prosedur menjalankan

```bat
set PYTHONPATH=.
.venv\Scripts\python.exe scripts\extract_documents.py
.venv\Scripts\python.exe scripts\build_index.py
.venv\Scripts\python.exe scripts\run_evaluation.py
.venv\Scripts\python.exe -m pytest -q
```

Output:

- `datasets/evaluation_results.json`
- `research/evaluation_results.md`

## 6. Hasil saat ini (ringkas)

Lihat `research/evaluation_results.md` untuk tabel per kasus.

- Decision accuracy: **1.0** (18/18 internal; 18/18 external).
- Rule match accuracy: **1.0**.
- Article match accuracy: **1.0**.
- Citation accuracy: **1.0**; citation verification rate: **1.0**.
- Missing-fact precision/recall: **1.0 / 1.0**.
- Explanation completeness: **1.0**.
- Trace consistency: **1.0**.
- Retrieval (Sentence Transformers + Qdrant, k=5): hit rate **0.9**, MRR **0.9**, precision@5 **0.18**.
- Decision latency mean **7.43 ms**, p95 **120.62 ms** (cold-start included); failure rate **0.0**.
- Retrieval latency mean **91.57 ms**, p95 **351.86 ms** (local machine, not a benchmark).
- Development vs held-out metrics are reported separately in `research/evaluation_results.md`.

**Semua hasil bersifat demo**: aturan berstatus `reviewed`, belum `active`/human-approved.

Angka ini berlaku untuk dataset kecil yang dibuat dari batas regulasi, bukan bukti akurasi pada mobil nyata.

## 7. Ancaman terhadap validitas

- Dataset hanya 18 kasus dan 5 aturan; tidak mewakili seluruh Section C.
- Label dibuat sendiri dan belum direview manusia; tidak ada inter-annotator agreement.
- Nilai Nominal Tyre Mass pada kasus uji adalah nilai ilustratif.
- Retrieval memiliki satu gold artikel per query sehingga Precision@k secara struktural terbatas.
- Satu query retrieval (C4.2) tertukar dengan C10.1 yang juga menyebut front/rear axle; terlihat pada hasil dan tidak disembunyikan.
- TF-IDF `max_features=4096` didominasi Section C sehingga sebagian istilah jurnal tidak masuk vocabulary.
- Penjelasan dinilai secara struktural (kelengkapan komponen), bukan oleh penilai manusia.
- Konfigurasi A dan B belum dijalankan sehingga belum ada perbandingan kausal.
- Held-out split mengurangi overfitting seleksi aturan, tetapi bukan pengganti validasi eksternal.
