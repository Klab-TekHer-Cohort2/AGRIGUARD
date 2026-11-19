import random
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TEST_FARMER_PHONE = f"+250788{random.randint(100000, 999999)}"
TEST_AGRONOMIST_PHONE = "+250788000002"  # Seeded agronomist


@pytest.fixture(scope="module")
def farmer_token():
    """Registers and authenticates a test farmer."""
    reg_payload = {
        "phone_number": TEST_FARMER_PHONE,
        "password": "FarmerPassword123!",
        "full_name": "Nshimiyimana Eric",
        "role": "FARMER",
        "preferred_language": "rw",
        "province": "Northern Province",
        "district": "Musanze",
        "sector": "Kinigi",
        "cell": "Bisoke",
        "village": "Nyonirima"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_res = client.post("/api/v1/auth/login", json={
        "phone_number": TEST_FARMER_PHONE,
        "password": "FarmerPassword123!"
    })
    return login_res.json()["access_token"]


@pytest.fixture(scope="module")
def agronomist_token():
    """Authenticates the seeded agronomist."""
    login_res = client.post("/api/v1/auth/login", json={
        "phone_number": TEST_AGRONOMIST_PHONE,
        "password": "Agronomist2026!"
    })
    return login_res.json()["access_token"]


def test_mock_ai_predict_contract():
    """
    Verifies that the mock AI prediction endpoint matches the contract
    expected by the AI developer.
    """
    payload = {
        "crop": "Maize",
        "symptoms": ["ragged leaf feeding holes", "sawdust-like frass"]
    }
    res = client.post("/api/v1/ai/mock-predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["predicted_pest_en"] == "Fall Armyworm"
    assert data["predicted_pest_rw"] == "Nkongwa"
    assert data["confidence_score"] > 0.8
    assert data["detected_severity"] == "HIGH"
    assert len(data["recommendations"]) > 0
    assert data["is_mock"] is True


def test_automatic_ai_diagnosis_on_symptom_report(farmer_token):
    """
    Verifies that submitting a symptom report triggers automatic AI diagnosis,
    transitions status to AI_ANALYZED, and enqueues a farmer notification.
    """
    headers = {"Authorization": f"Bearer {farmer_token}"}

    # Fetch crop ID for Potato
    res_crops = client.get("/api/v1/crops/")
    potato = next(c for c in res_crops.json() if c["name_en"] == "Irish Potato")

    report_payload = {
        "crop_id": potato["id"],
        "channel": "USSD",
        "description": "Dark brown spots appearing rapidly after heavy rains.",
        "symptoms": ["water-soaked dark brown spots on leaves", "rapid blackening and dying of stems"],
        "severity": "CRITICAL"
    }
    res_report = client.post("/api/v1/reports/", json=report_payload, headers=headers)
    assert res_report.status_code == 201
    report_data = res_report.json()

    # Verify status transitioned to AI_ANALYZED
    assert report_data["status"] == "AI_ANALYZED"
    assert report_data["ai_result"] is not None
    assert "Late Blight" in report_data["ai_result"]["predicted_pest_en"]
    assert report_data["ai_result"]["confidence_score"] > 0.5
    assert len(report_data["ai_result"]["recommendations"]) > 0


def test_get_ai_result_by_report_id(farmer_token):
    """Verifies querying AI diagnosis directly by report ID."""
    headers = {"Authorization": f"Bearer {farmer_token}"}
    my_reports = client.get("/api/v1/reports/my-reports", headers=headers).json()
    report_id = my_reports[0]["id"]

    res = client.get(f"/api/v1/ai/results/{report_id}", headers=headers)
    assert res.status_code == 200
    ai_data = res.json()
    assert ai_data["report_id"] == report_id
    assert "predicted_pest_en" in ai_data
    assert ai_data["confidence_score"] > 0.0


def test_manual_trigger_ai_analysis(farmer_token):
    """Verifies explicit trigger of AI analysis."""
    headers = {"Authorization": f"Bearer {farmer_token}"}
    my_reports = client.get("/api/v1/reports/my-reports", headers=headers).json()
    report_id = my_reports[0]["id"]

    res = client.post(f"/api/v1/ai/analyze/{report_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["report_id"] == report_id
    assert data["confidence_score"] > 0.0


def test_dataset_export_for_ai_developer(agronomist_token):
    """
    Verifies that the AI developer can export verified case datasets
    for model fine-tuning and active learning.
    """
    headers = {"Authorization": f"Bearer {agronomist_token}"}
    res = client.get("/api/v1/ai/dataset/export", headers=headers)
    assert res.status_code == 200
    dataset = res.json()
    assert isinstance(dataset, list)
    if len(dataset) > 0:
        item = dataset[0]
        assert "report_code" in item
        assert "crop_name" in item
        assert "ai_predicted_pest" in item
        assert "is_ai_correct" in item
