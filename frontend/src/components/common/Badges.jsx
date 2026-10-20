/**
 * ForestWatch AI - Category Badge Component
 */
import { getCategoryConfig } from '../../utils/colors';

export function CategoryBadge({ category, size = 'md' }) {
  const config = getCategoryConfig(category);
  return (
    <span className={`category-badge ${config.badgeClass}`}>
      <span>{config.icon}</span>
      <span>{config.shortLabel}</span>
    </span>
  );
}

export function ConfidenceBadge({ level, score }) {
  const classes = {
    tinggi: 'conf-tinggi',
    sedang: 'conf-sedang',
    rendah: 'conf-rendah',
  };
  const labels = { tinggi: 'Tinggi', sedang: 'Sedang', rendah: 'Rendah' };

  return (
    <span className={`conf-badge ${classes[level] || 'conf-rendah'}`}>
      {labels[level] || level} {score !== undefined && `(${(score * 100).toFixed(0)}%)`}
    </span>
  );
}

export function NDVIBar({ before, after }) {
  const beforePct = Math.max(0, Math.min(100, ((before + 0.2) / 1.2) * 100));
  const afterPct = Math.max(0, Math.min(100, ((after + 0.2) / 1.2) * 100));
  const change = after - before;

  return (
    <div style={{ fontSize: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3, color: 'var(--text-muted)' }}>
        <span>NDVI Sebelum</span>
        <span style={{ fontFamily: 'var(--font-mono)' }}>{before?.toFixed(3)}</span>
      </div>
      <div className="progress-bar" style={{ marginBottom: 5 }}>
        <div className="progress-fill" style={{ width: `${beforePct}%`, background: '#22c55e' }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3, color: 'var(--text-muted)' }}>
        <span>NDVI Sesudah</span>
        <span style={{ fontFamily: 'var(--font-mono)' }}>{after?.toFixed(3)}</span>
      </div>
      <div className="progress-bar" style={{ marginBottom: 5 }}>
        <div className="progress-fill" style={{ width: `${afterPct}%`, background: '#ef4444' }} />
      </div>
      <div style={{ textAlign: 'right', color: change < 0 ? '#ef4444' : '#22c55e', fontWeight: 600 }}>
        Δ {change?.toFixed(3)}
      </div>
    </div>
  );
}
