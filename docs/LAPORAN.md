# Laporan Singkat - ForestWatch AI
**Materi:** GIS, Machine Learning, HCI & visualisasi data, deteksi deforestasi dengan citra satelit. PRD: ForestWatch AI (Bagian I-III).

## Hubungan fitur dengan materi
| Materi | Implementasi | Bukti |
|---|---|---|
| GIS dalam industri: lokasi + basis data + analisis + komunikasi hasil | pipeline citra -> GeoJSON -> PostGIS/DB -> API -> peta | `docs/PIPELINE.md`, screenshot 01-02 |
| Sentinel-2 (optik): vegetasi, awan | NDVI/NBR, SCL masking, komposit median, buffer awan | `tests_pipeline/` |
| Deteksi perubahan != klasifikasi penyebab | dua jalur terpisah; data nyata hanya dideteksi (`tidak_diketahui`) | `docs/METHODOLOGY.md` |
| Tahapan ML: data, split, evaluasi, bias/overfitting | baseline, metrik per kelas, catatan optimistis, penjelasan oklusi | `docs/TEST_PLAN.md` |
| HCI/visualisasi: legenda, filter, sumber dan ketidakpastian tampil | label sumber, "perlu verifikasi", peringatan di popup, error state jujur | screenshot 02-04 |
| Validasi manusia | peran operator, verifikasi terpisah dari prediksi, ringkasan kesesuaian | `test_real_detection.py` |

## Hasil nyata
- **Citra nyata:** 1 AOI (33 x 28 km di sekitar IKN, 2020 vs 2023, 8 scene per periode): 81,2% piksel teramati, **341 kandidat perubahan = 1.560 ha (3,2% dari 48.729 ha vegetasi rapat awal)**; 35 gugus >= 10 ha. Tanpa validasi referensi, tanpa angka akurasi.
- **Model (sintetis):** akurasi 0,76 / macro-F1 0,76; regresi logistik setara (0,77); kelas mayoritas 0,17. Angka optimistis.
- 33 tes backend + 9 tes pipeline lulus; verifikasi alur di browser.
- Pelanggaran PRD yang ditemukan dan diperbaiki: data/metrik palsu di UI, fitur ML diisi konstanta diam-diam, kategori disimpan dari ground truth, build frontend gagal, halaman peta crash.

## Keterbatasan
Hanya satu AOI dan dua periode; tanpa validasi lapangan; classifier sintetis tidak berlaku pada citra nyata; label penyebab nyata belum ada; Sentinel-1/CNN belum; token statis bukan sistem identitas; Docker/PostGIS belum diuji. Pola positif palsu pada tepi sungai/estuari tercatat di `PIPELINE.md`.

## Demonstrasi
Jalankan backend dan frontend -> filter "Citra nyata" -> klik titik -> baca popup -> (operator) verifikasi -> Dashboard -> ekspor CSV/PDF -> Analisis ML -> Jalankan Klasifikasi -> penjelasan.
