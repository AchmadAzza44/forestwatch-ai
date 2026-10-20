/**
 * ForestWatch AI - About / Methodology Page
 */
export default function AboutPage() {
  const sections = [
    {
      icon: '🎯',
      title: 'Tujuan Sistem',
      content: `ForestWatch AI adalah sistem pemantauan deforestasi berbasis citra satelit dan Machine Learning. Sistem ini dirancang untuk membantu peneliti, instansi lingkungan, dan pengelola kawasan hutan dalam mengidentifikasi indikasi perubahan tutupan hutan dan mengklasifikasikan kemungkinan penyebab gangguan.`,
    },
    {
      icon: '🛰️',
      title: 'Data Satelit',
      content: null,
      items: [
        { label: 'Sentinel-2 L2A', desc: 'Data multispektral 10-20m untuk analisis kondisi vegetasi (NDVI, NBR, EVI). Saat ini menggunakan data simulasi.' },
        { label: 'Sentinel-1 GRD', desc: 'Data SAR (Synthetic Aperture Radar) untuk melengkapi pengamatan saat tutupan awan tinggi.' },
        { label: 'Integrasi GEE', desc: 'Sistem dirancang untuk terhubung ke Google Earth Engine API. Ganti modul sentinel_mock.py dengan panggilan GEE untuk data nyata.' },
      ],
    },
    {
      icon: '🌿',
      title: 'Indeks Spektral',
      content: null,
      items: [
        { label: 'NDVI (Normalized Difference Vegetation Index)', desc: '(NIR - Red) / (NIR + Red). Mengukur kerapatan vegetasi. Nilai tinggi (>0.6) = vegetasi lebat.' },
        { label: 'NBR (Normalized Burn Ratio)', desc: '(NIR - SWIR2) / (NIR + SWIR2). Sensitif terhadap kebakaran. dNBR < -0.1 mengindikasikan area terbakar.' },
        { label: 'EVI (Enhanced Vegetation Index)', desc: 'Versi NDVI yang lebih sensitif di area vegetasi lebat, mengurangi efek atmosfer dan tutupan awan.' },
      ],
    },
    {
      icon: '🤖',
      title: 'Model Machine Learning',
      content: `Saat ini menggunakan Random Forest dengan 150 estimator, dilatih pada data sintetis yang mencerminkan profil spektral nyata. Fitur input mencakup NDVI, NBR, EVI, nilai band Sentinel-2, backscatter Sentinel-1, dan metadata (area, tutupan awan).`,
      note: 'Untuk implementasi produksi: ganti data pelatihan sintetis dengan dataset berlabel dari citra Sentinel nyata. Pertimbangkan CNN untuk klasifikasi langsung dari patch citra.',
    },
    {
      icon: '📊',
      title: 'Kategori Gangguan',
      content: null,
      items: [
        { label: '🌾 Pertanian / Land Clearing', desc: 'Konversi hutan untuk lahan pertanian atau perkebunan. NDVI turun ke 0.2-0.5.' },
        { label: '🪓 Penebangan Liar', desc: 'Illegal logging. Penurunan NDVI signifikan tanpa pola kebakaran (NBR stabil).' },
        { label: '⛏️ Pertambangan', desc: 'Aktivitas tambang. NDVI sangat rendah (<0.2), backscatter SAR menurun drastis.' },
        { label: '🔥 Kebakaran Hutan', desc: 'Area terbakar. NBR turun ke nilai negatif, SWIR2 meningkat tajam.' },
        { label: '🌊 Gangguan Alami', desc: 'Banjir, angin, tanah longsor. Pola perubahan berbeda dari aktivitas manusia.' },
        { label: '❓ Tidak Diketahui', desc: 'Ketika keyakinan model di bawah ambang batas atau pola tidak cocok dengan kategori manapun.' },
      ],
    },
    {
      icon: '⚠️',
      title: 'Keterbatasan Sistem',
      content: null,
      items: [
        { label: 'Data Simulasi', desc: 'Data satelit saat ini adalah simulasi. Nilai spektral mencerminkan karakteristik umum, bukan piksel nyata dari lokasi tertentu.' },
        { label: 'Ketidakpastian Prediksi', desc: 'Model ML dapat salah mengklasifikasikan gangguan. Selalu tampilkan skor keyakinan dan gunakan kategori "Tidak Diketahui" untuk kasus ambigu.' },
        { label: 'Tutupan Awan', desc: 'Citra optik Sentinel-2 terbatas saat cuaca berawan. Sentinel-1 SAR dapat melengkapi, tetapi memerlukan preprocessing berbeda.' },
        { label: 'Verifikasi Lapangan', desc: 'Prediksi sistem bukan pengganti survei lapangan. Gunakan sebagai alat bantu prioritisasi, bukan bukti definitif.' },
        { label: 'Skala Spasial', desc: 'Resolusi 10-20m Sentinel-2 cocok untuk area >1 ha. Gangguan kecil mungkin tidak terdeteksi.' },
      ],
    },
    {
      icon: '🔬',
      title: 'Evaluasi Model',
      content: `Evaluasi menggunakan precision, recall, F1-score, dan confusion matrix. Data dibagi train/test (75%/25%) dengan stratifikasi kelas. Untuk data geospasial nyata: gunakan pemisahan spasial (spatial cross-validation) untuk menghindari kebocoran informasi antara data latih dan uji.`,
    },
    {
      icon: '🗺️',
      title: 'Arsitektur Sistem',
      content: null,
      items: [
        { label: 'Frontend', desc: 'React + Vite + Leaflet.js (peta interaktif) + Recharts (visualisasi data)' },
        { label: 'Backend', desc: 'FastAPI (Python) — REST API untuk data spasial, inferensi ML, dan statistik' },
        { label: 'Database', desc: 'PostgreSQL + PostGIS — penyimpanan geometri dan metadata disturbance' },
        { label: 'ML Layer', desc: 'scikit-learn Random Forest — dapat diganti CNN dengan PyTorch/TensorFlow' },
        { label: 'Deployment', desc: 'Docker Compose — semua service dalam container untuk reproduksibilitas' },
      ],
    },
  ];

  return (
    <div className="page-content" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div className="topbar">
        <div>
          <div className="topbar-title">ℹ️ Metodologi &amp; Informasi Sistem</div>
          <div className="topbar-subtitle">Dokumentasi teknis, keterbatasan, dan panduan penggunaan ForestWatch AI</div>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
        {/* Header banner */}
        <div className="card" style={{ marginBottom: 20, background: 'linear-gradient(135deg, rgba(0,229,160,0.05), rgba(59,130,246,0.05))', borderColor: 'var(--border-accent)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ fontSize: 48 }}>🌿</div>
            <div>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.4rem', fontWeight: 700, marginBottom: 6 }}>
                ForestWatch AI v1.0
              </h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', lineHeight: 1.6 }}>
                Sistem Pemantauan Deforestasi Berbasis GIS, Citra Satelit, dan Machine Learning
              </p>
              <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
                {['GIS', 'Sentinel-1/2', 'Random Forest', 'PostGIS', 'FastAPI', 'React'].map((tag) => (
                  <span key={tag} className="tag">{tag}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'start' }}>
          {sections.map((section, i) => (
            <div key={i} className="card animate-fade-in" style={{ animationDelay: `${i * 0.05}s` }}>
              <div className="card-title" style={{ marginBottom: 12, fontSize: '1rem' }}>
                <span>{section.icon}</span>
                <span>{section.title}</span>
              </div>

              {section.content && (
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.7, marginBottom: section.note ? 12 : 0 }}>
                  {section.content}
                </p>
              )}

              {section.note && (
                <div className="disclaimer-banner">
                  <span>💡</span>
                  <span style={{ fontSize: '0.78rem' }}>{section.note}</span>
                </div>
              )}

              {section.items && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {section.items.map((item, j) => (
                    <div key={j} style={{ borderLeft: '2px solid var(--color-accent)', paddingLeft: 12 }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
                        {item.label}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        {item.desc}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Footer note */}
        <div className="disclaimer-banner" style={{ marginTop: 20 }}>
          <span className="disclaimer-icon">📌</span>
          <div style={{ fontSize: '0.8rem', lineHeight: 1.6 }}>
            <strong>Catatan Penting:</strong> ForestWatch AI adalah sistem pendukung keputusan, bukan pengganti verifikasi lapangan. 
            Semua prediksi menampilkan tanggal data, sumber, kategori, dan skor keyakinan. 
            Pengguna bertanggung jawab untuk memvalidasi hasil sebelum mengambil keputusan berbasis data ini.
          </div>
        </div>
      </div>
    </div>
  );
}
