# Rule Selection — Fundamental Dimensions & Mass

Sumber tunggal: `FIA 2026 Formula One Regulations — Section C [Technical]`, Issue 21, 19-10-2026.
Halaman yang dirujuk adalah indeks halaman PDF dan berimpit dengan footer cetak (C1–C254).

## Prinsip representasi

- Setiap aturan adalah data JSON (`knowledge_base/rules/rules.json`), bukan kode dan bukan hasil generasi LLM.
- Setiap fakta memiliki nama, nilai, satuan, dan sumber (input pengguna, pengukuran, atau turunan).
- Perbandingan dilakukan apa adanya tanpa pembulatan, sesuai **C2.5**: "Any numerical values specified in these Regulations as limits (maxima or minima), will be considered to be the limits regardless of the decimals quoted."
- Tiga status inferensi: `TRUE` (terbukti memenuhi), `FALSE` (terbukti melanggar), `UNKNOWN` (fakta/bukti belum cukup). `UNKNOWN` tidak pernah diperlakukan sebagai `FALSE`.
- Aturan hanya aktif jika `status = "active"` dan `human_approved = true`. Saat ini semua aturan berstatus **`reviewed`** dan berjalan dalam demo mode; belum ada sign-off manusia. Log verifikasi ada di `research/rule_validation_log.md`.
- Status validasi di sini berarti **teks pasal, satuan, dan operator telah diperiksa ulang terhadap PDF FIA yang disediakan**; ini bukan sertifikasi dari FIA dan bukan persetujuan manusia.

---

## RULE 1 — `FIA26-C2.3.1-HALF-WIDTH`

**Pasal:** C2.3.1 Width (hlm. 10)

> "Except for the tyres, the Wheel Rims, and parts attached to the Wheel Rims as defined in Article C10.7.6, no part of the car may lie more than 950mm from the plane Y=0 at Legality Setup."

**Persyaratan yang diperiksa:** jarak maksimum setiap bagian mobil dari plane simetri Y=0 tidak melebihi 950 mm, dengan pengecualian ban, wheel rim, dan komponen yang terpasang pada rim.

**Fakta yang dibutuhkan:**
| Fakta | Satuan | Arti |
|---|---|---|
| `max_half_width_excluding_tyres_and_rims` | mm | Nilai maksimum \|Y\| seluruh bagian mobil yang tidak dikecualikan, diukur pada Legality Setup |

**Terpenuhi (TRUE):** nilai ≤ 950 mm.
**Dilanggar (FALSE):** nilai > 950 mm.
**Belum dapat ditentukan (UNKNOWN):** fakta tidak diberikan, atau komponen yang dikecualikan tidak dapat dipisahkan dari pengukuran (fakta dianggap tidak valid).

**Alasan dipilih:** batas numerik tunggal, pengecualian dinyatakan eksplisit di pasal, dan tidak membutuhkan geometri CAD bila pengguna memberikan nilai hasil pengukuran yang sudah mengecualikan ban/rim.

**Dependensi:** C10.7.6 (definisi bagian yang terpasang pada Wheel Rim) tersedia di Section C; tidak diubah menjadi aturan, hanya menjadi syarat penamaan fakta. "Legality Setup" didefinisikan di C10.1 dan diasumsikan sebagai konteks pengukuran fakta.

---

## RULE 2 — `FIA26-C2.3.3-WHEELBASE`

**Pasal:** C2.3.3 Wheelbase (hlm. 11)

> "The distance between the planes XF = 0 and XR = 0 must be less than or equal to 3400mm at Legality Setup."

**Persyaratan:** wheelbase (jarak plane XF=0 ke XR=0) ≤ 3400 mm.

**Fakta:** `wheelbase` (mm).

**Terpenuhi:** ≤ 3400 mm. **Dilanggar:** > 3400 mm. **UNKNOWN:** fakta tidak ada.

**Alasan dipilih:** satu pertidaksamaan dengan satuan eksplisit, mudah diuji dengan nilai batas (3400 lolos, 3400,1 gagal).

**Dependensi:** definisi plane XF/XR di C2.2 (tersedia). Nilai berasal dari pengukuran pengguna.

---

## RULE 3 — `FIA26-C2.3.5-COCKPIT-POSITION`

**Pasal:** C2.3.5 Cockpit Position (hlm. 11)

> "The distance between XA = 0 and XC = 0 must be greater than or equal to 1830mm and less than or equal to 2030mm."

**Persyaratan:** jarak XA=0 ke XC=0 berada dalam interval tertutup [1830, 2030] mm.

**Fakta:** `cockpit_position_distance` (mm), yaitu jarak XA=0 ke XC=0.

