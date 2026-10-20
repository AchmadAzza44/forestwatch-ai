"""
ForestWatch AI - Mock Sentinel Data Generator

Generates realistic mock satellite data for Sentinel-1 and Sentinel-2.
Replace this module with actual Google Earth Engine API calls when ready.

GEE Integration path:
    import ee
    ee.Initialize(credentials)
    collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    ...
"""
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random


# Realistic spectral signature ranges per land cover type
SPECTRAL_PROFILES = {
    "dense_forest": {
        "B2": (400, 600),    # Blue
        "B3": (600, 900),    # Green
        "B4": (300, 500),    # Red
        "B8": (3000, 5000),  # NIR
        "B11": (500, 1200),  # SWIR1
        "B12": (200, 600),   # SWIR2
        "ndvi": (0.7, 0.92),
        "nbr": (0.65, 0.85),
        "evi": (0.55, 0.80),
    },
    "degraded_forest": {
        "B2": (500, 800),
        "B3": (700, 1100),
        "B4": (400, 700),
        "B8": (2000, 3500),
        "B11": (800, 1800),
        "B12": (400, 900),
        "ndvi": (0.35, 0.65),
        "nbr": (0.30, 0.55),
        "evi": (0.30, 0.55),
    },
    "pertanian": {
        "B2": (600, 900),
        "B3": (900, 1300),
        "B4": (700, 1100),
        "B8": (1500, 2800),
        "B11": (1200, 2500),
        "B12": (600, 1500),
        "ndvi": (0.15, 0.50),
        "nbr": (0.10, 0.40),
        "evi": (0.12, 0.42),
    },
    "penebangan": {
        "B2": (700, 1100),
        "B3": (1000, 1500),
        "B4": (900, 1400),
        "B8": (1200, 2200),
        "B11": (1500, 2800),
        "B12": (800, 1800),
        "ndvi": (0.05, 0.30),
        "nbr": (0.05, 0.25),
        "evi": (0.05, 0.28),
    },
    "pertambangan": {
        "B2": (900, 1500),
        "B3": (1200, 1800),
        "B4": (1100, 1700),
        "B8": (800, 1500),
        "B11": (1800, 3000),
        "B12": (1200, 2200),
        "ndvi": (-0.10, 0.15),
        "nbr": (-0.20, 0.10),
        "evi": (-0.05, 0.12),
    },
    "kebakaran": {
        "B2": (500, 900),
        "B3": (700, 1100),
        "B4": (800, 1300),
        "B8": (900, 1800),
        "B11": (2000, 4000),
        "B12": (1500, 3500),
        "ndvi": (-0.20, 0.20),
        "nbr": (-0.35, -0.05),
        "evi": (-0.15, 0.15),
    },
    "alami": {
        "B2": (600, 1000),
        "B3": (900, 1400),
        "B4": (700, 1200),
        "B8": (1500, 3000),
        "B11": (1000, 2200),
        "B12": (600, 1400),
        "ndvi": (0.10, 0.45),
        "nbr": (0.08, 0.38),
        "evi": (0.08, 0.40),
    },
}

# SAR backscatter profiles (Sentinel-1 VV in dB)
SAR_PROFILES = {
    "dense_forest": (-12, -6),
    "degraded_forest": (-15, -9),
    "pertanian": (-18, -12),
    "penebangan": (-20, -14),
    "pertambangan": (-22, -16),
    "kebakaran": (-20, -13),
    "alami": (-17, -11),
}


def compute_ndvi(nir: float, red: float) -> float:
    """Normalized Difference Vegetation Index."""
    if (nir + red) == 0:
        return 0.0
    return (nir - red) / (nir + red)


def compute_nbr(nir: float, swir2: float) -> float:
    """Normalized Burn Ratio."""
    if (nir + swir2) == 0:
        return 0.0
    return (nir - swir2) / (nir + swir2)


def compute_evi(nir: float, red: float, blue: float) -> float:
    """Enhanced Vegetation Index."""
    denom = nir + 6 * red - 7.5 * blue + 1
    if denom == 0:
        return 0.0
    return 2.5 * (nir - red) / denom


