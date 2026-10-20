/**
 * ForestWatch AI - Disturbance Popup (Leaflet Popup content)
 */
import { useState } from 'react';
import { CategoryBadge, ConfidenceBadge, NDVIBar } from '../common/Badges';
import { CATEGORY_LIST } from '../../utils/colors';
import { disturbancesAPI } from '../../services/api';
import { formatDate, formatHa, formatCoord, formatPeriod } from '../../utils/formatters';

function VerifyForm({ id, onDone }) {
  const token = (() => { try { return localStorage.getItem('fw_token') || ''; } catch { return ''; } })();
  const [cat, setCat] = useState('tidak_diketahui');
  const [note, setNote] = useState('');
  const [msg, setMsg] = useState(null);
  if (!token) return <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Masukkan token operator di sidebar untuk memverifikasi.</div>;
  const submit = async () => {
    try {
      await disturbancesAPI.validate(id, { verified_category: cat, note }, token);
      setMsg({ ok: true, text: 'Verifikasi tersimpan.' });
      onDone?.(cat);
    } catch (e) {
      setMsg({ ok: false, text: e?.response?.status === 403 || e?.response?.status === 401 ? 'Token tidak berwenang.' : 'Gagal menyimpan verifikasi.' });
    }
  };
  return (
    <div style={{ display: 'grid', gap: 6 }}>
      <select className="filter-input" value={cat} onChange={(e) => setCat(e.target.value)} aria-label="Kategori hasil verifikasi">
        {CATEGORY_LIST.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
      </select>
      <input className="filter-input" placeholder="Catatan verifikasi" value={note} maxLength={1000} onChange={(e) => setNote(e.target.value)} />
      <button className="btn btn-ghost" onClick={submit}>Simpan verifikasi</button>
      {msg && <div role="status" style={{ fontSize: '0.7rem', color: msg.ok ? '#00e5a0' : '#f59e0b' }}>{msg.text}</div>}
    </div>
  );
}

export default function DisturbancePopup({ feature, onDetailClick }) {
  const p = feature?.properties || {};
  const [verified, setVerified] = useState(p.verified_category || null);
  const real = p.source_type === 'citra_nyata';

  return (
    <div className="popup-content" style={{ minWidth: 260 }}>
      <div className="popup-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <CategoryBadge category={p.category} />
          <ConfidenceBadge level={p.confidence_level} score={p.confidence_score} />
        </div>
        <div className="popup-category">{p.region}</div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          {p.province} · ID: {p.id}
        </div>
      </div>

      <div className="popup-row">
        <span>Sumber</span>
        <span className="popup-row-value" style={{ color: real ? '#60a5fa' : 'var(--text-muted)' }}>{real ? '🛰️ Citra Sentinel-2 nyata' : 'Simulasi'}</span>
      </div>
      <hr className="divider" />

      <div className="popup-row">
        <span>Luas Area</span>
        <span className="popup-row-value">{formatHa(p.area_ha)}</span>
      </div>
      <div className="popup-row">
        <span>Tgl Deteksi</span>
        <span className="popup-row-value">{formatDate(p.detected_date)}</span>
      </div>
      <div className="popup-row">
        <span>Periode</span>
        <span className="popup-row-value">{formatPeriod(p.period_start, p.period_end)}</span>
      </div>
      <div className="popup-row">
        <span>Koordinat</span>
        <span className="popup-row-value" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
          {formatCoord(feature?.geometry?.coordinates?.[1] || p.centroid_lat)},&nbsp;
          {formatCoord(feature?.geometry?.coordinates?.[0] || p.centroid_lon)}
        </span>
      </div>
      {(p.is_validated || verified) && (
        <div className="popup-row">
          <span>Verifikasi operator</span>
          <span className="popup-row-value" style={{ color: '#00e5a0' }}>✓ {verified ? (CATEGORY_LIST.find((c) => c.id === verified)?.shortLabel || verified) : 'Tervalidasi'}</span>
        </div>
      )}

      {/* NDVI section */}
      {p.ndvi_before !== null && p.ndvi_after !== null && (
        <>
          <hr className="divider" />
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Indeks NDVI
          </div>
          <NDVIBar before={p.ndvi_before} after={p.ndvi_after} />
        </>
      )}

      <hr className="divider" />

      <div className="disclaimer-banner" style={{ marginBottom: 10 }}>
        <span className="disclaimer-icon">⚠️</span>
        <span>{real ? 'Indikasi perubahan dari citra nyata. Penyebab BELUM diklasifikasi; perlu verifikasi.' : 'Prediksi ML pada data simulasi. Bukan verifikasi lapangan.'}</span>
      </div>

      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase' }}>Verifikasi (operator)</div>
      <VerifyForm id={p.id} onDone={setVerified} />

      {onDetailClick && (
        <button
          className="btn btn-primary"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={() => onDetailClick(p.id)}
        >
          Detail Lengkap →
        </button>
      )}
    </div>
  );
}
