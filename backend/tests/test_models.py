import json
import uuid
import pytest
from app.core.database import Base, engine, SessionLocal
from app.core.init_db import init_database
from app.models import (
    User,
    UserRole,
    Farmer,
    Agronomist,
    Organization,
    FarmerLocation,
    Crop,
    CropReport,
    ReportChannel,
    ReportSeverity,
    ReportStatus,
    ReportImage,
    ReportHistory,
    AIResult,
    Alert,
    AlertSeverity,
    AlertStatus,
    Notification,
    NotificationChannel,
    NotificationStatus,
    USSDSession,
    IVRSession,
    AuditLog,
)


@pytest.fixture(scope="module")
def db_session():
    """Initializes the database schema and yields a test session."""
    init_database()
    session = SessionLocal()
    yield session
    session.close()


def test_all_16_tables_registered():
    """Verifies that all 16 specified tables are registered in SQLAlchemy metadata."""
    expected_tables = {
        "users",
        "farmers",
        "farmer_locations",
        "crops",
        "crop_reports",
        "report_images",
        "ai_results",
        "agronomists",
        "organizations",
        "organization_members",
        "alerts",
        "notifications",
        "report_history",
        "ussd_sessions",
        "ivr_sessions",
        "audit_logs",
    }
    registered_tables = set(Base.metadata.tables.keys())
    missing = expected_tables - registered_tables
    assert not missing, f"Missing tables in metadata: {missing}"


def test_seed_data_created(db_session):
    """Verifies default crops, admin, agronomist, and farmer were seeded."""
    crops_count = db_session.query(Crop).count()
    assert crops_count >= 8

    admin = db_session.query(User).filter(User.role == UserRole.SYSTEM_ADMIN).first()
    assert admin is not None
    assert admin.phone_number == "+250788000001"

    agronomist = db_session.query(Agronomist).first()
    assert agronomist is not None
    assert "Musanze" in agronomist.assigned_districts

    farmer = db_session.query(Farmer).first()
    assert farmer is not None
    assert len(farmer.locations) > 0
    assert farmer.locations[0].district == "Musanze"


