# PROJECT BRIEF — AI EXPERT SYSTEM FORMULA 1

## 1. Peran dan tujuan

Bertindak sebagai Senior AI Engineer, Python Developer, dan Research Assistant.

Bangun sebuah prototipe **Sistem Pakar Pemeriksaan Kepatuhan Regulasi Teknis Formula 1** dengan pendekatan:

- Retrieval-Augmented Generation (RAG)
- Large Language Model (LLM)
- Backward Chaining (BC)
- Knowledge Base berbasis fakta dan aturan (rules)

Nama proyek:

`F1 Technical Regulation Expert System`

Tujuan sistem adalah membantu pengguna memeriksa apakah sekumpulan spesifikasi teknis yang diberikan memenuhi ketentuan regulasi teknis Formula 1 yang menjadi cakupan sistem.

Sistem harus mampu:
1. Menerima pertanyaan atau spesifikasi teknis dari pengguna.
2. Mengambil referensi dari dokumen regulasi resmi FIA.
3. Mengidentifikasi fakta yang relevan.
4. Memeriksa fakta menggunakan aturan yang telah divalidasi.
5. Menggunakan Backward Chaining untuk membuktikan atau menggagalkan suatu tujuan pemeriksaan.
6. Memberikan hasil beserta alasan, aturan yang digunakan, dan referensi pasal regulasi.
7. Menyatakan bahwa informasi belum cukup apabila fakta yang dibutuhkan tidak tersedia.

**Jangan mengklaim sistem dapat memeriksa seluruh kepatuhan sebuah mobil F1.** Batasi kesimpulan pada ketentuan yang benar-benar telah dimasukkan dan diuji.

---

## 2. Tahap pertama: audit dan membaca seluruh dokumen

Jangan langsung membuat aplikasi sebelum melakukan tahap ini.

Cari semua dokumen yang telah disediakan di workspace. Periksa folder proyek dan subfolder yang relevan.

Buat folder:

`knowledge_base/source_documents/`

Masukkan atau salin dokumen sumber ke folder tersebut tanpa mengubah dokumen aslinya.

Kelompokkan dokumen berdasarkan jenis:

A. Dokumen regulasi:
- FIA Formula One Technical Regulations, Section C, Issue 21 (2026), atau versi dokumen yang benar-benar tersedia.
- Dokumen FIA tambahan jika memang diperlukan oleh referensi silang dalam Section C.

B. Dokumen metodologi:
- Jurnal mengenai Backward Chaining.
- Jurnal mengenai RAG dan akurasi sitasi.
- Literatur lain yang relevan dengan pengembangan sistem pakar.

C. Materi pembelajaran:
- Modul Artificial Intelligence mengenai Expert System, Forward Chaining, dan Backward Chaining jika tersedia.

### Proses pembacaan dokumen

Gunakan Python dan PyMuPDF untuk mengekstrak teks PDF.

Untuk setiap dokumen:
1. Identifikasi nama dokumen.
2. Identifikasi penerbit atau penulis.
3. Identifikasi tahun dan versi/issue.
4. Ekstrak teks.
5. Pertahankan nomor halaman.
6. Pertahankan struktur judul, subjudul, artikel, dan subartikel.
7. Periksa apakah hasil ekstraksi terbaca dengan baik.
8. Tandai halaman yang membutuhkan OCR.
9. Jangan mengarang teks yang tidak berhasil diekstrak.

Simpan hasil ekstraksi di:

`knowledge_base/processed_documents/`

Buat juga:

`knowledge_base/document_manifest.json`

File tersebut harus mencatat:
- Nama dokumen.
- Jenis dokumen.
- Sumber/penerbit.
- Tahun.
- Versi atau issue.
- Tanggal dokumen.
- Lokasi file.
- Status ekstraksi.
- Catatan kualitas ekstraksi.

### Aturan penggunaan sumber

Bedakan sumber berdasarkan kewenangannya:

**FIA**
Merupakan sumber utama untuk isi regulasi, nilai teknis, definisi, batasan, dan ketentuan kepatuhan.

**Jurnal ilmiah**
Digunakan untuk mendukung metodologi RAG, Backward Chaining, representasi pengetahuan, dan metode evaluasi.

**Materi pembelajaran**
Digunakan sebagai referensi konsep dasar sistem pakar dan mekanisme inferensi.

Jangan menggunakan jurnal untuk menggantikan atau mengubah ketentuan resmi FIA.

Jangan membuat aturan regulasi berdasarkan interpretasi bebas dari LLM.

