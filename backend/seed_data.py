"""
ForestWatch AI - Database Seeder

Seeds the database with realistic mock disturbance data for Indonesia.
Covers hotspot deforestation regions: Kalimantan, Sumatera, Papua.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import random
import json
from shapely.geometry import mapping, Polygon
from database import SessionLocal, init_db
from models.disturbance import ForestDisturbance
from models.satellite_image import SatelliteImage
from gis.sentinel_mock import generate_change_detection_pair
from ml.classifier import get_model, extract_features, predict, FEATURE_NAMES

# Seed data: realistic coordinate clusters per region
REGIONS = [
    {
        "region": "Kalimantan Timur - IKN",
        "province": "Kalimantan Timur",
        "center": (-0.85, 117.10),
        "spread": 0.8,
        "dominant_categories": ["pertanian", "pertambangan", "penebangan"],
        "weight": 0.30,
    },
    {
        "region": "Kalimantan Tengah",
        "province": "Kalimantan Tengah",
        "center": (-1.50, 113.80),
        "spread": 1.2,
        "dominant_categories": ["kebakaran", "penebangan", "pertanian"],
        "weight": 0.25,
    },
    {
        "region": "Sumatera Selatan",
        "province": "Sumatera Selatan",
        "center": (-3.10, 104.50),
        "spread": 1.0,
        "dominant_categories": ["kebakaran", "pertanian", "tidak_diketahui"],
        "weight": 0.20,
    },
    {
        "region": "Riau - Gambut",
        "province": "Riau",
        "center": (0.50, 102.20),
        "spread": 0.9,
        "dominant_categories": ["kebakaran", "pertanian", "penebangan"],
        "weight": 0.15,
    },
    {
        "region": "Papua Barat",
        "province": "Papua Barat",
        "center": (-1.30, 133.20),
        "spread": 1.5,
        "dominant_categories": ["penebangan", "alami", "tidak_diketahui"],
        "weight": 0.10,
    },
]

CATEGORIES_ALL = [
    "pertanian", "penebangan", "pertambangan", "kebakaran", "alami", "tidak_diketahui"
]


def make_polygon(center_lat: float, center_lon: float, size_deg: float = 0.01) -> dict:
    """Create a small polygon around a center point."""
    s = size_deg / 2
    poly = Polygon([
        (center_lon - s, center_lat - s),
        (center_lon + s, center_lat - s),
        (center_lon + s, center_lat + s),
        (center_lon - s, center_lat + s),
        (center_lon - s, center_lat - s),
    ])
    return mapping(poly)


SEED = 42


def create_disturbance(session, region_info: dict, date_offset_days: int, rng: random.Random) -> ForestDisturbance:
    """Create a single disturbance record with satellite data (simulasi, dapat direproduksi lewat `rng`)."""
    lat_center, lon_center = region_info["center"]
    spread = region_info["spread"]
    
    lat = lat_center + rng.uniform(-spread, spread)
    lon = lon_center + rng.uniform(-spread, spread)
    
    # Pick category (biased toward dominant)
    if rng.random() < 0.70:
        category = rng.choice(region_info["dominant_categories"])
    else:
        category = rng.choice(CATEGORIES_ALL)
    
    detected_date = datetime(2023, 1, 1) + timedelta(days=date_offset_days)
    period_start = detected_date - timedelta(days=rng.randint(60, 180))
    period_end = detected_date
    
    # Generate satellite data
    pair = generate_change_detection_pair(category, region_info["region"], period_start, period_end, rng=rng)
    metrics = pair["change_metrics"]
    
    # Extract features and get ML prediction
    area_ha = round(rng.uniform(5.0, 350.0), 2)
    features = extract_features(
        ndvi_before=metrics["ndvi_before"], ndvi_after=metrics["ndvi_after"],
        nbr_before=metrics["nbr_before"], nbr_after=metrics["nbr_after"],
        evi_before=metrics["evi_before"], evi_after=metrics["evi_after"],
        b4_red_after=metrics["b4_red_after"], b8_nir_after=metrics["b8_nir_after"],
        b11_swir1_after=metrics["b11_swir1_after"], b12_swir2_after=metrics["b12_swir2_after"],
        sar_vv_before=metrics["sar_vv_before"], sar_vv_after=metrics["sar_vv_after"],
        cloud_coverage=pair["sentinel2_before"].get("cloud_coverage_pct", 20.0),
        area_ha=area_ha,
    )

    pred = predict(features)
    poly_geojson = make_polygon(lat, lon, size_deg=0.008)
    
    # Convert to WKT for GeoAlchemy2
    from shapely.geometry import shape
    geom = shape(poly_geojson)
    wkt = f"SRID=4326;{geom.wkt}"
    
    disturbance = ForestDisturbance(
        geometry=wkt,
        centroid_lat=round(lat, 6),
        centroid_lon=round(lon, 6),
        area_ha=area_ha,
        region=region_info["region"],
        province=region_info["province"],
        detected_date=detected_date,
        period_start=period_start,
        period_end=period_end,
        category=pred["predicted_category"],  # keluaran model; kategori simulasi disimpan terpisah di feature_vector
        confidence_score=pred["confidence_score"],
        confidence_level=pred["confidence_level"],
        ndvi_before=round(metrics["ndvi_before"], 4),
        ndvi_after=round(metrics["ndvi_after"], 4),
        ndvi_change=round(metrics["ndvi_change"], 4),
        nbr_before=round(metrics["nbr_before"], 4),
        nbr_after=round(metrics["nbr_after"], 4),
        sar_backscatter=round(metrics["sar_vv_after"], 2),
        cloud_coverage=round(pair["sentinel2_before"].get("cloud_coverage_pct", 20.0), 1),
        feature_vector={
            **{name: float(v) for name, v in zip(FEATURE_NAMES, features[0])},
            "simulated_truth": category,
        },
        prediction_probabilities=pred["all_probabilities"],
        sentinel2_scene_id=pair["sentinel2_after"]["scene_id"],
        sentinel1_scene_id=pair["sentinel1_after"]["scene_id"],
        data_source="Sentinel-2 L2A (Mock) + Sentinel-1 GRD (Mock)",
        is_validated=rng.random() < 0.15,
        notes=f"Data SIMULASI (bukan citra nyata); kategori adalah prediksi model, bukan penyebab terverifikasi. Periode: {period_start.strftime('%b %Y')} - {period_end.strftime('%b %Y')}",
    )
    
    return disturbance


def seed_database():
    """Main seeding function."""
    print("[Seeder] Initializing database...")
    init_db()
    
    # Pre-load model
    print("[Seeder] Loading ML model...")
    get_model()
    
    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(ForestDisturbance).count()
        if existing > 0:
            print(f"[Seeder] Database already has {existing} records. Skipping.")
            return
        
        print("[Seeder] Seeding disturbance data...")
        rng = random.Random(SEED)
        records_created = 0
        total_target = 200
        
        for i in range(total_target):
            # Pick region based on weight
            weights = [r["weight"] for r in REGIONS]
            region = rng.choices(REGIONS, weights=weights, k=1)[0]
            
            # Sebar tanggal 2023-2024
            date_offset = rng.randint(0, 730)  # 2023-01-01 s.d. ~2024-12-31
            
            disturbance = create_disturbance(db, region, date_offset, rng)
            db.add(disturbance)
            records_created += 1
            
            if records_created % 20 == 0:
                db.commit()
                print(f"[Seeder]   {records_created}/{total_target} records created...")
        
        db.commit()
        print(f"[Seeder] ✓ Created {records_created} disturbance records.")
        
    except Exception as e:
        db.rollback()
        print(f"[Seeder] ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
    print("[Seeder] Database seeding complete!")