def test_crop_report_full_lifecycle(db_session):
    """
    Tests creating a complete CropReport with:
    - Farmer and Crop relationships
    - ReportImage upload record
    - AIResult prediction
    - ReportHistory audit trail
    """
    farmer = db_session.query(Farmer).first()
    crop = db_session.query(Crop).filter(Crop.name_en == "Maize").first()
    assert farmer is not None
    assert crop is not None

    test_code = f"AG-TEST-{uuid.uuid4().hex[:6]}"
    # 1. Create CropReport
    report = CropReport(
        report_code=test_code,
        farmer_id=farmer.id,
        crop_id=crop.id,
        channel=ReportChannel.APP,
        description="Leaves showing ragged holes and caterpillar inside whorl",
        symptoms=json.dumps(["ragged leaf feeding holes", "sawdust-like frass"]),
        district=farmer.locations[0].district,
        sector=farmer.locations[0].sector,
        cell=farmer.locations[0].cell,
        village=farmer.locations[0].village,
        severity=ReportSeverity.HIGH,
        status=ReportStatus.PENDING,
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    assert report.id is not None
    assert report.report_code == test_code

    # 2. Attach ReportImage
    image = ReportImage(
        report_id=report.id,
        image_url="/uploads/maize_pest_test.jpg",
        file_name="maize_pest_test.jpg",
        file_size_bytes=245120,
        mime_type="image/jpeg",
        upload_channel="APP"
    )
    db_session.add(image)

    # 3. Attach AIResult
    ai_result = AIResult(
        report_id=report.id,
        model_name="yolov8-maize-pest",
        model_version="v1.0",
        predicted_pest_en="Fall Armyworm",
        predicted_pest_rw="Nkongwa",
        confidence_score=0.92,
        detected_severity="HIGH",
        recommendations=json.dumps(["Apply Neem extract in the morning"]),
        bounding_boxes=json.dumps([{"x": 100, "y": 150, "width": 80, "height": 60}]),
        inference_latency_ms=140,
        is_mock=True,
    )
    db_session.add(ai_result)

    # 4. Attach ReportHistory
    history = ReportHistory(
        report_id=report.id,
        new_status=ReportStatus.AI_ANALYZED.value,
        action_type="AI_ANALYSIS_COMPLETED",
        notes="AI identified Fall Armyworm with 92% confidence."
    )
    db_session.add(history)
    db_session.commit()

    # Query back and verify relationships
    queried = db_session.query(CropReport).filter(CropReport.report_code == test_code).first()
    assert queried is not None
    assert len(queried.images) == 1
    assert queried.images[0].file_name == "maize_pest_test.jpg"
    assert queried.ai_result is not None
    assert queried.ai_result.predicted_pest_en == "Fall Armyworm"
    assert len(queried.history) == 1


def test_ussd_and_ivr_sessions(db_session):
    """Verifies USSD and IVR session persistence and lookups."""
    test_ussd_id = f"USSD-TEST-{uuid.uuid4().hex[:6]}"
    test_call_sid = f"CA-TEST-{uuid.uuid4().hex[:6]}"

    # Test USSD session
    ussd_sess = USSDSession(
        session_id=test_ussd_id,
        phone_number="+250788111222",
        service_code="*777#",
        current_menu="SELECT_SYMPTOMS",
        language="rw",
        temp_payload=json.dumps({"crop": "Ibigori", "symptoms": ["imyobo mu mababi"]})
    )
    db_session.add(ussd_sess)

    # Test IVR session
    ivr_sess = IVRSession(
        call_sid=test_call_sid,
        phone_number="+250788111222",
        language="rw",
        current_step="REPORT_AUDIO",
        duration_seconds=45,
        dtmf_log=json.dumps(["1", "2"]),
        status="COMPLETED"
    )
    db_session.add(ivr_sess)
    db_session.commit()

    queried_ussd = db_session.query(USSDSession).filter(USSDSession.session_id == test_ussd_id).first()
    assert queried_ussd is not None
    assert queried_ussd.current_menu == "SELECT_SYMPTOMS"

    queried_ivr = db_session.query(IVRSession).filter(IVRSession.call_sid == test_call_sid).first()
    assert queried_ivr is not None
    assert queried_ivr.duration_seconds == 45


def test_alert_and_notification(db_session):
    """Verifies Alert creation and linked farmer Notification dispatch."""
    crop = db_session.query(Crop).filter(Crop.name_en == "Maize").first()
    farmer = db_session.query(Farmer).first()

    alert = Alert(
        title_en="Fall Armyworm Alert in Musanze",
        title_rw="Impuruza ya Nkongwa mu Karere ka Musanze",
        message_en="Multiple cases of Fall Armyworm detected in Muhoza sector. Inspect your maize crops.",
        message_rw="Hari ibimenyetso bya Nkongwa byabonetse mu Murenge wa Muhoza. Reba ibigori byawe.",
        crop_id=crop.id,
        target_district="Musanze",
        target_sector="Muhoza",
        severity=AlertSeverity.CRITICAL,
        status=AlertStatus.ACTIVE,
        outbreak_radius_km=15.0,
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)

    notification = Notification(
        user_id=farmer.user_id,
        alert_id=alert.id,
        channel=NotificationChannel.SMS,
        recipient_phone=farmer.user.phone_number,
        title="AgriGuard Alert",
        message=alert.message_rw,
        status=NotificationStatus.PENDING,
    )
    db_session.add(notification)
    db_session.commit()

    assert notification.id is not None
    assert notification.alert.target_district == "Musanze"


def test_audit_log(db_session):
    """Verifies audit trail creation."""
    admin = db_session.query(User).filter(User.role == UserRole.SYSTEM_ADMIN).first()
    log = AuditLog(
        user_id=admin.id,
        action="DATABASE_INIT",
        resource_type="Database",
        resource_id="schema",
        details=json.dumps({"status": "seeded", "table_count": 16})
    )
    db_session.add(log)
    db_session.commit()

    assert log.id is not None
    assert log.action == "DATABASE_INIT"
