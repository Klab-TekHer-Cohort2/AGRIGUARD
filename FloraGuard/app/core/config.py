"""Central configuration for the FloraGuard backend.

All settings are loaded from environment variables with sensible defaults.
Secrets are never committed to source control.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Project paths ---
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    UPLOAD_DIR: Path = BASE_DIR / "uploads"

    # --- Database ---
    DATABASE_PATH: Path = BASE_DIR / "floraguard.db"
    DATABASE_URL: str = f"sqlite:///{DATABASE_PATH.as_posix()}"

    # --- API ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False
    API_WORKERS: int = 1

    # --- CORS (future frontend integration) ---
    ALLOWED_ORIGINS: str = "*"

    # --- Weather (Open-Meteo, no API key required) ---
    WEATHER_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_TIMEOUT_SECONDS: float = 5.0
    WEATHER_CACHE_TTL_SECONDS: int = 300  # 5 minutes

    # --- AI model integration ---
    # Set to a callable module path or leave empty to disable.
    # Example: "app.services.ai_service:predict_image"
    AI_MODEL_PATH: str = ""
    AI_TIMEOUT_SECONDS: float = 10.0

    # --- Risk engine thresholds ---
    RISK_WINDOW_HOURS: int = 72
    RISK_SCORE_LOW_MAX: float = 29.0
    RISK_SCORE_MEDIUM_MAX: float = 59.0
    # Scores above this are HIGH

    # --- Alert generation ---
    AUTO_CREATE_ALERTS: bool = True
    ALERT_SCORE_THRESHOLD: float = 60.0

    # --- SMS delivery (future) ---
    SMS_PROVIDER: str = ""  # e.g. "twilio", "africas_talking"
    SMS_API_KEY: str = ""
    SMS_SENDER_ID: str = ""

    # --- Supported areas (configurable, no invented real locations) ---
    SUPPORTED_AREAS: str = "Gishari Flower Park,Nyabugogo Flora Market,Rwamagana Sector"

    # --- Image upload validation ---
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"

    # --- Rate limiting (optional, future) ---
    RATE_LIMIT_ENABLED: bool = False

    @property
    def supported_areas_list(self) -> List[str]:
        return [a.strip() for a in self.SUPPORTED_AREAS.split(",") if a.strip()]

    @property
    def allowed_image_types_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",") if t.strip()]

    def ensure_directories(self) -> None:
        """Create required directories if they do not exist."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()