Jika terdapat konflik versi dokumen, catat konflik tersebut dan jangan mencampur aturan dari versi berbeda tanpa penjelasan.

### Hasil tahap pertama

Buat laporan:

`research/document_analysis.md`

Laporan harus berisi:
- Daftar dokumen yang berhasil dibaca.
- Ringkasan isi setiap dokumen.
- Struktur regulasi FIA yang ditemukan.
- Artikel atau subartikel yang berpotensi dijadikan aturan.
- Ketentuan yang membutuhkan referensi silang.
- Keterbatasan hasil ekstraksi.
- Rekomendasi cakupan awal yang realistis.

Jangan memilih pasal hanya karena terlihat mudah. Pilih berdasarkan apakah ketentuan tersebut bisa direpresentasikan sebagai fakta, kondisi, dan aturan yang dapat diuji secara deterministik.

---

## 3. Menentukan ruang lingkup sistem

Setelah membaca dokumen, identifikasi satu subdomain kecil dari Technical Regulations.

Pilih sekitar 3–5 ketentuan awal yang memenuhi kriteria:
- Memiliki definisi dan batasan yang jelas.
- Memiliki kondisi yang dapat diubah menjadi fakta.
- Bisa diuji menggunakan aturan logis.
- Memiliki referensi pasal yang jelas.
- Tidak membutuhkan data rahasia tim F1.
- Dapat diuji menggunakan skenario buatan yang tetap berlandaskan dokumen FIA.

Jangan langsung mengimplementasikan seluruh Section C.

Sebelum mengoding aturan, buat:

`research/rule_selection.md`

Untuk setiap calon aturan, jelaskan:
- Artikel dan subartikel FIA.
- Persyaratan yang ingin diperiksa.
- Fakta yang dibutuhkan.
- Kondisi yang membuat aturan terpenuhi.
- Kondisi yang membuat aturan dilanggar.
- Kondisi yang membuat hasil belum dapat ditentukan.
- Alasan aturan tersebut dipilih.

Jika ketentuan membutuhkan dokumen lain yang belum tersedia, tandai sebagai dependensi. Jangan mengasumsikan isi dokumen tersebut.

---

## 4. Arsitektur teknis

Gunakan arsitektur modular berikut:

### A. Document Processing
Bertugas membaca dan memproses dokumen PDF.

Teknologi:
- Python
- PyMuPDF
- Pydantic

### B. Retrieval-Augmented Generation
Bertugas mengambil potongan regulasi yang relevan dengan pertanyaan pengguna.

Teknologi:
- Sentence Transformers untuk embedding.
- Qdrant untuk vector database.
- Metadata artikel, subartikel, halaman, dan versi dokumen.

RAG hanya mengambil bukti dari sumber. RAG bukan mesin yang menentukan kebenaran kepatuhan.

### C. LLM Layer
Bertugas:
- Memahami pertanyaan pengguna.
- Mengubah bahasa pengguna menjadi kandidat fakta terstruktur.
- Mengidentifikasi informasi yang belum diberikan.
- Menjelaskan hasil pemeriksaan dengan bahasa yang mudah dipahami.

Gunakan pendekatan hybrid:
- API LLM sebagai pilihan awal.
- Buat adapter agar model lokal melalui Ollama dapat digunakan kemudian.

Jangan mengunci aplikasi pada satu penyedia LLM.

API key harus disimpan di `.env`, bukan ditulis langsung dalam kode.

### D. Knowledge Base
Menyimpan fakta, aturan, dan metadata sumber regulasi.

Gunakan JSON atau SQLite pada tahap awal.

Pisahkan:
- Fakta.
- Aturan.
- Referensi sumber.
- Versi regulasi.

Setiap aturan harus memiliki identitas unik dan referensi pasal FIA.

### E. Backward Chaining Engine
Buat mesin inferensi yang melakukan pemeriksaan berdasarkan tujuan.

Contoh alur:

Tujuan:
`Apakah spesifikasi komponen X memenuhi ketentuan Y?`

Mesin:
1. Mencari aturan yang dapat membuktikan tujuan.
2. Memeriksa prasyarat aturan.
3. Mengidentifikasi fakta yang diperlukan.
4. Meminta fakta yang belum tersedia.
5. Memeriksa kondisi secara deterministik.
6. Menghasilkan hasil dan jejak penalaran.

Gunakan tiga status:
- TRUE: kondisi terbukti terpenuhi.
- FALSE: kondisi terbukti tidak terpenuhi.
- UNKNOWN: fakta atau bukti belum cukup.

