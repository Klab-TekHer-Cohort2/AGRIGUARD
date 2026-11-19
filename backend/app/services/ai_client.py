import json
import logging
import os
import time
from typing import List, Optional
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.neo4j_client import neo4j_client
from app.models.crop import Crop
from app.models.report import CropReport, ReportStatus, ReportSeverity, ReportHistory
from app.models.ai import AIResult
from app.models.alert import Notification, NotificationChannel, NotificationStatus
from app.schemas.ai import AIPredictionPayload

logger = logging.getLogger("agriguard.ai_client")


class AIServiceClient:
    """
    Modular integration adapter that connects AgriGuard with the AI Developer's Model API.
    Handles image uploads, symptom parsing, response validation, and resilient fallback mocks.
    """

    def __init__(self):
        self.endpoint_url = settings.AI_SERVICE_URL
        self.timeout = settings.AI_SERVICE_TIMEOUT_SECONDS
        self.mock_fallback = settings.AI_SERVICE_MOCK_FALLBACK

    def predict(
        self,
        crop_name: str,
        symptoms: Optional[List[str]] = None,
        image_path: Optional[str] = None,
    ) -> AIPredictionPayload:
        """
        Sends image and/or structured symptoms to the AI Developer's service.
        Falls back to Neo4j knowledge graph symptom reasoning if service is unreachable.
        """
        start_time = time.time()
        symptoms = symptoms or []

        # 1. Attempt call to live AI Service
        try:
            with httpx.Client(timeout=self.timeout) as client:
                if image_path and os.path.exists(image_path):
                    with open(image_path, "rb") as img_file:
                        files = {"image": (os.path.basename(image_path), img_file, "image/jpeg")}
                        data = {"crop": crop_name, "symptoms": json.dumps(symptoms)}
                        response = client.post(self.endpoint_url, files=files, data=data)
                else:
                    payload = {"crop": crop_name, "symptoms": symptoms}
                    response = client.post(self.endpoint_url, json=payload)

                if response.status_code == 200:
                    resp_json = response.json()
                    latency_ms = int((time.time() - start_time) * 1000)

                    # Validate response contract
                    return AIPredictionPayload(
                        model_name=resp_json.get("model_name", "live-ai-model"),
                        model_version=resp_json.get("model_version", "v1.0.0"),
                        predicted_pest_en=resp_json["predicted_pest_en"],
                        predicted_pest_rw=resp_json.get("predicted_pest_rw"),
                        confidence_score=float(resp_json["confidence_score"]),
                        detected_severity=resp_json.get("detected_severity", "MEDIUM"),
                        recommendations=resp_json.get("recommendations", []),
                        bounding_boxes=resp_json.get("bounding_boxes"),
                        raw_response=resp_json,
                        inference_latency_ms=latency_ms,
                        is_mock=False,
                    )
                else:
                    logger.warning(
                        f"AI service returned HTTP {response.status_code}: {response.text}"
                    )
        except Exception as exc:
            logger.warning(
                f"AI service at {self.endpoint_url} is unavailable ({exc}). "
                "Triggering fallback mock engine."
            )

        # 2. Resilient Fallback: Knowledge Graph Reasoning (Neo4j)
        if not self.mock_fallback:
            raise RuntimeError(f"AI Service unavailable at {self.endpoint_url}")

        latency_ms = int((time.time() - start_time) * 1000)
        graph_reasoning = neo4j_client.infer_pest_from_symptoms(crop_name, symptoms, language="en")

        # Mock bounding box for image demonstrations
        mock_bboxes = None
        if image_path:
            mock_bboxes = [
                {
                    "label": graph_reasoning["predicted_pest"],
                    "confidence": graph_reasoning["confidence"],
                    "box": {"x": 120, "y": 85, "width": 240, "height": 190}
                }
            ]

        return AIPredictionPayload(
            model_name="neo4j-knowledge-graph-reasoner",
            model_version="v1.0-mock",
            predicted_pest_en=graph_reasoning["predicted_pest"],
            predicted_pest_rw=graph_reasoning.get("predicted_pest_rw"),
            confidence_score=graph_reasoning["confidence"],
            detected_severity=graph_reasoning["severity"],
            recommendations=graph_reasoning["recommendations"],
            bounding_boxes=mock_bboxes,
            raw_response={"source": "neo4j_graph_reasoner", "data": graph_reasoning},
            inference_latency_ms=latency_ms,
            is_mock=True,
        )


# Singleton AI client
ai_client = AIServiceClient()