**Terpenuhi:** 1830 ≤ nilai ≤ 2030 mm. **Dilanggar:** nilai < 1830 mm atau > 2030 mm. **UNKNOWN:** fakta tidak ada.

**Alasan dipilih:** menguji aturan dengan dua batas (lower dan upper) sekaligus, dan menunjukkan bahwa satu aturan dapat memiliki lebih dari satu kondisi yang harus dipenuhi bersamaan.

**Dependensi:** XA=0 adalah plane pada batas depan Survival Cell dan XC=0 adalah plane di belakang Cockpit (C2.2). Nilai diberikan pengguna.

---

## RULE 4 — `FIA26-C4.1-MINIMUM-MASS`

**Pasal:** C4.1 Minimum mass (hlm. 59)

> "During the Sprint Qualifying and Qualifying sessions, The Minimum Mass is 726kg plus the Nominal Tyre Mass. In all other sessions, the Minimum Mass is 724kg plus the Nominal Tyre Mass."
>
> "At all times during the Competition, Car Mass must not be less than the Minimum Mass."
>
> "When a Heat Hazard is declared, the Minimum Mass will be increased by the Heat Hazard Mass Increase."

**Persyaratan:** Car Mass ≥ Minimum Mass, dengan
`Minimum Mass = base(session) + Nominal Tyre Mass + Heat Hazard Mass Increase (jika Heat Hazard dideklarasikan)`.

**Fakta yang dibutuhkan:**
| Fakta | Satuan/tipe | Arti |
|---|---|---|
| `car_mass` | kg | Massa mobil saat diperiksa |
| `nominal_tyre_mass` | kg | Nominal Tyre Mass sesuai definisi App. C1 dan prosedur C4.7 |
| `session_type` | string | `"SQ"` (Sprint Qualifying), `"Q"` (Qualifying), atau sesi lain |
| `session_category` | string | `"TTCS"` atau `"LTCS"` (dipakai oleh C4.6) |
| `heat_hazard_declared` | boolean | Heat Hazard dideklarasikan untuk sesi ini |
| `competition_heat_hazard_declared` | boolean | Heat Hazard dideklarasikan untuk salah satu sesi dalam Competition |

**Nilai turunan (subgoal):**
- `base_minimum_mass` = 726 kg jika `session_type` ∈ {SQ, Q}; 724 kg untuk sesi lain.
- `heat_hazard_mass_increase` mengikuti C4.6:
  - 5 kg jika `session_category = TTCS` dan `heat_hazard_declared = true`;
  - 2 kg jika `competition_heat_hazard_declared = true` dan sesi adalah LTCS, atau TTCS yang Heat Hazard sesinya tidak dideklarasikan;
  - 0 kg jika tidak ada Heat Hazard yang dideklarasikan pada tingkat Competition maupun sesi;
  - kombinasi yang tidak konsisten (mis. Competition tidak memiliki Heat Hazard tetapi sesi menyatakan ada) tidak menghasilkan nilai → `UNKNOWN`.
- `minimum_mass` = `base_minimum_mass` + `nominal_tyre_mass` + `heat_hazard_mass_increase`.

**Terpenuhi (TRUE):** `car_mass` ≥ `minimum_mass`.
**Dilanggar (FALSE):** `car_mass` < `minimum_mass`.
**UNKNOWN:** salah satu fakta di atas tidak tersedia, atau kombinasi Heat Hazard tidak konsisten.

**Alasan dipilih:** aturan inti Article C4, menunjukkan perhitungan turunan (subgoal), percabangan berdasarkan konteks sesi, dan dependensi eksternal yang jujur: nilai Nominal Tyre Mass **tidak ditetapkan sebagai angka tetap** dalam regulasi, melainkan diukur penyedia ban dan dipublikasikan (C4.7; App. C1 hlm. 193). Karena itu nilai tersebut wajib menjadi fakta input, bukan konstanta. Penanganan C4.6 dibuat eksplisit agar sistem tidak menyederhanakan 5 kg/2 kg menjadi satu angka.

**Dependensi:**
- C4.6 Heat Hazard Mass Increase (tersedia; 5 kg untuk TTCS dengan Heat Hazard, 2 kg untuk LTCS/TTCS tanpa Heat Hazard sesi ketika Competition memiliki Heat Hazard).
- C4.7 + App. C1 "Nominal Tyre Mass" (definisi tersedia; **nilai tidak tersedia di workspace**).
- Definisi jenis sesi dan kategori sesi berada di luar Section C. Sistem tidak mengasumsikan nilainya; jika tidak diberikan → `UNKNOWN`.

---

