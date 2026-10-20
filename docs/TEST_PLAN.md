# Test Plan
Backend: `cd backend && python -m pytest -q` -> **33 lulus** (SQLite; kolom geometri diganti teks hanya pada tes). Pipeline: `python -m pytest tests_pipeline -q` -> **9 lulus**. Frontend: `npm run build` sukses; `npm run lint` 0 error.

| Area | Kasus | Tes |
|---|---|---|
| ML | pelatihan identik di PYTHONHASHSEED berbeda; baseline dan confusion matrix; fitur wajib; rentang input; SWIR berpengaruh; keyakinan rendah -> perlu verifikasi | test_forestwatch.py |
| Simulasi | dapat diulang; periode salah ditolak; generator berseed | test_forestwatch.py |
| Data | kategori tersimpan = keluaran model; seeder dapat diulang; kesesuaian model-simulasi > 0,5 | test_forestwatch.py |
| Filter | statistik, tren, wilayah, GeoJSON, CSV memakai filter yang sama; selisih dua periode; parameter tidak valid | test_forestwatch.py, test_real_detection.py |
| Sumber nyata | impor: kategori `tidak_diketahui`, tidak terverifikasi, tanpa probabilitas; idempoten; filter `source` di semua endpoint | test_real_detection.py |
| Peran | viewer 403, token salah 401, operator 200, kategori tidak valid 422, id tak ada 404, token kosong = peran nonaktif; prediksi terpisah dari verifikasi | test_real_detection.py |
| Verifikasi | ringkasan kesesuaian mencatat catatan "bukan akurasi" | test_real_detection.py |
| Ekspor | CSV = jumlah statistik; PDF valid | test_real_detection.py |
| Penjelasan | 5 fitur teratas, terurut, berlabel "bukan SHAP" | test_real_detection.py |
| Notifikasi | `/disturbances/new` menghitung indikasi sejak waktu tertentu | test_real_detection.py |
| Pipeline | rumus indeks; kelas SCL valid; komposit mengabaikan awan; buffer awan 3 piksel (49 piksel dari 1); deteksi lahan terbuka 16 ha pada data buatan berjawaban pasti; derau 1 piksel dibuang; non-hutan tidak dilaporkan; piksel tanpa pengamatan tidak pernah terdeteksi; ambang menentukan hasil | test_change_detection.py |

## Verifikasi di browser (Playwright/Chromium) dengan data nyata + simulasi
Filter "Citra nyata" -> 341 titik; popup menampilkan sumber "Citra Sentinel-2 nyata", NDVI 0,789 -> 0,173, dan peringatan "penyebab BELUM diklasifikasi"; operator (token di sidebar) menyimpan verifikasi -> `validation-summary` mencatat 1 verifikasi; ekspor CSV berisi 341 baris hanya dari sumber nyata; PDF terunduh valid; halaman Analisis menampilkan penjelasan lokal. Tidak ada galat JavaScript. Backend dimatikan -> dashboard menampilkan pesan kegagalan tanpa data cadangan.

## Temuan dari pengujian ini yang diperbaiki
Gugus pada tepi awan (haze/bayangan lolos SCL) -> buffer 3 piksel; label provinsi ganda ("Kalimantan" x2); peran tidak tampil dari token tersimpan; peta tidak mengarah ke hasil setelah filter.

**Tidak diuji:** Docker Compose, PostgreSQL/PostGIS nyata, uji performa dan beban, usability dengan pengguna, aksesibilitas keyboard peta, tes komponen React otomatis, validasi hasil deteksi terhadap referensi independen.
