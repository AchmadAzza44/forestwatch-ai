"""
ForestWatch AI - ORM Models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from database import Base
import enum


class DisturbanceCategory(str, enum.Enum):
    PERTANIAN = "pertanian"
    PENEBANGAN = "penebangan"
    PERTAMBANGAN = "pertambangan"
    KEBAKARAN = "kebakaran"
    ALAMI = "alami"
    TIDAK_DIKETAHUI = "tidak_diketahui"


class ConfidenceLevel(str, enum.Enum):
    TINGGI = "tinggi"      # >= 0.75
    SEDANG = "sedang"      # 0.50 - 0.75
    RENDAH = "rendah"      # < 0.50


class ForestDisturbance(Base):
    __tablename__ = "forest_disturbances"

    id = Column(Integer, primary_key=True, index=True)
    
    # Spatial
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=True)
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    area_ha = Column(Float, nullable=True)  # Area in hectares
    
    # Location info
    region = Column(String(100), nullable=False)
    province = Column(String(100), nullable=False)
    
    # Temporal
    detected_date = Column(DateTime, nullable=False)
    period_start = Column(DateTime, nullable=False)  # Start of observation period
    period_end = Column(DateTime, nullable=False)    # End of observation period
    
    # Classification
    category = Column(String(50), nullable=False, default="tidak_diketahui")
    confidence_score = Column(Float, nullable=False, default=0.0)
    confidence_level = Column(String(20), nullable=False, default="rendah")
    
    # Analysis data
    ndvi_before = Column(Float, nullable=True)
    ndvi_after = Column(Float, nullable=True)
    ndvi_change = Column(Float, nullable=True)
    nbr_before = Column(Float, nullable=True)
    nbr_after = Column(Float, nullable=True)
    sar_backscatter = Column(Float, nullable=True)  # Sentinel-1 VV backscatter
    cloud_coverage = Column(Float, nullable=True)
    
    # ML features stored as JSON
    feature_vector = Column(JSON, nullable=True)
    prediction_probabilities = Column(JSON, nullable=True)  # Per-class probs
    
    # Satellite source
    sentinel2_scene_id = Column(String(200), nullable=True)
    sentinel1_scene_id = Column(String(200), nullable=True)
    data_source = Column(String(100), default="Sentinel-2 (Mock)")
    
    # Validation
    verified_category = Column(String(50), nullable=True)  # kategori hasil verifikasi operator (terpisah dari prediksi model)
    verified_at = Column(DateTime, nullable=True)
    is_validated = Column(Boolean, default=False)
    validated_by = Column(String(100), nullable=True)
    validation_note = Column(Text, nullable=True)
    
    # Meta
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    notes = Column(Text, nullable=True)


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    region = Column(String(100), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    total_detected = Column(Integer, default=0)
    total_area_ha = Column(Float, default=0.0)
    model_version = Column(String(50), nullable=True)
    parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