## RULE 5 — `FIA26-C4.2-MASS-DISTRIBUTION`

**Pasal:** C4.2 Mass distribution (hlm. 59)

> "At all times during the Qualifying and Sprint Qualifying Sessions, with the car resting on a horizontal plane:
> i. the mass measured at the front axle must not be less than the Minimum Mass specified in Article C4.1 factored by 0.44.
> ii. the mass measured at the rear axle must not be less than the Minimum Mass specified in Article C4.1 factored by 0.54."
>
> "If, when required for checking, a Heat Hazard has been declared, the increase in mass will not be considered."

**Persyaratan:** hanya pada sesi Q/SQ:
- `front_axle_mass` ≥ 0,44 × Minimum Mass, dan
- `rear_axle_mass` ≥ 0,54 × Minimum Mass,
dengan Minimum Mass **tanpa** penambahan Heat Hazard.

**Fakta yang dibutuhkan:**
| Fakta | Satuan/tipe | Arti |
|---|---|---|
| `front_axle_mass` | kg | Massa terukur pada front axle |
| `rear_axle_mass` | kg | Massa terukur pada rear axle |
| `session_type` | string | Harus `"Q"` atau `"SQ"` agar aturan berlaku |
| `nominal_tyre_mass` | kg | Untuk menghitung Minimum Mass (lewat subgoal C4.1) |

**Nilai turunan:** `minimum_mass_excluding_heat_hazard` = `base_minimum_mass` + `nominal_tyre_mass`.

**Terpenuhi (TRUE):** kedua pertidaksamaan terpenuhi.
**Dilanggar (FALSE):** salah satu pertidaksamaan tidak terpenuhi.
**UNKNOWN:**
- salah satu massa atau `nominal_tyre_mass` tidak tersedia;
- `session_type` tidak diketahui;
- `session_type` diketahui tetapi bukan Q/SQ → aturan **tidak berlaku**; hasil dilaporkan `UNKNOWN` dengan alasan `not_applicable` (bukan `TRUE`).

**Alasan dipilih:** menunjukkan hubungan antaraturan (C4.2 memakai hasil perhitungan C4.1) dan penanganan konteks penerapan. Juga menunjukkan detail penting: penambahan massa Heat Hazard **tidak** diperhitungkan pada C4.2, sehingga subgoal yang dipakai berbeda dari C4.1.

**Dependensi:** C4.1 (subgoal), C4.6 (dikecualikan pada C4.2).

---

## Kandidat yang belum diaktifkan

| Kandidat | Alasan belum diaktifkan |
|---|---|
| C2.3.4 Front Wheel Position | Valid dan deterministik, tetapi menambah aturan tanpa menambah jenis inferensi baru; disimpan untuk pengembangan berikutnya. |
| C2.3.6 Rear Bulkhead Position | Sama seperti C2.3.4; satu pertidaksamaan tambahan. |
| C4.5.2 Driver Mass | Bergantung pada prosedur FIA-F1-DOC-035 yang tidak tersedia; hanya batas 82 kg yang bisa diuji. |
| C4.3.x Ballast | Sebagian kualitatif (posisi, segel, fungsi tambahan) dan membutuhkan bukti desain. |
| C3 Aerodynamic Components | Membutuhkan Reference Volumes (App. C2), gambar (App. C3), dan pemeriksaan CAD; tidak dapat diuji deterministik dari fakta sederhana. |
| C5 Power Unit, C12/C13 Safety Structures | Sangat bergantung pada dokumen homologasi, gambar, dan pengujian fisik. |

---

## Pemetaan fakta → aturan

| Fakta | Dipakai oleh |
|---|---|
| `max_half_width_excluding_tyres_and_rims` | RULE 1 |
| `wheelbase` | RULE 2 |
| `cockpit_position_distance` | RULE 3 |
| `car_mass` | RULE 4 |
| `nominal_tyre_mass` | RULE 4, RULE 5 |
| `session_type` | RULE 4, RULE 5 |
| `session_category` | RULE 4 (C4.6 Heat Hazard Mass Increase) |
| `heat_hazard_declared` | RULE 4 (C4.6 Heat Hazard Mass Increase) |
| `competition_heat_hazard_declared` | RULE 4 (C4.6 Heat Hazard Mass Increase) |
| `front_axle_mass`, `rear_axle_mass` | RULE 5 |

Semua fakta di atas hanya bermakna bila diukur pada kondisi yang disyaratkan pasal (Legality Setup untuk dimensi; mobil diam di bidang horizontal untuk distribusi massa). Sistem mencatat konteks ini di penjelasan, tetapi tidak memverifikasinya secara fisik.
