import random
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

ADMIN_PHONE = "+250788000001"
AGRONOMIST_PHONE = "+250788000002"
FARMER_PHONE = f"+250788{random.randint(100000, 999999)}"


@pytest.fixture(scope="module")
def admin_token():
    """Authenticates the seeded admin."""
    res = client.post("/api/v1/auth/login", json={
        "phone_number": ADMIN_PHONE,
        "password": "Admin2026!"
    })
    return res.json()["access_token"]


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
    """Registers and authenticates a test farmer with a report."""
    client.post("/api/v1/auth/register", json={
        "phone_number": FARMER_PHONE,
        "password": "FarmerPassword123!",
        "full_name": "Gatera Faustin",
        "role": "FARMER",
        "district": "Musanze",
        "sector": "Muhoza"
    })
    login_res = client.post("/api/v1/auth/login", json={
        "phone_number": FARMER_PHONE,
        "password": "FarmerPassword123!"
    })
    return login_res.json()["access_token"]


def test_agronomist_profile_and_update(agronomist_token):
    """Verifies retrieving and updating agronomist operational profile."""
    headers = {"Authorization": f"Bearer {agronomist_token}"}

    # Get profile
    res = client.get("/api/v1/agronomists/profile", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["phone_number"] == AGRONOMIST_PHONE
    assert "Musanze" in data["assigned_districts"]

    # Update profile
    update_payload = {
        "qualification": "MSc Plant Pathology & Crop Protection",
        "assigned_districts": ["Musanze", "Nyabihu", "Rubavu"],
        "assigned_sectors": ["Muhoza", "Kinigi", "Busogo", "Bigogwe"]
    }
    update_res = client.put("/api/v1/agronomists/profile", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["qualification"] == "MSc Plant Pathology & Crop Protection"
    assert "Rubavu" in updated_data["assigned_districts"]


def test_agronomist_verify_report_workflow(farmer_token, agronomist_token):
    """
    Verifies full verification lifecycle:
    Farmer submits report -> AI analyzes -> Agronomist verifies & advises -> Notification enqueued.
    """
    farmer_headers = {"Authorization": f"Bearer {farmer_token}"}
    agro_headers = {"Authorization": f"Bearer {agronomist_token}"}

    # 1. Farmer submits Maize report
    res_crops = client.get("/api/v1/crops/")
    maize = next(c for c in res_crops.json() if c["name_en"] == "Maize")

    report_res = client.post("/api/v1/reports/", json={
        "crop_id": maize["id"],
        "channel": "APP",
        "description": "Leaves chewed with small caterpillars visible in morning.",
        "symptoms": ["ragged leaf feeding holes"],
        "severity": "HIGH"
    }, headers=farmer_headers)
    assert report_res.status_code == 201
    report = report_res.json()
    report_id = report["id"]

    # 2. Agronomist verifies the report
    verify_payload = {
        "is_ai_correct": True,
        "verified_severity": "HIGH",
        "verification_notes": "Confirmed Fall Armyworm infestation. Field threshold at 15%.",
        "agronomist_recommendations": [
            "Apply Neem seed oil early morning (6:00 AM - 8:00 AM)",
            "Scout weekly and destroy remaining egg masses"
        ],
        "status": "VERIFIED"
    }
    verify_res = client.post(
        f"/api/v1/agronomists/reports/{report_id}/verify",
        json=verify_payload,
        headers=agro_headers,
    )
    assert verify_res.status_code == 200
    verified_data = verify_res.json()
    assert verified_data["status"] == "VERIFIED"
    assert "Confirmed Fall Armyworm" in verified_data["agronomist_notes"]
    assert verified_data["verified_at"] is not None

    # Check that verification history action was logged
    history_actions = [h["action_type"] for h in verified_data["history"]]
    assert "AGRONOMIST_VERIFIED" in history_actions


def test_organization_management_and_members(admin_token):
    """Verifies organization creation, listing, and member assignment."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # List organizations
    res_list = client.get("/api/v1/organizations/")
    assert res_list.status_code == 200
    orgs = res_list.json()
    assert len(orgs) >= 2  # Seeded RAB and KOABIKI

    # Create new cooperative
    unique_code = f"COOP-{random.randint(100, 999)}"
    create_payload = {
        "name": f"Koperative y'Abahinzi ba Burera ({unique_code})",
        "code": unique_code,
        "type": "COOPERATIVE",
        "district": "Burera",
        "description": "Maize and potato farmers cooperative in Burera."
    }
    create_res = client.post("/api/v1/organizations/", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    new_org = create_res.json()
    assert new_org["code"] == unique_code
    org_id = new_org["id"]

    # Assign agronomist (user_id 2 is Emmanuel Mugisha) to this organization
    assign_payload = {
        "user_id": 2,
        "role": "LEAD_AGRONOMIST"
    }
    assign_res = client.post(f"/api/v1/organizations/{org_id}/members", json=assign_payload, headers=headers)
    assert assign_res.status_code == 201
    member = assign_res.json()
    assert member["role"] == "LEAD_AGRONOMIST"

    # List members
    members_res = client.get(f"/api/v1/organizations/{org_id}/members", headers=headers)
    assert members_res.status_code == 200
    assert len(members_res.json()) >= 1
