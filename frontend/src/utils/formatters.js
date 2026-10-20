/**
 * Formatting utilities
 */

export const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('id-ID', {
    day: '2-digit', month: 'short', year: 'numeric'
  });
};

export const formatDateShort = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('id-ID', {
    month: 'short', year: 'numeric'
  });
};

export const formatNumber = (n, decimals = 0) => {
  if (n === null || n === undefined) return '-';
  return Number(n).toLocaleString('id-ID', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const formatHa = (ha) => {
  if (!ha) return '-';
  if (ha >= 1000) return `${(ha / 1000).toFixed(1)} ribu ha`;
  return `${ha.toFixed(1)} ha`;
};

export const formatPercent = (n) => {
  if (n === null || n === undefined) return '-';
  return `${(n * 100).toFixed(1)}%`;
};

export const formatConfidence = (score) => {
  if (score === null || score === undefined) return '-';
  return `${(score * 100).toFixed(1)}%`;
};

export const formatNDVI = (n) => {
  if (n === null || n === undefined) return '-';
  return Number(n).toFixed(3);
};

export const formatCoord = (n) => {
  if (n === null || n === undefined) return '-';
  return Number(n).toFixed(5) + '°';
};

export const formatPeriod = (start, end) => {
  if (!start || !end) return '-';
  const s = formatDateShort(start);
  const e = formatDateShort(end);
  return `${s} – ${e}`;
};
