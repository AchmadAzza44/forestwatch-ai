"""
ForestWatch AI - API Router: Disturbances
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import List, Optional
from datetime import datetime
import json

from auth import require_role
from database import get_db
from models.disturbance import ForestDisturbance
from schemas.disturbance import DisturbanceResponse, DisturbanceListResponse, GeoJSONCollection, GeoJSONFeature

router = APIRouter(prefix="/disturbances", tags=["disturbances"])

VALID_CATEGORIES = {"pertanian", "penebangan", "pertambangan", "kebakaran", "alami", "tidak_diketahui"}


def disturbance_to_geojson_feature(d: ForestDisturbance) -> dict:
    """Convert ORM object to GeoJSON feature."""
    try:
        from geoalchemy2.shape import to_shape
        from shapely import to_geojson
        geom = to_shape(d.geometry) if d.geometry is not None else None
        # Sebelumnya str(dict).replace("'", '"') menghasilkan JSON tidak valid (tuple) sehingga
        # semua poligon diam-diam jatuh ke Point; to_geojson menghasilkan GeoJSON yang benar.
        geometry = json.loads(to_geojson(geom)) if geom is not None else {
            "type": "Point",
            "coordinates": [d.centroid_lon, d.centroid_lat]
        }
    except Exception:
        geometry = {
            "type": "Point",
            "coordinates": [d.centroid_lon, d.centroid_lat]
        }
    
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "id": d.id,
            "category": d.category,
            "confidence_score": d.confidence_score,
            "confidence_level": d.confidence_level,
            "area_ha": d.area_ha,
            "region": d.region,
            "province": d.province,
            "detected_date": d.detected_date.isoformat() if d.detected_date else None,
            "period_start": d.period_start.isoformat() if d.period_start else None,
            "period_end": d.period_end.isoformat() if d.period_end else None,
            "ndvi_change": d.ndvi_change,
            "ndvi_before": d.ndvi_before,
            "ndvi_after": d.ndvi_after,
            "is_validated": d.is_validated,
            "verified_category": d.verified_category,
            "data_source": d.data_source,
            "needs_verification": d.confidence_level == "rendah" or d.category == "tidak_diketahui",
            "source_type": "citra_nyata" if (d.data_source or "").startswith("Sentinel-2 L2A COG (citra nyata)") else "simulasi",
        }
    }


@router.get("/", response_model=dict)
def list_disturbances(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    provinces: Optional[str] = Query(None, description="Comma-separated provinces"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    min_area_ha: Optional[float] = Query(None),
    source: Optional[str] = Query(None, description="citra_nyata | simulasi | semua"),
    format: str = Query("json", description="Response format: json or geojson"),
    db: Session = Depends(get_db)
):
    """List disturbances with filtering and pagination (filter sama dengan peta dan dashboard)."""
    from routers.dashboard import filtered_query
    query = filtered_query(db, date_from, date_to, categories, provinces, min_confidence, source)
    if min_area_ha is not None:
        query = query.filter(ForestDisturbance.area_ha >= min_area_ha)

    total = query.count()
    items = query.order_by(desc(ForestDisturbance.detected_date))\
                 .offset((page - 1) * page_size)\
                 .limit(page_size)\
                 .all()
    
    if format == "geojson":
        features = [disturbance_to_geojson_feature(d) for d in items]
        return {
            "type": "FeatureCollection",
            "features": features,
            "total": total,
        }
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_serialize_disturbance(d) for d in items],
    }


@router.get("/geojson", response_model=dict)
def get_all_geojson(
    categories: Optional[str] = Query(None),
    provinces: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    source: Optional[str] = Query(None, description="citra_nyata | simulasi | semua"),
    db: Session = Depends(get_db)
):
    """Get all disturbances as GeoJSON FeatureCollection (for map display). Filter sama dengan dashboard."""
    from routers.dashboard import filtered_query
    query = filtered_query(db, date_from, date_to, categories, provinces, min_confidence, source)
    items = query.order_by(desc(ForestDisturbance.detected_date)).limit(1000).all()
    features = [disturbance_to_geojson_feature(d) for d in items]
    
    return {
        "type": "FeatureCollection",
        "features": features,
        "count": len(features),
    }


@router.get("/new", response_model=dict)
def new_disturbances(since: datetime = Query(..., description="ISO 8601; hanya indikasi yang dibuat setelah waktu ini"),
                     limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """Notifikasi berbasis polling: indikasi baru sejak ``since`` (PRD: sistem notifikasi untuk indikasi baru)."""
    query = db.query(ForestDisturbance).filter(ForestDisturbance.created_at > since)
    total = query.count()
    items = query.order_by(desc(ForestDisturbance.created_at)).limit(limit).all()
    return {"since": since.isoformat(), "total_new": total, "items": [_serialize_disturbance(d) for d in items]}


@router.patch("/{disturbance_id}/validate", response_model=dict)
def validate_disturbance(disturbance_id: int,
                         verified_category: str = Body(..., embed=True),
                         note: str = Body("", embed=True, max_length=1000),
                         role: str = Depends(require_role("operator")),
                         db: Session = Depends(get_db)):
    """Operator memverifikasi satu indikasi. Kategori verifikasi disimpan TERPISAH dari prediksi model."""
    if verified_category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Kategori harus salah satu dari: {', '.join(sorted(VALID_CATEGORIES))}.")
    d = db.query(ForestDisturbance).filter(ForestDisturbance.id == disturbance_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Disturbance not found")
    d.verified_category = verified_category
    d.verified_at = datetime.utcnow()
    d.is_validated = True
    d.validated_by = role
    d.validation_note = note
    db.commit()
    return _serialize_disturbance(d)


@router.get("/{disturbance_id}", response_model=dict)
def get_disturbance(disturbance_id: int, db: Session = Depends(get_db)):
    """Get single disturbance detail."""
    d = db.query(ForestDisturbance).filter(ForestDisturbance.id == disturbance_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Disturbance not found")
    
    result = _serialize_disturbance(d)
    result["prediction_probabilities"] = d.prediction_probabilities
    result["feature_vector"] = d.feature_vector
    result["sentinel2_scene_id"] = d.sentinel2_scene_id
    result["sentinel1_scene_id"] = d.sentinel1_scene_id
    result["validation_note"] = d.validation_note
    result["validated_by"] = d.validated_by
    
    return result


def _serialize_disturbance(d: ForestDisturbance) -> dict:
    return {
        "id": d.id,
        "centroid_lat": d.centroid_lat,
        "centroid_lon": d.centroid_lon,
        "area_ha": d.area_ha,
        "region": d.region,
        "province": d.province,
        "detected_date": d.detected_date.isoformat() if d.detected_date else None,
        "period_start": d.period_start.isoformat() if d.period_start else None,
        "period_end": d.period_end.isoformat() if d.period_end else None,
        "category": d.category,
        "confidence_score": d.confidence_score,
        "confidence_level": d.confidence_level,
        "ndvi_before": d.ndvi_before,
        "ndvi_after": d.ndvi_after,
        "ndvi_change": d.ndvi_change,
        "nbr_before": d.nbr_before,
        "nbr_after": d.nbr_after,
        "sar_backscatter": d.sar_backscatter,
        "cloud_coverage": d.cloud_coverage,
        "data_source": d.data_source,
        "source_type": "citra_nyata" if (d.data_source or "").startswith("Sentinel-2 L2A COG (citra nyata)") else "simulasi",
        "is_validated": d.is_validated,
        "verified_category": d.verified_category,
        "notes": d.notes,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }
