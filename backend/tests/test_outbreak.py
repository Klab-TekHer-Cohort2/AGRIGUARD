import random

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from app.models.alert import Notification, NotificationStatus
from app.services.outbreak_service import (
    _build_alert_messages,
    _haversine,
    get_weather_risk_factor,
)

client = TestClient(app)
AGRONOMIST_PHONE = "+250788000002"
ADMIN_PHONE = "+250788000001"


def _register_farmer(suffix, preferred_language="rw"):
    phone = f"+250788{suffix:06d}"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "phone_number": phone,
            "password": "FarmerPassword123!",
            "full_name": f"Outbreak Farmer {suffix}",
            "role": "FARMER",
            "preferred_language": preferred_language,
            "province": "Northern Province",
            "district": "Musanze",
            "sector": "Muhoza",
            "cell": "Mpenge",
            "village": f"Outbreak-{suffix}",
            "latitude": -1.4998,
            "longitude": 29.6349,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def agronomist_token():
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": AGRONOMIST_PHONE,
            "password": "Agronomist2026!",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def farmer_token():
    return _register_farmer(random.randint(100000, 999999))


@pytest.fixture(scope="module")
def two_matching_reports():
    crop_response = client.get("/api/v1/crops/")
    assert crop_response.status_code == 200
    maize = next(crop for crop in crop_response.json() if crop["name_en"] == "Maize")

    report_ids = []
    tokens = []
    for suffix in (random.randint(100000, 499999), random.randint(500000, 999999)):
        token = _register_farmer(suffix)
        tokens.append(token)
        response = client.post(
            "/api/v1/reports/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "crop_id": maize["id"],
                "channel": "APP",
                "description": "Signs of an outbreak in the field.",
                "symptoms": ["ragged leaf feeding holes", "sawdust-like frass"],
                "severity": "HIGH",
            },
        )
        assert response.status_code == 201, response.text
        report = response.json()
        assert report["ai_result"] is not None
        report_ids.append(report["id"])
    return tokens, report_ids


def test_haversine_and_weather_stub():
    assert _haversine(0.0, 0.0, 0.0, 0.0) == 0.0
    assert 110.0 < _haversine(0.0, 0.0, 1.0, 0.0) < 112.0
    assert get_weather_risk_factor("Musanze") == 1.0
    assert settings.OUTBREAK_RADIUS_KM >= 0.1


def test_build_alert_messages_is_bilingual_and_uses_two_tips():
    title_en, title_rw, message_en, message_rw = _build_alert_messages(
        pest_name_en="Fall Armyworm",
        pest_name_rw="Nkongwa",
        severity_label="HIGH",
        neo4j_tips=["Tip one", "Tip two", "Tip three"],
        district="Musanze",
        neo4j_tips_rw=["Inama ya mbere", "Inama ya kabiri", "Inama ya gatatu"],
    )
    assert title_en == "Outbreak Alert: Fall Armyworm in Musanze"
    assert title_rw == "Impuruza: Nkongwa mu Musanze"
    assert "Tip one Tip two" in message_en
    assert "Tip three" not in message_en
    assert "Inama ya mbere Inama ya kabiri" in message_rw
    assert "Inama ya gatatu" not in message_rw


def test_get_alerts_farmer_denied(farmer_token):
    response = client.get(
        "/api/v1/outbreak/alerts",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert response.status_code == 403


def test_get_alerts_agronomist_allowed(agronomist_token):
    response = client.get(
        "/api/v1/outbreak/alerts",
        headers={"Authorization": f"Bearer {agronomist_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_outbreak_alert_created_on_matching_reports(
    agronomist_token,
    two_matching_reports,
):
    _, report_ids = two_matching_reports
    headers = {"Authorization": f"Bearer {agronomist_token}"}
    alerts = client.get("/api/v1/outbreak/alerts", headers=headers)
    assert alerts.status_code == 200, alerts.text
    if not any(alert["pest_name"] == "Fall Armyworm" for alert in alerts.json()):
        check = client.post(
            "/api/v1/outbreak/check",
            headers=headers,
            json={"report_id": report_ids[1]},
        )
        assert check.status_code == 200, check.text
        assert check.json()["alert_created"] is True

    alerts = client.get(
        "/api/v1/outbreak/alerts?pest_name=Fall%20Armyworm&status=ACTIVE",
        headers=headers,
    )
    assert alerts.status_code == 200, alerts.text
    created_alert = next(
        alert for alert in alerts.json() if alert["pest_name"] == "Fall Armyworm"
    )
    details = client.get(
        f"/api/v1/outbreak/alerts/{created_alert['id']}",
        headers=headers,
    )
    assert details.status_code == 200, details.text
    assert details.json()["message_en"]

    db = SessionLocal()
    try:
        notifications = (
            db.query(Notification)
            .filter(Notification.alert_id == created_alert["id"])
            .all()
        )
        assert notifications
        assert all(
            notification.status == NotificationStatus.PENDING
            for notification in notifications
        )
    finally:
        db.close()


def test_cooldown_prevents_duplicate_alert(
    agronomist_token,
    two_matching_reports,
):
    _, report_ids = two_matching_reports
    response = client.post(
        "/api/v1/outbreak/check",
        headers={"Authorization": f"Bearer {agronomist_token}"},
        json={"report_id": report_ids[0]},
    )
    assert response.status_code == 200, response.text
    assert response.json()["alert_created"] is False


def test_resolve_alert(agronomist_token, two_matching_reports):
    headers = {"Authorization": f"Bearer {agronomist_token}"}
    alerts = client.get(
        "/api/v1/outbreak/alerts?pest_name=Fall%20Armyworm&status=ACTIVE",
        headers=headers,
    )
    assert alerts.status_code == 200, alerts.text
    alert_id = next(
        alert["id"] for alert in alerts.json() if alert["pest_name"] == "Fall Armyworm"
    )

    response = client.post(
        f"/api/v1/outbreak/alerts/{alert_id}/resolve",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "RESOLVED"
    assert response.json()["resolved_at"] is not None

    repeated = client.post(
        f"/api/v1/outbreak/alerts/{alert_id}/resolve",
        headers=headers,
    )
    assert repeated.status_code == 400


def test_get_risk_score(agronomist_token, two_matching_reports):
    response = client.get(
        "/api/v1/outbreak/risk-score?district=Musanze&pest_name=Fall%20Armyworm",
        headers={"Authorization": f"Bearer {agronomist_token}"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert isinstance(payload["risk_score"], float)
    assert 0.0 <= payload["risk_score"] <= 1.0
    assert payload["contributing_report_count"] >= 2
    assert payload["above_threshold"] is True


def test_get_risk_score_farmer_denied(farmer_token):
    response = client.get(
        "/api/v1/outbreak/risk-score?district=Musanze",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert response.status_code == 403
