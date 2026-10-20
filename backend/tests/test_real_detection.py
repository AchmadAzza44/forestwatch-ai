import json
from pathlib import Path

import pytest
from shapely.geometry import box, mapping

from database import SessionLocal
from import_detections import REAL_SOURCE, import_run
from models.disturbance import ForestDisturbance


@pytest.fixture
def run_dir(tmp_path):
    d = tmp_path / "run_uji"
    d.mkdir()
    feats = []
    for i in range(3):
        g = box(116.60 + i * 0.01, -0.97, 116.605 + i * 0.01, -0.965)
        c = g.centroid
        feats.append({"type": "Feature", "geometry": mapping(g), "properties": {
            "label": i + 1, "area_ha": 12.5 + i, "mean_dnbr": 0.4, "mean_dndvi": -0.35, "mean_ndvi_before": 0.8,
            "mean_ndvi_after": 0.45, "centroid_lat": c.y, "centroid_lon": c.x}})
    (d / "detections.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    (d / "run.json").write_text(json.dumps({
        "nama": "run_uji", "parameter": {"dnbr_min": 0.27},
        "periode_awal": {"rentang": ["2020-08-01", "2020-10-31"], "scene": [{"id": "A", "tanggal": "2020-09-14"}, {"id": "B", "tanggal": "2020-09-24"}]},
        "periode_akhir": {"rentang": ["2023-08-01", "2023-10-31"], "scene": [{"id": "C", "tanggal": "2023-09-04"}, {"id": "D", "tanggal": "2023-09-22"}]}}))
    return d


def test_import_marks_real_data_unclassified_and_unverified(seeded_db, run_dir):
    db = SessionLocal()
    try:
        assert import_run(run_dir, "Kalimantan Timur - IKN", "Kalimantan Timur", session=db) == 3
        rows = db.query(ForestDisturbance).filter(ForestDisturbance.data_source == REAL_SOURCE).all()
        assert len(rows) == 3
        for r in rows:
            assert r.category == "tidak_diketahui" and r.confidence_score == 0.0 and r.is_validated is False
            assert r.prediction_probabilities is None and "BUKAN deforestasi terverifikasi" in r.notes
            assert r.period_start < r.period_end and r.detected_date.year == 2023
        # impor ulang run yang sama menggantikan, tidak menggandakan
        import_run(run_dir, "Kalimantan Timur - IKN", "Kalimantan Timur", session=db)
        assert db.query(ForestDisturbance).filter(ForestDisturbance.data_source == REAL_SOURCE).count() == 3
    finally:
        db.close()


def test_source_filter_separates_real_from_simulated_everywhere(client, seeded_db, run_dir):
    db = SessionLocal()
    import_run(run_dir, "Kalimantan Timur - IKN", "Kalimantan Timur", session=db)
    db.close()
    real = client.get("/api/dashboard/stats", params={"source": "citra_nyata"}).json()
    sim = client.get("/api/dashboard/stats", params={"source": "simulasi"}).json()
    allr = client.get("/api/dashboard/stats").json()
    assert real["total_detections"] == 3 and sim["total_detections"] == 60 and allr["total_detections"] == 63
    assert set(real["categories_distribution"]) == {"tidak_diketahui"}
    geo = client.get("/api/disturbances/geojson", params={"source": "citra_nyata"}).json()
    assert geo["count"] == 3 and all(f["properties"]["source_type"] == "citra_nyata" and f["properties"]["needs_verification"] for f in geo["features"])
    lst = client.get("/api/disturbances/", params={"source": "citra_nyata"}).json()
    assert lst["total"] == 3 and all(i["source_type"] == "citra_nyata" for i in lst["items"])
    tl = client.get("/api/dashboard/timeline", params={"source": "citra_nyata"}).json()["timeline"]
    assert sum(t["count"] for t in tl) == 3
    assert client.get("/api/dashboard/stats", params={"source": "ngawur"}).status_code == 422


@pytest.fixture(autouse=True)
def _cleanup_real_rows():
    yield
    db = SessionLocal()
    db.query(ForestDisturbance).filter(ForestDisturbance.data_source == REAL_SOURCE).delete()
    db.commit()
    db.close()


def test_every_stats_endpoint_accepts_source(client, seeded_db):
    for path, extra in (("stats", {}), ("timeline", {}), ("region-comparison", {}),
                        ("period-comparison", dict(a_from="2023-01-01", a_to="2023-12-31", b_from="2024-01-01", b_to="2024-12-31"))):
        r = client.get(f"/api/dashboard/{path}", params={"source": "simulasi", **extra})
        assert r.status_code == 200, (path, r.text)


# ---------- peran, verifikasi, ekspor, penjelasan, notifikasi ----------
from datetime import datetime, timedelta

