# Document Analysis — F1 Technical Regulation Expert System

Tanggal analisis: 2026-11-17
Metode: ekstraksi teks PDF dengan PyMuPDF (`scripts/extract_documents.py`), tanpa OCR karena seluruh halaman memiliki text layer.
Manifest lengkap: `knowledge_base/document_manifest.json`

---

## 1. Dokumen yang berhasil dibaca

| # | Dokumen | Jenis | Penerbit / Penulis | Tahun | Versi / Issue | Halaman | Status ekstraksi |
|---|---------|-------|--------------------|-------|---------------|---------|------------------|
| 1 | FIA 2026 F1 Regulations — Section C [Technical] | Regulasi (utama) | Fédération Internationale de l'Automobile (FIA) | 2026 | Issue 21, 19-10-2026, WMSC approved | 254 | Sukses (0 halaman perlu OCR) |
| 2 | FIA 2026 F1 Regulations — Section A [General Provisions] | Regulasi (pendukung) | FIA | 2026 | Issue 03, 25-06-2026 | 84 | Sukses (0 halaman perlu OCR) |
| 3 | Backward chaining inference as a database stored procedure — the experiments on real-world knowledge bases | Jurnal metodologi | Tomasz Xieński & Roman Simiński — Journal of Information and Telecommunication, 2(4), 449–464 | 2018 | Vol. 2 No. 4, DOI 10.1080/24751839.2018.1479931 | 17 | Sukses (0 halaman perlu OCR) |
| 4 | Evaluating and Fine-Tuning Retrieval-Augmented Language Models to Generate Text With Accurate Citations | Jurnal metodologi | Vinzent Penzkofer & Timo Baumann — KONVENS 2024 (ACL), hlm. 57–64 | 2024 | Proceedings of KONVENS 2024 | 8 | Sukses (0 halaman perlu OCR) |

Tidak ada dokumen yang gagal dibaca. Tidak ada materi pembelajaran (modul kuliah Expert System / Forward–Backward Chaining) di workspace; bagian konsep inferensi akan mengacu pada jurnal Backward Chaining dan literatur standar, dan akan ditandai sebagai referensi metodologi, bukan sumber regulasi.

Total teks terekstrak: ±937.000 karakter (Section C: 635.021; Section A: 227.599; dua jurnal: 74.256).

Manifest juga menyimpan **SHA-256** dan ukuran byte setiap file sumber, sehingga integritas dokumen dapat diverifikasi ulang.

### Kualitas ekstraksi per dokumen
- **Section C**: rata-rata ±2.500 karakter/halaman; struktur artikel, subartikel, tabel, dan nomor halaman terbaca. Footer/header berulang ("SECTION C: TECHNICAL REGULATIONS", nomor halaman, versi) ikut terekstrak dan perlu difilter saat chunking.
- **Section A**: rata-rata ±2.709 karakter/halaman; struktur artikel dan lampiran terbaca.
- **Kedua jurnal**: teks dua kolom terekstrak dengan baik; beberapa karakter non-ASCII (mis. "Xięski", "ﬁ") dinormalisasi saat indexing.

---

## 2. Ringkasan isi setiap dokumen

### 2.1 FIA 2026 Section C [Technical] — Issue 21
Regulasi teknis mobil Formula 1 musim 2026. Berisi 18 artikel (C1–C18) dan 6 lampiran (C1–C6, penomoran terpisah). Cakupan meliputi prinsip umum, konvensi koordinat dan dimensi fundamental, komponen aerodinamika, massa, power unit, sistem bahan bakar, sistem oli/pendingin, sistem elektrikal, transmisi, suspensi/roda/ban, rem, survival cell, struktur keselamatan dan homologasi, peralatan keselamatan, material, bahan bakar dan oli mesin, serta klasifikasi komponen. Konvensi warna: teks hitam = tidak berubah dari Issue 20, merah muda = perubahan yang disetujui WMSC 19-10-2026, merah = informasi governance, oranye = referensi dokumen FIA lain, hijau = komentar non-regulasi.

