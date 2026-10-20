"""CLI: deteksi indikasi perubahan vegetasi antara dua periode dari Sentinel-2 L2A nyata -> GeoJSON + run.json + pratinjau PNG.

Contoh:
  python -m pipeline.run_detection --name ikn_2020_2023 --tile 50MMD --aoi 116.55 -1.20 116.85 -0.95 \
      --before 2020-08-01 2020-10-31 --after 2023-08-01 2023-10-31 --scenes 4
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

from .change_detection import DetectionParams, composite, detect_change, ndvi
from .s2_cog import list_scenes, pick_scenes, read_aoi

LIMITATIONS = [
    "Hasil adalah INDIKASI perubahan vegetasi, bukan deforestasi terverifikasi dan bukan penyebab perubahan.",
    "Piksel 20 m; 'hutan' didefinisikan dari NDVI periode awal (>= ambang), bukan dari peta tutupan hutan resmi.",
    "Komposit median dari beberapa scene dalam satu periode; perubahan musiman/fenologi dan sisa awan dapat memicu positif palsu.",
    "Tidak ada validasi terhadap data referensi independen atau verifikasi lapangan.",
    "Kategori penyebab TIDAK diberikan: classifier proyek dilatih pada data sintetis dan tidak berlaku untuk citra nyata.",
]


def _to_utm_bounds(aoi: tuple[float, float, float, float], epsg: int) -> tuple[float, float, float, float]:
    from pyproj import Transformer

    tr = Transformer.from_crs(4326, epsg, always_xy=True)
    xs, ys = zip(*(tr.transform(lon, lat) for lon in (aoi[0], aoi[2]) for lat in (aoi[1], aoi[3])))
    return (float(np.floor(min(xs) / 20) * 20), float(np.floor(min(ys) / 20) * 20), float(np.ceil(max(xs) / 20) * 20), float(np.ceil(max(ys) / 20) * 20))


def _epsg_for_tile(tile: str) -> int:
    from .s2_cog import parse_tile

    zone, band = parse_tile(tile).split("/")[:2]
    return (32600 if band >= "N" else 32700) + int(zone)


def _period(scenes, aoi_utm, label):
    reads = []
    for s in scenes:
        bands, scl, transform = read_aoi(s, aoi_utm)
        reads.append((s, bands, scl, transform))
        print(f"  {label}: {s.scene_id} (awan tile {s.cloud_cover_pct:.0f}%)")
    comp, n_valid = composite([r[1] for r in reads], [r[2] for r in reads])
    return comp, n_valid, reads[0][3]


def polygonize(labels: np.ndarray, transform, clusters: list[dict], epsg: int) -> list[dict]:
    import rasterio.features
    from pyproj import Transformer
    from shapely.geometry import mapping, shape
    from shapely.ops import transform as shp_transform

    tr = Transformer.from_crs(epsg, 4326, always_xy=True)
    by_label = {c["label"]: c for c in clusters}
    feats = []
    for geom, value in rasterio.features.shapes(labels.astype("int32"), mask=labels > 0, transform=transform, connectivity=8):
        cluster = by_label.get(int(value))
        if cluster is None:
            continue
        g = shp_transform(tr.transform, shape(geom)).simplify(0.00001)
        c = g.centroid
        feats.append({"type": "Feature", "geometry": mapping(g),
                      "properties": {"label": cluster["label"], "area_ha": round(cluster["area_ha"], 2),
                                     "mean_dnbr": round(cluster["mean_dnbr"], 3), "mean_dndvi": round(cluster["mean_dndvi"], 3),
                                     "mean_ndvi_before": round(cluster["mean_ndvi_before"], 3), "mean_ndvi_after": round(cluster["mean_ndvi_after"], 3),
                                     "centroid_lat": round(c.y, 6), "centroid_lon": round(c.x, 6)}})
    return feats


def preview(path: Path, before, after, mask, ndvi_b, ndvi_a) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def rgb(c):
        img = np.stack([c["B12"], c["B08"], c["B04"]], axis=2)  # warna palsu SWIR2-NIR-merah
        img = np.nan_to_num(img, nan=0.0)
        return np.clip(img / 0.45, 0, 1)

    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    ax[0].imshow(rgb(before)); ax[0].set_title("Periode awal (komposit, warna palsu SWIR2/NIR/Merah)")
    ax[1].imshow(rgb(after)); ax[1].set_title("Periode akhir (komposit)")
    ax[2].imshow(np.nan_to_num(ndvi_a - ndvi_b, nan=0.0), cmap="RdYlGn", vmin=-0.6, vmax=0.6)
    ax[2].contour(mask, levels=[0.5], colors="k", linewidths=0.6); ax[2].set_title("Δ NDVI (akhir - awal) dan gugus kandidat (kontur)")
    for a in ax:
        a.axis("off")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--tile", required=True)
    ap.add_argument("--aoi", type=float, nargs=4, metavar=("LON_MIN", "LAT_MIN", "LON_MAX", "LAT_MAX"), required=True)
    ap.add_argument("--before", nargs=2, required=True, metavar=("DARI", "SAMPAI"))
    ap.add_argument("--after", nargs=2, required=True, metavar=("DARI", "SAMPAI"))
    ap.add_argument("--scenes", type=int, default=4, help="jumlah scene per periode untuk komposit")
    ap.add_argument("--max-cloud", type=float, default=85.0)
    ap.add_argument("--out", default="data/detections")
    a = ap.parse_args()

    epsg = _epsg_for_tile(a.tile)
    aoi_utm = _to_utm_bounds(tuple(a.aoi), epsg)
    periods = {}
    for key, (d0, d1) in (("before", a.before), ("after", a.after)):
        start, end = date.fromisoformat(d0), date.fromisoformat(d1)
        scenes = list_scenes(a.tile, start, end)
        chosen = pick_scenes(scenes, a.scenes, a.max_cloud)
        if not chosen:
            raise SystemExit(f"Tidak ada scene {key} dengan awan <= {a.max_cloud}% pada {d0}..{d1} ({len(scenes)} scene ditemukan).")
        print(f"Periode {key}: {len(scenes)} scene tersedia, dipakai {len(chosen)}")
        periods[key] = (chosen, *_period(chosen, aoi_utm, key))
    (sb, cb, nb, transform), (sa, ca, na, _) = periods["before"][0:1] + periods["before"][1:], periods["after"][0:1] + periods["after"][1:]
    params = DetectionParams()
    res = detect_change(cb, ca, nb, na, pixel_area_m2=400.0, params=params)
    feats = polygonize(res["labels"], transform, res["clusters"], epsg)

    out = Path(a.out) / a.name
    out.mkdir(parents=True, exist_ok=True)
    geojson = {"type": "FeatureCollection", "features": feats}
    (out / "detections.geojson").write_text(json.dumps(geojson), encoding="utf-8")
    preview(out / "preview.png", cb, ca, res["mask"], ndvi(cb["B08"], cb["B04"]), ndvi(ca["B08"], ca["B04"]))
    meta = {
        "nama": a.name, "dibuat_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sumber": "Sentinel-2 L2A COG, AWS Open Data (sentinel-cogs); data Copernicus Sentinel (ESA)",
        "tile": a.tile, "aoi_lonlat": a.aoi, "crs_analisis": f"EPSG:{epsg}", "piksel_m": 20,
        "periode_awal": {"rentang": a.before, "scene": [{"id": s.scene_id, "tanggal": s.acquired.isoformat(), "awan_tile_pct": s.cloud_cover_pct} for s in sb]},
        "periode_akhir": {"rentang": a.after, "scene": [{"id": s.scene_id, "tanggal": s.acquired.isoformat(), "awan_tile_pct": s.cloud_cover_pct} for s in sa]},
        "parameter": res["params"],
        "hasil": {"jumlah_gugus": len(res["clusters"]), "luas_berubah_ha": round(res["changed_ha"], 1), "luas_vegetasi_rapat_awal_ha": round(res["forest_before_ha"], 1),
                  "fraksi_piksel_teramati": round(res["observed_fraction"], 3)},
        "geojson_sha256": hashlib.sha256((out / "detections.geojson").read_bytes()).hexdigest(),
        "perangkat_lunak": {"python": platform.python_version(), "numpy": np.__version__},
        "batasan": LIMITATIONS,
    }
    (out / "run.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(meta["hasil"], indent=2))


if __name__ == "__main__":
    main()
