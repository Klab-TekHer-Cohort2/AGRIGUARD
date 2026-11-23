"""Weather-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WeatherObservation(BaseModel):
    """Weather data point."""

    temperature: Optional[float] = None
    humidity: Optional[float] = None
    retrieved_at: datetime
    source: str = "open-meteo"
    available: bool = True