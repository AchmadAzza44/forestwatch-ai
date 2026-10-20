"""Deteksi INDIKASI perubahan tutupan vegetasi dari dua komposit Sentinel-2. Murni numpy/scipy (mudah diuji).

Hasilnya adalah kandidat lokasi yang perlu diperiksa, BUKAN bukti deforestasi dan BUKAN penyebab perubahan.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np
from scipy import ndimage

# SCL (Scene Classification Layer) Sentinel-2 L2A: kelas yang dianggap pengamatan VALID untuk analisis vegetasi.
# 4 vegetasi, 5 non-vegetasi, 6 air, 7 tidak terklasifikasi. Dikecualikan: 0 nodata, 1 jenuh, 2 area gelap,
# 3 bayangan awan, 8-9 awan sedang/tinggi, 10 cirrus tipis, 11 salju.
VALID_SCL = (4, 5, 6, 7)
REFLECTANCE_SCALE = 10000.0
EPS = 1e-6


@dataclass(frozen=True)
class DetectionParams:
    """Ambang deteksi. Semuanya pilihan analis (bukan standar baku) dan dicatat pada setiap eksekusi."""

    forest_ndvi_min: float = 0.70      # piksel dianggap vegetasi rapat pada periode awal bila NDVI >= nilai ini
    dnbr_min: float = 0.27             # penurunan NBR minimum (NBR_awal - NBR_akhir); 0,27 lazim untuk dampak sedang-tinggi
    dndvi_max: float = -0.20           # perubahan NDVI maksimum (NDVI_akhir - NDVI_awal) (negatif = berkurang)
    min_area_ha: float = 1.0           # gugus lebih kecil dibuang (mengurangi derau)
    min_valid_obs: int = 1             # jumlah pengamatan valid minimum per periode per piksel
    open_iterations: int = 1           # pembukaan morfologi untuk menghapus piksel terpencil

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    return (nir - red) / (nir + red + EPS)


def nbr(nir: np.ndarray, swir2: np.ndarray) -> np.ndarray:
    return (nir - swir2) / (nir + swir2 + EPS)


def valid_mask_from_scl(scl: np.ndarray) -> np.ndarray:
    return np.isin(scl, VALID_SCL)


CLOUD_BUFFER_PX = 3  # tepi awan/bayangan sering lolos dari SCL (haze, bayangan tipis): buang 3 piksel (60 m) di sekelilingnya


def composite(bands: list[dict[str, np.ndarray]], scl: list[np.ndarray], buffer_px: int = CLOUD_BUFFER_PX) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Median per piksel dari pengamatan VALID saja (awan/bayangan diabaikan). Kembalikan (band, jumlah pengamatan valid).

    Piksel tak valid diperluas ``buffer_px`` piksel per scene agar tepi awan dan bayangan tidak ikut terhitung.

    Piksel tanpa pengamatan valid bernilai NaN. ``bands``: daftar dict {nama: array reflektansi mentah (DN)}, sejajar dengan ``scl``.
    """
    if not bands or len(bands) != len(scl):
        raise ValueError("bands dan scl harus berjumlah sama dan tidak kosong.")
    shape = scl[0].shape
    if any(s.shape != shape for s in scl) or any(b[k].shape != shape for b in bands for k in b):
        raise ValueError("Semua array harus berukuran sama.")
    valid = np.stack([valid_mask_from_scl(s) for s in scl])
    if buffer_px > 0:
        valid = np.stack([~ndimage.binary_dilation(~v, structure=np.ones((3, 3), bool), iterations=buffer_px) for v in valid])
    names = list(bands[0])
    out: dict[str, np.ndarray] = {}
    for name in names:
        stack = np.stack([b[name].astype("float32") / REFLECTANCE_SCALE for b in bands])
        stack[~valid] = np.nan
        with np.errstate(all="ignore"):
            out[name] = np.nanmedian(stack, axis=0).astype("float32")
    return out, valid.sum(axis=0).astype("int16")


def detect_change(before: dict[str, np.ndarray], after: dict[str, np.ndarray], n_before: np.ndarray, n_after: np.ndarray,
                  pixel_area_m2: float, params: DetectionParams | None = None) -> dict[str, Any]:
    """Cari piksel yang berhutan/bervegetasi rapat pada awal lalu turun tajam pada akhir; kelompokkan menjadi gugus.

    Kembalikan dict: mask (bool), labels (int), stats per gugus, dan ringkasan cakupan data.
    Nama band yang diperlukan: B04 (red), B08 (nir), B12 (swir2), sebagai reflektansi 0-1 (NaN = tidak valid).
    """
    p = params or DetectionParams()
    ndvi_b, ndvi_a = ndvi(before["B08"], before["B04"]), ndvi(after["B08"], after["B04"])
    nbr_b, nbr_a = nbr(before["B08"], before["B12"]), nbr(after["B08"], after["B12"])
    observed = (n_before >= p.min_valid_obs) & (n_after >= p.min_valid_obs) & np.isfinite(ndvi_b) & np.isfinite(ndvi_a) \
        & np.isfinite(nbr_b) & np.isfinite(nbr_a)
    dnbr, dndvi = nbr_b - nbr_a, ndvi_a - ndvi_b
    candidate = observed & (ndvi_b >= p.forest_ndvi_min) & (dnbr >= p.dnbr_min) & (dndvi <= p.dndvi_max)
    if p.open_iterations > 0:
        candidate = ndimage.binary_opening(candidate, structure=np.ones((3, 3), bool), iterations=p.open_iterations)
    labels, n = ndimage.label(candidate, structure=np.ones((3, 3), int))  # 8-ketetanggaan
    min_px = max(1, int(np.ceil(p.min_area_ha * 10_000 / pixel_area_m2)))
    clusters = []
    if n:
        ids = np.arange(1, n + 1)
        sizes = ndimage.sum(candidate, labels, ids).astype(int)
        keep = ids[sizes >= min_px]
        keep_mask = np.isin(labels, keep)
        labels = np.where(keep_mask, labels, 0)
        for cid in keep:
            m = labels == cid
            clusters.append({"label": int(cid), "pixels": int(m.sum()), "area_ha": float(m.sum() * pixel_area_m2 / 10_000),
                             "mean_dnbr": float(dnbr[m].mean()), "mean_dndvi": float(dndvi[m].mean()),
                             "mean_ndvi_before": float(ndvi_b[m].mean()), "mean_ndvi_after": float(ndvi_a[m].mean())})
    mask = labels > 0
    forest_before = observed & (ndvi_b >= p.forest_ndvi_min)
    return {
        "mask": mask, "labels": labels, "clusters": clusters,
        "observed_fraction": float(observed.mean()),
        "forest_before_ha": float(forest_before.sum() * pixel_area_m2 / 10_000),
        "changed_ha": float(mask.sum() * pixel_area_m2 / 10_000),
        "params": p.to_dict(),
    }
