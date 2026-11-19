"""AgriGuard AI API Routes.

All AI/data endpoints are mounted under ``/api/ai``.

    POST /api/ai/analyse-report       → crop report analysis (smartphone + USSD)
    POST /api/ai/ask                  → Ask AgriGuard assistant
    POST /api/ai/community-risk       → community risk analysis from reports
    POST /api/ai/outbreak-detection    → full outbreak detection + alertable farmers
    POST /api/ai/ussd-response        → USSD-formatted short response
    GET  /api/ai/demo                 → run the full demo scenario

Request/response contracts are documented in ``docs/AI_DOCUMENTATION.md``.

Validation intentionally returns HTTP 400 with the JSON shape
``{"success": false, "error": "VALIDATION_ERROR", "message": ...}`` to match
the previous Express behaviour exactly (rather than FastAPI's default 422).

Mirrors ``src/routes/aiRoutes.js``.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.services.crop_analysis_service import crop_analysis_service
from app.services.ai_assistant_service import ai_assistant_service
from app.services.outbreak_detection_service import outbreak_detection_service
from app.services.ussd_response_formatter import ussd_response_formatter
from app.data.prototype_dataset import prototype_dataset as dataset

router = APIRouter(prefix="/api/ai", tags=["ai"])


# ── Request models (lenient: extra fields ignored, required fields optional
#    so we can validate manually and return the AgriGuard 400 shape) ──────────
class AnalyseReportRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    crop: Optional[str] = None
    description: Optional[str] = None
    image: Optional[Any] = None
    location: Optional[Dict[str, Any]] = None
    language: Optional[str] = None
    farmerRequestedHelp: Optional[bool] = False


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question: Optional[str] = None
    language: Optional[str] = None
    cropId: Optional[str] = None


class CommunityRiskRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    reports: Optional[List[Dict[str, Any]]] = None
    farmers: Optional[List[Dict[str, Any]]] = None
    timeWindowDays: Optional[int] = None
    alertRadiusKm: Optional[float] = None


class UssdRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    farmerId: Optional[str] = None
    crop: Optional[str] = None
    problemDescription: Optional[str] = None
    location: Optional[str] = None
    language: Optional[str] = None


def _validation_error(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": "VALIDATION_ERROR", "message": message},
    )


def _round2(value):
    import math
    return math.floor(value * 100 + 0.5) / 100


# ── POST /api/ai/analyse-report ────────────────────────────────────────────
@router.post("/analyse-report")
async def analyse_report(body: AnalyseReportRequest):
    crop = (body.crop or "").strip()
    if not crop:
        return _validation_error('Field "crop" is required.')

    result = await crop_analysis_service.analyse_crop_report(
        {
            "crop": body.crop,
            "description": body.description,
            "image": body.image,
            "location": body.location,
            "language": body.language,
            "farmerRequestedHelp": body.farmerRequestedHelp,
        }
    )
    return {"success": True, "data": result}


# ── POST /api/ai/ask ────────────────────────────────────────────────────────
@router.post("/ask")
async def ask(body: AskRequest):
    question = (body.question or "").strip()
    if not question:
        return _validation_error('Field "question" is required.')

    result = await ai_assistant_service.answer_agricultural_question(
        body.question,
        {"language": body.language, "cropId": body.cropId},
    )
    return {"success": True, "data": result}


# ── POST /api/ai/community-risk ──────────────────────────────────────────────
@router.post("/community-risk")
async def community_risk(body: CommunityRiskRequest):
    if not isinstance(body.reports, list):
        return _validation_error('Field "reports" must be an array.')

    result = outbreak_detection_service.detect_community_risk(
        body.reports,
        {"timeWindowDays": body.timeWindowDays, "alertRadiusKm": body.alertRadiusKm},
    )
    return {"success": True, "data": result}


# ── POST /api/ai/outbreak-detection ──────────────────────────────────────────
# Full outbreak detection including alertable farmers within the radius.
@router.post("/outbreak-detection")
async def outbreak_detection(body: CommunityRiskRequest):
    if not isinstance(body.reports, list):
        return _validation_error('Field "reports" must be an array.')

    risk = outbreak_detection_service.detect_community_risk(
        body.reports,
        {"timeWindowDays": body.timeWindowDays, "alertRadiusKm": body.alertRadiusKm},
    )

    alertable_farmers = []
    if risk["alertRecommended"] and isinstance(body.farmers, list):
        alertable_farmers = outbreak_detection_service.find_alertable_farmers(
            risk, body.farmers, body.alertRadiusKm
        )

    data = {**risk, "alertableFarmers": alertable_farmers, "alertableCount": len(alertable_farmers)}
    return {"success": True, "data": data}


# ── POST /api/ai/ussd-response ────────────────────────────────────────────────
# USSD channel: same AI layer, USSD-formatted short output.
@router.post("/ussd-response")
async def ussd_response(body: UssdRequest):
    crop = (body.crop or "").strip()
    if not crop:
        return _validation_error('Field "crop" is required.')

    # Run the same analysis pipeline used by the smartphone flow.
    result = await crop_analysis_service.analyse_crop_report(
        {
            "crop": body.crop,
            "description": body.problemDescription,
            "location": {"community": body.location} if body.location else None,
            "language": body.language,
        }
    )

    # Format for USSD (short plain text).
    ussd_text = ussd_response_formatter.format_crop_analysis(result)

    return {
        "success": True,
        "data": {
            "farmerId": body.farmerId or None,
            "ussdResponse": ussd_text,
            "analysis": result,
        },
    }


# ── GET /api/ai/demo ────────────────────────────────────────────────────────
# Runs the full hackathon demo scenario end-to-end so the presentation can hit
# one endpoint and see the complete flow.
@router.get("/demo")
async def demo():
    demo_scenarios = dataset["demoScenarios"]

    # 1. Smartphone crop report analysis (Fall Armyworm)
    smartphone = await crop_analysis_service.analyse_crop_report(demo_scenarios["smartphoneReport"])

    # 2. Unknown / low-confidence report
    unknown = await crop_analysis_service.analyse_crop_report(demo_scenarios["unknownReport"])

    # 3. Farmer requests help → escalation
    help_request = await crop_analysis_service.analyse_crop_report(demo_scenarios["farmerRequestsHelp"])

    # 4. Community outbreak detection
    community_risk = outbreak_detection_service.detect_community_risk(dataset["reports"])
    alertable_farmers = outbreak_detection_service.find_alertable_farmers(
        community_risk, dataset["farmers"]
    )

    # 5. Ask AgriGuard (English + Kinyarwanda)
    ask_en = await ai_assistant_service.answer_agricultural_question(demo_scenarios["englishQuestion"])
    ask_rw = await ai_assistant_service.answer_agricultural_question(demo_scenarios["kinyarwandaQuestion"])

    # 6. USSD short response
    ussd_analysis = await crop_analysis_service.analyse_crop_report(
        {
            "crop": demo_scenarios["ussdReport"]["crop"],
            "description": demo_scenarios["ussdReport"]["problemDescription"],
            "location": {"community": demo_scenarios["ussdReport"]["location"]},
        }
    )
    ussd_text = ussd_response_formatter.format_crop_analysis(ussd_analysis)

    return {
        "success": True,
        "data": {
            "step1_smartphoneAnalysis": smartphone,
            "step2_unknownReport": unknown,
            "step3_farmerRequestsHelp": help_request,
            "step4_communityRisk": community_risk,
            "step4b_alertableFarmers": [
                {
                    "id": f["id"],
                    "name": f["name"],
                    "community": f["community"],
                    "distanceKm": _round2(f["distanceKm"]),
                }
                for f in alertable_farmers
            ],
            "step5_askAgriGuardEnglish": ask_en,
            "step5b_askAgriGuardKinyarwanda": ask_rw,
            "step6_ussdResponse": ussd_text,
        },
    }
