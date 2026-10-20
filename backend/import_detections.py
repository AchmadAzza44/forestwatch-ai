"""Impor hasil `pipeline.run_detection` (Sentinel-2 NYATA) ke database sebagai INDIKASI perubahan.

Kategori penyebab sengaja `tidak_diketahui`: classifier proyek dilatih pada data sintetis dan tidak berlaku untuk citra nyata,
sehingga tidak dijalankan pada data ini. Idempoten: impor ulang run yang sama menggantikan barisnya.
Pemakaian: python import_detections.py ../data/detections/ikn_2020_2023
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from database import SessionLocal, init_db
from models.disturbance import ForestDisturbance

REAL_SOURCE = "Sentinel-2 L2A COG (citra nyata)"
PROVINCES = {"IKN": ("Kalimantan Timur - IKN", "Kalimantan Timur")}


def _mean_date(scenes: list[dict]) -> datetime:
    days = [datetime.fromisoformat(s["tanggal"]) for s in scenes]
    return datetime.fromtimestamp(sum(d.timestamp() for d in days) / len(days))


def import_run(run_dir: str | Path, region: str, province: str, session=None) -> int:
    run_dir = Path(run_dir)
    meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    collection = json.loads((run_dir / "detections.geojson").read_text(encoding="utf-8"))
    from shapely.geometry import shape

    tag = f"[run:{meta['nama']}]"
    before, after = meta["periode_awal"]["scene"], meta["periode_akhir"]["scene"]
    period_start, period_end = _mean_date(before), _mean_date(after)
    detected = max(datetime.fromisoformat(s["tanggal"]) for s in after)
    own = session is None
    db = session or SessionLocal()
    try:
        db.query(ForestDisturbance).filter(ForestDisturbance.notes.like(f"{tag}%")).delete(synchronize_session="fetch")
        for f in collection["features"]:
            p = f["properties"]
            geom = shape(f["geometry"])
            if geom.geom_type == "MultiPolygon":
                geom = max(geom.geoms, key=lambda g: g.area)
            db.add(ForestDisturbance(
                geometry=f"SRID=4326;{geom.wkt}", centroid_lat=p["centroid_lat"], centroid_lon=p["centroid_lon"], area_ha=p["area_ha"],
                region=region, province=province, detected_date=detected, period_start=period_start, period_end=period_end,
                category="tidak_diketahui", confidence_score=0.0, confidence_level="rendah",
                ndvi_before=p["mean_ndvi_before"], ndvi_after=p["mean_ndvi_after"], ndvi_change=p["mean_dndvi"],
                sentinel2_scene_id=f"{after[0]['id']} (+{len(after) - 1} scene komposit)",
                data_source=REAL_SOURCE,
                feature_vector={"mean_dnbr": p["mean_dnbr"], "parameter": meta["parameter"]},
                notes=(f"{tag} Indikasi perubahan vegetasi dari citra nyata ({meta['periode_awal']['rentang'][0][:7]} -> "
                       f"{meta['periode_akhir']['rentang'][0][:7]}); BUKAN deforestasi terverifikasi. Penyebab belum diklasifikasi. "
                       f"dNBR rata-rata {p['mean_dnbr']}."),
            ))
        db.commit()
        return len(collection["features"])
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    init_db()
    name = Path(sys.argv[1]).name
    region, province = PROVINCES["IKN"]
    print(f"{import_run(sys.argv[1], region, province)} indikasi diimpor dari {name}")
