import random
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

AGRONOMIST_PHONE = "+250788000002"
FARMER_PHONE = f"+250788{random.randint(100000, 999999)}"


@pytest.fixture(scope="module")
def agronomist_token():
    """Authenticates the seeded agronomist."""
    res = client.post("/api/v1/auth/login", json={
        "phone_number": AGRONOMIST_PHONE,
        "password": "Agronomist2026!"
    })
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def farmer_token():
    """Registers and authenticates a farmer to verify RBAC access control."""
    client.post("/api/v1/auth/register", json={
        "phone_number": FARMER_PHONE,
        "password": "FarmerPassword123!",
        "full_name": "Rutayisire Jean",
        "role": "FARMER"
    })
    res = client.post("/api/v1/auth/login", json={
        "phone_number": FARMER_PHONE,
        "password": "FarmerPassword123!"
    })
    return res.json()["access_token"]


def test_dashboard_access_control(farmer_token, agronomist_token):
    """
    Verifies that farmers are forbidden (403) from accessing the agronomist dashboard,
    while agronomists have full authorized access (200).
    """
    # Farmer attempt -> 403 Forbidden
    farmer_headers = {"Authorization": f"Bearer {farmer_token}"}
    res_forbidden = client.get("/api/v1/dashboard/stats", headers=farmer_headers)
    assert res_forbidden.status_code == 403

    # Agronomist attempt -> 200 OK
    agro_headers = {"Authorization": f"Bearer {agronomist_token}"}
    res_ok = client.get("/api/v1/dashboard/stats", headers=agro_headers)
    assert res_ok.status_code == 200


def test_dashboard_kpis_and_overview(agronomist_token):
    """Verifies dashboard overview returns valid metrics, charts, and lists."""
    headers = {"Authorization": f"Bearer {agronomist_token}"}
    res = client.get("/api/v1/dashboard/stats", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Verify KPI structure
    kpis = data["kpis"]
    assert "total_farmers" in kpis
    assert "total_reports" in kpis
    assert "verified_reports" in kpis
    assert kpis["total_farmers"] >= 1
    assert kpis["total_reports"] >= 1

    # Verify pest statistics list
    assert "pest_statistics" in data
    assert isinstance(data["pest_statistics"], list)

    # Verify location breakdown
    assert "location_breakdown" in data
    assert isinstance(data["location_breakdown"], list)

    # Verify recent reports
    assert "recent_reports" in data
    assert len(data["recent_reports"]) >= 1


def test_dashboard_filtering_by_district(agronomist_token):
    """Verifies that geographic filtering scopes dashboard data accurately."""
    headers = {"Authorization": f"Bearer {agronomist_token}"}
    res = client.get("/api/v1/dashboard/stats?district=Musanze", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["kpis"]["total_reports"] >= 1

    # All returned recent reports should belong to Musanze
    for r in data["recent_reports"]:
        assert r["district"].lower() == "musanze"


def test_dashboard_pest_trends(agronomist_token):
    """Verifies pest frequency rankings endpoint."""
    headers = {"Authorization": f"Bearer {agronomist_token}"}
    res = client.get("/api/v1/dashboard/pest-trends", headers=headers)
    assert res.status_code == 200
    trends = res.json()
    assert isinstance(trends, list)
    if len(trends) > 0:
        first = trends[0]
        assert "pest_name" in first
        assert "count" in first
        assert "percentage" in first


def test_dashboard_map_clusters(agronomist_token):
    """Verifies geolocated report points for the interactive map."""
    headers = {"Authorization": f"Bearer {agronomist_token}"}
    res = client.get("/api/v1/dashboard/map-clusters", headers=headers)
    assert res.status_code == 200
    points = res.json()
    assert isinstance(points, list)
    for p in points:
        assert "latitude" in p
        assert "longitude" in p
        assert "severity" in p
        assert "crop_name" in p