### 2.2 FIA 2026 Section A [General Provisions] — Issue 03
Ketentuan umum kejuaraan: prinsip umum, status kejuaraan dunia, entri dan lisensi, integritas, peran stakeholder, investigasi dan pelanggaran, adjudikasi dan sanksi, kerahasiaan, periode berlaku, serta lampiran definisi (A1) dan lampiran supply power unit/fuel/oil 2026–2030 (A7). Section A relevan sebagai sumber definisi istilah dan aturan lintas-dokumen, bukan sumber nilai teknis.

### 2.3 Jurnal Backward Chaining (Xieński & Simiński, 2018)
Membandingkan implementasi backward chaining klasik (goal-driven, di klien) dengan implementasi sebagai stored procedure di database. Memuat deskripsi rinci algoritma inferensi backward, diagram blok, pseudocode, dan versi rekursif. Relevan untuk desain `backward_chaining.py`: pencarian goal-driven, resolusi subgoal, dan penelusuran jejak inferensi.

### 2.4 Jurnal RAG & sitasi (Penzkofer & Baumann, 2024)
Memperkenalkan RAGE, kerangka evaluasi kemampuan model menandai sumber (citation) dalam sistem RAG, dengan metrik Citation-Precision, Citation-Recall, Distinct Citations, dan F1. Relevan untuk `app/evaluation/` dan untuk prinsip bahwa RAG hanya menyediakan bukti, bukan penentu kepatuhan.

**Aturan penggunaan sumber:** FIA adalah satu-satunya sumber nilai teknis, definisi, dan ketentuan kepatuhan. Kedua jurnal hanya dipakai untuk metodologi implementasi dan evaluasi, tidak untuk mengubah atau menggantikan ketentuan FIA.

---

## 3. Struktur regulasi FIA Section C yang ditemukan

| Artikel | Judul | Halaman (indeks PDF) |
|---|---|---|
| C1 | General Principles | 7 |
| C2 | Conventions and Fundamental Dimensions | 9 |
| C3 | Aerodynamic Components | 12 |
| C4 | Mass | 59 |
| C5 | Power Unit | 61 |
| C6 | Fuel System | 85 |
| C7 | Oil and Coolant Systems and Charge Air Cooling | 89 |
| C8 | Electrical Systems | 90 |
| C9 | Transmission System | 100 |
| C10 | Suspension, Steering Systems, Wheels and Tyres | 106 |
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
| App. C4 | Power Unit Systems, Functions, Components and Supply Perimeter | 225 |
| App. C5 | Homologation and Development of Power Units, Fuel and Oil 2026–2030 | 237 |
| App. C6 | Components' Classification and Perimeter | 244 |

Subartikel yang menjadi kandidat aturan berada di **C2.3 (Fundamental Dimensions)** dan **C4 (Mass)** — keduanya berisi batas numerik eksplisit dengan referensi pasal yang dapat diverifikasi.

---

## 4. Artikel/subartikel yang berpotensi menjadi aturan

Penilaian determinisme: **Tinggi** = batas numerik tunggal dan satuan jelas; **Sedang** = membutuhkan definisi/konstruksi geometri pendukung; **Rendah** = bergantung pada gambar, CAD, atau penilaian teknis FIA.

