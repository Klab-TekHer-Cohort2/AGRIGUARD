import io
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
        "full_name": "Hakizimana Claude",
        "role": "FARMER",
        "preferred_language": "rw",
        "province": "Northern Province",
        "district": "Musanze",
        "sector": "Muhoza",
        "cell": "Mpenge",
        "village": "Gasharu"
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


def test_list_crops_and_categories():
    """Verifies crop catalogue and category filtering."""
    # List all
    res = client.get("/api/v1/crops/")
    assert res.status_code == 200
    crops = res.json()
    assert len(crops) >= 8

    # Category filter
    res_tubers = client.get("/api/v1/crops/?category=TUBER")
    assert res_tubers.status_code == 200
    tubers = res_tubers.json()
    names = [c["name_en"] for c in tubers]
    assert "Irish Potato" in names
    assert "Cassava" in names


def test_get_single_crop():
    """Verifies single crop retrieval by ID."""
    res_all = client.get("/api/v1/crops/")
    maize = next(c for c in res_all.json() if c["name_en"] == "Maize")

    res_single = client.get(f"/api/v1/crops/{maize['id']}")
    assert res_single.status_code == 200
    data = res_single.json()
    assert data["name_rw"] == "Ibigori"
    assert "Fall Armyworm" in data["common_pests"]


def test_submit_crop_problem_report(farmer_token):
    """Verifies submitting a problem report with symptoms and auto-location."""
    res_all = client.get("/api/v1/crops/")
    maize = next(c for c in res_all.json() if c["name_en"] == "Maize")

    headers = {"Authorization": f"Bearer {farmer_token}"}
    report_payload = {
        "crop_id": maize["id"],
        "channel": "APP",
        "description": "Caterpillars eating young leaves from inside the whorl.",
        "symptoms": ["ragged leaf feeding holes", "sawdust-like frass"],
        "severity": "HIGH"
    }
    res = client.post("/api/v1/reports/", json=report_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert "report_code" in data
    assert data["report_code"].startswith("AG")
    assert data["crop_name_en"] == "Maize"
    assert data["crop_name_rw"] == "Ibigori"
    assert data["district"] == "Musanze"
    assert data["sector"] == "Muhoza"
    assert data["severity"] == "HIGH"
    assert data["status"] in ["PENDING", "AI_ANALYZED"]
    assert data["ai_result"] is not None
    assert len(data["history"]) >= 1


def test_upload_crop_image_and_static_access(farmer_token):
    """Verifies photo upload and static HTTP access."""
    headers = {"Authorization": f"Bearer {farmer_token}"}

    # Fetch farmer's report
    my_reports_res = client.get("/api/v1/reports/my-reports", headers=headers)
    assert my_reports_res.status_code == 200
    report_id = my_reports_res.json()[0]["id"]

    # Create dummy JPEG image in memory
    fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00" + b"\x00" * 200
    files = {
        "file": ("test_pest_photo.jpg", io.BytesIO(fake_image_bytes), "image/jpeg")
    }

    upload_res = client.post(f"/api/v1/reports/{report_id}/images", files=files, headers=headers)
    assert upload_res.status_code == 201
    img_data = upload_res.json()
    assert "image_url" in img_data
    assert img_data["image_url"].startswith("/uploads/")

    # Test static access via GET /uploads/<filename>
    static_res = client.get(img_data["image_url"])
    assert static_res.status_code == 200
    assert len(static_res.content) == len(fake_image_bytes)
    assert static_res.headers["content-disposition"] == "attachment"
    assert static_res.headers["x-content-type-options"] == "nosniff"

    # Client-provided MIME types must not allow an executable extension.
    malicious_file = {
        "file": ("crop.html", io.BytesIO(b"<script>alert(1)</script>"), "image/jpeg")
    }
    rejected_upload = client.post(
        f"/api/v1/reports/{report_id}/images",
        files=malicious_file,
        headers=headers,
    )
    assert rejected_upload.status_code == 400


def test_get_report_details_by_code(farmer_token):
    """Verifies looking up report by its unique code with attached images."""
    headers = {"Authorization": f"Bearer {farmer_token}"}
    my_reports = client.get("/api/v1/reports/my-reports", headers=headers).json()
    report_code = my_reports[0]["report_code"]

    res = client.get(f"/api/v1/reports/{report_code}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["report_code"] == report_code
    assert len(data["images"]) >= 1
    assert data["images"][0]["file_name"].startswith("report_")


def test_agronomist_list_reports(agronomist_token):
    """Verifies agronomists can filter and inspect reports across districts."""
    headers = {"Authorization": f"Bearer {agronomist_token}"}
    res = client.get("/api/v1/reports/?district=Musanze", headers=headers)
    assert res.status_code == 200
    reports = res.json()
    assert len(reports) >= 1
    assert any(r["district"] == "Musanze" for r in reports)
