import os
import random
import tempfile

# Harus diatur sebelum modul aplikasi diimpor: tes memakai SQLite, bukan PostGIS.
_DB = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_DB}"

import pytest
from fastapi.testclient import TestClient

from geoalchemy2 import Geometry
from sqlalchemy import Text

from database import Base, SessionLocal, engine
from models import disturbance, satellite_image  # noqa: F401
from seed_data import REGIONS, create_disturbance


@pytest.fixture(scope="session")
def seeded_db():
    # SQLite tidak punya PostGIS: pada tes, kolom geometri diganti teks. Model produksi tidak berubah.
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, Geometry):
                col.type = Text()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    rng = random.Random(7)
    for i in range(60):
        db.add(create_disturbance(db, REGIONS[i % len(REGIONS)], rng.randint(0, 700), rng))
    db.commit()
    db.close()
    return True


@pytest.fixture(scope="session")
def client(seeded_db):
    from main import app

    return TestClient(app)  # tanpa context manager: lifespan (seeder penuh) tidak dijalankan


GOOD_INPUT = dict(
    ndvi_before=0.72, ndvi_after=0.05, nbr_before=0.68, nbr_after=-0.2, evi_before=0.62, evi_after=0.03,
    b4_red_after=1000, b8_nir_after=1300, b11_swir1_after=3000, b12_swir2_after=2500,
    sar_vv_before=-9, sar_vv_after=-16, cloud_coverage=30, area_ha=150,
)
