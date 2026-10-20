"""
ForestWatch AI - FastAPI Main Application
"""
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    print(f"[ForestWatch] Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Initialize database
    try:
        init_db()
        print("[ForestWatch] Database initialized.")
    except Exception as e:
        print(f"[ForestWatch] DB init warning: {e}")
    
    # Pre-load ML model
    try:
        from ml.classifier import get_model
        _, eval_data = get_model()
        print(f"[ForestWatch] ML model loaded. Accuracy: {eval_data['accuracy']:.3f}")
    except Exception as e:
        print(f"[ForestWatch] ML model warning: {e}")
    
    # Seed data if empty
    try:
        from seed_data import seed_database
        seed_database()
    except Exception as e:
        print(f"[ForestWatch] Seeder warning: {e}")
    
    yield
    
    print("[ForestWatch] Shutting down...")


app = FastAPI(
    title="ForestWatch AI API",
    description="""
    ## ForestWatch AI - Sistem Pemantauan Deforestasi

    API untuk sistem pemantauan dan klasifikasi penyebab deforestasi berbasis 
    citra satelit Sentinel-1/2 dan Machine Learning.
    
    ### Catatan Metodologis
    Data citra satelit yang digunakan saat ini adalah **data simulasi** yang mencerminkan 
    karakteristik spektral nyata Sentinel-2 dan Sentinel-1. Untuk implementasi produksi, 
    ganti modul `gis/sentinel_mock.py` dengan panggilan Google Earth Engine API.
    
    ### Keterbatasan Model
    Model klasifikasi dilatih menggunakan data sintetis. Prediksi hanya merupakan **indikasi awal** 
    dan bukan pengganti verifikasi lapangan.
    """,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
from routers.disturbances import router as disturbances_router
from routers.dashboard import router as dashboard_router
from routers.ml_inference import router as ml_router
from routers.export import router as export_router

app.include_router(disturbances_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(ml_router, prefix="/api")
app.include_router(export_router, prefix="/api")


@app.get("/api/health")
def health_check():
    from sqlalchemy import text
    from database import engine
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:  # noqa: BLE001
        db_status = f"error: {type(exc).__name__}"
    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "database": db_status,
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api/auth/role")
def current_role(x_api_key: str | None = Header(default=None)):
    """Peran untuk token yang diberikan (viewer bila tanpa token); token salah -> 401."""
    from auth import resolve_role
    return {"role": resolve_role(x_api_key)}


@app.get("/api/regions")
def get_regions():
    """Get available research regions."""
    return {
        "regions": [
            {"id": "kaltim", "name": "Kalimantan Timur - IKN", "province": "Kalimantan Timur", "center": [-0.85, 117.10]},
            {"id": "kalteng", "name": "Kalimantan Tengah", "province": "Kalimantan Tengah", "center": [-1.50, 113.80]},
            {"id": "sumsel", "name": "Sumatera Selatan", "province": "Sumatera Selatan", "center": [-3.10, 104.50]},
            {"id": "riau", "name": "Riau - Gambut", "province": "Riau", "center": [0.50, 102.20]},
            {"id": "papbar", "name": "Papua Barat", "province": "Papua Barat", "center": [-1.30, 133.20]},
        ]
    }
