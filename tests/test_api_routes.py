"""Tests: API routes (integration via FastAPI TestClient).

Mirrors ``tests/api.routes.test.js``.
"""

import re

from fastapi.testclient import TestClient

from app.main import app
from app.data.prototype_dataset import prototype_dataset as dataset

client = TestClient(app)


def test_health_returns_ok():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert re.search(r"AgriGuard", body["service"])


def test_analyse_report_with_valid_input():
    res = client.post("/api/ai/analyse-report", json=dataset["demoScenarios"]["smartphoneReport"])
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["category"] is not None
    assert body["data"]["confidence"] >= 0


def test_analyse_report_rejects_missing_crop():
    res = client.post("/api/ai/analyse-report", json={"description": "something"})
    assert res.status_code == 400
    assert res.json()["error"] == "VALIDATION_ERROR"


def test_ask_with_valid_question():
    res = client.post("/api/ai/ask", json={"question": "How do I prevent Fall Armyworm in maize?"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["answer"] is not None


def test_community_risk_with_prototype_reports():
    res = client.post("/api/ai/community-risk", json={"reports": dataset["reports"]})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["riskLevel"] is not None
    assert data["prototype"] is True


def test_outbreak_detection_returns_alertable_farmers():
    res = client.post(
        "/api/ai/outbreak-detection",
        json={"reports": dataset["reports"], "farmers": dataset["farmers"]},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert "alertableFarmers" in data
    assert isinstance(data["alertableCount"], int)


def test_ussd_response_returns_short_text():
    res = client.post("/api/ai/ussd-response", json=dataset["demoScenarios"]["ussdReport"])
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["ussdResponse"] is not None
    assert isinstance(data["ussdResponse"], str)


def test_demo_runs_the_full_flow():
    res = client.get("/api/ai/demo")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["step1_smartphoneAnalysis"] is not None
    assert data["step2_unknownReport"] is not None
    assert data["step4_communityRisk"] is not None
    assert data["step5_askAgriGuardEnglish"] is not None
    assert data["step5b_askAgriGuardKinyarwanda"] is not None
    assert data["step6_ussdResponse"] is not None


def test_unknown_route_returns_404():
    res = client.get("/api/ai/nonexistent")
    assert res.status_code == 404
