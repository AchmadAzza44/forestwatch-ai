/**
 * Category configuration: colors, icons, labels
 */
export const CATEGORIES = {
  pertanian: {
    id: 'pertanian',
    label: 'Pertanian / Land Clearing',
    shortLabel: 'Pertanian',
    color: '#f59e0b',
    icon: '🌾',
    shape: 'circle',
    badgeClass: 'badge-pertanian',
  },
  penebangan: {
    id: 'penebangan',
    label: 'Penebangan Liar',
    shortLabel: 'Penebangan',
    color: '#ef4444',
    icon: '🪓',
    shape: 'triangle',
    badgeClass: 'badge-penebangan',
  },
  pertambangan: {
    id: 'pertambangan',
    label: 'Pertambangan',
    shortLabel: 'Tambang',
    color: '#94a3b8',
    icon: '⛏️',
    shape: 'square',
    badgeClass: 'badge-pertambangan',
  },
  kebakaran: {
    id: 'kebakaran',
    label: 'Kebakaran Hutan',
    shortLabel: 'Kebakaran',
    color: '#f97316',
    icon: '🔥',
    shape: 'diamond',
    badgeClass: 'badge-kebakaran',
  },
  alami: {
    id: 'alami',
    label: 'Gangguan Alami',
    shortLabel: 'Alami',
    color: '#60a5fa',
    icon: '🌊',
    shape: 'pentagon',
    badgeClass: 'badge-alami',
  },
  tidak_diketahui: {
    id: 'tidak_diketahui',
    label: 'Tidak Diketahui / Perlu Verifikasi',
    shortLabel: 'Tdk Diketahui',
    color: '#a78bfa',
    icon: '❓',
    shape: 'hexagon',
    badgeClass: 'badge-tidak_diketahui',
  },
};

export const CATEGORY_LIST = Object.values(CATEGORIES);

export const getCategoryConfig = (cat) =>
  CATEGORIES[cat] || CATEGORIES.tidak_diketahui;

export const getCategoryColor = (cat) =>
  getCategoryConfig(cat).color;

export const CONFIDENCE_LEVELS = {
  tinggi: { label: 'Tinggi', color: '#00e5a0', class: 'conf-tinggi', min: 0.75 },
  sedang: { label: 'Sedang', color: '#f59e0b', class: 'conf-sedang', min: 0.50 },
  rendah: { label: 'Rendah', color: '#ef4444', class: 'conf-rendah', min: 0 },
};
