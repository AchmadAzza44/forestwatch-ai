# Progress
## M0 Foundation
- [x] Struktur, Dockerfile backend/frontend, `.env.example`
## M1 Data
- [x] Generator simulasi dapat direproduksi
- [x] **Citra Sentinel-2 nyata** (1 AOI x 2 periode) dengan provenance
- [ ] Label penyebab nyata dan dataset latih nyata (belum ada sumber berlabel yang sah)
## M2 Core MVP
- [x] Peta, filter (termasuk sumber data), dashboard, klasifikasi (simulasi), kategori "tidak diketahui"
- [x] Pipeline deteksi perubahan (nyata); perbandingan dua periode
- [x] Error state tanpa data palsu
## M3 Evaluation
- [x] Metrik per kelas, confusion matrix, baseline (sintetis)
- [x] 33 + 9 tes; build frontend; verifikasi browser
- [ ] Evaluasi deteksi terhadap referensi independen; evaluasi model pada data nyata; usability; Docker/PostGIS
## M4 Release
- [x] Peran operator/admin, verifikasi, ekspor CSV/PDF, penjelasan prediksi, notifikasi polling
- [x] Screenshot, laporan (`docs/LAPORAN.md`)
- [ ] CNN, fusi Sentinel-1/2, push notifikasi
