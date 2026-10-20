# Pipeline GIS (Sentinel-2 nyata) - deteksi INDIKASI perubahan

Pipeline offline (PRD bagian 8: "pipeline pengolahan citra dapat dijalankan offline") yang membaca **citra Sentinel-2 L2A nyata** dan menghasilkan kandidat lokasi perubahan vegetasi. Ia memisahkan **deteksi perubahan** dari **klasifikasi penyebab**: hanya deteksi yang dilakukan pada data nyata.

## Menjalankan
```bash
pip install -r pipeline/requirements.txt
python -m pipeline.run_detection --name ikn_2020_2023 --tile 50MMD --aoi 116.55 -1.20 116.85 -0.95 \
    --before 2020-08-01 2020-10-31 --after 2023-08-01 2023-10-31 --scenes 8 --max-cloud 90
cd backend && python import_detections.py ../data/detections/ikn_2020_2023     # muat ke database
python -m pytest tests_pipeline -q                                              # 9 tes
```
Butuh akses HTTPS ke `sentinel-cogs.s3.us-west-2.amazonaws.com` (publik, tanpa akun). Satu eksekusi ~1-2 menit untuk AOI 33 x 28 km.

## Sumber data
Sentinel-2 L2A COG, AWS Open Data (bucket `sentinel-cogs`, https://registry.opendata.aws/sentinel-2-l2a-cogs/), data Copernicus Sentinel (ESA). Katalog STAC tidak dipakai karena tidak dapat dijangkau dari lingkungan pengembangan; scene dicari lewat listing S3 dan metadata item JSON (`eo:cloud_cover`). Periksa syarat penggunaan Copernicus sebelum redistribusi.

## Langkah
1. **Pilih scene:** per periode, 8 scene berawan tile terendah (satu per tanggal).
2. **Baca AOI** (jendela COG, tanpa mengunduh seluruh scene) pada grid 20 m: B04 (merah), B08 (NIR), B12 (SWIR2), SCL. B04/B08 (10 m) dirata-ratakan ke 20 m.
3. **Masking awan:** hanya SCL 4-7 (vegetasi, non-vegetasi, air, tak terklasifikasi) dianggap valid; awan, bayangan, cirrus, area gelap, jenuh dibuang, **diperluas 3 piksel (60 m)** karena tepi awan/bayangan sering lolos dari SCL.
4. **Komposit median** per periode dari pengamatan valid; jumlah pengamatan valid per piksel dicatat; piksel tanpa pengamatan valid **tidak dianalisis** (tidak dianggap tidak berubah).
5. **Indeks:** NDVI = (NIR-Merah)/(NIR+Merah); NBR = (NIR-SWIR2)/(NIR+SWIR2).
6. **Kandidat perubahan:** NDVI awal >= 0,70 (vegetasi rapat), dNBR (awal-akhir) >= 0,27, dNDVI <= -0,20; pembukaan morfologi 3x3; gugus 8-tetangga; gugus < 1 ha dibuang.
7. **Keluaran** (`data/detections/<nama>/`): `detections.geojson` (poligon + luas, dNBR, dNDVI, NDVI awal/akhir), `run.json` (provenance: ID dan tanggal scene, awan, parameter, hash GeoJSON, versi, batasan), `preview.png` (pemeriksaan visual).
Semua ambang adalah **pilihan analis, bukan standar baku**, dan dicatat tiap eksekusi.

## Hasil eksekusi nyata: IKN, Kalimantan Timur (tile 50MMD), AOI 116,55-116,85 BT, 1,20-0,95 LS
- Periode awal 1 Agu-31 Okt 2020 (8 scene, awan tile 23-43%); periode akhir 1 Agu-31 Okt 2023 (8 scene, awan tile 18-32%).
- Piksel teramati pada kedua periode: **81,2%**. Vegetasi rapat awal: 48.729 ha. **Kandidat perubahan: 341 gugus, 1.560 ha (3,2% dari vegetasi rapat awal)**; median 2,1 ha, 35 gugus >= 10 ha (754 ha), terbesar 127 ha; dNBR rata-rata 0,52.
- Pemeriksaan visual (`preview.png`): pada komposit akhir tampak jaringan jalan di bagian utara AOI yang konsisten dengan pembukaan lahan pembangunan kawasan; kontur kandidat mengikuti area itu.

## Keterbatasan yang diketahui (wajib dibaca)
- Ini **indikasi perubahan vegetasi**, bukan deforestasi terverifikasi dan **bukan penyebab**. Tidak ada validasi terhadap data referensi independen atau verifikasi lapangan; **tidak ada angka akurasi** untuk deteksi ini.
- "Hutan" didefinisikan dari NDVI >= 0,70, bukan dari peta tutupan hutan resmi; perkebunan, semak rapat, dan mangrove dapat ikut terhitung.
- **Pola positif palsu yang teramati:** sebagian gugus memanjang di tepi sungai/estuari (kemungkinan efek pasang-surut, kelembapan, atau ketidaksejajaran) dan sebagian berada di dekat area tanpa pengamatan valid. Gugus seperti ini perlu dicek dulu sebelum dipakai.
- Komposit median dari scene bulan berbeda dalam satu periode dapat mencampur fenologi; AOI hanya satu lokasi dan dua periode.
- Cakupan 81,2%: 18,8% piksel tidak dapat dinilai (awan persisten, buffer awan, tepi air), sehingga perubahan di sana tidak terdeteksi (negatif palsu).
- Kategori penyebab **tidak** diberikan pada data nyata: classifier proyek dilatih pada data sintetis dan tidak valid untuk citra nyata. Semua indikasi nyata berkategori `tidak_diketahui` dan perlu verifikasi.
- Sentinel-1 (radar), masking awan berbasis model, dan koreksi topografi belum diterapkan.
