/**
 * ForestWatch AI - Interactive Leaflet Map
 */
import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { createRoot } from 'react-dom/client';
import { getCategoryColor, getCategoryConfig } from '../../utils/colors';
import DisturbancePopup from './DisturbancePopup';
import MapLegend from './MapLegend';
import FilterPanel from '../FilterPanel/FilterPanel';
import { disturbancesAPI, dashboardAPI } from '../../services/api';
import { toParams } from '../../utils/filters';

// Fix Leaflet default icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const INDONESIA_CENTER = [-2.5, 118.0];
const DEFAULT_ZOOM = 5;

function createDisturbanceIcon(category, confidenceLevel) {
  const color = getCategoryColor(category);
  const cat = getCategoryConfig(category);
  const size = confidenceLevel === 'tinggi' ? 14 : confidenceLevel === 'sedang' ? 12 : 10;
  const borderColor = {
    tinggi: '#00e5a0', sedang: '#f59e0b', rendah: '#ef4444'
  }[confidenceLevel] || '#ffffff';

  return L.divIcon({
    className: '',
    html: `<div style="
      width:${size}px; height:${size}px;
      background:${color};
      border:2px solid ${borderColor};
      border-radius:50%;
      box-shadow: 0 0 8px ${color}80, 0 2px 6px rgba(0,0,0,0.5);
      cursor:pointer;
      transition: transform 0.15s ease;
    " title="${cat.label}"></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

export default function MapView() {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);
  const [filters, setFilters] = useState({});
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [markerCount, setMarkerCount] = useState(0);

  // Initialize map
  useEffect(() => {
    if (mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
      center: INDONESIA_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: false,
      attributionControl: true,
    });

    // Dark satellite base layer
    L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      {
        attribution: '© OpenStreetMap contributors © CARTO',
        subdomains: 'abcd',
        maxZoom: 19,
      }
    ).addTo(map);

    // Custom zoom control (top-right)
    L.control.zoom({ position: 'topright' }).addTo(map);

    // Markers layer
    markersLayerRef.current = L.layerGroup().addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Load data when filters change
  useEffect(() => {
    loadDisturbances();
  }, [filters]);

  // Load stats
  useEffect(() => {
    dashboardAPI.getStats(toParams(filters))
      .then((r) => setStats(r.data))
      .catch(() => setStats(null));
  }, [filters]);

  const loadDisturbances = async () => {
    if (!mapInstanceRef.current) return;
    setLoading(true);
    setError(null);

    try {
      const params = toParams(filters);

      const res = await disturbancesAPI.getGeoJSON(params);
      const geojson = res.data;

      // Clear existing markers
      markersLayerRef.current.clearLayers();

      // Add markers
      let count = 0;
      if (geojson.features) {
        geojson.features.forEach((feature) => {
          const p = feature.properties;
          const geom = feature.geometry;

          let latlng;
          if (geom.type === 'Point') {
            latlng = [geom.coordinates[1], geom.coordinates[0]];
          } else if (geom.type === 'Polygon') {
            // Use centroid
            const coords = geom.coordinates[0];
            const lat = coords.reduce((s, c) => s + c[1], 0) / coords.length;
            const lon = coords.reduce((s, c) => s + c[0], 0) / coords.length;
            latlng = [lat, lon];
          } else return;

          const icon = createDisturbanceIcon(p.category, p.confidence_level);
          const marker = L.marker(latlng, { icon });

          // Popup
          marker.on('click', () => {
            const container = document.createElement('div');
            const root = createRoot(container);
            root.render(
              <DisturbancePopup
                feature={{ ...feature, geometry: { type: 'Point', coordinates: [latlng[1], latlng[0]] } }}
                onDetailClick={null}
              />
            );
            L.popup({ maxWidth: 320, className: 'fw-popup' })
              .setLatLng(latlng)
              .setContent(container)
              .openOn(mapInstanceRef.current);
          });

          markersLayerRef.current.addLayer(marker);
          count++;
        });
      }
      setMarkerCount(count);
      if (count > 0 && Object.keys(params).length > 0) {
        // Setelah filter diterapkan, arahkan peta ke sebaran hasil agar langsung terlihat.
        const bounds = markersLayerRef.current.getBounds?.();
        if (bounds && bounds.isValid()) mapInstanceRef.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 11 });
      }
    } catch (err) {
      // Tidak ada data pengganti: peta dikosongkan dan kegagalan ditampilkan.
      markersLayerRef.current.clearLayers();
      setMarkerCount(0);
      setError('Gagal memuat data dari backend (port 8000). Peta tidak menampilkan data apa pun.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-content" style={{ position: 'relative' }}>
      {/* Map topbar */}
      <div className="topbar">
        <div>
          <div className="topbar-title">🗺️ Peta GIS Interaktif</div>
          <div className="topbar-subtitle">
            {loading ? 'Memuat data...' : `${markerCount} indikasi gangguan ditampilkan`}
            {error && <span style={{ color: '#f59e0b', marginLeft: 8 }}>⚠️ {error}</span>}
          </div>
        </div>
        <div className="topbar-actions">
          {stats && (
            <div style={{ display: 'flex', gap: 16, fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              <span>
                <strong style={{ color: 'var(--color-accent)' }}>{stats.total_detections}</strong> total deteksi
              </span>
              <span>
                <strong style={{ color: '#f59e0b' }}>{stats.total_area_ha?.toLocaleString('id-ID', { maximumFractionDigits: 0 })}</strong> ha
              </span>
            </div>
          )}
          <button className="btn btn-ghost btn-sm" onClick={loadDisturbances}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Map */}
      <div className="map-wrapper" style={{ flex: 1, position: 'relative' }}>
        <div ref={mapRef} style={{ width: '100%', height: '100%' }} />

        {/* Filter Panel */}
        <FilterPanel filters={filters} onChange={setFilters} />

        {/* Legend */}
        <MapLegend />

        {/* Quick stats overlay */}
        {stats && (
          <div className="map-panel map-panel-stats">
            <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: 10 }}>
              Ringkasan
            </div>
            {stats.categories_distribution &&
              Object.entries(stats.categories_distribution).slice(0, 5).map(([cat, data]) => {
                const config = { pertanian: { icon: '🌾', color: '#f59e0b', shortLabel: 'Pertanian' }, penebangan: { icon: '🪓', color: '#ef4444', shortLabel: 'Penebangan' }, pertambangan: { icon: '⛏️', color: '#94a3b8', shortLabel: 'Tambang' }, kebakaran: { icon: '🔥', color: '#f97316', shortLabel: 'Kebakaran' }, alami: { icon: '🌊', color: '#60a5fa', shortLabel: 'Alami' }, tidak_diketahui: { icon: '❓', color: '#a78bfa', shortLabel: 'Tdk Diketahui' } }[cat] || {};
                return (
                  <div key={cat} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5, fontSize: '0.76rem' }}>
                    <span>{config.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                        <span style={{ color: 'var(--text-secondary)' }}>{config.shortLabel}</span>
                        <span style={{ color: config.color, fontWeight: 600 }}>{data.count}</span>
                      </div>
                      <div className="progress-bar">
                        <div
                          className="progress-fill"
                          style={{
                            width: `${(data.count / stats.total_detections) * 100}%`,
                            background: config.color
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })
            }
          </div>
        )}

        {/* Loading overlay */}
        {loading && (
          <div style={{
            position: 'absolute', inset: 0,
            background: 'rgba(8,13,23,0.5)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 2000,
          }}>
            <div className="loading-spinner">
              <div className="spinner" />
              <span>Memuat data peta...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
