"""Africa's-Talking USSD adapter (form <-> neutral).

Isolates the provider wire format so a different provider can be swapped in by
replacing only this file (the menu and the session model are untouched). The
router's ``Form(...)`` params perform FastAPI validation (422 on bounds) before
this code runs; ``parse_request`` maps the validated values to the neutral
``USSDInput`` and ``render`` maps the neutral ``USSDOutput`` to a ``CON/END``
``text/plain`` body.
"""
from app.schemas.ussd import USSDOutput
from app.ussd.menu import USSDInput


def parse_request(session_id: str, service_code: str, phone_number: str,
                   text: str) -> USSDInput:
    """Map validated form values to the neutral USSDInput.

    ``current_input`` is the last ``*``-delimited segment of the accumulated
    trail ("" on first dial). Server-side session state is the source of truth,
    so the menu is robust to either gateway convention.
    """
    raw_text = text or ""
    segments = raw_text.split("*")
    current_input = segments[-1].strip() if segments else ""
    return USSDInput(
        session_id=session_id,
        service_code=service_code or "*777#",
        phone_number=phone_number,
        text=raw_text,
        current_input=current_input,
    )


def render(output: USSDOutput) -> str:
    """Render the neutral output to an Africa's-Talking CON/END text body."""
    prefix = "CON " if output.continue_session else "END "
    return prefix + (output.text or "")