def process_report_ai_analysis(
    report_id: int,
    db: Session,
    image_path: Optional[str] = None,
) -> AIResult:
    """
    Executes AI diagnosis for a report, updates report status, attaches prediction,
    and enqueues farmer notification.
    """
    report = db.query(CropReport).filter(CropReport.id == report_id).first()
    if not report:
        raise ValueError(f"CropReport with ID {report_id} does not exist.")

    crop = db.query(Crop).filter(Crop.id == report.crop_id).first()
    crop_name = crop.name_en if crop else "Maize"

    # Parse symptoms
    symptoms = []
    if report.symptoms:
        try:
            symptoms = json.loads(report.symptoms) if isinstance(report.symptoms, str) else report.symptoms
        except Exception:
            symptoms = [str(report.symptoms)]

    # Resolve latest image path if not explicitly provided
    if not image_path and report.images:
        latest_img = report.images[-1]
        potential_path = settings.upload_path / latest_img.file_name
        if potential_path.exists():
            image_path = str(potential_path)

    # Execute AI prediction
    prediction = ai_client.predict(crop_name=crop_name, symptoms=symptoms, image_path=image_path)

    # Save or update AIResult
    ai_record = db.query(AIResult).filter(AIResult.report_id == report.id).first()
    if not ai_record:
        ai_record = AIResult(
            report_id=report.id,
            model_name=prediction.model_name,
            model_version=prediction.model_version,
            predicted_pest_en=prediction.predicted_pest_en,
            predicted_pest_rw=prediction.predicted_pest_rw,
            confidence_score=prediction.confidence_score,
            detected_severity=prediction.detected_severity,
            recommendations=json.dumps(prediction.recommendations),
            bounding_boxes=json.dumps(prediction.bounding_boxes) if prediction.bounding_boxes else None,
            raw_response=json.dumps(prediction.raw_response) if prediction.raw_response else None,
            inference_latency_ms=prediction.inference_latency_ms,
            is_mock=prediction.is_mock,
        )
        db.add(ai_record)
    else:
        ai_record.model_name = prediction.model_name
        ai_record.model_version = prediction.model_version
        ai_record.predicted_pest_en = prediction.predicted_pest_en
        ai_record.predicted_pest_rw = prediction.predicted_pest_rw
        ai_record.confidence_score = prediction.confidence_score
        ai_record.detected_severity = prediction.detected_severity
        ai_record.recommendations = json.dumps(prediction.recommendations)
        ai_record.bounding_boxes = json.dumps(prediction.bounding_boxes) if prediction.bounding_boxes else None
        ai_record.raw_response = json.dumps(prediction.raw_response) if prediction.raw_response else None
        ai_record.inference_latency_ms = prediction.inference_latency_ms
        ai_record.is_mock = prediction.is_mock

    # Update Report state
    previous_status = report.status.value
    report.status = ReportStatus.AI_ANALYZED
    try:
        report.severity = ReportSeverity(prediction.detected_severity)
    except Exception:
        pass

    # Log report audit history
    history = ReportHistory(
        report_id=report.id,
        changed_by_user_id=None,  # System AI actor
        previous_status=previous_status,
        new_status=ReportStatus.AI_ANALYZED.value,
        action_type="AI_ANALYSIS_COMPLETED",
        notes=(
            f"AI identified '{prediction.predicted_pest_en}' with {int(prediction.confidence_score * 100)}% "
            f"confidence ({'MOCK DATA' if prediction.is_mock else 'LIVE MODEL'})."
        ),
    )
    db.add(history)

    # Enqueue farmer notification
    if report.farmer and report.farmer.user:
        lang = report.farmer.preferred_language
        pest_label = prediction.predicted_pest_rw if (lang == "rw" and prediction.predicted_pest_rw) else prediction.predicted_pest_en

        if lang == "rw":
            msg = f"AgriGuard: Raporo yawe {report.report_code} yasuzumwe na AI. Ikibazo gikekwa: {pest_label}. Fungura ubutumwa urebemo inama zo gufata."
        else:
            msg = f"AgriGuard: Analysis complete for report {report.report_code}. Detected issue: {pest_label}. Open AgriGuard for preventive recommendations."

        notif = Notification(
            user_id=report.farmer.user.id,
            report_id=report.id,
            channel=NotificationChannel.SMS,
            recipient_phone=report.farmer.user.phone_number,
            title=f"AI Diagnosis: {pest_label}",
            message=msg,
            status=NotificationStatus.PENDING,
        )
        db.add(notif)

    db.commit()
    db.refresh(ai_record)
    try:
        from app.services.outbreak_service import check_and_raise_outbreak

        db.refresh(report)
        check_and_raise_outbreak(report, db)
    except Exception as exc:
        logger.warning(
            "Outbreak check failed after AI analysis (report_id=%s): %r",
            report_id,
            exc,
        )
    return ai_record
