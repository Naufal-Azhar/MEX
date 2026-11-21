# Rencana kerja konkret: AI pendamping belajar teknik F1

Tanggal: 19 November 2026. Status: rancangan implementasi, bukan klaim bahwa fitur baru sudah berjalan.

## Keputusan produk

Target pengguna: penggemar F1 dan mahasiswa/klub yang ingin memahami aturan teknis lewat contoh, bukan tim F1 atau pemeriksa resmi. Judul yang sudah disetujui dosen tetap dipakai: *Development of an Evidence-Based Motorsport Engineering Expert AI Using Retrieval-Augmented Generation*.

Satu alur pertama: pengguna bertanya tentang perubahan wheelbase, memasukkan contoh 3500 mm, lalu melihat (1) jawaban bersumber; (2) pemeriksaan batas pada dokumen 2025 Issue 3 dan 2026 Issue 21; (3) pasal, halaman, satuan, jejak inferensi, dan selisih minimal ke batas 2026. Keluaran adalah pemeriksaan **batas wheelbase dalam skenario pembelajaran**, bukan kepatuhan seluruh mobil.

Keputusan numerik berasal dari rule engine. RAG mengambil FIA dan literatur teknik yang relevan. Model bahasa hanya menyusun penjelasan dari bukti dan hasil engine; ia tidak boleh menetapkan batas, mengubah fakta, atau mengganti verdict.

## Posisi kode saat ini

- Sudah ada: PDF FIA 2026 Issue 21 dalam knowledge base, 13 rule entry/5 compliance goal, backward chaining, validasi satuan, tiga nilai internal, verifikasi kutipan, FastAPI, Streamlit, retrieval, dan dataset uji awal.
- Tersedia sebagai bahan riset tetapi belum terintegrasi: PDF FIA 2025 Issue 3 di `folder_dokumen/`.
- Belum ada: pemilihan rule set berdasarkan tahun+issue, pemeriksaan satu input pada dua versi, delta/perubahan minimum, jawaban RAG generatif, dan literatur ilmiah **teknik motorsport** di indeks. Dua jurnal yang ada sekarang membahas metode AI, bukan dinamika kendaraan.
- Semua rule saat ini `reviewed`, belum disetujui reviewer manusia. Status ini harus tetap terlihat di setiap hasil demo.

## Urutan implementasi dan kriteria selesai

### 0. Bekukan spesifikasi satu skenario

1. Baca langsung pasal 3.4.2 dan definisi bidang XF/XR pada PDF 2025 Issue 3, serta C2.3.3, C2.2, dan definisi Legality Setup pada PDF 2026 Issue 21.
2. Catat kutipan persis, halaman PDF, tahun, issue, operator, nilai, unit, pengecualian, dan **kondisi pengukuran** pada kartu aturan.
3. Definisikan input demo sebagai *wheelbase contoh yang diasumsikan memiliki nilai sama saat diterapkan pada kondisi ukur masing-masing dokumen*. Tampilkan asumsi tersebut; jika tidak disetujui pengguna, minta nilai terpisah per kondisi. Jangan menyamakan Legality Ride Height dengan Legality Setup.
4. Bekukan kontrak hasil: `SATISFIED`, `VIOLATED`, `INSUFFICIENT_DATA`, atau `UNSUPPORTED` per dokumen; `required_change_mm` hanya untuk batas numerik yang bisa dihitung dan memiliki fakta valid.

**Selesai bila:** tabel sumber dan contoh 3500 mm bisa diperiksa ulang dari PDF tanpa mengandalkan ingatan atau keluaran LLM.

### 1. Masukkan dokumen dan rule 2025

1. Salin PDF 2025 Issue 3 ke `knowledge_base/source_documents/REGULASI FIA/` dan isi metadata judul, tanggal, issue, tipe `regulation`, serta sumber FIA di `knowledge_base/metadata/document_overrides.json`.
2. Jalankan `scripts/extract_documents.py` dan `scripts/build_index.py`; cek manifest SHA-256, halaman, artikel, dan hasil retrieval untuk dua pasal wheelbase.
3. Buat `knowledge_base/rules/2025-issue-03.json` berisi **satu rule wheelbase** dulu. Pertahankan `knowledge_base/rules/rules.json` sebagai rule set 2026 lama, lalu beri identitas eksplisit `2026-issue-21` dalam katalog. Status rule 2025 tetap `reviewed`/demo sampai ada review manusia.
4. Sesuaikan `app/expert_system/knowledge_base.py` dan `app/expert_system/service.py` agar memilih rule set dengan `(year, issue, section)`. Permintaan versi yang tidak ada menghasilkan `UNSUPPORTED`, bukan diam-diam memakai 2026.

**Selesai bila:** `/v1/check` dapat memeriksa wheelbase 2025 atau 2026 secara terpisah, dan setiap hasil menunjuk PDF, issue, pasal, dan halaman yang benar.

### 2. Bangun perbandingan dan perubahan minimum

1. Tambahkan schema request/response di `app/schemas/api.py` dan `app/schemas/results.py`: `goal_id`, dua identitas dokumen, fakta bersatuan, asumsi pengukuran, dua report, perubahan limit, dan saran perubahan minimum.
2. Tambahkan layanan perbandingan di `app/expert_system/` yang **memanggil engine yang sama dua kali**. Jangan membuat algoritma verdict kedua di UI.
3. Untuk operator `<=` pada wheelbase, hitung `max(0, input_mm - limit_mm)`. Label sebagai *penurunan minimum agar memenuhi batas wheelbase pada issue tujuan*, bukan rekomendasi desain/performa. Untuk data kosong, tidak valid, aturan nonnumerik, atau sumber tak terverifikasi, jangan tampilkan angka saran.
4. Tambahkan `POST /v1/compare` di `app/api/routes.py`; respons memuat dua `CheckReport` asli beserta delta dan konteks pengukuran.