| Artikel | Ketentuan (ringkas) | Halaman | Determinisme | Catatan |
|---|---|---|---|---|
| C2.3.1 | Tidak ada bagian mobil (kecuali ban, wheel rim, dan komponen terpasang pada rim menurut C10.7.6) yang boleh lebih dari 950 mm dari plane Y=0 pada Legality Setup | 10 | Tinggi (dengan pengecualian eksplisit) | Perlu memisahkan komponen yang dikecualikan |
| C2.3.3 | Jarak plane XF=0 dan XR=0 ≤ 3400 mm pada Legality Setup | 11 | Tinggi | Langsung berupa satu pertidaksamaan |
| C2.3.4 | Plane XF=0 harus berada antara XA=0 dan XA=150 inklusif | 11 | Tinggi | Batas interval |
| C2.3.5 | Jarak XA=0 ke XC=0 ≥ 1830 mm dan ≤ 2030 mm | 11 | Tinggi | Batas interval |
| C2.3.6 | Jarak XC=0 ke XPU=0 ≥ 360 mm | 11 | Tinggi | Satu pertidaksamaan |
| C4.1 | Minimum Mass 726 kg + Nominal Tyre Mass (Sprint Qualifying/Qualifying) atau 724 kg + Nominal Tyre Mass (sesi lain); Car Mass tidak boleh kurang; Heat Hazard menambah massa | 59 | Tinggi, dengan dependensi eksternal | Nominal Tyre Mass ditetapkan penyedia ban (C4.7), bukan nilai tetap dalam regulasi |
| C4.2 | Pada Qualifying/Sprint Qualifying, massa di front axle ≥ 0,44 × Minimum Mass dan rear axle ≥ 0,54 × Minimum Mass | 59 | Tinggi | Bergantung pada hasil C4.1 (antar-aturan) |
| C4.3.2 | Driver ballast: densitas > 7500 kg/m³, posisi, tersegel, tidak berfungsi tambahan | 59–60 | Sedang | Sebagian kualitatif (posisi, fungsi) |
| C4.5.2 | Reference Mass Driver + Driver Ballast ≥ 82 kg | 60 | Tinggi | Batas numerik sederhana |
| C4.6 | Heat Hazard Mass Increase 5 kg (TTCS dengan Heat Hazard) atau 2 kg (LTCS/non-heat-hazard dalam Competition yang memiliki Heat Hazard) | 60 | Sedang | Bergantung pada status sesi dan deklarasi Heat Hazard |
| C2.5 | Nilai numerik batas berlaku apa adanya, terlepas dari jumlah desimal | 11 | Tinggi | Aturan semantik pembandingan (tanpa pembulatan) |

Kandidat yang **tidak** dipilih pada iterasi awal: C3 (aerodinamika — bergantung pada Reference Volumes/App. C2, gambar, dan pengecekan CAD), C5 (power unit — banyak referensi ke App. C4/C5 dan dokumen homologasi), C12–C13 (survival cell/struktur — bergantung pada gambar dan uji dinamik).

---

## 5. Ketentuan yang membutuhkan referensi silang

| Ketentuan | Referensi | Status ketersediaan |
|---|---|---|
| C2.3.1 | C10.7.6 (bagian yang terpasang pada Wheel Rim), ban, wheel rim | Tersedia di Section C |
| C2.3.3, C2.3.4, C2.3.5, C2.3.6 | Definisi plane XA, XC, XF, XR, XPU di C2.2; Legality Setup di C10.1 | Tersedia di Section C |
| C2.3.1, C2.3.3 | "Legality Setup" (C10.1) | Tersedia; definisinya bersifat prosedural dan tidak diubah menjadi fakta otomatis |
| C4.1 | Nominal Tyre Mass (App. C1, hlm. 193; prosedur C4.7) | Definisi tersedia, tetapi **nilai** ditetapkan penyedia ban dan dipublikasikan — tidak tersedia di workspace |
| C4.1 | Heat Hazard Mass Increase (C4.6) | Tersedia |
| C4.1 | Jenis sesi (Sprint Qualifying, Qualifying, sesi lain) | Istilah sesi didefinisikan di luar Section C (Section A / Sporting Regulations). Nilai sesi harus diberikan sebagai fakta konteks, tidak diasumsikan |
| C4.2 | Minimum Mass dari C4.1 | Tersedia; menjadi subgoal backward chaining |
| C4.3.2 | C4.5.2 (driver mass), C13.2 (impact test) | Tersedia di Section C |
| C4.5.2 | Prosedur FIA-F1-DOC-035 | **Tidak tersedia** — hanya dirujuk; tidak boleh diasumsikan |

