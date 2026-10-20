"""
ForestWatch AI - Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class CategoryEnum(str, Enum):
    pertanian = "pertanian"
    penebangan = "penebangan"
    pertambangan = "pertambangan"
    kebakaran = "kebakaran"
    alami = "alami"
    tidak_diketahui = "tidak_diketahui"


class DisturbanceBase(BaseModel):
    centroid_lat: float
    centroid_lon: float
    area_ha: Optional[float] = None
    region: str
    province: str
    detected_date: datetime
    period_start: datetime
    period_end: datetime
    category: CategoryEnum = CategoryEnum.tidak_diketahui
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_level: str
    ndvi_before: Optional[float] = None
    ndvi_after: Optional[float] = None
    ndvi_change: Optional[float] = None
    nbr_before: Optional[float] = None
    nbr_after: Optional[float] = None
    sar_backscatter: Optional[float] = None
    cloud_coverage: Optional[float] = None
    data_source: str = "Sentinel-2 (Mock)"
    notes: Optional[str] = None


class DisturbanceCreate(DisturbanceBase):
    geometry_geojson: Optional[Dict] = None


class DisturbanceResponse(DisturbanceBase):
    id: int
    is_validated: bool
    validated_by: Optional[str] = None
    validation_note: Optional[str] = None
    prediction_probabilities: Optional[Dict[str, float]] = None
    sentinel2_scene_id: Optional[str] = None
    sentinel1_scene_id: Optional[str] = None
    created_at: datetime
    geometry_geojson: Optional[Dict] = None

    class Config:
        from_attributes = True


class DisturbanceListResponse(BaseModel):
    total: int
    items: List[DisturbanceResponse]
    page: int
    page_size: int


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]


class GeoJSONCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


class FilterParams(BaseModel):
    categories: Optional[List[str]] = None
    provinces: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_confidence: Optional[float] = None
    min_area_ha: Optional[float] = None
