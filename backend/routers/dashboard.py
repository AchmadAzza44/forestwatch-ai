"""
ForestWatch AI - Dashboard Statistics Router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from typing import Optional
from datetime import datetime
from collections import defaultdict

from database import get_db
from models.disturbance import ForestDisturbance

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

REAL_SOURCE_PREFIX = "Sentinel-2 L2A COG (citra nyata)"


def _split(value: Optional[str]) -> list:
    return [v.strip() for v in value.split(",") if v.strip()] if value else []


def filtered_query(
    db: Session,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    categories: Optional[str] = None,
    provinces: Optional[str] = None,
    min_confidence: Optional[float] = None,
    source: Optional[str] = None,
):
    """Satu jalur filter dipakai peta, statistik, tren, dan perbandingan agar semuanya konsisten."""
    query = db.query(ForestDisturbance)
    if date_from:
        query = query.filter(ForestDisturbance.detected_date >= date_from)
    if date_to:
        query = query.filter(ForestDisturbance.detected_date <= date_to)
    if _split(categories):
        query = query.filter(ForestDisturbance.category.in_(_split(categories)))
    if _split(provinces):
        query = query.filter(ForestDisturbance.province.in_(_split(provinces)))
    if min_confidence is not None:
        query = query.filter(ForestDisturbance.confidence_score >= min_confidence)
    if source == "citra_nyata":
        query = query.filter(ForestDisturbance.data_source.like(f"{REAL_SOURCE_PREFIX}%"))
    elif source == "simulasi":
        query = query.filter(~ForestDisturbance.data_source.like(f"{REAL_SOURCE_PREFIX}%"))
    elif source not in (None, "", "semua"):
        raise HTTPException(status_code=422, detail="source harus citra_nyata, simulasi, atau semua.")
    return query


@router.get("/stats")
def get_dashboard_stats(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    categories: Optional[str] = Query(None, description="Dipisah koma"),
    provinces: Optional[str] = Query(None, description="Dipisah koma"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    source: Optional[str] = Query(None, description="citra_nyata | simulasi | semua"),
    db: Session = Depends(get_db)
):
    """Statistik ringkasan; menerima filter yang sama dengan peta."""
    all_records = filtered_query(db, date_from, date_to, categories, provinces, min_confidence, source).all()
    
    if not all_records:
        return {
            "total_detections": 0,
            "total_area_ha": 0,
            "categories_distribution": {},
            "provinces_distribution": {},
            "validated_count": 0,
            "high_confidence_count": 0,
        }
    
    total = len(all_records)
    total_area = sum(r.area_ha or 0 for r in all_records)
    
    # Category distribution
    cat_dist = defaultdict(lambda: {"count": 0, "area_ha": 0.0})
    for r in all_records:
        cat_dist[r.category]["count"] += 1
        cat_dist[r.category]["area_ha"] = round(cat_dist[r.category]["area_ha"] + (r.area_ha or 0), 2)
    
    # Province distribution
    prov_dist = defaultdict(lambda: {"count": 0, "area_ha": 0.0})
    for r in all_records:
        prov_dist[r.province]["count"] += 1
        prov_dist[r.province]["area_ha"] = round(prov_dist[r.province]["area_ha"] + (r.area_ha or 0), 2)
    
    validated = sum(1 for r in all_records if r.is_validated)
    high_conf = sum(1 for r in all_records if r.confidence_level == "tinggi")
    avg_confidence = sum(r.confidence_score for r in all_records) / total if total > 0 else 0
    
    return {
        "total_detections": total,
        "total_area_ha": round(total_area, 2),
        "validated_count": validated,
        "high_confidence_count": high_conf,
        "avg_confidence_score": round(avg_confidence, 3),
        "categories_distribution": {k: v for k, v in sorted(cat_dist.items(), key=lambda x: -x[1]["count"])},
        "provinces_distribution": {k: v for k, v in sorted(prov_dist.items(), key=lambda x: -x[1]["count"])},
    }


@router.get("/timeline")
def get_timeline(
    period: str = Query("monthly", pattern="^(monthly|quarterly)$", description="monthly or quarterly"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    categories: Optional[str] = Query(None),
    provinces: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Time series data for charts."""
    records = (filtered_query(db, date_from, date_to, categories, provinces, min_confidence, source)
               .order_by(ForestDisturbance.detected_date).all())
    
    timeline = defaultdict(lambda: {
        "count": 0, "area_ha": 0.0,
        "pertanian": 0, "penebangan": 0, "pertambangan": 0,
        "kebakaran": 0, "alami": 0, "tidak_diketahui": 0
    })
    
    for r in records:
        if not r.detected_date:
            continue
        if period == "quarterly":
            q = (r.detected_date.month - 1) // 3 + 1
            key = f"{r.detected_date.year}-Q{q}"
        else:
            key = r.detected_date.strftime("%Y-%m")
        
        timeline[key]["count"] += 1
        timeline[key]["area_ha"] = round(timeline[key]["area_ha"] + (r.area_ha or 0), 2)
        timeline[key][r.category] = timeline[key].get(r.category, 0) + 1
    
    sorted_timeline = [{"period": k, **v} for k, v in sorted(timeline.items())]
    
    return {"timeline": sorted_timeline, "period_type": period}