**Konflik versi:** hanya satu versi Section C (Issue 21) dan satu versi Section A (Issue 03) tersedia. Tidak ada konflik antarversi yang dapat dianalisis. Issue 21 memuat penandaan perubahan terhadap Issue 20, tetapi Issue 20 tidak tersedia, sehingga perbedaan versi tidak diverifikasi.

---

## 6. Keterbatasan hasil ekstraksi

1. **Gambar, diagram, dan CAD drawing tidak diekstrak sebagai data terstruktur.** Appendix C2 (Reference Volumes/Surfaces: RV-FLOOR-BODY, RV-FLOOR-BIB, RV-FLOOR-FOOT, RV-FLOOR-SIDEWALL, RV-FLOOR-FENCE, dll.) dan Appendix C3 (Drawings) harus dibaca manual jika geometri ingin diperiksa.
2. **Tabel kompleks** (mis. daftar komponen, material, dimensi ban) terekstrak sebagai teks berurutan tanpa struktur kolom yang terjamin. Nilai dari tabel tidak dijadikan aturan pada iterasi ini.
3. **Warna teks** (hitam/merah muda/merah/oranye/hijau) yang menandai status perubahan hilang pada ekstraksi teks biasa. Untuk Issue 21, status perubahan terhadap Issue 20 tidak dapat direkonstruksi.
4. **Header/footer berulang** ikut terekstrak; sudah dipisahkan saat chunking berdasarkan pola.
5. **Nomor halaman** yang disimpan adalah indeks halaman PDF (1-based). Pada dokumen ini footer cetak (C1…C254 / A1…) berimpit dengan indeks PDF, sehingga rujukan halaman konsisten. Jika dokumen lain memiliki cover tanpa nomor, offset harus dicatat pada manifest.
6. **Superscript/subscript dan simbol matematis** (mis. mm², °, ±) sebagian kehilangan format; nilai numerik utama tetap terbaca.
7. Tidak ada halaman yang membutuhkan OCR pada keempat dokumen (`pages_needing_ocr` kosong).

---

## 7. Rekomendasi cakupan awal

**Subdomain yang dipilih: "Fundamental Dimensions dan Mass" (C2.3 dan C4).**

Alasan:
- Memiliki batas numerik eksplisit, satuan jelas (mm, kg), dan pasal yang dapat diverifikasi.
- Dapat direpresentasikan sebagai fakta terukur + aturan pertidaksamaan deterministik.
- Tidak memerlukan data rahasia tim (nilai dapat diukur/diberikan pengguna).
- Memuat contoh dependensi antaraturan yang sah: C4.2 membutuhkan hasil C4.1.
- Memuat contoh dependensi eksternal yang jelas: Nominal Tyre Mass (C4.7/App. C1) — cocok untuk menguji perilaku `UNKNOWN`.

**Lima aturan awal yang direkomendasikan** (detail di `research/rule_selection.md`):
1. `FIA26-C2.3.1-HALF-WIDTH` — batas 950 mm dari plane Y=0.
2. `FIA26-C2.3.3-WHEELBASE` — wheelbase ≤ 3400 mm.
3. `FIA26-C2.3.5-COCKPIT-POSITION` — jarak XA–XC dalam [1830, 2030] mm.
4. `FIA26-C4.1-MINIMUM-MASS` — Car Mass ≥ Minimum Mass (726/724 kg + Nominal Tyre Mass, plus Heat Hazard Mass Increase bila dideklarasikan).
5. `FIA26-C4.2-MASS-DISTRIBUTION` — distribusi massa front/rear ≥ 0,44/0,54 × Minimum Mass pada sesi Q/SQ.

Aturan `C2.3.4`, `C2.3.6`, `C4.5.2`, dan `C4.6` dipertahankan sebagai kandidat lanjutan dan tidak diaktifkan pada iterasi ini agar jumlah aturan tetap kecil, teruji, dan dapat dipertanggungjawabkan.

**Yang secara eksplisit TIDAK diklaim:** sistem tidak memeriksa kepatuhan mobil F1 secara keseluruhan, tidak mengevaluasi geometri 3D, dan tidak menggantikan pemeriksaan FIA technical delegate.
