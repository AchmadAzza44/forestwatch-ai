/**
 * ForestWatch AI - Sidebar Navigation Component
 */
import { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { authAPI } from '../../services/api';

const NAV_ITEMS = [
  { path: '/map', icon: '🗺️', label: 'Peta GIS', section: 'Pemantauan' },
  { path: '/dashboard', icon: '📊', label: 'Dashboard', section: 'Pemantauan' },
  { path: '/analysis', icon: '🔬', label: 'Analisis ML', section: 'Machine Learning' },
  { path: '/about', icon: 'ℹ️', label: 'Metodologi', section: 'Informasi' },
];

export default function Sidebar() {
  const location = useLocation();
  const [token, setToken] = useState(() => { try { return localStorage.getItem('fw_token') || ''; } catch { return ''; } });
  const [role, setRole] = useState('viewer');
  const [authMsg, setAuthMsg] = useState(null);

  // Token tersimpan dicek saat halaman dibuka agar peran yang ditampilkan sesuai.
  useEffect(() => { if (token) applyToken(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const applyToken = async () => {
    try {
      const res = await authAPI.role(token);
      setRole(res.data.role);
      setAuthMsg(null);
      try { token ? localStorage.setItem('fw_token', token) : localStorage.removeItem('fw_token'); } catch { /* penyimpanan tidak tersedia */ }
    } catch (e) {
      setRole('viewer');
      setAuthMsg(e?.response?.status === 401 ? 'Token tidak valid.' : 'Backend tidak terjangkau.');
    }
  };

  const sections = [...new Set(NAV_ITEMS.map((i) => i.section))];

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🌿</div>
        <div className="sidebar-logo-text">
          <div className="sidebar-logo-name">ForestWatch AI</div>
          <div className="sidebar-logo-version">v1.0 · MVP</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {sections.map((section) => (
          <div key={section}>
            <div className="sidebar-section-label">{section}</div>
            {NAV_ITEMS.filter((i) => i.section === section).map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `nav-item${isActive ? ' active' : ''}`
                }
              >
                <span className="nav-icon">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div style={{ padding: '0 16px 12px' }}>
        <label className="filter-label" htmlFor="fw-token">Token operator (opsional)</label>
        <input id="fw-token" type="password" className="filter-input" value={token} autoComplete="off"
          onChange={(e) => setToken(e.target.value)} onBlur={applyToken} placeholder="kosong = pembaca" />
        <div role="status" style={{ fontSize: '0.68rem', color: authMsg ? '#f59e0b' : 'var(--text-muted)', marginTop: 4 }}>
          Peran: <strong>{role}</strong>{authMsg ? ` · ${authMsg}` : ''}
        </div>
      </div>

      {/* Footer status */}
      <div className="sidebar-footer">
        <div className="data-status-badge">
          <div className="status-dot" />
          <div>
            <div style={{ fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.72rem' }}>
              Sumber data berlabel
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
              Citra nyata vs simulasi: lihat filter
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
