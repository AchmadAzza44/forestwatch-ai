/**
 * ForestWatch AI - Map Filter Panel
 */
import { CATEGORY_LIST } from '../../utils/colors';

const PROVINCE_LABELS = {
  'Kalimantan Timur': 'Kaltim', 'Kalimantan Tengah': 'Kalteng', 'Sumatera Selatan': 'Sumsel', 'Riau': 'Riau', 'Papua Barat': 'Papua Barat',
};

const PROVINCES = [
  'Kalimantan Timur', 'Kalimantan Tengah', 'Sumatera Selatan', 'Riau', 'Papua Barat'
];

export default function FilterPanel({ filters, onChange }) {
  const toggleCategory = (cat) => {
    const cats = filters.categories || [];
    const next = cats.includes(cat)
      ? cats.filter((c) => c !== cat)
      : [...cats, cat];
    onChange({ ...filters, categories: next.length === 0 ? null : next });
  };

  const toggleProvince = (prov) => {
    const provs = filters.provinces || [];
    const next = provs.includes(prov)
      ? provs.filter((p) => p !== prov)
      : [...provs, prov];
    onChange({ ...filters, provinces: next.length === 0 ? null : next });
  };

  return (
    <div className="map-panel map-panel-filter">
      <div className="filter-panel">
        <div className="filter-title">
          <span>⚙️</span> Filter Data
        </div>

        {/* Source filter */}
        <div className="filter-group">
          <div className="filter-label">Sumber Data</div>
          <div className="filter-chips">
            {[['semua', 'Semua'], ['citra_nyata', '🛰️ Citra nyata'], ['simulasi', 'Simulasi']].map(([id, label]) => (
              <button
                key={id}
                className={`filter-chip${(filters.source || 'semua') === id ? ' active' : ''}`}
                onClick={() => onChange({ ...filters, source: id === 'semua' ? null : id })}
                title={id === 'citra_nyata' ? 'Indikasi dari Sentinel-2 nyata; penyebab belum diklasifikasi' : id === 'simulasi' ? 'Data buatan untuk demonstrasi' : 'Semua sumber'}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Category filter */}
        <div className="filter-group">
          <div className="filter-label">Kategori Gangguan</div>
          <div className="filter-chips">
            {CATEGORY_LIST.map((cat) => {
              const active = !filters.categories || filters.categories.includes(cat.id);
              return (
                <button
                  key={cat.id}
                  className={`filter-chip${active ? ' active' : ''}`}
                  style={{ '--chip-color': cat.color }}
                  onClick={() => toggleCategory(cat.id)}
                  title={cat.label}
                >
                  {cat.icon} {cat.shortLabel}
                </button>
              );
            })}
          </div>
        </div>

        {/* Province filter */}
        <div className="filter-group">
          <div className="filter-label">Provinsi</div>
          <div className="filter-chips">
            {PROVINCES.map((prov) => {
              const active = !filters.provinces || filters.provinces.includes(prov);
              return (
                <button
                  key={prov}
                  className={`filter-chip${active ? ' active' : ''}`}
                  onClick={() => toggleProvince(prov)}
                >
                  {PROVINCE_LABELS[prov] || prov}
                </button>
              );
            })}
          </div>
        </div>

        {/* Confidence filter */}
        <div className="filter-group">
          <div className="filter-label">
            Min. Keyakinan Model: {filters.min_confidence
              ? `${(filters.min_confidence * 100).toFixed(0)}%`
              : 'Semua'}
          </div>
          <input
            type="range"
            className="filter-slider"
            min={0} max={0.9} step={0.05}
            value={filters.min_confidence || 0}
            onChange={(e) =>
              onChange({
                ...filters,
                min_confidence: parseFloat(e.target.value) || null,
              })
            }
          />
        </div>

        {/* Date range */}
        <div className="filter-group">
          <div className="filter-label">Periode Deteksi</div>
          <div style={{ display: 'grid', gap: 6 }}>
            <input
              type="date"
              className="filter-input"
              value={filters.date_from || ''}
              onChange={(e) => onChange({ ...filters, date_from: e.target.value || null })}
              placeholder="Dari"
            />
            <input
              type="date"
              className="filter-input"
              value={filters.date_to || ''}
              onChange={(e) => onChange({ ...filters, date_to: e.target.value || null })}
              placeholder="Sampai"
            />
          </div>
        </div>

        {/* Reset */}
        <button
          className="btn btn-ghost"
          style={{ width: '100%', justifyContent: 'center', fontSize: '0.78rem' }}
          onClick={() => onChange({})}
        >
          ↩ Reset Filter
        </button>
      </div>
    </div>
  );
}
