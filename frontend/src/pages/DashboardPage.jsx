/**
 * ForestWatch AI - Dashboard Page
 * Analytics dashboard with charts and data table
 */
import { useState, useEffect } from 'react';
import {
  AreaChart, Area, BarChart, Bar, Cell, PieChart, Pie, Sector,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { dashboardAPI, disturbancesAPI, exportURL } from '../services/api';
import { CategoryBadge, ConfidenceBadge } from '../components/common/Badges';
import { formatDate, formatHa, formatNumber } from '../utils/formatters';
import { CATEGORY_LIST, getCategoryColor } from '../utils/colors';

// Custom Pie active shape
const renderActiveShape = (props) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent, value } = props;
  return (
    <g>
      <text x={cx} y={cy - 10} textAnchor="middle" fill="var(--text-primary)" style={{ fontSize: 18, fontWeight: 700, fontFamily: 'var(--font-display)' }}>
        {value}
      </text>
      <text x={cx} y={cy + 14} textAnchor="middle" fill="var(--text-secondary)" style={{ fontSize: 11 }}>
        {payload.name}
      </text>
      <text x={cx} y={cy + 30} textAnchor="middle" fill={fill} style={{ fontSize: 11, fontWeight: 600 }}>
        {(percent * 100).toFixed(1)}%
      </text>
      <Sector cx={cx} cy={cy} innerRadius={innerRadius} outerRadius={outerRadius + 8} startAngle={startAngle} endAngle={endAngle} fill={fill} />
      <Sector cx={cx} cy={cy} innerRadius={outerRadius + 12} outerRadius={outerRadius + 16} startAngle={startAngle} endAngle={endAngle} fill={fill} />
    </g>
  );
};

