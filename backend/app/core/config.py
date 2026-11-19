import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "AgriGuard"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Relational Database (SQLite / PostgreSQL)
    DATABASE_URL: str = "sqlite:///./agriguard.db"

    # Neo4j Graph Database (AI Knowledge Graph & Outbreak Detection)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_MOCK_FALLBACK: bool = True

    # Security & JWT Authentication
    SECRET_KEY: str = "agriguard-change-this-secret-key-for-production-min32bytes-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # AI Service Integration (Person 2's API)
    AI_SERVICE_URL: str = "http://localhost:8001/api/v1/predict"
    AI_SERVICE_TIMEOUT_SECONDS: int = 10
    AI_SERVICE_MOCK_FALLBACK: bool = True

    # Notification & SMS Gateway (Africa's Talking / Mock)
    SMS_PROVIDER: str = "mock"
    AFRICASTALKING_USERNAME: str = "sandbox"
    AFRICASTALKING_API_KEY: str = ""
    SMS_SENDER_ID: str = "AgriGuard"

    # File Uploads
    UPLOAD_DIR: str = "app/static/uploads"
    MAX_IMAGE_SIZE_MB: int = 10

    # USSD & IVR Gateway Channels
    # Shared secret used to authenticate the gateway caller (NOT JWT). Fail-closed
    # when unset/empty: the verify_gateway_secret dependency rejects with 503.
    USSD_IVR_GATEWAY_SECRET: str = "agriguard-dev-ussd-ivr-secret-change-me"
    USSD_PROVIDER: str = "africas_talking"
    IVR_PROVIDER: str = "generic_voice"

    # Outbreak Detection Engine
    OUTBREAK_RADIUS_KM: float = 10.0
    OUTBREAK_MIN_REPORTS: int = 2
    ALERT_COOLDOWN_HOURS: int = 24

    # Pydantic Settings Config
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def upload_path(self) -> Path:
        """Returns the absolute upload path and ensures it exists."""
        base_dir = Path(os.path.dirname(os.path.dirname(__file__)))
        target = base_dir / "static" / "uploads"
        target.mkdir(parents=True, exist_ok=True)
        return target


settings = Settings()
