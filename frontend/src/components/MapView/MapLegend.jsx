/**
 * ForestWatch AI - Map Legend Component
 */
import { CATEGORY_LIST } from '../../utils/colors';

export default function MapLegend() {
  return (
    <div className="map-panel map-panel-legend">
      <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: 10 }}>
        Legenda Kategori
      </div>
      {CATEGORY_LIST.map((cat) => (
        <div key={cat.id} className="legend-item">
          <div
            className="legend-dot"
            style={{ background: cat.color, boxShadow: `0 0 6px ${cat.color}60` }}
          />
          <span>{cat.icon}</span>
          <span>{cat.shortLabel}</span>
        </div>
      ))}

      <hr className="divider" style={{ margin: '10px 0' }} />

      <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: 8 }}>
        Keyakinan Model
      </div>
      {[
        { label: 'Tinggi (≥75%)', color: '#00e5a0' },
        { label: 'Sedang (50-75%)', color: '#f59e0b' },
        { label: 'Rendah (<50%)', color: '#ef4444' },
      ].map(({ label, color }) => (
        <div key={label} className="legend-item">
          <div style={{
            width: 12, height: 12, borderRadius: 2,
            border: `2px solid ${color}`, flexShrink: 0
          }} />
          <span>{label}</span>
        </div>
      ))}

      <hr className="divider" style={{ margin: '10px 0' }} />
      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
        ⚠️ Data simulasi.<br />
        Bukan verifikasi lapangan.
      </div>
    </div>
  );
}
