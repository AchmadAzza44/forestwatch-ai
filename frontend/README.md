# ForestWatch AI - Frontend

React + Vite + Leaflet + Recharts. Lihat `../README.md` untuk cara menjalankan keseluruhan sistem.

```bash
npm ci
VITE_API_URL=http://localhost:8000/api npm run dev   # pengembangan
npm run build && npm run lint
```

Frontend tidak memiliki data cadangan: bila backend tidak terjangkau, halaman menampilkan pesan kegagalan.
