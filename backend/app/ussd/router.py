"""USSD webhook router (Africa's-Talking convention).

POST /ussd is gateway-secret-gated (never JWT). FastAPI validates the explicit
``Form(...)`` params (422 on missing required field / oversized field — finding
#2) before the handler runs. The adapter parses the validated form values to
the neutral ``USSDInput``; the menu advances server-side state; the router
persists the ``USSDSession`` row and renders the CON/END text/plain body.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_gateway_secret
from app.core.phone import normalize_phone_number
from app.models.base import utc_now
from app.models.session import USSDSession
from app.services.farmer_service import identify_farmer_by_phone
from app.ussd import adapter, menu

router = APIRouter(prefix="/ussd", tags=["USSD Channel"])

# Form(...) params carrying the §6 bounds (FastAPI validates -> 422).
SessionIdField = Annotated[str, Form(min_length=1, max_length=128)]    # required
ServiceCodeField = Annotated[str, Form(max_length=32)]                 # optional
PhoneNumberField = Annotated[str, Form(min_length=6, max_length=32)]   # required
TextField = Annotated[str, Form(max_length=640)]                        # optional


@router.post("/")
def ussd_webhook(
    sessionId: SessionIdField,
    phoneNumber: PhoneNumberField,
    serviceCode: ServiceCodeField = "*777#",
    text: TextField = "",
    db: Session = Depends(get_db),
    _: None = Depends(verify_gateway_secret),
):
    ussd_input = adapter.parse_request(sessionId, serviceCode, phoneNumber, text)

    # Load/create the session row keyed by sessionId (server-side source of truth).
    session = (
        db.query(USSDSession)
        .filter(USSDSession.session_id == ussd_input.session_id)
        .first()
    )
    is_new_session = session is None
    if is_new_session:
        clean_phone = normalize_phone_number(ussd_input.phone_number)
        farmer = identify_farmer_by_phone(db, ussd_input.phone_number)
        if farmer:
            session = USSDSession(
                session_id=ussd_input.session_id,
                phone_number=clean_phone,
                service_code=ussd_input.service_code,
                current_menu="MAIN_MENU",
                language=farmer.preferred_language or "rw",
                temp_payload="{}",
                is_active=True,
            )
        else:
            session = USSDSession(
                session_id=ussd_input.session_id,
                phone_number=clean_phone,
                service_code=ussd_input.service_code,
                current_menu="LANG_SELECT",
                language="rw",
                temp_payload="{}",
                is_active=True,
            )
        db.add(session)
        db.flush()  # assign id; keep the row pending in the outer transaction

    output = menu.advance(session, ussd_input, db, is_new_session=is_new_session)

    # Persist the final session state for the turn.
    session.current_menu = output.new_menu or session.current_menu
    session.language = output.language
    session.last_activity = utc_now()
    if not output.continue_session:
        session.is_active = False
    db.commit()

    body = adapter.render(output)
    return Response(content=body, media_type="text/plain")