@router.get("/region-comparison")
def get_region_comparison(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    categories: Optional[str] = Query(None),
    provinces: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Per-region comparison for bar chart."""
    records = filtered_query(db, date_from, date_to, categories, provinces, min_confidence, source).all()
    
    regions = defaultdict(lambda: {
        "total": 0, "area_ha": 0.0, "categories": defaultdict(int)
    })
    
    for r in records:
        regions[r.region]["total"] += 1
        regions[r.region]["area_ha"] = round(regions[r.region]["area_ha"] + (r.area_ha or 0), 2)
        regions[r.region]["categories"][r.category] += 1
    
    result = []
    for region, data in sorted(regions.items(), key=lambda x: -x[1]["total"]):
        result.append({
            "region": region,
            "total": data["total"],
            "area_ha": data["area_ha"],
            **{f"cat_{k}": v for k, v in data["categories"].items()}
        })
    
    return {"regions": result}


def _period_summary(records: list) -> dict:
    cats = defaultdict(int)
    for r in records:
        cats[r.category] += 1
    return {
        "total_detections": len(records),
        "total_area_ha": round(sum(r.area_ha or 0 for r in records), 2),
        "categories": dict(cats),
    }


@router.get("/period-comparison")
def get_period_comparison(
    a_from: datetime = Query(...), a_to: datetime = Query(...),
    b_from: datetime = Query(...), b_to: datetime = Query(...),
    categories: Optional[str] = Query(None),
    provinces: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Bandingkan dua periode pengamatan (PRD 6.1-C). Selisih = periode B dikurangi periode A."""
    if a_from > a_to or b_from > b_to:
        raise HTTPException(status_code=422, detail="Tanggal awal harus sebelum atau sama dengan tanggal akhir.")
    a = _period_summary(filtered_query(db, a_from, a_to, categories, provinces, min_confidence, source).all())
    b = _period_summary(filtered_query(db, b_from, b_to, categories, provinces, min_confidence, source).all())
    all_cats = set(a["categories"]) | set(b["categories"])
    return {
        "period_a": {"from": a_from.isoformat(), "to": a_to.isoformat(), **a},
        "period_b": {"from": b_from.isoformat(), "to": b_to.isoformat(), **b},
        "delta": {
            "total_detections": b["total_detections"] - a["total_detections"],
            "total_area_ha": round(b["total_area_ha"] - a["total_area_ha"], 2),
            "categories": {c: b["categories"].get(c, 0) - a["categories"].get(c, 0) for c in sorted(all_cats)},
        },
        "note": "Perbandingan jumlah indikasi terdeteksi, bukan laju deforestasi terverifikasi.",
    }


@router.get("/validation-summary")
def get_validation_summary(source: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Kesesuaian prediksi model dengan verifikasi operator (hanya indikasi yang sudah diverifikasi)."""
    rows = filtered_query(db, source=source).filter(ForestDisturbance.verified_category.isnot(None)).all()
    pairs = defaultdict(int)
    for r in rows:
        pairs[f"{r.category} -> {r.verified_category}"] += 1
    agree = sum(1 for r in rows if r.category == r.verified_category)
    return {
        "verified_count": len(rows),
        "agreement_count": agree,
        "agreement_pct": round(agree / len(rows) * 100, 1) if rows else None,
        "pairs": dict(sorted(pairs.items(), key=lambda kv: -kv[1])),
        "note": ("Sampel verifikasi tidak dipilih acak dan biasanya kecil; persentase ini bukan akurasi model. "
                 "Indikasi dari citra nyata tidak diklasifikasi model sehingga 'tidak_diketahui' bukan kesalahan prediksi."),
    }


@router.get("/model-performance")
def get_model_performance():
    """Return ML model evaluation metrics."""
    from ml.classifier import get_model, CATEGORIES, CATEGORY_LABELS
    _, evaluation = get_model()
    
    # Format confusion matrix nicely
    cm = evaluation.get("confusion_matrix", [])
    labels = evaluation.get("confusion_matrix_labels", CATEGORIES)
    
    # Per-class metrics
    report = evaluation.get("classification_report", {})
    per_class = []
    for cat in CATEGORIES:
        if cat in report:
            per_class.append({
                "category": cat,
                "label": CATEGORY_LABELS.get(cat, cat),
                "precision": round(report[cat]["precision"], 3),
                "recall": round(report[cat]["recall"], 3),
                "f1_score": round(report[cat]["f1-score"], 3),
                "support": report[cat]["support"],
            })
    
    return {
        "model_type": evaluation.get("model_type"),
        "accuracy": round(evaluation.get("accuracy", 0), 4),
        "macro_f1": round(evaluation.get("macro_f1", 0), 4),
        "weighted_f1": round(evaluation.get("weighted_f1", 0), 4),
        "training_samples": evaluation.get("training_samples"),
        "test_samples": evaluation.get("test_samples"),
        "per_class_metrics": per_class,
        "confusion_matrix": cm,
        "confusion_matrix_labels": labels,
        "baselines": evaluation.get("baselines"),
        "note": evaluation.get("note"),
    }
