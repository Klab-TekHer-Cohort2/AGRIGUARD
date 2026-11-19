"""IVR webhook router (generic voice-webhook convention).

POST /ivr is gateway-secret-gated (never JWT). FastAPI validates the
``IVRRequest`` body (422 on malformed/oversized/missing-field body — finding
#2) before the handler runs. The adapter parses the validated request to the
neutral ``IVRInput``; the menu advances server-side state (appending resolved
entries to ``dtmf_log``); the router persists the ``IVRSession`` row and
returns the neutral JSON rendered by the adapter.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_gateway_secret
from app.core.phone import normalize_phone_number
from app.models.session import IVRSession
from app.services.farmer_service import identify_farmer_by_phone
from app.schemas.ivr import IVRRequest
from app.ivr import adapter, menu

router = APIRouter(prefix="/ivr", tags=["IVR Channel"])


@router.post("/")
def ivr_webhook(
    payload: IVRRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_gateway_secret),
):
    ivr_input = adapter.parse_request(payload)

    # Load/create the session row keyed by call_sid (server-side source of truth).
    session = (
        db.query(IVRSession)
        .filter(IVRSession.call_sid == ivr_input.call_sid)
        .first()
    )
    is_new_session = session is None
    if is_new_session:
        clean_phone = normalize_phone_number(ivr_input.phone_number)
        farmer = identify_farmer_by_phone(db, ivr_input.phone_number)
        if farmer:
            session = IVRSession(
                call_sid=ivr_input.call_sid,
                phone_number=clean_phone,
                language=farmer.preferred_language or "rw",
                current_step="MAIN_MENU",
                dtmf_log="[]",
                status="IN_PROGRESS",
            )
        else:
            session = IVRSession(
                call_sid=ivr_input.call_sid,
                phone_number=clean_phone,
                language=ivr_input.language or "rw",
                current_step="WELCOME",
                dtmf_log="[]",
                status="IN_PROGRESS",
            )
        db.add(session)
        db.flush()  # assign id; keep the row pending in the outer transaction

    output = menu.advance(session, ivr_input, db, is_new_session=is_new_session)

    # Persist the final session state for the turn.
    session.current_step = output.session_state
    session.language = output.language
    if ivr_input.recording_url:
        session.recording_url = ivr_input.recording_url
    session.duration_seconds = (session.duration_seconds or 0) + 1
    if output.action == "hangup":
        session.status = "COMPLETED"
    else:
        session.status = "IN_PROGRESS"
    db.commit()

    body = adapter.render(output)
    return JSONResponse(content=body)
