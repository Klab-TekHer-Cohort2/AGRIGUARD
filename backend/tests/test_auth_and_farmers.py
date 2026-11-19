import random
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

TEST_PHONE = f"+250788{random.randint(200000, 899999)}"
TEST_EMAIL = f"farmer_{random.randint(1000, 9999)}@example.rw"


def test_farmer_registration_full_flow():
    """
    Tests registering a new Rwandan farmer with phone, credentials,
    and farm location in Musanze district.
    """
    payload = {
        "phone_number": TEST_PHONE,
        "password": "StrongPassword123!",
        "full_name": "Kwizera Jean de Dieu",
        "email": TEST_EMAIL,
        "role": "FARMER",
        "preferred_language": "rw",
        "national_id": "1199080034125678",
        "cooperative_name": "KOABIKI",
        "province": "Northern Province",
        "district": "Musanze",
        "sector": "Kinigi",
        "cell": "Bisoke",
        "village": "Nyonirima",
        "latitude": -1.4332,
        "longitude": 29.5891
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "FARMER"
    assert data["phone_number"] == TEST_PHONE
    assert data["full_name"] == "Kwizera Jean de Dieu"


def test_duplicate_registration_rejected():
    """Verifies duplicate phone numbers cannot be registered."""
    payload = {
        "phone_number": TEST_PHONE,
        "password": "AnotherPassword123!",
        "full_name": "Duplicate User",
        "role": "FARMER"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_farmer_login():
    """Verifies valid and invalid login scenarios."""
    # Successful login
    valid_payload = {
        "phone_number": TEST_PHONE,
        "password": "StrongPassword123!"
    }
    res_valid = client.post("/api/v1/auth/login", json=valid_payload)
    assert res_valid.status_code == 200
    token_data = res_valid.json()
    assert "access_token" in token_data

    # Invalid login (wrong password)
    invalid_payload = {
        "phone_number": TEST_PHONE,
        "password": "WrongPassword!"
    }
    res_invalid = client.post("/api/v1/auth/login", json=invalid_payload)
    assert res_invalid.status_code == 401


def test_me_protected_endpoint():
    """Verifies protected /auth/me endpoint with Bearer authentication."""
    # Obtain token
    login_res = client.post("/api/v1/auth/login", json={
        "phone_number": TEST_PHONE,
        "password": "StrongPassword123!"
    })
    token = login_res.json()["access_token"]

    # Call with token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["phone_number"] == TEST_PHONE
    assert user_data["role"] == "FARMER"

    # Call without token
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401


def test_farmer_profile_and_update():
    """Verifies retrieving and updating the farmer profile."""
    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "phone_number": TEST_PHONE,
        "password": "StrongPassword123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch profile
    profile_res = client.get("/api/v1/farmers/profile", headers=headers)
    assert profile_res.status_code == 200
    data = profile_res.json()
    assert data["preferred_language"] == "rw"
    assert len(data["locations"]) >= 1
    assert data["locations"][0]["district"] == "Musanze"

    # Update profile
    update_res = client.put(
        "/api/v1/farmers/profile",
        json={"cooperative_name": "COOP-KINIGI-UPDATED", "preferred_language": "en"},
        headers=headers,
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["cooperative_name"] == "COOP-KINIGI-UPDATED"
    assert updated_data["preferred_language"] == "en"


def test_fast_phone_lookup_for_ussd_and_ivr():
    """Verifies the secured phone-number lookup used by USSD and IVR sessions.

    The endpoint is now gated behind the gateway shared secret and returns only
    the minimal identification fields (PII such as user_id and location/village
    removed).
    """
    gw_headers = {"X-AgriGuard-Gateway-Secret": settings.USSD_IVR_GATEWAY_SECRET}

    # Unauthenticated call now rejected (PII leak closed).
    res_unauth = client.get(f"/api/v1/farmers/by-phone/{TEST_PHONE}")
    assert res_unauth.status_code == 401

    # Gateway-authenticated lookup of an existing farmer returns minimal fields.
    res_found = client.get(f"/api/v1/farmers/by-phone/{TEST_PHONE}", headers=gw_headers)
    assert res_found.status_code == 200
    data_found = res_found.json()
    assert data_found["is_registered"] is True
    assert data_found["full_name"] == "Kwizera Jean de Dieu"
    assert data_found["preferred_language"] in ("rw", "en")
    assert "farmer_id" in data_found and data_found["farmer_id"] is not None
    assert "primary_district" not in data_found
    assert "user_id" not in data_found

    # Non-registered phone lookup (still gateway-authenticated).
    res_not_found = client.get("/api/v1/farmers/by-phone/+250788999999", headers=gw_headers)
    assert res_not_found.status_code == 200
    assert res_not_found.json()["is_registered"] is False

    # A wrong gateway secret is rejected.
    res_wrong = client.get(
        f"/api/v1/farmers/by-phone/{TEST_PHONE}",
        headers={"X-AgriGuard-Gateway-Secret": "definitely-wrong"},
    )
    assert res_wrong.status_code == 401


def test_farmer_location_management():
    """Verifies adding a secondary farm plot and switching primary location."""
    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "phone_number": TEST_PHONE,
        "password": "StrongPassword123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add a second plot in Nyabihu
    plot_payload = {
        "province": "Western Province",
        "district": "Nyabihu",
        "sector": "Mukamira",
        "cell": "Jenda",
        "village": "Kageyo",
        "latitude": -1.5833,
        "longitude": 29.5000,
        "is_primary": False
    }
    add_res = client.post("/api/v1/locations/", json=plot_payload, headers=headers)
    assert add_res.status_code == 201
    new_loc = add_res.json()
    assert new_loc["district"] == "Nyabihu"
    new_loc_id = new_loc["id"]

    # Get my locations
    my_locs_res = client.get("/api/v1/locations/my-locations", headers=headers)
    assert my_locs_res.status_code == 200
    assert len(my_locs_res.json()) >= 2

    # Set the Nyabihu plot as primary
    set_primary_res = client.put(f"/api/v1/locations/{new_loc_id}/primary", headers=headers)
    assert set_primary_res.status_code == 200
    assert set_primary_res.json()["is_primary"] is True
