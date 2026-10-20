/**
 * ForestWatch AI - ML Analysis Page
 * Sentinel comparison, ML inference form, model evaluation
 */
import { useState, useEffect } from 'react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { mlAPI, dashboardAPI } from '../services/api';
import { CategoryBadge, ConfidenceBadge } from '../components/common/Badges';
import { getCategoryColor, CATEGORY_LIST } from '../utils/colors';

export default function AnalysisPage() {
  const [form, setForm] = useState({
    ndvi_before: '0.72',
    ndvi_after: '0.18',
    nbr_before: '0.68',
    nbr_after: '0.08',
    sar_vv_before: '-9.0',
    sar_vv_after: '-17.0',
    cloud_coverage: '20',
    area_ha: '75',
    evi_before: '0.62',
    evi_after: '0.10',
    b4_red_after: '1000',
    b8_nir_after: '1300',
    b11_swir1_after: '3000',
    b12_swir2_after: '2500',
  });
  const [prediction, setPrediction] = useState(null);
  const [predLoading, setPredLoading] = useState(false);
  const [modelPerf, setModelPerf] = useState(null);
  const [perfError, setPerfError] = useState(null);
  const [predError, setPredError] = useState(null);
  const [activeTab, setActiveTab] = useState('inference');

  useEffect(() => {
    dashboardAPI.getModelPerformance()
      .then((r) => setModelPerf(r.data))
      .catch(() => setPerfError('Metrik model gagal dimuat dari backend. Tidak ada angka cadangan yang ditampilkan.'));
  }, []);

  const handlePredict = async () => {
    setPredLoading(true);
    setPredError(null);
    try {
      const payload = {
        ndvi_before: parseFloat(form.ndvi_before),
        ndvi_after: parseFloat(form.ndvi_after),
        nbr_before: parseFloat(form.nbr_before),
        nbr_after: parseFloat(form.nbr_after),
        sar_vv_before: parseFloat(form.sar_vv_before),
        sar_vv_after: parseFloat(form.sar_vv_after),
        cloud_coverage: parseFloat(form.cloud_coverage),
        area_ha: parseFloat(form.area_ha),
        evi_before: parseFloat(form.evi_before),
        evi_after: parseFloat(form.evi_after),
        b4_red_after: parseFloat(form.b4_red_after),
        b8_nir_after: parseFloat(form.b8_nir_after),
        b11_swir1_after: parseFloat(form.b11_swir1_after),
        b12_swir2_after: parseFloat(form.b12_swir2_after),
      };
      if (Object.values(payload).some((v) => Number.isNaN(v))) {
        setPredError('Semua kolom harus diisi dengan angka sebelum prediksi dijalankan.');
        setPredLoading(false);
        return;
      }
      const res = await mlAPI.predict(payload);
      setPrediction(res.data);
    } catch (e) {
      setPrediction(null);
      const detail = e?.response?.data?.detail;
      setPredError(
        Array.isArray(detail)
          ? 'Input tidak valid: ' + detail.map((d) => `${d.loc?.slice(-1)[0]} ${d.msg}`).join('; ')
          : (typeof detail === 'string' ? detail : 'Prediksi gagal: backend tidak dapat dihubungi.')
      );
    } finally {
      setPredLoading(false);
    }
  };

  // Radar chart data for class metrics
  const radarData = (modelPerf?.per_class_metrics || []).map((m) => ({
    category: CATEGORY_LIST.find((c) => c.id === m.category)?.shortLabel || m.category,
    Precision: Math.round(m.precision * 100),
    Recall: Math.round(m.recall * 100),
    F1: Math.round(m.f1_score * 100),
  }));

  // Probability bar data
  const probData = prediction
    ? Object.entries(prediction.prediction?.all_probabilities || {}).map(([cat, prob]) => ({
        name: CATEGORY_LIST.find((c) => c.id === cat)?.shortLabel || cat,
        cat,
        prob: Math.round(prob * 100),
      })).sort((a, b) => b.prob - a.prob)
    : [];

  return (
    <div className="page-content" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Topbar */}
      <div className="topbar">
        <div>
          <div className="topbar-title">🔬 Analisis ML & Evaluasi Model</div>
          <div className="topbar-subtitle">Inferensi klasifikasi gangguan hutan &amp; evaluasi performa model</div>
        </div>
        <div className="topbar-actions">
          {['inference', 'evaluation', 'sentinel'].map((tab) => (
            <button
              key={tab}
              className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-ghost'} btn-sm`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'inference' ? '🎯 Inferensi' : tab === 'evaluation' ? '📊 Evaluasi' : '🛰️ Simulasi'}
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* ── Tab: Inference ── */}
        {activeTab === 'inference' && (
          <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 16 }}>
            {/* Input form */}
            <div>
              <div className="card">
                <div className="card-header">
                  <div className="card-title">⚙️ Input Fitur Spektral</div>
                </div>

                <div className="disclaimer-banner" style={{ marginBottom: 16 }}>
                  <span className="disclaimer-icon">ℹ️</span>
                  <span>Masukkan nilai indeks spektral dari Sentinel-2 dan Sentinel-1. Seluruh 14 fitur wajib diisi; tidak ada nilai bawaan tersembunyi. Nilai awal formulir hanyalah contoh.</span>
                </div>

                {/* Sentinel-2 section */}
                <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--color-accent)', marginBottom: 10 }}>
                  🛰️ Sentinel-2 (Optik)
                </div>
                <div className="form-row">
                  {[
                    { key: 'ndvi_before', label: 'NDVI Sebelum', hint: '-1 to 1' },
                    { key: 'ndvi_after', label: 'NDVI Sesudah', hint: '-1 to 1' },
                  ].map(({ key, label, hint }) => (
                    <div key={key} className="form-group">
                      <label className="form-label">{label}</label>
                      <input
                        type="number" step="0.01" min="-1" max="1"
                        className="form-input"
                        value={form[key]}
                        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                        placeholder={hint}
                      />
                    </div>
                  ))}
                </div>
                <div className="form-row">
                  {[
                    { key: 'nbr_before', label: 'NBR Sebelum', hint: '-1 to 1' },
                    { key: 'nbr_after', label: 'NBR Sesudah', hint: '-1 to 1' },
                  ].map(({ key, label, hint }) => (
                    <div key={key} className="form-group">
                      <label className="form-label">{label}</label>
                      <input
                        type="number" step="0.01" min="-1" max="1"
                        className="form-input"
                        value={form[key]}
                        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                        placeholder={hint}
                      />
                    </div>
                  ))}
                </div>
                <div className="form-row">
                  {[
                    { key: 'evi_before', label: 'EVI Sebelum' },
                    { key: 'evi_after', label: 'EVI Sesudah' },
                  ].map(({ key, label }) => (
                    <div key={key} className="form-group">
                      <label className="form-label">{label}</label>
                      <input type="number" step="0.01" className="form-input" value={form[key]}
                        onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
                    </div>
                  ))}
                </div>
                <div className="form-row">
                  {[
                    { key: 'b4_red_after', label: 'B4 Red (×10⁴)' },
                    { key: 'b8_nir_after', label: 'B8 NIR (×10⁴)' },
                    { key: 'b11_swir1_after', label: 'B11 SWIR1 (×10⁴)' },
                    { key: 'b12_swir2_after', label: 'B12 SWIR2 (×10⁴)' },
                  ].map(({ key, label }) => (
                    <div key={key} className="form-group">
                      <label className="form-label">{label}</label>
                      <input type="number" step="10" min="0" className="form-input" value={form[key]}
                        onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
                    </div>
                  ))}
                </div>
                <div className="form-group">
                  <label className="form-label">Tutupan Awan (%)</label>
                  <input type="number" step="1" min="0" max="100"
                    className="form-input" value={form.cloud_coverage}
                    onChange={(e) => setForm({ ...form, cloud_coverage: e.target.value })}
                  />
                </div>

                <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#60a5fa', marginBottom: 10, marginTop: 8 }}>
                  📡 Sentinel-1 (SAR)
                </div>
                <div className="form-row">
                  {[
                    { key: 'sar_vv_before', label: 'VV Before (dB)' },
                    { key: 'sar_vv_after', label: 'VV After (dB)' },
                  ].map(({ key, label }) => (
                    <div key={key} className="form-group">
                      <label className="form-label">{label}</label>
                      <input type="number" step="0.5" className="form-input"
                        value={form[key]}
                        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                      />
                    </div>
                  ))}
                </div>
                <div className="form-group">
                  <label className="form-label">Luas Area (Ha)</label>
                  <input type="number" step="5" min="1" className="form-input"
                    value={form.area_ha}
                    onChange={(e) => setForm({ ...form, area_ha: e.target.value })}
                  />
                </div>

                {/* NDVI change preview */}
                <div style={{ background: 'var(--color-bg-glass)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 12, marginBottom: 14 }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 6 }}>Preview Perubahan</div>
                  {[
                    { label: 'ΔNDVI', val: (parseFloat(form.ndvi_after) - parseFloat(form.ndvi_before)).toFixed(3) },
                    { label: 'ΔNBR', val: (parseFloat(form.nbr_after) - parseFloat(form.nbr_before)).toFixed(3) },
                    { label: 'ΔSAR VV', val: (parseFloat(form.sar_vv_after) - parseFloat(form.sar_vv_before)).toFixed(2) + ' dB' },
                  ].map(({ label, val }) => (
                    <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: 3 }}>
                      <span style={{ color: 'var(--text-muted)' }}>{label}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: parseFloat(val) < 0 ? '#ef4444' : '#22c55e', fontWeight: 600 }}>{val}</span>
                    </div>
                  ))}
                </div>

                <button
                  className="btn btn-primary"
                  style={{ width: '100%', justifyContent: 'center', padding: '11px 0', fontSize: '0.9rem' }}
                  onClick={handlePredict}
                  disabled={predLoading}
                >
                  {predLoading ? '⏳ Memproses...' : '🤖 Jalankan Klasifikasi'}
                </button>
              </div>
            </div>

            {/* Prediction output */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {!prediction && !predLoading && (
                <div className="card" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div className="empty-state">
                    <div className="empty-state-icon">🤖</div>
                    <div className="empty-state-text">
                      Masukkan nilai fitur spektral dan tekan<br /><strong>"Jalankan Klasifikasi"</strong> untuk mendapatkan prediksi.
                    </div>
                  </div>
                </div>
              )}

              {predError && !predLoading && (
                <div className="disclaimer-banner" role="alert"><span>⚠️</span><span>{predError}</span></div>
              )}

              {predLoading && (
                <div className="card" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div className="loading-spinner">
                    <div className="spinner" />
                    <span>Model sedang memproses fitur...</span>
                  </div>
                </div>
              )}

              {prediction && !predLoading && (
                <>
                  {/* Main result */}
                  <div className="card" style={{
                    borderColor: getCategoryColor(prediction.prediction?.predicted_category),
                    boxShadow: `0 0 20px ${getCategoryColor(prediction.prediction?.predicted_category)}25`
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                      <div style={{
                        width: 52, height: 52, borderRadius: 12,
                        background: `${getCategoryColor(prediction.prediction?.predicted_category)}20`,
                        border: `2px solid ${getCategoryColor(prediction.prediction?.predicted_category)}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24
                      }}>
                        {CATEGORY_LIST.find(c => c.id === prediction.prediction?.predicted_category)?.icon || '❓'}
                      </div>
                      <div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                          Prediksi Kategori
                        </div>
                        <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                          {prediction.prediction?.category_label}
                        </div>
                        <div style={{ display: 'flex', gap: 8 }}>
                          <CategoryBadge category={prediction.prediction?.predicted_category} />
                          <ConfidenceBadge
                            level={prediction.prediction?.confidence_level}
                            score={prediction.prediction?.confidence_score}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="metric-grid">
                      {[
                        { label: 'Skor Keyakinan', val: `${(prediction.prediction?.confidence_score * 100).toFixed(1)}%`, color: 'var(--color-accent)' },
                        { label: 'Δ NDVI', val: prediction.ndvi_change?.toFixed(3), color: prediction.ndvi_change < 0 ? '#ef4444' : '#22c55e' },
                        { label: 'Δ NBR', val: prediction.nbr_change?.toFixed(3), color: prediction.nbr_change < 0 ? '#ef4444' : '#22c55e' },
                        { label: 'Level', val: { tinggi: '🟢', sedang: '🟡', rendah: '🔴' }[prediction.prediction?.confidence_level], color: 'var(--text-primary)' },
                      ].map(({ label, val, color }) => (
                        <div key={label} className="metric-item">
                          <div className="metric-value" style={{ color }}>{val}</div>
                          <div className="metric-label">{label}</div>
                        </div>
                      ))}
                    </div>

                    <div className="disclaimer-banner" style={{ marginTop: 12 }}>
                      <span className="disclaimer-icon">⚠️</span>
                      <span>{prediction.prediction?.model_disclaimer}</span>
                    </div>
                  </div>

                  {/* Probability bars */}
                  <div className="card">
                    <div className="card-header">
                      <div className="card-title">🔎 Penjelasan Lokal (oklusi)</div>
                      <span className="tag">perkiraan</span>
                    </div>
                    {prediction.explanation ? (
                      <>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 8 }}>
                          Fitur yang paling mendorong kelas “{prediction.explanation.target_category}” (turunnya probabilitas bila fitur diganti median data latih).
                        </div>
                        <table className="data-table">
                          <thead><tr><th>Fitur</th><th style={{ textAlign: 'right' }}>Nilai</th><th style={{ textAlign: 'right' }}>Kontribusi</th></tr></thead>
                          <tbody>
                            {prediction.explanation.top_features.map((f) => (
                              <tr key={f.feature}>
                                <td className="mono">{f.feature}</td>
                                <td style={{ textAlign: 'right' }}>{f.value.toFixed(3)}</td>
                                <td style={{ textAlign: 'right', color: f.contribution >= 0 ? '#00e5a0' : '#f59e0b' }}>{f.contribution >= 0 ? '+' : ''}{(f.contribution * 100).toFixed(1)} poin</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 6 }}>{prediction.explanation.caveat}</div>
                      </>
                    ) : null}
                  </div>

                  <div className="card">
                    <div className="card-header">
                      <div className="card-title">📊 Probabilitas Per Kategori</div>
                    </div>
                    <div style={{ height: 200 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={probData} layout="vertical" margin={{ left: 20, right: 20 }}>
                          <XAxis type="number" domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
                          <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} width={80} />
                          <Tooltip
                            formatter={(v) => [`${v}%`, 'Probabilitas']}
                            contentStyle={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--border-medium)', borderRadius: 8, fontSize: 12, color: 'var(--text-primary)' }}
                          />
                          <Bar dataKey="prob" radius={[0, 4, 4, 0]}>
                            {probData.map((d) => (
                              <Cell key={d.cat} fill={getCategoryColor(d.cat)} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* ── Tab: Evaluation ── */}
        {activeTab === 'evaluation' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Disclaimer */}
            {perfError && <div className="disclaimer-banner" role="alert"><span>⚠️</span><span>{perfError}</span></div>}
              <div className="disclaimer-banner" style={{ padding: '12px 16px' }}>
              <span className="disclaimer-icon">⚠️</span>
              <div>
                <strong>Catatan Metodologis:</strong> {modelPerf?.note}
              </div>
            </div>

            {/* Overall metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
              {[
                { label: 'Akurasi', val: modelPerf ? `${(modelPerf.accuracy * 100).toFixed(1)}%` : '—', color: '#00e5a0' },
                { label: 'Macro F1', val: modelPerf ? `${(modelPerf.macro_f1 * 100).toFixed(1)}%` : '—', color: '#60a5fa' },
                { label: 'Weighted F1', val: modelPerf ? `${(modelPerf.weighted_f1 * 100).toFixed(1)}%` : '—', color: '#a78bfa' },
                { label: 'Model', val: 'RF', color: '#f59e0b' },
              ].map(({ label, val, color }) => (
                <div key={label} className="kpi-card" style={{ '--kpi-color': color }}>
                  <div className="kpi-value" style={{ fontSize: '1.6rem', color }}>{val}</div>
                  <div className="kpi-label">{label}</div>
                </div>
              ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {/* Per-class metrics table */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">📋 Metrik Per Kelas</div>
                  <span className="tag">Precision · Recall · F1</span>
                </div>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Kategori</th>
                      <th style={{ textAlign: 'right' }}>Prec.</th>
                      <th style={{ textAlign: 'right' }}>Recall</th>
                      <th style={{ textAlign: 'right' }}>F1</th>
                      <th style={{ textAlign: 'right' }}>Support</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(modelPerf?.per_class_metrics || []).map((m) => (
                      <tr key={m.category}>
                        <td><CategoryBadge category={m.category} /></td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>{(m.precision * 100).toFixed(1)}%</td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>{(m.recall * 100).toFixed(1)}%</td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--color-accent)' }}>{(m.f1_score * 100).toFixed(1)}%</td>
                        <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>{m.support}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Radar chart */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">🕸️ Radar Metrik Per Kelas</div>
                </div>
                <div style={{ height: 250 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="var(--border-subtle)" />
                      <PolarAngleAxis dataKey="category" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
                      <PolarRadiusAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 8 }} tickCount={4} />
                      <Radar name="Precision" dataKey="Precision" stroke="#00e5a0" fill="#00e5a0" fillOpacity={0.15} />
                      <Radar name="Recall" dataKey="Recall" stroke="#60a5fa" fill="#60a5fa" fillOpacity={0.12} />
                      <Radar name="F1" dataKey="F1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.10} />
                      <Tooltip contentStyle={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--border-medium)', borderRadius: 8, fontSize: 11, color: 'var(--text-primary)' }} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Confusion Matrix */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">🔲 Confusion Matrix</div>
                <span className="tag">Data uji sintetis (n={modelPerf?.test_samples ?? "-"})</span>
              </div>
              <div style={{ overflowX: 'auto', padding: '8px 0' }}>
                <div style={{ display: 'flex', gap: 4 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, paddingTop: 42 }}>
                    {(modelPerf?.confusion_matrix_labels || []).map((l) => (
                      <div key={l} style={{ height: 42, display: 'flex', alignItems: 'center', fontSize: '0.7rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', paddingRight: 8, width: 80, textAlign: 'right', justifyContent: 'flex-end' }}>
                        {l}
                      </div>
                    ))}
                  </div>
                  <div>
                    <div style={{ display: 'flex', gap: 4, marginBottom: 4, paddingLeft: 0 }}>
                      {(modelPerf?.confusion_matrix_labels || []).map((l) => (
                        <div key={l} style={{ width: 52, textAlign: 'center', fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600 }}>{l.substring(0, 5)}</div>
                      ))}
                    </div>
                    {(modelPerf?.confusion_matrix || []).map((row, ri) => (
                      <div key={ri} style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
                        {row.map((val, ci) => {
                          const maxVal = Math.max(...(modelPerf?.confusion_matrix || [[1]]).flat(), 1);
                          const intensity = val / maxVal;
                          const isDiag = ri === ci;
                          const bg = isDiag
                            ? `rgba(0, 229, 160, ${0.15 + intensity * 0.7})`
                            : val > 2 ? `rgba(239, 68, 68, ${intensity * 0.7})` : 'rgba(255,255,255,0.03)';
                          return (
                            <div key={ci} style={{
                              width: 52, height: 42,
                              background: bg,
                              border: `1px solid ${isDiag ? 'rgba(0,229,160,0.4)' : 'var(--border-subtle)'}`,
                              borderRadius: 4,
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontFamily: 'var(--font-mono)', fontSize: '0.8rem',
                              fontWeight: isDiag ? 700 : 400,
                              color: isDiag ? '#00e5a0' : val > 2 ? '#ef4444' : 'var(--text-muted)',
                            }}>
                              {val}
                            </div>
                          );
                        })}
                      </div>
                    ))}
                  </div>
                </div>
                <div style={{ marginTop: 12, display: 'flex', gap: 16, fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 12, height: 12, background: 'rgba(0,229,160,0.5)', borderRadius: 2 }} />
                    Prediksi benar (diagonal)
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 12, height: 12, background: 'rgba(239,68,68,0.4)', borderRadius: 2 }} />
                    Kesalahan klasifikasi
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Tab: Sentinel Simulation ── */}
        {activeTab === 'sentinel' && (
          <SentinelSimulationTab />
        )}
      </div>
    </div>
  );
}

function SentinelSimulationTab() {
  const [simForm, setSimForm] = useState({ latitude: '-1.50', longitude: '113.80', region: 'Kalimantan Tengah' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [simError, setSimError] = useState(null);

  const handleSimulate = async () => {
    setLoading(true);
    setSimError(null);
    try {
      const res = await mlAPI.simulateSentinel({
        latitude: parseFloat(simForm.latitude),
        longitude: parseFloat(simForm.longitude),
        region: simForm.region,
      });
      setResult(res.data);
    } catch (e) {
      setResult(null);
      setSimError(e?.response?.data?.detail
        ? (typeof e.response.data.detail === 'string' ? e.response.data.detail : 'Input simulasi tidak valid.')
        : 'Simulasi gagal: backend tidak dapat dihubungi. Tidak ada hasil cadangan yang ditampilkan.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 16 }}>
      <div className="card">
        <div className="card-header">
          <div className="card-title">🛰️ Simulasi Data Sentinel</div>
        </div>
        <div className="disclaimer-banner" style={{ marginBottom: 16 }}>
          <span>ℹ️</span>
          <span>Mensimulasikan pengambilan data Sentinel-1/2 untuk koordinat tertentu. Data nyata memerlukan Google Earth Engine API.</span>
        </div>
        <div className="form-group">
          <label className="form-label">Latitude</label>
          <input type="number" step="0.01" className="form-input" value={simForm.latitude}
            onChange={(e) => setSimForm({ ...simForm, latitude: e.target.value })} />
        </div>
        <div className="form-group">
          <label className="form-label">Longitude</label>
          <input type="number" step="0.01" className="form-input" value={simForm.longitude}
            onChange={(e) => setSimForm({ ...simForm, longitude: e.target.value })} />
        </div>
        <div className="form-group">
          <label className="form-label">Region</label>
          <select className="form-input" value={simForm.region}
            onChange={(e) => setSimForm({ ...simForm, region: e.target.value })}>
            {['Kalimantan Timur - IKN', 'Kalimantan Tengah', 'Sumatera Selatan', 'Riau', 'Papua Barat'].map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
        <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}
          onClick={handleSimulate} disabled={loading}>
          {loading ? '⏳ Simulasi...' : '▶ Jalankan Simulasi'}
        </button>
      </div>

      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Sentinel-2 comparison */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">🛰️ Sentinel-2 — Perbandingan Sebelum/Sesudah</div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {['before', 'after'].map((period) => {
                const data = result[`sentinel2_${period}`];
                const indices = data?.indices || result.change_metrics;
                const ndvi = period === 'before' ? result.change_metrics?.ndvi_before : result.change_metrics?.ndvi_after;
                const nbr = period === 'before' ? result.change_metrics?.nbr_before : result.change_metrics?.nbr_after;
                return (
                  <div key={period} className="scene-card">
                    <div className="scene-label">{period === 'before' ? '⏪ Sebelum' : '⏩ Sesudah'}</div>
                    <div style={{ marginBottom: 10 }}>
                      {[
                        { label: 'NDVI', val: ndvi?.toFixed(3), color: ndvi > 0.5 ? '#22c55e' : ndvi > 0.2 ? '#f59e0b' : '#ef4444', width: Math.max(5, ((ndvi + 0.2) / 1.2) * 100) },
                        { label: 'NBR', val: nbr?.toFixed(3), color: nbr > 0.4 ? '#22c55e' : nbr > 0 ? '#f59e0b' : '#ef4444', width: Math.max(5, ((nbr + 0.4) / 1.4) * 100) },
                      ].map(({ label, val, color, width }) => (
                        <div key={label} style={{ marginBottom: 8 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: 3 }}>
                            <span style={{ color: 'var(--text-muted)' }}>{label}</span>
                            <span style={{ fontFamily: 'var(--font-mono)', color, fontWeight: 600 }}>{val}</span>
                          </div>
                          <div className="progress-bar">
                            <div className="progress-fill" style={{ width: `${width}%`, background: color }} />
                          </div>
                        </div>
                      ))}
                    </div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                      ☁️ Awan: {data?.cloud_coverage_pct?.toFixed(0) || '?'}%
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* SAR + prediction */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="card">
              <div className="card-header">
                <div className="card-title">📡 Sentinel-1 SAR (VV)</div>
              </div>
              {[
                { label: 'Sebelum (VV dB)', val: result.sentinel1_summary?.before_VV_dB?.toFixed(2) },
                { label: 'Sesudah (VV dB)', val: result.sentinel1_summary?.after_VV_dB?.toFixed(2) },
                { label: 'Perubahan', val: (result.sentinel1_summary?.after_VV_dB - result.sentinel1_summary?.before_VV_dB)?.toFixed(2) + ' dB' },
              ].map(({ label, val }) => (
                <div key={label} className="popup-row">
                  <span>{label}</span>
                  <span className="popup-row-value" style={{ fontFamily: 'var(--font-mono)' }}>{val}</span>
                </div>
              ))}
              <div className="disclaimer-banner" style={{ marginTop: 10 }}>
                <span>ℹ️</span>
                <span>SAR berguna ketika citra optik terhalang awan.</span>
              </div>
            </div>

            <div className="card" style={{
              borderColor: getCategoryColor(result.prediction?.predicted_category),
              boxShadow: `0 0 15px ${getCategoryColor(result.prediction?.predicted_category)}20`
            }}>
              <div className="card-header">
                <div className="card-title">🤖 Hasil Prediksi</div>
              </div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 12 }}>
                <div style={{ fontSize: 32 }}>
                  {CATEGORY_LIST.find(c => c.id === result.prediction?.predicted_category)?.icon}
                </div>
                <div>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '0.95rem', marginBottom: 4 }}>
                    {result.prediction?.category_label}
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <CategoryBadge category={result.prediction?.predicted_category} />
                    <ConfidenceBadge level={result.prediction?.confidence_level} score={result.prediction?.confidence_score} />
                  </div>
                </div>
              </div>
              <div className="disclaimer-banner">
                <span>⚠️</span>
                <span style={{ fontSize: '0.7rem' }}>{result.simulation_note}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {simError && <div className="disclaimer-banner" role="alert"><span>⚠️</span><span>{simError}</span></div>}
      {!result && !loading && !simError && (
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="empty-state">
            <div className="empty-state-icon">🛰️</div>
            <div className="empty-state-text">Pilih koordinat dan jalankan simulasi untuk melihat data Sentinel mock dan prediksi ML.</div>
          </div>
        </div>
      )}
    </div>
  );
}
