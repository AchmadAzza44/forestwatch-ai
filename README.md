# ForestWatch AI

Web GIS untuk melihat **indikasi** gangguan hutan dan **prediksi model** kemungkinan penyebabnya (pertanian, penebangan, pertambangan, kebakaran, alami, tidak diketahui). PRD: `../PRD_Tiga_Implementasi_Informatika.md` dan PRD ForestWatch (bagian I).

> **Penting:** sistem memuat **dua jenis data yang selalu diberi label**: (1) **citra nyata** - indikasi perubahan vegetasi hasil `pipeline/` dari Sentinel-2 L2A (1 AOI di sekitar IKN, 2020 vs 2023); penyebab **belum diklasifikasi**; (2) **simulasi** - data buatan (`backend/gis/sentinel_mock.py`) untuk demonstrasi model. Classifier dilatih pada data sintetis dan **tidak** dijalankan pada citra nyata. Hasil bukan bukti penyebab deforestasi, bukan peringatan dini, dan metrik model bukan akurasi dunia nyata. Deteksi perubahan dan klasifikasi penyebab adalah dua hal berbeda; penyebab hanya "terverifikasi" bila operator memverifikasinya.


## Struktur folder
```text
backend/              # FastAPI: routers/ (disturbances, dashboard, ml_inference, export), ml/, gis/ (generator simulasi), auth.py, import_detections.py, tests/ (33 tes)
frontend/             # React + Vite + Leaflet + Recharts (peta, dashboard, analisis)
pipeline/             # pipeline GIS offline Sentinel-2 nyata (s2_cog, change_detection, run_detection)
tests_pipeline/       # 9 tes pipeline
data/detections/      # hasil deteksi nyata (GeoJSON, run.json provenance, preview.png)
db/                   # init.sql (ekstensi PostGIS)
docker-compose.yml    # PostGIS + backend + frontend (belum diuji)
docs/                 # PIPELINE, METHODOLOGY, ARCHITECTURE, TEST_PLAN, PROGRESS, LAPORAN, screenshots/
```

## Menjalankan
**Docker (PostGIS + API + UI):** `docker compose up --build` lalu buka http://localhost:3000 (API: http://localhost:8000/api/docs). Ganti kredensial pada `docker-compose.yml`/`.env.example` di luar laptop pengembangan. *Jalur Docker/PostGIS belum saya uji dalam sesi ini* (tidak ada Docker); yang diuji: API pada SQLite dan frontend dengan Vite.

**Lokal tanpa Docker:** butuh PostgreSQL + PostGIS dan `DATABASE_URL`.
```bash
cd backend && pip install -r requirements.txt && uvicorn main:app --reload      # seeder 200 data simulasi (seed 42) saat DB kosong
cd frontend && npm ci && npm run dev                                           # http://localhost:5173
```

## Pengujian
```bash
cd backend && python -m pytest -q      # 33 tes, SQLite, tanpa PostGIS
python -m pytest tests_pipeline -q     # 9 tes pipeline
cd frontend && npm run build && npm run lint
```
Rencana dan hasil: `docs/TEST_PLAN.md`. Pipeline Sentinel-2: `docs/PIPELINE.md`. Metodologi dan keterbatasan: `docs/METHODOLOGY.md`. Arsitektur: `docs/ARCHITECTURE.md`. Laporan: `docs/LAPORAN.md`. Screenshot: `docs/screenshots/`.

**Peran:** tanpa token = pembaca. Setel `OPERATOR_TOKEN` / `ADMIN_TOKEN` (lihat `.env.example`) lalu isi token di sidebar untuk memverifikasi indikasi. Token kosong = peran dinonaktifkan.
