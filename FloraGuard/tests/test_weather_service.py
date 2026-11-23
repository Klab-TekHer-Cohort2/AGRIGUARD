"""Focused tests for WeatherData and weather service error handling."""

import time
from unittest.mock import patch

import httpx

from app.services.weather_service import WeatherData, WeatherService


def test_weatherdata_defaults():
    w = WeatherData()
    assert w.temperature is None
    assert w.humidity is None
    assert w.available is True
    assert w.source == "open-meteo"
    assert w.retrieved_at > 0


def test_weatherdata_custom():
    w = WeatherData(temperature=20.0, humidity=50.0, available=False, retrieved_at=123.0)
    assert w.temperature == 20.0
    assert w.humidity == 50.0
    assert w.available is False
    assert w.retrieved_at == 123.0


def test_fetch_weather_timeout_returns_unavailable():
    svc = WeatherService(base_url="http://example.com", timeout=0.01)
    with patch("httpx.Client.get", side_effect=httpx.TimeoutException("timeout")):
        w = svc.fetch_weather(1.0, 2.0)
    assert w.available is False
    assert w.is_valid is False


def test_fetch_weather_invalid_response():
    svc = WeatherService(base_url="http://example.com", timeout=1.0)
    class FakeResp:
        def raise_for_status(self):
            pass
        def json(self):
            return {"foo": "bar"}
    with patch("httpx.Client.get", return_value=FakeResp()):
        w = svc.fetch_weather(1.0, 2.0)
    assert w.available is False
