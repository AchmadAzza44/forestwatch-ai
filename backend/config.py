"""
ForestWatch AI - Application Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://forestwatch:forestwatch_secret@localhost:5432/forestwatch"
    
    # App
    APP_NAME: str = "ForestWatch AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "dev-secret-key"

    # Peran: tanpa token = pembaca (viewer, hanya baca). Token kosong = peran itu dinonaktifkan.
    OPERATOR_TOKEN: str = ""
    ADMIN_TOKEN: str = ""
    
    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # ML
    MODEL_PATH: Optional[str] = None
    CONFIDENCE_THRESHOLD: float = 0.45

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
