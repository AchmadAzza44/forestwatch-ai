/**
 * ForestWatch AI - API Service
 * Axios client for all backend API calls.
 * Set VITE_API_URL in .env to point to your backend.
 */
import axios from 'axios';

export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Disturbances ──────────────────────────────────────────
export const disturbancesAPI = {
  getAll: (params = {}) => api.get('/disturbances/', { params }),
  getGeoJSON: (params = {}) => api.get('/disturbances/geojson', { params }),
  getById: (id) => api.get(`/disturbances/${id}`),
  validate: (id, body, token) => api.patch(`/disturbances/${id}/validate`, body, { headers: { 'X-API-Key': token } }),
  getNew: (since) => api.get('/disturbances/new', { params: { since } }),
};

// ─── Dashboard ─────────────────────────────────────────────
export const dashboardAPI = {
  getStats: (params = {}) => api.get('/dashboard/stats', { params }),
  getTimeline: (period = 'monthly', params = {}) => api.get('/dashboard/timeline', { params: { period, ...params } }),
  getRegionComparison: (params = {}) => api.get('/dashboard/region-comparison', { params }),
  getPeriodComparison: (params) => api.get('/dashboard/period-comparison', { params }),
  getModelPerformance: () => api.get('/dashboard/model-performance'),
  getValidationSummary: (params = {}) => api.get('/dashboard/validation-summary', { params }),
};

// ─── ML Inference ──────────────────────────────────────────
export const mlAPI = {
  predict: (data) => api.post('/ml/predict', data),
  simulateSentinel: (data) => api.post('/ml/simulate-sentinel', data),
  getModelInfo: () => api.get('/ml/model-info'),
};

// ─── Auth & ekspor ─────────────────────────────────────────
export const authAPI = {
  role: (token) => api.get('/auth/role', { headers: token ? { 'X-API-Key': token } : {} }),
};

export const exportURL = (kind, params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return `${API_BASE}/export/${kind}${qs ? `?${qs}` : ''}`;
};

// ─── Utility ───────────────────────────────────────────────
export const utilAPI = {
  health: () => api.get('/health'),
  getRegions: () => api.get('/regions'),
};

export default api;
