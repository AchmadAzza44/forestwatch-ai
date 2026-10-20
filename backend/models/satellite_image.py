"""
ForestWatch AI - Satellite Image Model
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from database import Base


class SatelliteImage(Base):
    __tablename__ = "satellite_images"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(String(200), unique=True, nullable=False)
    sensor = Column(String(50), nullable=False)  # Sentinel-2, Sentinel-1
    acquisition_date = Column(DateTime, nullable=False)
    cloud_coverage = Column(Float, nullable=True)
    region = Column(String(100), nullable=False)
    bbox = Column(Geometry("POLYGON", srid=4326), nullable=True)
    bands = Column(JSON, nullable=True)
    processing_level = Column(String(50), nullable=True)
    tile_url = Column(String(500), nullable=True)
    is_mock = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
