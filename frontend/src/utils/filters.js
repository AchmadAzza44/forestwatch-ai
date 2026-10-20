/** Ubah state filter UI menjadi parameter query API (satu tempat agar peta dan dashboard konsisten). */
export function toParams(filters = {}) {
  const params = {};
  if (filters.categories?.length) params.categories = filters.categories.join(',');
  if (filters.provinces?.length) params.provinces = filters.provinces.join(',');
  if (filters.date_from) params.date_from = filters.date_from;
  if (filters.date_to) params.date_to = filters.date_to;
  if (filters.min_confidence) params.min_confidence = filters.min_confidence;
  if (filters.source && filters.source !== 'semua') params.source = filters.source;
  return params;
}
