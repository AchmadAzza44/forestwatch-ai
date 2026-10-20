# Metodologi dan Keterbatasan

## Tiga hal yang dibedakan (PRD bagian 7)
1. **Indikasi perubahan** - penurunan NDVI/NBR antara dua periode. **Pada citra Sentinel-2 nyata** (lihat `PIPELINE.md`) dan pada data simulasi.
2. **Prediksi kategori penyebab** - keluaran Random Forest + skor keyakinan.
3. **Penyebab terverifikasi** - hanya ada bila **operator** menyimpan `verified_category` (kolom terpisah dari prediksi model). Pada data bawaan hanya verifikasi yang dimasukkan secara manual; data simulasi memiliki penanda `is_validated` acak dari seeder yang **bukan** verifikasi nyata.

## Data
**Citra nyata:** satu AOI Sentinel-2 L2A (IKN, 2020 vs 2023) lewat `pipeline/`; rincian, ambang, hasil, dan keterbatasan ada di `PIPELINE.md`. **Simulasi:** scene Sentinel-1/2 dibangkitkan `gis/sentinel_mock.py` dari rentang nilai per kelas. Nilai tiap band diundi seragam + derau 5%. Data simulasi bukan citra, bukan statistik nyata, dan tidak mewakili tutupan awan, topografi, atau variasi musiman.

## Model
Random Forest (150 pohon, `class_weight=balanced`) pada 17 fitur (NDVI/NBR/EVI sebelum-sesudah dan selisih, B4/B8/B11/B12, SAR VV, awan, luas). Data latih (600 sampel, 100/kelas) berasal dari generator yang sama dengan data demo. Kelas "tidak_diketahui" dipetakan ke profil `degraded_forest`; selain itu prediksi dengan keyakinan < 0,45 dipaksa menjadi "tidak_diketahui".

Hasil evaluasi pada split 75/25 (seed 42, 150 uji): accuracy 0,76, macro-F1 0,76. Pembanding: regresi logistik 0,77 dan kelas mayoritas 0,17. Artinya Random Forest **tidak lebih baik** dari baseline linear pada data ini, dan kelas `pertanian` vs `alami` saling tumpang tindih. Angka ini **optimistis**: pelatihan dan pengujian dari generator yang sama, sampel i.i.d., tanpa pemisahan spasial/temporal.

## Keterbatasan
- Tidak ada validasi terhadap data lapangan atau dataset penyebab nyata; target akurasi sengaja tidak ditetapkan (PRD bagian 12). Classifier **tidak dijalankan** pada citra nyata karena dilatih pada distribusi sintetis.
- Kesesuaian prediksi dengan `simulated_truth` pada data demo hanya menguji konsistensi internal.
- Skor keyakinan Random Forest bukan probabilitas terkalibrasi.
- Pengujian pada data nyata memerlukan: citra Sentinel dengan masking awan, label penyebab bertanggung jawab, pembagian train/test per lokasi dan periode (hindari kebocoran), dan metrik per kelas.
