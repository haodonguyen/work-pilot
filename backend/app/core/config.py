import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "WorkPilot"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./workpilot.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "workpilot-api")
    access_token_minutes: int = 60 * 24


settings = Settings()
