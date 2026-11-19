"""Generic-voice IVR adapter (JSON <-> neutral).

Isolates the provider wire format so a TwiML provider can be swapped in by
replacing only ``render`` (to emit XML instead of JSON). The router's
``IVRRequest`` body dependency performs FastAPI validation (422 — finding #2)
before this code runs; ``parse_request`` maps the validated request to the
neutral ``IVRInput`` and ``render`` maps the neutral ``IVROutput`` to JSON.
"""
from app.schemas.ivr import IVRRequest, IVROutput
from app.ivr.menu import IVRInput


def parse_request(payload: IVRRequest) -> IVRInput:
    """Map the validated IVRRequest to the neutral IVRInput."""
    return IVRInput(
        call_sid=payload.call_sid,
        phone_number=payload.phone_number,
        digits=payload.digits,
        recording_url=payload.recording_url,
        language=payload.language,
    )


def render(output: IVROutput) -> dict:
    """Render the neutral output to a provider-neutral JSON dict (maps 1:1 to TwiML)."""
    return {
        "action": output.action,
        "prompt": output.prompt,
        "gather_digits": output.gather_digits,
        "language": output.language,
        "session_state": output.session_state,
    }