**Selesai bila:** 3500 mm → 2025 memenuhi, 2026 melampaui batas, perubahan minimum 100 mm, dan kedua sumber tampil. Layanan tetap memakai evidence gate dan mode demo yang ada.

### 3. Wujudkan RAG sebagai jawaban, bukan hanya daftar kutipan

1. Pilih satu literatur ilmiah teknik kendaraan/motorsport yang relevan untuk menerangkan arti wheelbase, lalu catat identitas bibliografi dan halaman. Jangan menyimpulkan dampak performa spesifik dari perubahan 100 mm tanpa model fisika/data.
2. Pakai `app/rag/retriever.py` untuk mengambil pasal FIA per issue dan literatur teknik secara terpisah. FIA menjadi sumber normatif; jurnal menjadi sumber penjelasan teknik.
3. Tambahkan layanan jawaban dan endpoint `POST /v1/ask`. Prompt harus menerima pertanyaan, bukti terpilih, dan hasil terstruktur engine; jawaban hanya boleh memuat klaim yang didukung sumber. LLM yang tidak tersedia memberi status layanan jelas dan UI masih dapat menampilkan laporan deterministik.
4. Gunakan adapter provider yang ada di `app/llm/`, uji satu backend nyata, dan tampilkan kutipan per klaim, nomor halaman, issue, serta batasan jawaban. Jawaban yang sumbernya lemah harus menyatakan tidak cukup bukti.

**Selesai bila:** pertanyaan “Apa arti perubahan wheelbase 2025–2026 untuk contoh 3500 mm?” menghasilkan jawaban teknis dengan sitasi FIA dan literatur; angka verdict selalu sama dengan engine dan tidak berubah saat LLM diulang.

### 4. Satu UI yang menghubungkan semuanya

1. Jadikan halaman utama di `frontend/streamlit_app.py` sebagai alur **Tanya → Isi contoh → Bandingkan → Baca alasan dan sumber**. Pertahankan halaman penelusuran sumber/aturan sebagai detail lanjutan.
2. Sediakan contoh 3500 mm, input nilai dan satuan mm/cm/m, opsi asumsi pengukuran yang jelas, tombol jalankan, reset, dan unduh laporan. Semua tombol harus mempunyai efek yang diuji.
3. Tampilkan dua kartu hasil tahun/issue, selisih batas, perubahan minimum, pasal dan halaman, serta tautan/teks kutipan; berikan penanda demo dan status data kosong.

**Selesai bila:** pengguna baru bisa menyelesaikan skenario tanpa membuka Swagger, mengetik JSON, atau memahami struktur rule internal.

### 5. Uji, evaluasi, dan klaim penelitian

1. Tambahkan kasus 3399, 3400, 3401, 3500, 3600, 3601 mm; 3,5 m; nilai kosong, negatif, satuan salah, versi tak ada, sumber hilang, dan asumsi pengukuran tidak dipenuhi.
2. Uji API dan UI pada dua versi, termasuk semua tombol; jalankan `pytest`, `scripts/validate_rules.py`, dan evaluasi retrieval. Periksa sitasi terhadap PDF per issue, bukan sekadar URL.
3. Bandingkan baseline **RAG saja** dengan sistem gabungan pada tugas numerik yang sama: akurasi verdict, akurasi nilai batas, ketepatan sitasi, stabilitas jawaban, dan penanganan fakta kurang. Nilai pada dataset kecil harus dilaporkan sebagai hasil prototipe, bukan validasi dunia nyata.
4. Dokumentasikan prior art di `research/pembanding_simulator_regulasi.md`; rumuskan novelty sebagai alur pembelajaran F1 yang menggabungkan jawaban bersumber, evaluasi numerik lintas issue, jejak aturan, dan perubahan minimum. Jangan klaim algoritma baru atau “pertama di dunia”.

**Selesai bila:** satu demo end-to-end terekam/terdokumentasi, semua kasus uji lulus, tabel pembanding dan batasan ditulis, dan dosen dapat mengulangi contoh 3500 mm.

## Batas rilis pertama

Rilis pertama hanya wheelbase pada 2025 Issue 3 versus 2026 Issue 21. Aturan massa/lebar, isu 2026 lain, simulasi lap time/CFD, CAD, seluruh Section C, dan perkiraan efek performa **masuk backlog setelah alur pertama terbukti**. Ini mencegah contoh utama tenggelam dalam cakupan yang belum tervalidasi.

## Syarat akademik yang perlu dinyatakan jujur

- Validasi dokumen dan uji otomatis tidak sama dengan persetujuan ahli F1. Jangan membuat nama reviewer atau mengubah `human_approved` tanpa review nyata.
- Kontribusi sistem pakar untuk modul tetap backward chaining, aturan IF–THEN, fakta, jejak inferensi, dan uji kasus. RAG melengkapi penjelasan sesuai judul.
- Perubahan regulasi 2025–2026 bukan otomatis perubahan performa kendaraan. Jika kelak ingin menganalisis performa, perlu model dan data teknik tersendiri.
