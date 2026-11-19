"""End-to-end IVR channel tests (generic voice-webhook JSON convention)."""
import json
import random
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.phone import normalize_phone_number
from app.models.user import User, Farmer
from app.models.session import IVRSession
from app.models.report import CropReport, ReportChannel
from app.models.ai import AIResult
from app.models.alert import Notification, NotificationChannel, NotificationStatus

client = TestClient(app)

GW_HEADERS = {"X-AgriGuard-Gateway-Secret": settings.USSD_IVR_GATEWAY_SECRET}
IVR_URL = "/api/v1/ivr/"


def ivr(call_sid, phone, digits=None, language=None, recording_url=None):
    body = {"call_sid": call_sid, "phone_number": phone}
    if digits is not None:
        body["digits"] = digits
    if language is not None:
        body["language"] = language
    if recording_url is not None:
        body["recording_url"] = recording_url
    return client.post(IVR_URL, json=body, headers=GW_HEADERS)


def ivr_register_and_report(call_sid, phone):
    """Drive WELCOME -> MAIN_MENU -> REPORT_CROP -> REPORT_SYMPTOM -> submit."""
    ivr(call_sid, phone)               # first call -> WELCOME (gather)
    ivr(call_sid, phone, digits="1")    # Kinyarwanda -> auto-register -> MAIN_MENU
    ivr(call_sid, phone, digits="1")    # MAIN_MENU -> REPORT_CROP
    ivr(call_sid, phone, digits="1")    # crop 1 (Maize) -> REPORT_SYMPTOM
    ivr(call_sid, phone, digits="1")    # symptom 1 -> REPORT_CONFIRM
    return ivr(call_sid, phone, digits="1")  # confirm -> submit


def latest_report_code(phone):
    db = SessionLocal()
    try:
        clean = normalize_phone_number(phone)
        user = db.query(User).filter(User.phone_number == clean).first()
        if not user or not user.farmer_profile:
            return None
        rpt = (
            db.query(CropReport)
            .filter(CropReport.farmer_id == user.farmer_profile.id)
            .order_by(CropReport.created_at.desc())
            .first()
        )
        return rpt.report_code if rpt else None
    finally:
        db.close()


def test_ivr_rejects_missing_secret():
    phone = f"+250790{random.randint(100000, 999999)}"
    res = client.post(
        IVR_URL,
        json={"call_sid": "cs-no-secret", "phone_number": phone},
    )
    assert res.status_code == 401


def test_ivr_rejects_wrong_secret():
    phone = f"+250790{random.randint(100000, 999999)}"
    res = client.post(
        IVR_URL,
        json={"call_sid": "cs-wrong-secret", "phone_number": phone},
        headers={"X-AgriGuard-Gateway-Secret": "definitely-wrong"},
    )
    assert res.status_code == 401


def test_ivr_request_body_validated_422():
    """Missing required phone_number -> 422 (IVRRequest body validation, finding #2)."""
    res = client.post(
        IVR_URL,
        json={"call_sid": "cs-422"},
        headers=GW_HEADERS,
    )
    assert res.status_code == 422


def test_ivr_report_submission_flow():
    phone = f"+250790{random.randint(100000, 999999)}"
    call_sid = f"ca-ivr-full-{random.randint(0, 1_000_000)}"

    done = ivr_register_and_report(call_sid, phone)
    assert done.status_code == 200
    data = done.json()
    assert data["action"] == "hangup"
    assert data["session_state"] == "REPORT_DONE"
    assert "AG" in data["prompt"]

    code = latest_report_code(phone)
    assert code is not None and code.startswith("AG")

    db = SessionLocal()
    try:
        # IVRSession row with structured dtmf_log carrying resolved values (finding #9)
        sess = db.query(IVRSession).filter(IVRSession.call_sid == call_sid).first()
        assert sess is not None
        assert sess.status == "COMPLETED"
        log = json.loads(sess.dtmf_log)
        crop_entries = [e for e in log if e.get("step") == "REPORT_CROP"]
        sym_entries = [e for e in log if e.get("step") == "REPORT_SYMPTOM"]
        assert len(crop_entries) == 1 and crop_entries[0]["crop_id"] is not None
        assert len(sym_entries) == 1 and sym_entries[0]["symptom"]

        # CropReport created via the IVR channel
        report = db.query(CropReport).filter(CropReport.report_code == code).first()
        assert report is not None
        assert report.channel == ReportChannel.IVR

        # Auto-registered farmer, NOT phone-verified
        farmer = db.query(Farmer).filter(Farmer.id == report.farmer_id).first()
        assert farmer is not None
        assert farmer.is_phone_verified is False

        # AI triggers via the DTMF symptom -> AIResult + PENDING Notification
        ai = db.query(AIResult).filter(AIResult.report_id == report.id).first()
        assert ai is not None
        notif = (
            db.query(Notification)
            .filter(Notification.report_id == report.id)
            .first()
        )
        assert notif is not None
        assert notif.channel == NotificationChannel.SMS
        assert notif.status == NotificationStatus.PENDING
    finally:
        db.close()


def test_ivr_status_and_alerts():
    phone = f"+250790{random.randint(100000, 999999)}"

    # Submit a report first.
    report_sid = f"ca-status-{random.randint(0, 1_000_000)}"
    ivr_register_and_report(report_sid, phone)
    code = latest_report_code(phone)
    assert code is not None

    # STATUS: new call for the registered farmer -> MAIN_MENU -> STATUS.
    status_sid = f"ca-status2-{random.randint(0, 1_000_000)}"
    ivr(status_sid, phone)              # first call -> MAIN_MENU (registered)
    # Navigate to STATUS via digit 2.
    status = ivr(status_sid, phone, digits="2")
    assert status.status_code == 200
    status_data = status.json()
    assert status_data["action"] == "hangup"
    assert code in status_data["prompt"]

    # ALERTS: new call for a fresh farmer -> WELCOME -> register -> ALERTS -> opt-in.
    alerts_phone = f"+250790{random.randint(100000, 999999)}"
    alerts_sid = f"ca-alerts-{random.randint(0, 1_000_000)}"
    ivr(alerts_sid, alerts_phone)               # WELCOME
    ivr(alerts_sid, alerts_phone, digits="1")   # register -> MAIN_MENU
    alerts_menu = ivr(alerts_sid, alerts_phone, digits="3")  # -> ALERTS
    assert alerts_menu.json()["action"] == "gather"
    assert alerts_menu.json()["session_state"] == "ALERTS"
    opt_in = ivr(alerts_sid, alerts_phone, digits="1")  # opt-in -> ALERTS_DONE hangup
    opt = opt_in.json()
    assert opt["action"] == "hangup"
    assert opt["session_state"] == "ALERTS_DONE"
    assert "impuruza" in opt["prompt"].lower() or "alert" in opt["prompt"].lower()
