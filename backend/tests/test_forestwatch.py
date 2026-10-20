import copy
import json
import os
import random
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from conftest import GOOD_INPUT
from database import SessionLocal
from gis.sentinel_mock import generate_change_detection_pair
from ml.classifier import CATEGORIES, build_and_train_model
from models.disturbance import ForestDisturbance
from routers.disturbances import disturbance_to_geojson_feature

BACKEND = Path(__file__).resolve().parents[1]


# ---------- ML ----------
def test_training_reproducible_across_python_hash_seeds():
    """Regresi: hash() bawaan membuat data latih berbeda tiap proses."""
    code = "from ml.classifier import build_and_train_model as b; e=b()[1]; print(e['accuracy'], e['macro_f1'])"
    outs = {
        subprocess.run([sys.executable, "-c", code], cwd=BACKEND, capture_output=True, text=True,
                       env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": str(BACKEND)}).stdout
        for seed in ("1", "2", "3")
    }
    assert len(outs) == 1 and next(iter(outs)).strip()


def test_evaluation_has_baselines_and_per_class_metrics():
    _, ev = build_and_train_model()
    assert set(ev["baselines"]) == {"majority_class", "logistic_regression"}
    assert ev["baselines"]["majority_class"]["macro_f1"] < ev["macro_f1"]
    assert set(ev["confusion_matrix_labels"]) == set(CATEGORIES)
    assert "SINTETIS" in ev["note"].upper() or "synthetic" in ev["note"].lower()


# ---------- /ml ----------
def test_predict_requires_every_feature(client):
    for missing in ("b11_swir1_after", "evi_after", "sar_vv_after"):
        body = {k: v for k, v in GOOD_INPUT.items() if k != missing}
        assert client.post("/api/ml/predict", json=body).status_code == 422


def test_predict_validates_ranges(client):
    assert client.post("/api/ml/predict", json={**GOOD_INPUT, "ndvi_after": 2}).status_code == 422
    assert client.post("/api/ml/predict", json={**GOOD_INPUT, "area_ha": 0}).status_code == 422


def test_predict_uses_given_swir_not_defaults(client):
    """Fitur SWIR harus memengaruhi hasil (dulu diganti konstanta)."""
    a = client.post("/api/ml/predict", json=GOOD_INPUT).json()["prediction"]["all_probabilities"]
    b = client.post("/api/ml/predict", json={**GOOD_INPUT, "b11_swir1_after": 1000, "b12_swir2_after": 700}).json()["prediction"]["all_probabilities"]
    assert a != b


def test_predict_response_contract(client):
    r = client.post("/api/ml/predict", json=GOOD_INPUT).json()
    p = r["prediction"]
    assert p["predicted_category"] in CATEGORIES and 0 <= p["confidence_score"] <= 1
    assert abs(sum(p["all_probabilities"].values()) - 1) < 0.01
    assert "verifikasi" in p["model_disclaimer"].lower() and "needs_verification" in p
    assert r["label"] == "prediksi_model"


def test_low_confidence_maps_to_unknown(client):
    ambiguous = dict(ndvi_before=0.65, ndvi_after=0.35, nbr_before=0.6, nbr_after=0.3, evi_before=0.55, evi_after=0.3,
                     b4_red_after=850, b8_nir_after=2100, b11_swir1_after=1700, b12_swir2_after=1000,
                     sar_vv_before=-10, sar_vv_after=-14, cloud_coverage=40, area_ha=80)
    p = client.post("/api/ml/predict", json=ambiguous).json()["prediction"]
    if p["confidence_score"] < 0.45:
        assert p["predicted_category"] == "tidak_diketahui"
    assert p["needs_verification"] == (p["predicted_category"] == "tidak_diketahui" or p["confidence_level"] == "rendah")


def test_simulation_is_reproducible_and_labelled(client):
    body = {"latitude": -1.2, "longitude": 116.8, "region": "Kalimantan Timur"}
    a, b = client.post("/api/ml/simulate-sentinel", json=body).json(), client.post("/api/ml/simulate-sentinel", json=body).json()
    assert a == b
    c = client.post("/api/ml/simulate-sentinel", json={**body, "seed": 999}).json()
    assert c["seed"] == 999 and "SIMULASI" in c["simulation_note"] and "simulated_truth" in c


def test_simulation_rejects_bad_period(client):
    r = client.post("/api/ml/simulate-sentinel", json={"latitude": -1, "longitude": 117, "period_start": "2023-06-01", "period_end": "2023-01-01"})
    assert r.status_code == 422
    assert client.post("/api/ml/simulate-sentinel", json={"latitude": -1, "longitude": 117, "period_start": "bukan-tanggal"}).status_code == 422


def test_mock_generator_seeded_identical():
    args = ("kebakaran", "X", datetime(2023, 1, 1), datetime(2023, 5, 1))
    a = generate_change_detection_pair(*args, rng=random.Random(5))["change_metrics"]
    b = generate_change_detection_pair(*args, rng=random.Random(5))["change_metrics"]
    assert a == b and {"b11_swir1_after", "evi_after"} <= set(a)


# ---------- seed / data ----------
def test_seeded_category_is_model_output_not_ground_truth(seeded_db):
    db = SessionLocal()
    rows = db.query(ForestDisturbance).all()
    db.close()
    assert len(rows) == 60
    for r in rows:
        probs = r.prediction_probabilities
        top = max(probs, key=probs.get)
        # kategori tersimpan = argmax probabilitas, atau 'tidak_diketahui' bila di bawah ambang
        assert r.category == top or r.category == "tidak_diketahui"
        assert "simulated_truth" in r.feature_vector and len(r.feature_vector) == 18


def test_model_agrees_with_its_own_simulation_far_above_chance(seeded_db):
    """Pelatihan dan data demo memakai generator yang sama; kesesuaian harus jauh di atas acak (1/6)."""
    db = SessionLocal()
    rows = db.query(ForestDisturbance).all()
    db.close()
    agree = sum(r.category == r.feature_vector["simulated_truth"] for r in rows) / len(rows)
    unknown = sum(r.category == "tidak_diketahui" for r in rows) / len(rows)
    assert agree > 0.5, f"kesesuaian hanya {agree:.2f}"
    assert unknown < 0.4


def test_seed_is_reproducible():
    from seed_data import REGIONS, create_disturbance
    mk = lambda: create_disturbance(None, REGIONS[0], 100, random.Random(3))
    a, b = mk(), mk()
    assert (a.category, a.area_ha, a.centroid_lat, a.confidence_score) == (b.category, b.area_ha, b.centroid_lat, b.confidence_score)


# ---------- API: filter konsisten ----------
def test_stats_and_list_agree_under_same_filters(client):
    params = {"categories": "kebakaran,pertanian", "min_confidence": 0.5}
    stats = client.get("/api/dashboard/stats", params=params).json()
    geo = client.get("/api/disturbances/geojson", params=params).json()
    assert stats["total_detections"] == geo["count"]
    assert set(stats["categories_distribution"]) <= {"kebakaran", "pertanian"}
    timeline = client.get("/api/dashboard/timeline", params=params).json()["timeline"]
    assert sum(t["count"] for t in timeline) == stats["total_detections"]
    regions = client.get("/api/dashboard/region-comparison", params=params).json()["regions"]
    assert sum(r["total"] for r in regions) == stats["total_detections"]


def test_province_filter_applies_everywhere(client):
    stats = client.get("/api/dashboard/stats", params={"provinces": "Riau"}).json()
    assert set(stats["provinces_distribution"]) <= {"Riau"}
    assert client.get("/api/disturbances/geojson", params={"provinces": "Riau"}).json()["count"] == stats["total_detections"]


def test_unfiltered_total_matches_database(client):
    assert client.get("/api/dashboard/stats").json()["total_detections"] == 60


def test_period_comparison_delta(client):
    q = dict(a_from="2023-01-01", a_to="2023-06-30", b_from="2023-07-01", b_to="2023-12-31")
    r = client.get("/api/dashboard/period-comparison", params=q).json()
    assert r["delta"]["total_detections"] == r["period_b"]["total_detections"] - r["period_a"]["total_detections"]
    for c, d in r["delta"]["categories"].items():
        assert d == r["period_b"]["categories"].get(c, 0) - r["period_a"]["categories"].get(c, 0)
    assert client.get("/api/dashboard/period-comparison", params={**q, "a_from": "2024-01-01"}).status_code == 422


def test_invalid_query_values_rejected(client):
    assert client.get("/api/dashboard/timeline", params={"period": "weekly"}).status_code == 422
    assert client.get("/api/dashboard/stats", params={"min_confidence": 2}).status_code == 422
    assert client.get("/api/disturbances/99999").status_code == 404


def test_model_performance_exposes_real_metrics(client):
    r = client.get("/api/dashboard/model-performance").json()
    assert 0.5 < r["accuracy"] <= 1 and len(r["confusion_matrix"]) == len(CATEGORIES)
    assert r["baselines"]["majority_class"]["accuracy"] < r["accuracy"]
    assert sum(map(sum, r["confusion_matrix"])) == r["test_samples"]


# ---------- GeoJSON polygon ----------
def test_polygon_geometry_is_returned_not_point_fallback():
    from geoalchemy2.shape import from_shape
    poly = Polygon([(117.0, -1.0), (117.01, -1.0), (117.01, -0.99), (117.0, -0.99)])
    d = ForestDisturbance(id=1, geometry=from_shape(poly, srid=4326), centroid_lat=-0.995, centroid_lon=117.005,
                          detected_date=datetime(2023, 1, 1), period_start=datetime(2023, 1, 1), period_end=datetime(2023, 2, 1),
                          category="pertanian", confidence_score=0.8, confidence_level="tinggi", region="r", province="p")
    f = disturbance_to_geojson_feature(d)
    assert f["geometry"]["type"] == "Polygon"
    assert f["geometry"]["coordinates"][0][0] == [117.0, -1.0]
    json.dumps(f)


def test_health_reports_database(client):
    r = client.get("/api/health").json()
    assert r["database"] == "ok" and r["status"] == "healthy"