const ChartTooltipStyle = {
  contentStyle: {
    background: 'var(--color-bg-secondary)',
    border: '1px solid var(--border-medium)',
    borderRadius: 8,
    fontSize: 12,
    color: 'var(--text-primary)',
  },
  labelStyle: { color: 'var(--text-secondary)', marginBottom: 4 },
};

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [recentData, setRecentData] = useState([]);
  const [activePieIndex, setActivePieIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setError(null);
      const [statsRes, timelineRes, recentRes] = await Promise.allSettled([
        dashboardAPI.getStats(),
        dashboardAPI.getTimeline('monthly'),
        disturbancesAPI.getAll({ page: 1, page_size: 20 }),
      ]);
      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
      if (timelineRes.status === 'fulfilled') setTimeline(timelineRes.value.data.timeline);
      if (recentRes.status === 'fulfilled') setRecentData(recentRes.value.data.items || []);
      if ([statsRes, timelineRes, recentRes].some((r) => r.status === 'rejected')) {
        // Tidak ada data pengganti: tampilkan kegagalan apa adanya.
        setError('Sebagian atau seluruh data gagal dimuat dari backend (http://localhost:8000). Tidak ada data cadangan yang ditampilkan.');
      }
      setLoading(false);
    };
    fetchAll();
  }, []);

  // Prepare pie data
  const pieData = stats?.categories_distribution
    ? Object.entries(stats.categories_distribution).map(([cat, data]) => ({
        name: CATEGORY_LIST.find((c) => c.id === cat)?.shortLabel || cat,
        value: data.count,
        cat,
        fill: getCategoryColor(cat),
      }))
    : [];

  // Region bar data
  const regionData = Object.entries(stats?.provinces_distribution || {}).map(([prov, data]) => ({
    name: prov.split(' ')[0],
    fullName: prov,
    count: data.count,
    area: data.area_ha,
  }));

  const kpiCards = [
    { icon: '🚨', label: 'Total Deteksi', value: formatNumber(stats?.total_detections), color: '#ef4444', trend: 'Data simulasi' },
    { icon: '🌲', label: 'Total Area (Ha)', value: formatNumber(stats?.total_area_ha, 0), color: '#f59e0b', trend: 'Estimasi' },
    { icon: '✅', label: 'Tervalidasi', value: formatNumber(stats?.validated_count), color: '#00e5a0', trend: stats?.total_detections ? `${((stats.validated_count / stats.total_detections) * 100).toFixed(0)}% dari total` : '—' },
    { icon: '🎯', label: 'Keyakinan Tinggi', value: formatNumber(stats?.high_confidence_count), color: '#60a5fa', trend: `≥75% confidence` },
  ];

  return (
    <div className="page-content" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Topbar */}
      <div className="topbar">
        <div>
          <div className="topbar-title">📊 Dashboard Analitik</div>
          <div className="topbar-subtitle">Ringkasan deteksi dan distribusi gangguan hutan</div>
        </div>
        <div className="topbar-actions">
          <div className="disclaimer-banner" style={{ padding: '4px 12px', fontSize: '0.72rem' }}>
            <span>⚠️</span>
            <span>Data simulasi — bukan data lapangan nyata</span>
          </div>
        </div>
      </div>

      <div className="dashboard-layout" style={{ padding: '20px', gap: 16, overflowY: 'auto' }}>
        {loading && <div className="disclaimer-banner"><span>⏳</span><span>Memuat data dari backend...</span></div>}
        {error && <div className="disclaimer-banner" role="alert"><span>⚠️</span><span>{error}</span></div>}
        {!loading && !error && stats && stats.total_detections === 0 && (
          <div className="disclaimer-banner"><span>ℹ️</span><span>Belum ada indikasi gangguan pada database. Jalankan seeder atau impor data hasil analisis.</span></div>
        )}
        {/* KPI Row */}
        <div className="kpi-grid stagger-children">
          {kpiCards.map((kpi) => (
            <div key={kpi.label} className="kpi-card" style={{ '--kpi-color': kpi.color }}>
              <div className="kpi-icon">{kpi.icon}</div>
              <div className="kpi-value">{kpi.value}</div>
              <div className="kpi-label">{kpi.label}</div>
              <div className="kpi-trend">{kpi.trend}</div>
            </div>
          ))}
        </div>

        <div className="card" style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <div className="card-title">⬇️ Ekspor</div>
          <a className="btn btn-ghost" href={exportURL('disturbances.csv')} download>Data indikasi (CSV)</a>
          <a className="btn btn-ghost" href={exportURL('report.pdf')} download>Laporan ringkas (PDF)</a>
          <a className="btn btn-ghost" href={exportURL('disturbances.csv', { source: 'citra_nyata' })} download>Hanya citra nyata (CSV)</a>
        </div>

        <PeriodComparison />

        {/* Row 2: Timeline + Donut */}
        <div className="dashboard-row dashboard-row-2" style={{ gridTemplateColumns: '2fr 1fr' }}>
          {/* Timeline Area Chart */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">📈 Tren Temporal Deteksi</div>
              <span className="tag">Bulanan</span>
            </div>
            <div style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeline} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    {CATEGORY_LIST.map((cat) => (
                      <linearGradient key={cat.id} id={`grad-${cat.id}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={cat.color} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={cat.color} stopOpacity={0} />
                      </linearGradient>
                    ))}
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                  <XAxis dataKey="period" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickLine={false} />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip {...ChartTooltipStyle} />
                  <Area type="monotone" dataKey="kebakaran" stackId="1" stroke="#f97316" fill="url(#grad-kebakaran)" />
                  <Area type="monotone" dataKey="pertanian" stackId="1" stroke="#f59e0b" fill="url(#grad-pertanian)" />
                  <Area type="monotone" dataKey="penebangan" stackId="1" stroke="#ef4444" fill="url(#grad-penebangan)" />
                  <Area type="monotone" dataKey="pertambangan" stackId="1" stroke="#94a3b8" fill="url(#grad-pertambangan)" />
                  <Area type="monotone" dataKey="alami" stackId="1" stroke="#60a5fa" fill="url(#grad-alami)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Donut Chart */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">🥧 Distribusi Kategori</div>
            </div>
            <div style={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    activeIndex={activePieIndex}
                    activeShape={renderActiveShape}
                    data={pieData}
                    cx="50%" cy="50%"
                    innerRadius={55} outerRadius={80}
                    dataKey="value"
                    onMouseEnter={(_, index) => setActivePieIndex(index)}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={entry.cat} fill={entry.fill} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
              {pieData.map((d) => (
                <div key={d.cat} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  <div style={{ width: 8, height: 8, borderRadius: 2, background: d.fill, flexShrink: 0 }} />
                  {d.name}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Row 3: Region bar + Category area breakdown */}
        <div className="dashboard-row dashboard-row-2">
          {/* Region comparison bar */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">🗺️ Perbandingan Per Provinsi</div>
            </div>
            <div style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={regionData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickLine={false} />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip {...ChartTooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                  <Bar dataKey="count" name="Jumlah Deteksi" radius={[4, 4, 0, 0]}>
                    {regionData.map((_, i) => (
                      <Cell key={i} fill={['#f59e0b', '#ef4444', '#f97316', '#60a5fa', '#a78bfa'][i % 5]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Category stats table */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">📋 Statistik Kategori</div>
            </div>
            <table className="data-table" style={{ fontSize: '0.78rem' }}>
              <thead>
                <tr>
                  <th>Kategori</th>
                  <th style={{ textAlign: 'right' }}>Deteksi</th>
                  <th style={{ textAlign: 'right' }}>Area (Ha)</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats?.categories_distribution || {}).map(([cat, data]) => (
                  <tr key={cat}>
                    <td><CategoryBadge category={cat} /></td>
                    <td style={{ textAlign: 'right' }} className="primary">{data.count}</td>
                    <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>{formatNumber(data.area_ha, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent detections table */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🕐 Deteksi Terbaru</div>
            <span className="tag">20 terakhir</span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Kategori</th>
                  <th>Keyakinan</th>
                  <th>Region</th>
                  <th>Area</th>
                  <th>NDVI Δ</th>
                  <th>Tgl Deteksi</th>
                  <th>Validasi</th>
                </tr>
              </thead>
              <tbody>
                {recentData.length === 0 && (
                  <tr><td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    {loading ? 'Memuat...' : 'Tidak ada data untuk ditampilkan.'}
                  </td></tr>
                )}
                {recentData.map((d) => (
                  <tr key={d.id}>
                    <td className="mono">#{d.id}</td>
                    <td><CategoryBadge category={d.category} /></td>
                    <td><ConfidenceBadge level={d.confidence_level} score={d.confidence_score} /></td>
                    <td className="primary" style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.region}</td>
                    <td>{formatHa(d.area_ha)}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', color: d.ndvi_change < 0 ? '#ef4444' : '#22c55e' }}>
                      {d.ndvi_change?.toFixed(3)}
                    </td>
                    <td>{formatDate(d.detected_date)}</td>
                    <td style={{ color: d.is_validated ? '#00e5a0' : 'var(--text-muted)' }}>
                      {d.is_validated ? '✓' : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}


function PeriodComparison() {
  const [range, setRange] = useState({ a_from: '2023-01-01', a_to: '2023-12-31', b_from: '2024-01-01', b_to: '2024-12-31' });
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const invalid = range.a_from > range.a_to || range.b_from > range.b_to;

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await dashboardAPI.getPeriodComparison(range);
      setData(res.data);
    } catch (e) {
      setData(null);
      setError(typeof e?.response?.data?.detail === 'string' ? e.response.data.detail : 'Perbandingan gagal: backend tidak dapat dihubungi.');
    } finally {
      setLoading(false);
    }
  };

  const cats = data ? Object.keys(data.delta.categories) : [];
  const sign = (n) => (n > 0 ? `+${n}` : `${n}`);

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">🗓️ Perbandingan Dua Periode</div>
        <span className="tag">Selisih = B − A</span>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'flex-end' }}>
        {[['a_from', 'Periode A: dari'], ['a_to', 'sampai'], ['b_from', 'Periode B: dari'], ['b_to', 'sampai']].map(([k, label]) => (
          <label key={k} className="form-group" style={{ margin: 0 }}>
            <span className="form-label">{label}</span>
            <input type="date" className="form-input" value={range[k]} onChange={(e) => setRange({ ...range, [k]: e.target.value })} />
          </label>
        ))}
        <button className="btn btn-primary" onClick={run} disabled={loading || invalid}>
          {loading ? 'Memuat...' : 'Bandingkan'}
        </button>
      </div>
      {invalid && <div role="alert" style={{ color: '#f59e0b', marginTop: 8 }}>Tanggal awal harus sebelum tanggal akhir pada setiap periode.</div>}
      {error && <div role="alert" style={{ color: '#f59e0b', marginTop: 8 }}>⚠️ {error}</div>}
      {data && (
        <div style={{ overflowX: 'auto', marginTop: 12 }}>
          <table className="data-table">
            <thead>
              <tr><th>Metrik</th><th style={{ textAlign: 'right' }}>Periode A</th><th style={{ textAlign: 'right' }}>Periode B</th><th style={{ textAlign: 'right' }}>Selisih</th></tr>
            </thead>
            <tbody>
              <tr><td>Total indikasi</td><td style={{ textAlign: 'right' }}>{data.period_a.total_detections}</td><td style={{ textAlign: 'right' }}>{data.period_b.total_detections}</td><td style={{ textAlign: 'right' }}>{sign(data.delta.total_detections)}</td></tr>
              <tr><td>Total area (Ha)</td><td style={{ textAlign: 'right' }}>{formatNumber(data.period_a.total_area_ha, 0)}</td><td style={{ textAlign: 'right' }}>{formatNumber(data.period_b.total_area_ha, 0)}</td><td style={{ textAlign: 'right' }}>{sign(data.delta.total_area_ha)}</td></tr>
              {cats.map((c) => (
                <tr key={c}>
                  <td><CategoryBadge category={c} /></td>
                  <td style={{ textAlign: 'right' }}>{data.period_a.categories[c] || 0}</td>
                  <td style={{ textAlign: 'right' }}>{data.period_b.categories[c] || 0}</td>
                  <td style={{ textAlign: 'right' }}>{sign(data.delta.categories[c])}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 6 }}>{data.note}</div>
        </div>
      )}
    </div>
  );
}
