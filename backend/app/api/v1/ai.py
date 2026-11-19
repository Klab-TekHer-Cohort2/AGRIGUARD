import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.report import CropReport
from app.models.ai import AIResult
from app.models.crop import Crop
from app.schemas.ai import AIResultResponse, AIPredictionPayload, AIDatasetExportItem
from app.services.ai_client import process_report_ai_analysis

router = APIRouter(prefix="/ai", tags=["AI Pest Detection & Datasets"])


@router.post("/analyze/{report_id}", response_model=AIResultResponse)
def trigger_ai_analysis(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Triggers AI pest/disease diagnosis for a report.
    Transmits uploaded photos or structured symptom data to the AI service
    and records the diagnosis, confidence score, and recommendations.
    """
    report = db.query(CropReport).filter(CropReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found.",
        )

    # Permission check: owner or agronomist/admin
    if current_user.role == UserRole.FARMER and current_user.farmer_profile:
        if report.farmer_id != current_user.farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to trigger analysis on this report.",
            )

    ai_record = process_report_ai_analysis(report_id=report.id, db=db)

    return AIResultResponse(
        id=ai_record.id,
        report_id=report.id,
        report_code=report.report_code,
        model_name=ai_record.model_name,
        model_version=ai_record.model_version,
        predicted_pest_en=ai_record.predicted_pest_en,
        predicted_pest_rw=ai_record.predicted_pest_rw,
        confidence_score=ai_record.confidence_score,
        detected_severity=ai_record.detected_severity,
        recommendations=ai_record.recommendations,
        bounding_boxes=ai_record.bounding_boxes,
        inference_latency_ms=ai_record.inference_latency_ms,
        is_mock=ai_record.is_mock,
        is_verified_correct=ai_record.is_verified_correct,
        created_at=ai_record.created_at,
    )


@router.get("/results/{report_id}", response_model=AIResultResponse)
def get_ai_result(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves stored AI diagnosis, confidence metrics, and preventive recommendations.
    """
    ai_record = db.query(AIResult).filter(AIResult.report_id == report_id).first()
    if not ai_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No AI analysis found for report ID {report_id}.",
        )

    report = db.query(CropReport).filter(CropReport.id == report_id).first()

    return AIResultResponse(
        id=ai_record.id,
        report_id=report.id,
        report_code=report.report_code if report else None,
        model_name=ai_record.model_name,
        model_version=ai_record.model_version,
        predicted_pest_en=ai_record.predicted_pest_en,
        predicted_pest_rw=ai_record.predicted_pest_rw,
        confidence_score=ai_record.confidence_score,
        detected_severity=ai_record.detected_severity,
        recommendations=ai_record.recommendations,
        bounding_boxes=ai_record.bounding_boxes,
        inference_latency_ms=ai_record.inference_latency_ms,
        is_mock=ai_record.is_mock,
        is_verified_correct=ai_record.is_verified_correct,
        created_at=ai_record.created_at,
    )


@router.post("/mock-predict", response_model=AIPredictionPayload)
async def mock_ai_service_endpoint(request: Request):
    """
    Reference mock implementation simulating Person 2's AI Model Service.
    Accepts crop and symptoms or image and returns standardized pest predictions.
    """
    content_type = request.headers.get("content-type", "")
    crop = "Maize"

    if "application/json" in content_type:
        body = await request.json()
        crop = body.get("crop", "Maize")
    elif "multipart/form-data" in content_type:
        form = await request.form()
        crop = form.get("crop", "Maize")

    return AIPredictionPayload(
        model_name="yolov8-rwandan-pests-v1",
        model_version="1.0.0",
        predicted_pest_en="Fall Armyworm",
        predicted_pest_rw="Nkongwa",
        confidence_score=0.94,
        detected_severity="HIGH",
        recommendations=[
            "Spray neem extract early in the morning.",
            "Handpick caterpillars in young whorls.",
            "Contact local extension worker if spread exceeds 20%."
        ],
        bounding_boxes=[
            {"box": [110, 80, 220, 180], "label": "Fall Armyworm", "confidence": 0.94}
        ],
        raw_response={"status": "success", "device": "cuda:0"},
        inference_latency_ms=85,
        is_mock=True,
    )


@router.get("/dataset/export", response_model=List[AIDatasetExportItem])
def export_training_dataset(
    crop_id: Optional[int] = Query(None, description="Filter by crop"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Active Learning Dataset Export endpoint for Person 2 (AI Developer).
    Returns verified ground-truth cases validated by human agronomists.
    """
    if current_user.role not in [UserRole.AGRONOMIST, UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Restricted to Agronomists and AI Developers.",
        )

    # Query reports with AI results
    query = db.query(CropReport).join(AIResult).filter(CropReport.status.in_(["VERIFIED", "AI_ANALYZED"]))
    if crop_id:
        query = query.filter(CropReport.crop_id == crop_id)

    reports = query.all()

    export_items = []
    for r in reports:
        image_url = r.images[0].image_url if r.images else None
        symptoms = []
        if r.symptoms:
            try:
                symptoms = json.loads(r.symptoms) if isinstance(r.symptoms, str) else r.symptoms
            except Exception:
                symptoms = [str(r.symptoms)]

        export_items.append(
            AIDatasetExportItem(
                report_code=r.report_code,
                crop_name=r.crop.name_en if r.crop else "Unknown",
                crop_scientific_name=r.crop.scientific_name if r.crop else None,
                image_url=image_url,
                symptoms_reported=symptoms,
                district=r.district,
                sector=r.sector,
                ai_predicted_pest=r.ai_result.predicted_pest_en if r.ai_result else "N/A",
                ai_confidence=r.ai_result.confidence_score if r.ai_result else 0.0,
                ground_truth_pest=r.ai_result.predicted_pest_en if r.ai_result else "Unverified",
                is_ai_correct=r.ai_result.is_verified_correct if (r.ai_result and r.ai_result.is_verified_correct is not None) else True,
                agronomist_notes=r.agronomist_notes,
                verified_at=r.verified_at,
            )
        )
    return export_items
