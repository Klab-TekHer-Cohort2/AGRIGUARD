"""SQLAlchemy models for FloraGuard database.

Tables:
- reports: All incoming reports from smartphone, USSD, and IVR channels.
- weather_observations: Cached weather data from Open-Meteo.
- risk_assessments: Deterministic risk engine results.
- alerts: Generated alerts for HIGH risk conditions.

All tables are created safely using SQLAlchemy metadata.create_all().
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Report(Base):
    """A pest/disease report from any channel."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Where the report came from: smartphone, USSD or IVR
    input_channel: Mapped[str] = mapped_column(String(20), index=True)

    # Problem reported or detected
    problem_type: Mapped[str] = mapped_column(String(100), index=True)

    # Reported severity: mild, moderate or severe
    severity: Mapped[str] = mapped_column(String(20), index=True)

    # AI confidence; remains null for USSD and IVR
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Location information
    area: Mapped[str] = mapped_column(String(100), index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Optional image location (smartphone only)
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Optional human description (USSD/IVR/smartphone)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Associated weather data (nullable; weather may be unavailable)
    weather_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_humidity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Time the report was received
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        index=True,
    )


class WeatherObservation(Base):
    """Cached weather observation from Open-Meteo."""

    __tablename__ = "weather_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Source identifier, e.g. "open-meteo"
    source: Mapped[str] = mapped_column(String(50), default="open-meteo")

    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        index=True,
    )


class RiskAssessment(Base):
    """Deterministic risk engine result for an area/problem."""

    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    area: Mapped[str] = mapped_column(String(100), index=True)
    problem_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    risk_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(20), index=True)

    # Number of reports that contributed to this assessment
    contributing_report_count: Mapped[int] = mapped_column(Integer, default=0)

    # Supporting reasons (stored as newline-separated text)
    reasons: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Weather snapshot at assessment time
    weather_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    weather_available: Mapped[bool] = mapped_column(Integer, default=0)

    assessment_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        index=True,
    )


class Alert(Base):
    """Generated alert for HIGH risk conditions."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    problem_type: Mapped[str] = mapped_column(String(100), index=True)
    area: Mapped[str] = mapped_column(String(100), index=True)
    risk_level: Mapped[str] = mapped_column(String(20), index=True)
    risk_score: Mapped[float] = mapped_column(Float)

    # Supporting reasons (newline-separated)
    reasons: Mapped[str | None] = mapped_column(Text, nullable=True)

    # General preventive guidance (no pesticide mixing instructions)
    preventive_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Delivery status: pending, sent, failed, skipped
    delivery_status: Mapped[str] = mapped_column(String(20), default="pending")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        index=True,
    )