from config import settings
from conftest import GOOD_INPUT


@pytest.fixture
def tokens(monkeypatch):
    monkeypatch.setattr(settings, "OPERATOR_TOKEN", "op-token-123")
    monkeypatch.setattr(settings, "ADMIN_TOKEN", "admin-token-456")


def test_validation_requires_operator_role(client, seeded_db, tokens):
    url = "/api/disturbances/1/validate"
    body = {"verified_category": "pertanian", "note": "cek citra resolusi tinggi"}
    assert client.patch(url, json=body).status_code == 403                                   # viewer
    assert client.patch(url, json=body, headers={"X-API-Key": "salah"}).status_code == 401    # token salah
    ok = client.patch(url, json=body, headers={"X-API-Key": "op-token-123"})
    assert ok.status_code == 200 and ok.json()["verified_category"] == "pertanian" and ok.json()["is_validated"] is True
    assert client.patch(url, json={"verified_category": "ngawur"}, headers={"X-API-Key": "op-token-123"}).status_code == 422
    assert client.patch("/api/disturbances/99999/validate", json=body, headers={"X-API-Key": "admin-token-456"}).status_code == 404


def test_disabled_role_when_token_not_configured(client, seeded_db, monkeypatch):
    monkeypatch.setattr(settings, "OPERATOR_TOKEN", "")
    monkeypatch.setattr(settings, "ADMIN_TOKEN", "")
    r = client.patch("/api/disturbances/1/validate", json={"verified_category": "alami"}, headers={"X-API-Key": ""})
    assert r.status_code == 403  # header kosong = viewer; tidak ada token yang bisa menyamar


def test_prediction_stays_separate_from_verification(client, seeded_db, tokens):
    before = client.get("/api/disturbances/2").json()
    client.patch("/api/disturbances/2/validate", json={"verified_category": "kebakaran"}, headers={"X-API-Key": "op-token-123"})
    after = client.get("/api/disturbances/2").json()
    assert after["category"] == before["category"] and after["verified_category"] == "kebakaran"


def test_validation_summary_counts_agreement(client, seeded_db, tokens):
    for i in (3, 4):
        assert client.patch(f"/api/disturbances/{i}/validate", json={"verified_category": "alami"}, headers={"X-API-Key": "op-token-123"}).status_code == 200
    summary = client.get("/api/dashboard/validation-summary").json()
    assert summary["verified_count"] >= 2 and summary["agreement_count"] <= summary["verified_count"]
    assert "bukan akurasi" in summary["note"]


def test_csv_export_matches_filters(client, seeded_db):
    params = {"categories": "kebakaran", "source": "simulasi"}
    r = client.get("/api/export/disturbances.csv", params=params)
    lines = r.text.strip().splitlines()
    assert r.headers["content-type"].startswith("text/csv") and lines[0].startswith("id,region")
    assert len(lines) - 1 == client.get("/api/dashboard/stats", params=params).json()["total_detections"]
    assert all(",kebakaran," in l for l in lines[1:])


def test_pdf_report_valid(client, seeded_db):
    r = client.get("/api/export/report.pdf", params={"provinces": "Riau"})
    assert r.status_code == 200 and r.content.startswith(b"%PDF") and len(r.content) > 1500


def test_prediction_explanation_is_consistent_and_labelled(client, seeded_db):
    e = client.post("/api/ml/predict", json=GOOD_INPUT).json()["explanation"]
    assert e["target_category"] and 0 <= e["base_probability"] <= 1 and len(e["top_features"]) == 5
    assert "bukan SHAP" in e["method"] and "bukan bukti" in e["caveat"]
    contribs = [abs(f["contribution"]) for f in e["top_features"]]
    assert contribs == sorted(contribs, reverse=True) and contribs[0] > 0


def test_new_indications_endpoint(client, seeded_db):
    future = (datetime.utcnow() + timedelta(days=1)).isoformat()
    assert client.get("/api/disturbances/new", params={"since": future}).json()["total_new"] == 0
    past = (datetime.utcnow() - timedelta(days=3650)).isoformat()
    r = client.get("/api/disturbances/new", params={"since": past, "limit": 5}).json()
    assert r["total_new"] >= 60 and len(r["items"]) == 5
    assert client.get("/api/disturbances/new").status_code == 422


def test_role_endpoint(client, seeded_db, tokens):
    assert client.get("/api/auth/role").json() == {"role": "viewer"}
    assert client.get("/api/auth/role", headers={"X-API-Key": "op-token-123"}).json() == {"role": "operator"}
    assert client.get("/api/auth/role", headers={"X-API-Key": "admin-token-456"}).json() == {"role": "admin"}
    assert client.get("/api/auth/role", headers={"X-API-Key": "salah"}).status_code == 401
