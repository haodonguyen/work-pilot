import os
from pathlib import Path

from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_URL = f"sqlite:///{ROOT_DIR / 'workpilot.db'}"


class Settings(BaseModel):
    app_name: str = "WorkPilot"
    database_url: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "workpilot-api")
    access_token_minutes: int = 60 * 24


settings = Settings()
