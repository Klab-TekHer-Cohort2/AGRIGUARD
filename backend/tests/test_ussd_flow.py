"""End-to-end USSD channel tests (Africa's-Talking CON/END convention)."""
import json
import random
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.phone import normalize_phone_number
from app.models.user import User, Farmer
from app.models.session import USSDSession
from app.models.report import CropReport, ReportChannel
from app.models.ai import AIResult
from app.models.alert import Notification, NotificationChannel, NotificationStatus

client = TestClient(app)

GW_HEADERS = {"X-AgriGuard-Gateway-Secret": settings.USSD_IVR_GATEWAY_SECRET}
USSD_URL = "/api/v1/ussd/"


def ussd(session_id, phone, text=""):
    return client.post(
        USSD_URL,
        data={
            "sessionId": session_id,
            "serviceCode": "*777#",
            "phoneNumber": phone,
            "text": text,
        },
        headers=GW_HEADERS,
    )


def register_and_report(phone, session_id, symptom="ragged leaf feeding holes"):
    """Drive LANG_SELECT -> registration -> MAIN_MENU -> report submit.

    Returns the final (REPORT_DONE) response.
    """
    ussd(session_id, phone, "")                              # first dial -> LANG_SELECT
    ussd(session_id, phone, "1")                             # Kinyarwanda
    ussd(session_id, phone, "1*Test Farmer")                # name
    ussd(session_id, phone, "1*Test Farmer*Musanze")        # district
    ussd(session_id, phone, "1*Test Farmer*Musanze*1")      # reg language -> MAIN_MENU
    ussd(session_id, phone, "1*Test Farmer*Musanze*1*1")    # MAIN_MENU -> report
    ussd(session_id, phone, "1*Test Farmer*Musanze*1*1*1")  # crop 1 (Maize)
    ussd(session_id, phone, f"1*Test Farmer*Musanze*1*1*1*{symptom}")  # symptoms
    return ussd(session_id, phone, f"1*Test Farmer*Musanze*1*1*1*{symptom}*1")  # confirm


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


def test_ussd_rejects_missing_secret():
    phone = f"+250789{random.randint(100000, 999999)}"
    res = client.post(
        USSD_URL,
        data={"sessionId": "sid-no-secret", "serviceCode": "*777#",
              "phoneNumber": phone, "text": ""},
    )
    assert res.status_code == 401


def test_ussd_rejects_wrong_secret():
    phone = f"+250789{random.randint(100000, 999999)}"
    res = client.post(
        USSD_URL,
        data={"sessionId": "sid-wrong-secret", "serviceCode": "*777#",
              "phoneNumber": phone, "text": ""},
        headers={"X-AgriGuard-Gateway-Secret": "definitely-wrong"},
    )
    assert res.status_code == 401


def test_ussd_register_and_report_full_flow():
    phone = f"+250789{random.randint(100000, 999999)}"
    session_id = f"ussd-full-{random.randint(0, 1_000_000)}"

    done = register_and_report(phone, session_id)
    assert done.status_code == 200
    body = done.text
    assert body.startswith("END ")
    assert "AG" in body

    code = latest_report_code(phone)
    assert code is not None and code.startswith("AG")

    db = SessionLocal()
    try:
        # USSDSession row with expected final state + trail
        sess = db.query(USSDSession).filter(USSDSession.session_id == session_id).first()
        assert sess is not None
        assert sess.current_menu == "REPORT_DONE"
        assert sess.is_active is False
        payload = json.loads(sess.temp_payload)
        assert "trail" in payload and len(payload["trail"]) > 0
        assert payload.get("last_report_code") == code

        # CropReport created via the USSD channel
        report = db.query(CropReport).filter(CropReport.report_code == code).first()
        assert report is not None
        assert report.channel == ReportChannel.USSD

        # Farmer auto-registered, NOT phone-verified
        farmer = db.query(Farmer).filter(Farmer.id == report.farmer_id).first()
        assert farmer is not None
        assert farmer.is_phone_verified is False

        # AIResult created via process_report_ai_analysis
        ai = db.query(AIResult).filter(AIResult.report_id == report.id).first()
        assert ai is not None

        # PENDING SMS Notification enqueued
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


def test_ussd_check_status():
    phone = f"+250789{random.randint(100000, 999999)}"
    session_id = f"ussd-status-{random.randint(0, 1_000_000)}"
    register_and_report(phone, session_id)
    code = latest_report_code(phone)
    assert code is not None

    # New dial for the now-registered farmer -> MAIN_MENU -> STATUS
    status_sid = session_id + "-chk"
    first = ussd(status_sid, phone, "")
    assert first.text.startswith("CON ")
    assert "Hitamo" in first.text or "Choose" in first.text  # MAIN_MENU

    status = ussd(status_sid, phone, "2")  # STATUS
    assert status.status_code == 200
    # A report exists -> STATUS returns CON and echoes the report code.
    assert status.text.startswith("CON ")
    assert code in status.text


def test_ussd_alerts_opt_in():
    phone = f"+250789{random.randint(100000, 999999)}"
    session_id = f"ussd-alerts-{random.randint(0, 1_000_000)}"

    # Register (ends at MAIN_MENU).
    ussd(session_id, phone, "")
    ussd(session_id, phone, "1")
    ussd(session_id, phone, "1*Alert Farmer")
    ussd(session_id, phone, "1*Alert Farmer*Musanze")
    main = ussd(session_id, phone, "1*Alert Farmer*Musanze*1")  # -> MAIN_MENU
    assert main.text.startswith("CON ")

    alerts = ussd(session_id, phone, "1*Alert Farmer*Musanze*1*3")  # -> ALERTS
    assert alerts.text.startswith("CON ")
    assert "mpuruza" in alerts.text.lower() or "alert" in alerts.text.lower()

    opt_in = ussd(session_id, phone, "1*Alert Farmer*Musanze*1*3*1")  # opt-in
    assert opt_in.text.startswith("END ")
    assert "impuruza" in opt_in.text.lower() or "alert" in opt_in.text.lower()

    db = SessionLocal()
    try:
        sess = db.query(USSDSession).filter(USSDSession.session_id == session_id).first()
        assert sess is not None
        assert sess.current_menu == "ALERTS_DONE"
        assert sess.is_active is False
        payload = json.loads(sess.temp_payload)
        assert payload.get("alerts_opted_in") is True
        assert any(e.get("input") == "1" for e in payload.get("trail", []))
    finally:
        db.close()


def test_ussd_bounds_enforced_422():
    """Oversized/missing required Form() fields return 422 (finding #2)."""
    phone = f"+250789{random.randint(100000, 999999)}"
    # Missing required phoneNumber -> 422 (validation surface is the Form params).
    res = client.post(
        USSD_URL,
        data={"sessionId": "sid-422", "serviceCode": "*777#", "text": ""},
        headers=GW_HEADERS,
    )
    assert res.status_code == 422
