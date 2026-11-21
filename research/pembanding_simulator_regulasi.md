# Pencarian awal pembanding simulator regulasi F1

Tanggal pencarian: 17 November 2026. Sasaran ide: penggemar F1 dan mahasiswa/anggota klub. Ide yang diperiksa: membandingkan dua versi regulasi teknis, memasukkan satu spesifikasi kendaraan, melihat hasil pemeriksaan pada kedua versi beserta alasan dan sumber.

## Cara pencarian dan batasnya

Pencarian web memakai kombinasi kata kunci bahasa Inggris: `F1 regulation change simulator wheelbase compare 2025 2026 interactive compliance`, `F1 regulation comparison tool simulate car dimensions regulations 2025 2026`, `github F1 regulations comparison rule changes compliance checker AI`, dan `F1 regulations interactive learning tool compare 2026 car dimensions rules`. Hasil dibaca dari halaman produk, deskripsi repositori, atau dokumentasi yang tersedia; fitur tidak diuji secara menyeluruh di aplikasi. Tidak menyebut suatu fitur pada sumber yang dibaca bukan bukti bahwa fitur itu tidak ada. Pencarian ini belum sistematis atau mencakup semua perangkat lunak privat, komersial, karya akademik, dan bahasa lain.

## Temuan

| Pembanding dan sumber | Kemampuan yang didokumentasikan | Relevansi dan hal yang belum terverifikasi |
|---|---|---|
| [Your Tech Director — Formula 1](https://www.formula1.com/en/latest/article/meet-your-tech-director-f1s-newest-ai-expert-for-the-biggest-rules-shake-up.2gNAcCO2qIp7q4bZaFXaPB.2gNAcCO2qIp7q4bZaFXaPB) | AI untuk penggemar yang menjelaskan regulasi 2026, berdasar regulasi FIA dan analisis tim teknis F1. | Target pengguna dan penjelasan sangat mirip. Artikel yang dibaca tidak menjelaskan pemeriksaan satu spesifikasi pengguna pada dua versi; belum diuji langsung. |
| [Interactive F1 — BadCodesGG](https://github.com/BadCodesGG/interactive-f1) | Mobil 3D interaktif; pemilih aturan 2022/2026, panel komponen dan sumber, serta simulasi sederhana wind tunnel. | Sangat dekat dalam aspek pembelajaran interaktif dan perbandingan era. README tidak mendokumentasikan pemeriksaan wheelbase yang diinput pengguna terhadap dua pasal; belum diuji langsung. |
| [F1 Analytics — Ignara Strategy Lab](https://app.ignarastrategies.com/f1) | Regulations Lab, ringkasan perubahan dan simulator konfigurasi dengan slider untuk proyeksi lap dan energi. | Sudah menggabungkan regulasi dan simulasi interaktif. Halaman yang dibaca menunjukkan simulasi performa, bukan rincian pemeriksaan satu ukuran pada dua versi; fungsi lengkap belum diuji. |
| [TechReg Analyst](https://github.com/Ishaan2510/f1-regulations-rag-system) | README menjelaskan pertanyaan bahasa alami untuk enam section regulasi F1 2026, retrieval, LLM, dan jawaban dengan sumber. | Menunjukkan bahwa tanya jawab RAG regulasi F1 sudah ada. README tidak mendokumentasikan pemeriksaan spesifikasi pada dua versi; tidak berarti fungsi tersebut pasti tidak ada. |
| [Car Explorer — tyredeg](https://tyredeg.com/car-explorer/) | Cuplikan halaman menjelaskan dimensi mobil 2026 dengan tautan pasal, serta membedakan nilai aturan dan interpretasi. | Dekat pada penjelasan dimensi dengan sumber. Halaman lengkap gagal dibuka pada saat pemeriksaan; interaksi dan perbandingan lintas versi belum terverifikasi. |
| [F1 2026 vs 2025 Lap Time Comparison — Bart Blockmans](https://bartblockmans.com/simulations/f1-2026-regulations) | Simulasi performa dan pengelolaan energi yang membandingkan mobil 2025 dan 2026. | Membuktikan simulasi dampak perubahan regulasi sudah ada dalam bentuk performa. Halaman tidak mendokumentasikan pemeriksaan kepatuhan input spesifikasi; belum diuji langsung. |
| [F1 rule version history — OpenSourceSports](https://www.opensourcesports.io/rules/formula-1-fia/changelog) | Halaman riwayat perubahan regulasi. | Pembanding untuk perbandingan versi; fungsi pemeriksaan input dan sumber pasal per versi belum diverifikasi. |

## Kesimpulan sementara

AI yang menjelaskan aturan F1 untuk penggemar, tampilan interaktif antar era, dan simulasi dampak perubahan regulasi **sudah ada**. Pencarian terbatas ini belum menemukan bukti publik yang mendokumentasikan kombinasi seluruh fungsi spesifik berikut: satu input dimensi pengguna, evaluasi deterministik terhadap dua versi regulasi F1, dan penjelasan dengan pasal/halaman serta kondisi masing-masing untuk pembelajaran. Ini bukan bukti bahwa kombinasi tersebut belum pernah dibuat.

Kandidat contoh: dokumen FIA 2025 Issue 3 pasal 3.4.2 menyatakan wheelbase maksimum 3600 mm, sedangkan 2026 Issue 21 C2.3.3 menyatakan 3400 mm pada Legality Setup. FIA juga menjelaskan pengurangan 200 mm dalam [penjelasan resminya](https://www.fia.com/news/f1s-new-era-everything-you-need-know-about-how-fia-making-formula-1-more-competitive-more). Sebelum implementasi, cek definisi, konteks, dan syarat setiap versi; 2025 Issue 3 tidak diklaim final. Sistem yang ada baru memiliki aturan 2026 dan belum memvalidasi model 2025.

## Langkah verifikasi lanjutan

1. Coba fitur pembanding secara langsung bila tersedia, dokumentasikan tanggal dan apa yang benar-benar bisa diuji.
2. Perluas pencarian ke Google Scholar, repositori, dan produk komersial dengan sinonim untuk rule comparison, what-if, dan compliance; catat kata kunci serta hasil.
3. Buat matriks yang membedakan: fitur ditemukan, belum ditemukan pada dokumentasi, dan belum diuji.
4. Periksa versi 2025 yang sesuai tujuan perbandingan, rumuskan aturan kedua versi, serta buat contoh uji batas 3400 dan 3600 mm termasuk data kosong dan satuan.
5. Gunakan rumusan sementara: “Berdasarkan pencarian awal yang terbatas, belum ditemukan produk publik yang mendokumentasikan kombinasi fungsi ini.” Hindari klaim pertama di dunia.

## Tindak lanjut 17 November 2026

### Uji langsung Ignara setelah percobaan ulang

Pada 17 November 2026 situs [Ignara F1 Analytics](https://app.ignarastrategies.com/f1) berhasil dibuka melalui browser. Panel **Car Simulator** dibuka, lalu tombol **Simulate Lap** dijalankan pada konfigurasi awal yang ditampilkan: Monza, ban Medium, aero/grip/power/deployment 50, dan bahan bakar 70 kg. Situs menampilkan proses simulasi kemudian hasil proyeksi 1:21.450, pembagian sektor, dan energi baterai. Angka ini adalah keluaran model situs, bukan pengukuran mobil nyata atau validasi akurasi.

Panel **Regulation Changes** juga dibuka; panel tersebut menampilkan ringkasan dan tabel perbandingan 2022–2025 dengan 2026, termasuk massa dan tenaga. Pada panel simulator yang diperiksa, input yang terlihat adalah sirkuit, ban, aero, grip, power unit, deployment, dan fuel; tidak terlihat input wheelbase atau hasil pemeriksaan spesifikasi terhadap dua pasal. Ini temuan terbatas pada panel yang diperiksa, bukan jaminan bahwa situs tidak memiliki fitur tersebut di tempat lain. Fitur lainnya dan variasi input belum diuji.

Uji langsung ini memperbarui status Ignara pada matriks sebelumnya: pembukaan panel dan menjalankan satu simulasi **berhasil**, sedangkan pengujian seluruh situs dan kebenaran model **belum dilakukan**. Catatan timeout di bawah menggambarkan percobaan sebelumnya.

Pencarian tambahan memakai `formula 1 regulations compliance 2025 2026 simulator dimensions`, `F1 regulation compliance checker car dimensions wheelbase software github`, `formula 1 regulation version comparison compliance AI what if`, `regulation change impact analysis rule based what if compliance decision support research`, `formula student rules rule checker car design compliance software`, serta pencarian repositori GitHub. Sumber ditelusuri melalui pencarian web dan halaman publik; ini bukan tinjauan sistematis, dan akses langsung ke Google Scholar belum terverifikasi.

**Temuan penting:** [Impact analysis of regulatory requirement changes on business process compliance](https://doi.org/10.1016/j.infsof.2026.108079), Information and Software Technology (2026), menjelaskan pendekatan yang menggabungkan LLM dan algoritma untuk menemukan perubahan persyaratan serta menjelaskan dampaknya terhadap kepatuhan proses bisnis. Karena itu, analisis dampak perubahan regulasi dan gabungan AI dengan aturan tidak dapat diklaim baru sebagai metode umum. Domain, target pembelajar, dan skenario spesifikasi F1 adalah kandidat perbedaan aplikasi yang masih harus diuji terhadap produk lain.

[Rules Delta: FIA F1](https://www.rulesdelta.com/leagues/fia-f1/) menyediakan katalog dokumen regulasi F1 beberapa tahun, termasuk teknis 2025 Issue 2 dan 2026 Issue 20. Katalog dan riwayat versi ditemukan; pemeriksaan satu nilai terhadap kedua versi dan penjelasan perbandingan belum diverifikasi.

### Matriks bukti pembanding

`Ditemukan` berarti terlihat pada sumber yang ditautkan; `tidak didokumentasikan` berarti tidak terlihat pada sumber yang diperiksa, bukan berarti tidak tersedia; `belum diuji` berarti fungsi tidak dijalankan langsung.

| Pembanding | Fitur ditemukan pada sumber | Fitur yang tidak didokumentasikan dalam sumber dibaca | Uji interaksi |
|---|---|---|---|
| Your Tech Director | Jawaban regulasi untuk penggemar, sumber FIA dan analisis teknis | Input wheelbase dan dua evaluasi berbasis versi | Belum diuji |
| Interactive F1 | Peralihan mobil dan angka 2022/2026, detail komponen beserta sumber, slider lain | Input wheelbase yang diperiksa pada dua aturan | Belum diuji |
| Ignara | Slider setup, simulasi proyeksi lap 2026, bagian perubahan regulasi | Pemeriksaan dimensi terhadap dua pasal | Satu simulasi default berhasil dijalankan pada 17 November 2026; fitur lain belum diuji |
| TechReg Analyst | Pertanyaan 2026, jawaban dan kutipan | Pemeriksaan satu dimensi pada 2025 dan 2026 | Belum diuji |
| Rules Delta | Katalog dokumen regulasi F1 beberapa versi | Pemeriksaan satu spesifikasi pada dua versi | Belum diuji |
| RC4PC, artikel riset | Analisis perubahan persyaratan dan efeknya pada kepatuhan proses bisnis | Kasus ukuran F1 untuk pembelajaran | Belum diuji |

Percobaan membuka Ignara melalui browser interaktif berakhir timeout; inventaris browser kemudian tidak menunjukkan tab yang terbuka. Karena itu tidak ada klaim bahwa slider/tombol telah berhasil dicoba. Halaman yang dapat dibaca melalui pencarian menjelaskan antarmukanya, tetapi bukan hasil pengujian langsung. Fitur yang tidak terdokumentasi pada tabel tetap merupakan pertanyaan terbuka.

### Pemeriksaan sumber untuk satu skenario

- **2025 Issue 3, pasal 3.4.2, halaman PDF/cetak 15:** jarak bidang XF=0 dan XR=0 tidak boleh melebihi 3600 mm. Pasal 2.11.1(a)(iv), halaman PDF/cetak 9, mendefinisikan bidang tersebut dengan roda lurus dan kendaraan pada Legality Ride Height, sebagaimana pasal 10.1.4. Dokumen ini adalah issue spesifik, bukan klaim bahwa semua issue 2025 identik; [arsip FIA](https://www.fia.com/regulation/category/110/technical-regulations?page=5) mencantumkan Issue 3 untuk teknis 2025.
- **2026 Issue 21, C2.3.3, halaman PDF/cetak 11:** jarak XF=0 dan XR=0 ≤ 3400 mm pada Legality Setup. C2.2(e), halaman 10, mendefinisikan bidang tersebut; Legality Setup dijelaskan pada C10.1. Istilah kondisi pengukuran berbeda dan harus ditampilkan sesuai sumber, tidak disamakan secara otomatis.
- Kedua limit bersifat inklusif. Dengan asumsi masing-masing fakta pengukuran relevan untuk kondisi dokumennya, berikut ekspektasi **perbandingan batas wheelbase saja**, bukan validasi seluruh kendaraan. Hasil di bawah merupakan kalkulasi manual dari teks, bukan hasil eksekusi implementasi lintas versi.

| Input | 2025 Issue 3 (≤3600 mm) | 2026 Issue 21 (≤3400 mm) |
|---|---|---|
| 3399 mm | Memenuhi batas | Memenuhi batas |
| 3400 mm | Memenuhi batas | Memenuhi batas |
| 3401 mm | Memenuhi batas | Melebihi batas |
| 3500 mm / 3,5 m | Memenuhi batas | Melebihi batas |
| 3600 mm | Memenuhi batas | Melebihi batas |
| 3601 mm | Melebihi batas | Melebihi batas |
| Kosong | Data tidak cukup | Data tidak cukup |
| Satuan tidak jelas atau nilai negatif | Input tidak valid | Input tidak valid |

Sistem saat ini hanya memiliki rule set Issue 21 2026; rule set 2025 belum dibuat atau diuji. Kasus tersebut adalah rancangan uji, bukan laporan pengujian lintas versi yang telah lulus. Pemetaan dari fakta pengguna ke kondisi pengukuran kedua tahun dan interpretasi pasal tetap memerlukan peninjauan.

### Keputusan sementara

Layak untuk **studi kelayakan prototipe pembelajaran** pada satu skenario wheelbase, dengan kontribusi berupa penerapan dan kombinasi fungsi yang dinyatakan secara terbatas, bukan klaim penemuan teknologi baru. Bukti yang ada belum membuktikan kebaruan absolut dan pengujian produk pembanding secara langsung masih tertunda akibat kendala browser. Sebelum mengunci arah, pastikan klaim pembeda diterima dan perluas pencarian/pengujian produk yang belum bisa diakses.

## Pencarian lanjutan 19 November 2026: menguji klaim pembeda

Pencarian diperluas ke produk F1, repositori GitHub, produk Formula Student, dan paper tentang RAG serta pemeriksaan kepatuhan berbasis skenario. Kata kunci mencakup `Formula 1 rulebook AI compliance checker`, `F1 regulation counterfactual learning`, `F1 regulation checker enter car dimensions`, `motorsport technical regulation minimal change`, dan `version-aware retrieval augmented generation regulation compliance`. README dan kode sumber dibaca bila tersedia. Pencarian web tidak menginventarisasi semua produk privat, bahasa, dan repositori yang tidak terindeks.

| Pembanding baru | Bukti yang diperiksa | Implikasi |
|---|---|---|
| [Formula Rules RAG](https://github.com/Messinavu10/formula-rules-rag), khususnya [kode alat pembanding](https://github.com/Messinavu10/formula-rules-rag/blob/main/src/rag/tools.py) | README menyatakan dukungan regulasi 2024–2026, jawaban RAG dengan sumber, dan perbandingan tahun. Kode `RegulationComparisonTool` memang memanggil pipeline RAG untuk dua tahun dan menampilkan dua jawaban beserta sumber. | **RAG + perbandingan pasal antar tahun sudah diimplementasikan**, jadi bukan novelty yang dapat diklaim sendiri. Kode yang diperiksa membandingkan teks/jawaban per pasal; tidak terlihat evaluasi numerik satu spesifikasi pengguna pada kedua tahun. Aplikasi belum dijalankan. |
| [F1 Garage](https://github.com/mathcrypto/f1-garage) | README mendokumentasikan AI pembelajar untuk fan, sumber FIA, tampilan mobil interaktif, dan mode penjelasan fan/engineer. | Sasaran fan, tutor AI, dan jawaban bersumber pun sudah memiliki pembanding dekat. Tidak terlihat pemeriksaan numerik dua versi pada README yang diperiksa. |
| [QuickSim](https://quicksim.dev/) | Cuplikan situs publik menyebut 178 pemeriksaan aturan FSAE/Formula Student 2027 dan kegagalan ditandai pada mobil. Halaman lengkap gagal diambil saat pencarian. | Pemeriksaan aturan desain mobil interaktif sudah ada di cabang motorsport lain. Detail keluaran, kualitas, dan fitur lain belum diverifikasi. |
| [FSUK 2027 Electric Vehicle Design Study](https://github.com/Thilac01/Formula_Student) | README menjelaskan dimensi dalam JSON, pemeriksaan numerik terpilih berdasar dokumen aturan, viewer, dan laporan engineering. | Input desain → hasil numerik berbasis aturan bukan metode baru di motorsport. Proyek ini untuk Formula Student dan tidak mendokumentasikan pembandingan dua issue F1. |
| [A Compliance Checking Framework Based on Retrieval Augmented Generation](https://aclanthology.org/2025.coling-main.178.pdf) dan [RegulaRAG](https://arxiv.org/abs/2608.16394) | Paper membahas RAG untuk pemeriksaan kepatuhan atau generasi skenario yang taat regulasi pada domain lain. | Kombinasi RAG dan pemeriksaan kepatuhan tidak baru sebagai metode umum. Kontribusi perlu dinyatakan pada alur dan evaluasi domain F1, bukan klaim algoritma baru. |

### Revisi klaim novelty

Klaim “AI F1 berbasis RAG”, “AI tutor untuk fan”, “membandingkan aturan 2025–2026”, dan “simulator regulasi” terlalu luas; masing-masing sudah memiliki pembanding. Klaim “belum pernah dibuat di dunia” **tidak dapat dibuktikan** dari pencarian ini.

Pembeda yang paling dapat dipertanggungjawabkan sebagai **rancangan produk penelitian**, dan belum terlihat bersama pada sumber pembanding yang diperiksa, adalah satu alur berikut: pengguna memasukkan ukuran contoh; sistem menerapkan aturan numerik dari **dua issue dokumen yang disebut eksplisit**, menunjukkan putusan dan jejak aturan untuk masing-masing; lalu memberi **perubahan minimum** yang diperlukan agar contoh melewati batas issue yang dipilih, sambil menampilkan pasal, halaman, satuan, dan perbedaan kondisi pengukuran. Penjelasan RAG dapat menambahkan konteks teknik dari literatur, tetapi putusan numerik dan nilai perubahan minimum dihitung oleh rule engine.

Contoh terbatas: input wheelbase 3500 mm memenuhi batas 3600 mm pada 2025 Issue 3 dan melebihi batas 3400 mm pada 2026 Issue 21; agar memenuhi **batas wheelbase saja** pada issue 2026 itu, nilai perlu berkurang setidaknya 100 mm. Ini bukan putusan kepatuhan seluruh mobil dan belum mengatasi perbedaan kondisi pengukuran kedua dokumen. Sistem saat ini belum memiliki aturan 2025, kalkulasi perubahan minimum, atau jawaban RAG generatif, sehingga pembeda tersebut **belum terimplementasi**.

Klaim yang aman untuk proposal: “Prototipe pembelajaran F1 yang menggabungkan RAG bersumber dengan evaluasi skenario numerik lintas issue dan penjelasan perubahan minimum. Berdasarkan pembanding publik yang diperiksa sampai 19 November 2026, kombinasi alur tersebut belum terdokumentasi pada satu produk yang sama.” Nyatakan sebagai *novelty pada penerapan dan alur pembelajaran*, bukan penemuan algoritma AI baru. Evaluasi sebaiknya membandingkan akurasi putusan dan keterlacakan sumber terhadap baseline RAG saja, menguji nilai batas, data kosong, satuan, serta pemahaman pengguna.