Penting:
UNKNOWN tidak boleh dianggap FALSE.

Jika ada beberapa prasyarat, pastikan mesin dapat menangani seluruh prasyarat dan hubungan antaraturan.

### F. User Interface
Gunakan Streamlit untuk membuat antarmuka prototipe.

Antarmuka minimal memiliki:
- Kolom pertanyaan pengguna.
- Form input spesifikasi teknis.
- Hasil pemeriksaan.
- Status TRUE/FALSE/UNKNOWN.
- Referensi pasal.
- Penjelasan hasil.
- Jejak Backward Chaining.

### G. Backend
Gunakan FastAPI untuk menyediakan endpoint pemeriksaan.

Pisahkan backend, retrieval, LLM, dan inference engine agar mudah diuji serta dikembangkan.

---

## 5. Struktur folder proyek

Buat struktur berikut dan sesuaikan hanya jika ada alasan teknis yang jelas.

f1-expert-system/
|
|-- app/
|   |-- main.py
|   |-- api/
|   |   |-- routes.py
|   |-- document_processing/
|   |   |-- pdf_loader.py
|   |   |-- text_extractor.py
|   |   |-- chunker.py
|   |-- rag/
|   |   |-- embeddings.py
|   |   |-- retriever.py
|   |   |-- vector_store.py
|   |-- llm/
|   |   |-- base.py
|   |   |-- api_provider.py
|   |   |-- local_provider.py
|   |   |-- fact_extractor.py
|   |-- expert_system/
|   |   |-- knowledge_base.py
|   |   |-- rule_engine.py
|   |   |-- backward_chaining.py
|   |   |-- explanation.py
|   |-- schemas/
|   |   |-- facts.py
|   |   |-- rules.py
|   |   |-- results.py
|   |-- evaluation/
|       |-- metrics.py
|       |-- evaluator.py
|
|-- knowledge_base/
|   |-- source_documents/
|   |-- processed_documents/
|   |-- metadata/
|   |-- facts/
|   |-- rules/
|
|-- datasets/
|   |-- test_cases.json
|   |-- expected_results.json
|
|-- research/
|   |-- document_analysis.md
|   |-- rule_selection.md
|   |-- architecture.md
|   |-- evaluation_plan.md
|
|-- frontend/
|   |-- streamlit_app.py
|
|-- tests/
|   |-- test_document_processing.py
|   |-- test_retrieval.py
|   |-- test_backward_chaining.py
|   |-- test_rule_engine.py
|   |-- test_end_to_end.py
|
|-- configs/
|-- scripts/
|-- .env.example
|-- .gitignore
|-- requirements.txt
|-- Dockerfile
|-- docker-compose.yml
|-- README.md

---

## 6. Format representasi aturan

Gunakan format aturan yang terstruktur.

Contoh ilustratif berikut bukan aturan FIA yang sesungguhnya. Jangan memasukkannya sebagai regulasi sebelum memvalidasi pasal aslinya.

{
  "rule_id": "RULE_001",
  "name": "Illustrative technical compliance rule",
  "source": {
    "document": "FIA Technical Regulations",
    "issue": "ISSUE_VERSION",
    "article": "ARTICLE_REFERENCE",
    "page": null
  },
  "conditions": [
    {
      "fact": "example_measurement",
      "operator": "<=",
      "value": 100,
      "unit": "mm"
    }
  ],
  "conclusion": {
    "goal": "example_compliance",
    "value": true
  },
  "status": "pending_validation"
}

Setiap aturan yang benar-benar digunakan harus:
- Memiliki sumber FIA.
- Memiliki pasal yang dapat diverifikasi.
- Memiliki satuan yang konsisten.
- Memiliki kondisi penerapan yang jelas.
- Memiliki pengujian.
- Memiliki status validasi.

Jangan mengaktifkan aturan dengan status `pending_validation`.

---

## 7. Pengujian dan evaluasi

Buat dataset pengujian awal minimal 15 skenario:
- 5 skenario yang memenuhi ketentuan.
- 5 skenario yang melanggar ketentuan.
- 5 skenario yang informasinya tidak lengkap.

Jumlah ini merupakan target awal prototipe, bukan klaim bahwa seluruh regulasi telah tervalidasi.

Setiap skenario harus memiliki:
- Input fakta.
- Tujuan pemeriksaan.
- Hasil yang diharapkan.
- Aturan yang digunakan.
- Referensi FIA.
- Alasan hasil.

