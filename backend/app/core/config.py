import os
from pathlib import Path

from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_URL = f"sqlite:///{ROOT_DIR / 'workpilot.db'}"


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Settings(BaseModel):
    app_name: str = "WorkPilot"
    database_url: str = normalize_database_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "workpilot-api")
    access_token_minutes: int = 60 * 24
    allow_signups: bool = os.getenv("ALLOW_SIGNUPS", "true").lower() in {"1", "true", "yes", "on"}
    signup_invite_code: str | None = os.getenv("SIGNUP_INVITE_CODE") or None
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


def validate_production_settings() -> None:
    if not settings.is_sqlite and settings.jwt_secret == "change-me-in-production":
        raise RuntimeError("JWT_SECRET must be set for production deployments")


settings = Settings()
