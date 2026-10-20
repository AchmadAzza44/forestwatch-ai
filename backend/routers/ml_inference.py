"""
ForestWatch AI - ML Inference Router
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from ml.classifier import extract_features, predict, explain, get_model, CATEGORIES, CATEGORY_LABELS
from gis.sentinel_mock import generate_change_detection_pair
from datetime import datetime
import random
import zlib

router = APIRouter(prefix="/ml", tags=["ml-inference"])


class PredictionRequest(BaseModel):
    """Semua fitur wajib diisi; tidak ada nilai bawaan tersembunyi."""
    ndvi_before: float = Field(..., ge=-1, le=1, description="NDVI sebelum gangguan")
    ndvi_after: float = Field(..., ge=-1, le=1, description="NDVI sesudah gangguan")
    nbr_before: float = Field(..., ge=-1, le=1, description="NBR sebelum")
    nbr_after: float = Field(..., ge=-1, le=1, description="NBR sesudah")
    evi_before: float = Field(..., ge=-1, le=3, description="EVI sebelum")
    evi_after: float = Field(..., ge=-1, le=3, description="EVI sesudah")
    b4_red_after: float = Field(..., ge=0, le=10000, description="Sentinel-2 B4 (red), reflektansi x10000")
    b8_nir_after: float = Field(..., ge=0, le=10000, description="Sentinel-2 B8 (NIR)")
    b11_swir1_after: float = Field(..., ge=0, le=10000, description="Sentinel-2 B11 (SWIR1)")
    b12_swir2_after: float = Field(..., ge=0, le=10000, description="Sentinel-2 B12 (SWIR2)")
    sar_vv_before: float = Field(..., ge=-40, le=10, description="Sentinel-1 VV sebelum (dB)")
    sar_vv_after: float = Field(..., ge=-40, le=10, description="Sentinel-1 VV sesudah (dB)")
    cloud_coverage: float = Field(..., ge=0, le=100)
    area_ha: float = Field(..., gt=0, le=100000)


class MockSentinelRequest(BaseModel):
    latitude: float = Field(..., ge=-11, le=6)
    longitude: float = Field(..., ge=95, le=141)
    region: str = Field("Kalimantan Timur", max_length=100)
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    seed: Optional[int] = Field(None, description="Seed simulasi; default diturunkan dari koordinat sehingga hasil dapat diulang")


def _features_from_metrics(metrics: dict, cloud: float, area_ha: float):
    return extract_features(
        ndvi_before=metrics["ndvi_before"], ndvi_after=metrics["ndvi_after"],
        nbr_before=metrics["nbr_before"], nbr_after=metrics["nbr_after"],
        evi_before=metrics["evi_before"], evi_after=metrics["evi_after"],
        b4_red_after=metrics["b4_red_after"], b8_nir_after=metrics["b8_nir_after"],
        b11_swir1_after=metrics["b11_swir1_after"], b12_swir2_after=metrics["b12_swir2_after"],
        sar_vv_before=metrics["sar_vv_before"], sar_vv_after=metrics["sar_vv_after"],
        cloud_coverage=cloud, area_ha=area_ha,
    )


@router.post("/predict")
def run_prediction(req: PredictionRequest):
    """Klasifikasi kemungkinan penyebab dari fitur spektral. Hasil = prediksi model, bukan penyebab terverifikasi."""
    features = extract_features(**req.model_dump())
    result = predict(features)
    return {
        "input": req.model_dump(),
        "prediction": result,
        "explanation": explain(features, result["predicted_category"]),
        "ndvi_change": round(req.ndvi_after - req.ndvi_before, 4),
        "nbr_change": round(req.nbr_after - req.nbr_before, 4),
        "label": "prediksi_model",
    }


@router.post("/simulate-sentinel")
def simulate_sentinel(req: MockSentinelRequest):
    """
    Bangkitkan data Sentinel SIMULASI untuk suatu lokasi lalu jalankan inferensi.

    Kategori simulasi dipilih deterministik dari seed; kategori itu disebut `simulated_truth` dan
    dipisahkan dari `prediction` agar tampak seberapa jauh model cocok dengan data simulasinya.
    """
    try:
        period_start = datetime.fromisoformat(req.period_start) if req.period_start else datetime(2023, 1, 1)
        period_end = datetime.fromisoformat(req.period_end) if req.period_end else datetime(2023, 6, 1)
    except ValueError:
        raise HTTPException(status_code=422, detail="period_start/period_end harus berformat ISO 8601 (YYYY-MM-DD).")
    if period_end <= period_start:
        raise HTTPException(status_code=422, detail="period_end harus setelah period_start.")

    seed = req.seed if req.seed is not None else zlib.crc32(f"{req.latitude:.4f},{req.longitude:.4f}".encode())
    rng = random.Random(seed)
    sim_category = rng.choice(["pertanian", "penebangan", "kebakaran", "pertambangan"])
    pair = generate_change_detection_pair(sim_category, req.region, period_start, period_end, rng=rng)
    metrics = pair["change_metrics"]
    area_ha = round(rng.uniform(20, 200), 2)
    prediction = predict(_features_from_metrics(metrics, pair["sentinel2_before"].get("cloud_coverage_pct", 20.0), area_ha))

    return {
        "location": {"lat": req.latitude, "lon": req.longitude, "region": req.region},
        "seed": seed,
        "area_ha": area_ha,
        "sentinel2_before": pair["sentinel2_before"],
        "sentinel2_after": pair["sentinel2_after"],
        "sentinel1_summary": {
            "before_VV_dB": pair["sentinel1_before"]["backscatter"]["VV_dB"],
            "after_VV_dB": pair["sentinel1_after"]["backscatter"]["VV_dB"],
        },
        "change_metrics": metrics,
        "simulated_truth": sim_category,
        "prediction": prediction,
        "simulation_note": (
            "Data SIMULASI, bukan citra nyata. Pada produksi data diambil dari Google Earth Engine "
            "(earthengine-api). Kesesuaian prediksi dengan simulated_truth tidak menunjukkan akurasi di lapangan."
        ),
    }


@router.get("/model-info")
def get_model_info():
    """Get current model information."""
    _, evaluation = get_model()
    return {
        "model_type": evaluation.get("model_type"),
        "version": "1.0.0-synthetic",
        "categories": [
            {"id": cat, "label": CATEGORY_LABELS[cat]} for cat in CATEGORIES
        ],
        "features_used": evaluation.get("feature_names"),
        "accuracy": round(evaluation.get("accuracy", 0), 4),
        "training_data": "Synthetic (mirror of Sentinel spectral profiles)",
        "baselines": evaluation.get("baselines"),
        "disclaimer": evaluation.get("note"),
    }