def generate_sentinel2_scene(
    category: str,
    acquisition_date: datetime,
    region: str,
    cloud_coverage: float = None,
    rng=None,
) -> Dict:
    """
    Generate mock Sentinel-2 spectral data for a given land cover category.
    
    In production, replace with:
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterDate(start, end)
            .filterBounds(aoi)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            .median()
            .sample(aoi, scale=10)
    """
    rng = rng or random
    profile = SPECTRAL_PROFILES.get(category, SPECTRAL_PROFILES["pertanian"])
    
    if cloud_coverage is None:
        cloud_coverage = rng.uniform(5, 45)
    
    # Generate band values
    b2 = rng.uniform(*profile["B2"])
    b3 = rng.uniform(*profile["B3"])
    b4 = rng.uniform(*profile["B4"])
    b8 = rng.uniform(*profile["B8"])
    b11 = rng.uniform(*profile["B11"])
    b12 = rng.uniform(*profile["B12"])
    
    # Add some noise
    noise = lambda v: v * (1 + rng.gauss(0, 0.05))
    b2, b3, b4, b8, b11, b12 = [noise(x) for x in [b2, b3, b4, b8, b11, b12]]
    
    ndvi = compute_ndvi(b8, b4)
    nbr = compute_nbr(b8, b12)
    evi = compute_evi(b8, b4, b2)
    
    return {
        "sensor": "Sentinel-2",
        "scene_id": f"S2A_MSIL2A_{acquisition_date.strftime('%Y%m%d')}_{region[:3].upper()}_{rng.randint(1000,9999)}",
        "acquisition_date": acquisition_date.isoformat(),
        "region": region,
        "cloud_coverage_pct": round(cloud_coverage, 1),
        "processing_level": "L2A",
        "bands": {
            "B2_blue": round(b2, 2),
            "B3_green": round(b3, 2),
            "B4_red": round(b4, 2),
            "B8_nir": round(b8, 2),
            "B11_swir1": round(b11, 2),
            "B12_swir2": round(b12, 2),
        },
        "indices": {
            "ndvi": round(ndvi, 4),
            "nbr": round(nbr, 4),
            "evi": round(evi, 4),
        },
        "is_mock": True,
        "note": "Mock data. Replace with GEE API integration for real analysis."
    }


def generate_sentinel1_scene(
    category: str,
    acquisition_date: datetime,
    region: str,
    rng=None,
) -> Dict:
    """
    Generate mock Sentinel-1 SAR backscatter data.
    
    In production, replace with:
        ee.ImageCollection('COPERNICUS/S1_GRD')
            .filterDate(start, end)
            .filterBounds(aoi)
            .filter(ee.Filter.eq('instrumentMode', 'IW'))
            .select(['VV', 'VH'])
            .mean()
    """
    rng = rng or random
    vv_range = SAR_PROFILES.get(category, SAR_PROFILES["pertanian"])
    vv = rng.uniform(*vv_range)
    vh = vv - rng.uniform(5, 12)  # VH typically lower than VV
    ratio_vv_vh = vv - vh
    
    return {
        "sensor": "Sentinel-1",
        "scene_id": f"S1A_IW_GRDH_{acquisition_date.strftime('%Y%m%d')}_{region[:3].upper()}_{rng.randint(1000,9999)}",
        "acquisition_date": acquisition_date.isoformat(),
        "region": region,
        "instrument_mode": "IW",
        "polarization": ["VV", "VH"],
        "backscatter": {
            "VV_dB": round(vv, 2),
            "VH_dB": round(vh, 2),
            "VV_VH_ratio_dB": round(ratio_vv_vh, 2),
        },
        "is_mock": True,
        "note": "Mock SAR data. Replace with GEE Sentinel-1 GRD collection."
    }


def generate_change_detection_pair(
    category: str,
    region: str,
    period_start: datetime,
    period_end: datetime,
    rng=None,
) -> Dict:
    """Generate before/after satellite scenes for change detection.

    ``rng`` (random.Random) membuat keluaran dapat direproduksi; tanpa rng dipakai modul random global.
    """
    rng = rng or random
    # Before: dense forest
    before_scene = generate_sentinel2_scene("dense_forest", period_start, region, rng=rng)
    # After: disturbed land
    after_scene = generate_sentinel2_scene(category, period_end, region, rng=rng)
    
    # SAR data (complementary, especially for cloudy periods)
    sar_before = generate_sentinel1_scene("dense_forest", period_start, region, rng=rng)
    sar_after = generate_sentinel1_scene(category, period_end, region, rng=rng)
    
    ndvi_before = before_scene["indices"]["ndvi"]
    ndvi_after = after_scene["indices"]["ndvi"]
    ndvi_change = ndvi_after - ndvi_before
    
    nbr_before = before_scene["indices"]["nbr"]
    nbr_after = after_scene["indices"]["nbr"]
    
    return {
        "sentinel2_before": before_scene,
        "sentinel2_after": after_scene,
        "sentinel1_before": sar_before,
        "sentinel1_after": sar_after,
        "change_metrics": {
            "ndvi_before": ndvi_before,
            "ndvi_after": ndvi_after,
            "ndvi_change": round(ndvi_change, 4),
            "nbr_before": nbr_before,
            "nbr_after": nbr_after,
            "nbr_change": round(nbr_after - nbr_before, 4),
            "sar_vv_before": sar_before["backscatter"]["VV_dB"],
            "sar_vv_after": sar_after["backscatter"]["VV_dB"],
            "evi_before": before_scene["indices"]["evi"],
            "evi_after": after_scene["indices"]["evi"],
            "b4_red_after": after_scene["bands"]["B4_red"],
            "b8_nir_after": after_scene["bands"]["B8_nir"],
            "b11_swir1_after": after_scene["bands"]["B11_swir1"],
            "b12_swir2_after": after_scene["bands"]["B12_swir2"],
        }
    }