Uji minimal:
1. Akurasi keputusan aturan.
2. Precision, recall, dan F1 jika sesuai dengan bentuk klasifikasi.
3. Ketepatan retrieval terhadap artikel yang benar.
4. Ketepatan sitasi.
5. Kualitas penjelasan.
6. Kemampuan mendeteksi informasi yang belum tersedia.
7. Konsistensi jejak Backward Chaining.

Bandingkan tiga konfigurasi jika memungkinkan:

A. LLM tanpa RAG dan BC.

B. RAG + LLM.

C. RAG + LLM + Backward Chaining.

Gunakan model, data, dan kondisi pengujian yang sama agar perbandingan adil.

Jangan mengklaim BC meningkatkan akurasi sebelum hasil eksperimen mendukung klaim tersebut.

---

## 8. Keamanan dan kualitas implementasi

Terapkan ketentuan berikut:
- Jangan mengarang artikel, angka, atau ketentuan FIA.
- Jangan membiarkan LLM membuat atau mengubah aturan secara otomatis.
- Pisahkan jawaban LLM dengan hasil mesin inferensi.
- Simpan sumber dan versi regulasi pada setiap hasil.
- Tangani satuan pengukuran secara eksplisit.
- Validasi input pengguna.
- Tangani fakta yang bertentangan.
- Catat error dan aktivitas penting.
- Jangan menyimpan API key di Git.
- Buat unit test untuk setiap aturan.
- Pastikan sistem dapat dijalankan ulang dari dokumentasi.

Jika dokumen tidak menyediakan bukti yang cukup, sistem harus menyampaikan keterbatasannya.

---

## 9. Prioritas pengerjaan

Kerjakan secara bertahap.

### Tahap 1 — Document Audit
- Temukan semua dokumen.
- Baca dan ekstrak dokumen.
- Buat document manifest.
- Buat laporan analisis dokumen.

### Tahap 2 — Research dan Knowledge Modeling
- Tentukan subdomain.
- Pilih 3–5 aturan.
- Buat representasi fakta dan aturan.
- Validasi referensi sumber.

### Tahap 3 — Core Engine
- Implementasikan knowledge base.
- Implementasikan rule engine.
- Implementasikan Backward Chaining.
- Buat unit test.

### Tahap 4 — RAG dan LLM
- Buat indexing dokumen.
- Implementasikan retrieval.
- Buat ekstraksi fakta dari bahasa alami.
- Hubungkan LLM dengan inference engine.

### Tahap 5 — Interface
- Buat API.
- Buat Streamlit.
- Tampilkan hasil, sumber, dan reasoning trace.

### Tahap 6 — Evaluation
- Buat dataset pengujian.
- Jalankan pengujian.
- Catat metrik dan hasil.
- Dokumentasikan keterbatasan.

---

## 10. Hasil akhir yang wajib diserahkan

Pastikan proyek menghasilkan:

1. Source code yang dapat dijalankan.
2. Dokumen regulasi yang sudah diproses.
3. Document manifest.
4. Laporan analisis dokumen.
5. Knowledge base berisi aturan tervalidasi.
6. Backward Chaining engine.
7. RAG retrieval pipeline.
8. Integrasi LLM.
9. Antarmuka prototipe.
10. Dataset dan hasil pengujian.
11. README berisi instruksi instalasi dan penggunaan.
12. Dokumentasi arsitektur dan keterbatasan sistem.

---

## 11. Instruksi eksekusi kepada agent

Mulai dengan melakukan audit terhadap workspace dan dokumen yang tersedia.

Jangan langsung membuat seluruh aplikasi sekaligus.

Setelah Tahap 1 selesai:
- Tampilkan daftar dokumen yang berhasil dibaca.
- Tampilkan ringkasan hasil analisis.
- Tampilkan rekomendasi 3–5 aturan yang paling layak.
- Tunjukkan alasan pemilihan aturan.
- Jelaskan jika ada dokumen yang tidak dapat dibaca.

Setelah itu lanjutkan implementasi secara bertahap. Jika ada ketidakpastian pada isi regulasi, jangan menebak. Tandai sebagai pertanyaan atau dependensi yang membutuhkan verifikasi.

Prioritaskan sistem yang benar, dapat diuji, dan dapat dijelaskan daripada sistem yang terlihat canggih tetapi hasilnya tidak dapat dipertanggungjawabkan.

**Prinsip utama proyek: setiap keputusan kepatuhan harus dapat ditelusuri kembali ke fakta, aturan, dan sumber regulasi FIA yang mendasarinya.**