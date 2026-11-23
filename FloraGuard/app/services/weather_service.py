"""Weather integration service using Open-Meteo (free, no API key required).

Handles:
- Fetching temperature and humidity for given coordinates
- Timeout and network error handling
- Data validation
- Caching of recent observations

The service is designed to be testable with mocked HTTP responses.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Structured weather observation."""

    temperature: Optional[float] = None
    humidity: Optional[float] = None
    retrieved_at: float = field(default_factory=lambda: time.time())  # epoch seconds
    source: str = "open-meteo"
    available: bool = True

    @property
    def is_valid(self) -> bool:
        """Check if the weather data contains usable values."""
        return self.temperature is not None or self.humidity is not None


class WeatherService:
    """Fetches weather data from Open-Meteo."""

    def __init__(self, base_url: str = "", timeout: float = 0.0) -> None:
        self._base_url = base_url or settings.WEATHER_BASE_URL
        self._timeout = timeout or settings.WEATHER_TIMEOUT_SECONDS
        self._cache: dict[str, tuple[float, WeatherData]] = {}
        self._cache_ttl = settings.WEATHER_CACHE_TTL_SECONDS

    def _cache_key(self, lat: float, lon: float) -> str:
        return f"{lat:.4f},{lon:.4f}"

    def _get_cached(self, lat: float, lon: float) -> Optional[WeatherData]:
        key = self._cache_key(lat, lon)
        if key in self._cache:
            ts, data = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return data
            del self._cache[key]
        return None

    def _cache_set(self, lat: float, lon: float, data: WeatherData) -> None:
        key = self._cache_key(lat, lon)
        self._cache[key] = (time.time(), data)

    def fetch_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> WeatherData:
        """Fetch current weather for the given coordinates.

        Returns a WeatherData object. If the service fails, returns
        an unavailable WeatherData with available=False.
        """
        # Check cache first
        cached = self._get_cached(latitude, longitude)
        if cached is not None:
            return cached

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m",
            "timezone": "auto",
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(self._base_url, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            logger.warning("Weather request timed out for %s, %s", latitude, longitude)
            return WeatherData(retrieved_at=time.time(), available=False)
        except httpx.NetworkError as exc:
            logger.warning("Weather network error: %s", exc)
            return WeatherData(retrieved_at=time.time(), available=False)
        except httpx.HTTPStatusError as exc:
            logger.warning("Weather HTTP error %s: %s", exc.response.status_code, exc)
            return WeatherData(retrieved_at=time.time(), available=False)
        except Exception as exc:
            logger.warning("Weather fetch failed: %s", exc)
            return WeatherData(retrieved_at=time.time(), available=False)

        # Validate response structure
        current = data.get("current") if isinstance(data, dict) else None
        if not isinstance(current, dict):
            logger.warning("Weather response missing 'current' field")
            return WeatherData(retrieved_at=time.time(), available=False)

        temperature = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")

        # Validate types
        if temperature is not None and not isinstance(temperature, (int, float)):
            temperature = None
        if humidity is not None and not isinstance(humidity, (int, float)):
            humidity = None

        weather = WeatherData(
            temperature=float(temperature) if temperature is not None else None,
            humidity=float(humidity) if humidity is not None else None,
            retrieved_at=time.time(),
            source="open-meteo",
            available=True,
        )

        # Only cache if we got at least one usable value
        if weather.is_valid:
            self._cache_set(latitude, longitude, weather)

        return weather


# Singleton instance
weather_service = WeatherService()