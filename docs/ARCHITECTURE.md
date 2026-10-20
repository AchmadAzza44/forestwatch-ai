# Arsitektur
```text
React + Leaflet + Recharts (frontend)  --axios-->  FastAPI (backend)  --SQLAlchemy/GeoAlchemy2-->  PostgreSQL + PostGIS
                                                      |-- routers/disturbances  (list, geojson, detail)
                                                      |-- routers/dashboard     (stats, timeline, region, period-comparison, model-performance)
                                                      |-- routers/ml_inference  (predict, simulate-sentinel, model-info)
                                                      |-- ml/classifier         (pelatihan, evaluasi, baseline, inferensi)
                                                      |-- routers/export        (CSV, PDF dengan filter yang sama)
                                                      |-- auth                  (peran viewer/operator/admin via X-API-Key)
                                                      `-- gis/sentinel_mock     (generator spektral SIMULASI)

pipeline/ (offline)  Sentinel-2 L2A COG (AWS) -> komposit bebas awan -> NDVI/NBR -> kandidat perubahan -> GeoJSON + run.json
                     -> backend/import_detections.py -> database (kategori tidak_diketahui, sumber 'citra nyata')
```
- **Filter tunggal:** `dashboard.filtered_query` dipakai peta (GeoJSON) dan semua endpoint statistik, sehingga angka dashboard cocok dengan titik di peta.
- **Reproduksibilitas:** generator mock menerima `random.Random`; seeder memakai seed 42; simulasi per-lokasi diseed dari koordinat; pelatihan model memakai crc32 (bukan `hash()` yang diacak per proses).
- **Tanpa fitur tersembunyi:** `/ml/predict` mewajibkan 14 fitur; sebelumnya 6 fitur (SWIR/NIR/EVI) diisi konstanta diam-diam.
- **Batas:** model dilatih saat startup dari data simulasi (tidak ada artefak model tersimpan); tidak ada autentikasi; CORS terbatas pada localhost.

- **Dua sumber, satu skema:** kolom `data_source` membedakan 'Sentinel-2 L2A COG (citra nyata)' dari simulasi; filter `source` tersedia di semua endpoint. Kategori prediksi (`category`) dan hasil verifikasi operator (`verified_category`) adalah kolom terpisah.
- **Peran:** token statis pada header; autentikasi dasar untuk MVP, bukan sistem identitas (tanpa akun per pengguna, rotasi, atau pembatasan laju).
