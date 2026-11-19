"""Provider-neutral IVR menu state machine (generic voice-webhook convention).

Accepts the neutral ``IVRInput`` (from the adapter) + the ``IVRSession`` row +
``db`` and returns a neutral ``IVROutput``. No ``temp_payload`` column exists on
``IVRSession``; IVR state is fully reconstructable from ``current_step`` + the
structured ``dtmf_log`` plus fresh DB/graph lookups.

Finding #8/#9: each ``dtmf_log`` entry stores the RESOLVED values at selection
time (``{"step","digit","crop_id","symptom"}``), so IVR state is self-contained
and immune to mid-call list mutation. On REPORT_CONFIRM redo, entries whose
``step`` is REPORT_CROP or REPORT_SYMPTOM are dropped and re-serialized.
"""
import json
import logging
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.orm import Session

from app.core.neo4j_client import neo4j_client
from app.models.session import IVRSession
from app.models.crop import Crop
from app.models.report import CropReport, ReportChannel
from app.schemas.ivr import IVROutput
from app.services.farmer_service import (
    identify_farmer_by_phone,
    self_register_farmer,
    FarmerAlreadyRegisteredError,
)
from app.services.report_service import create_crop_report
from app.services.alert_service import set_alert_preference

logger = logging.getLogger("agriguard.ivr.menu")


@dataclass
class IVRInput:
    """Neutral input the adapter produces from the validated IVRRequest."""

    call_sid: str
    phone_number: str
    digits: Optional[str]
    recording_url: Optional[str]
    language: Optional[str]


# --- dtmf_log helpers --------------------------------------------------------

def _log(session: IVRSession) -> list:
    try:
        data = json.loads(session.dtmf_log or "[]")
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _set_log(session: IVRSession, log: list) -> None:
    session.dtmf_log = json.dumps(log)


def _lang(session: IVRSession) -> str:
    return session.language or "rw"


def _active_crops(db: Session):
    return db.query(Crop).filter(Crop.is_active == True).order_by(Crop.id.asc()).all()


def _last_entry(log: list, step: str) -> Optional[dict]:
    for entry in reversed(log):
        if entry.get("step") == step:
            return entry
    return None


# --- prompt builders (TTS; provider-neutral) ---------------------------------

def _welcome(lang: str) -> str:
    return ("Welcome to AgriGuard. Choose language: 1 Kinyarwanda, 2 English."
            if lang == "en"
            else "Murakaza neza kuri AgriGuard. Hitamo ururimi: 1 Kinyarwanda, 2 English.")


def _main_menu(lang: str) -> str:
    return ("Choose: 1 Report a problem, 2 Report status, 3 Alerts, 0 Exit."
            if lang == "en"
            else "Hitamo: 1 Kumenyesha ikibazo, 2 Ibyavuye kuri raporo, 3 Impuruza, 0 Sohoka.")


def _report_crop_prompt(crops, lang: str) -> str:
    parts = []
    for i, crop in enumerate(crops, start=1):
        parts.append(f"{i} {crop.name_en if lang == 'en' else crop.name_rw}")
    head = "Choose crop:" if lang == "en" else "Hitamo igihingwa:"
    return head + " " + ", ".join(parts) + "."


def _report_symptom_prompt(symptoms, lang: str) -> str:
    # symptoms: list of display strings (already language-resolved).
    parts = [f"{i} {s}" for i, s in enumerate(symptoms, start=1)]
    other = "other" if lang == "en" else "Ikindi"
    parts.append(f"9 {other}")
    head = "Choose problem:" if lang == "en" else "Hitamo ikibazo:"
    return head + " " + ", ".join(parts) + "."


def _report_confirm(lang: str) -> str:
    return ("Confirm 1, redo 2, exit 0." if lang == "en"
            else "Emeza 1, ongera 2, sohoka 0.")


def _report_done(code, lang: str) -> str:
    return (f"Report {code} submitted. Advice will follow by SMS. Thank you!"
            if lang == "en"
            else f"Raporo {code} yatorewe. Azahabwa inama muri SMS. Murakoze.")


def _status_has_report(code, crop_name, status_text, pest, conf, lang: str) -> str:
    return (f"Your last report {code}, {crop_name}. Status {status_text}. "
            f"AI {pest} ({conf}%)." if lang == "en"
            else f"Raporo yawe yanyuma {code}, {crop_name}. Status {status_text}. "
            f"AI {pest} ({conf}%).")


def _status_no_report(lang: str) -> str:
    return "No reports yet." if lang == "en" else "Nta raporo uhari."


def _alerts(lang: str) -> str:
    return ("1 Enable alerts, 2 Disable alerts." if lang == "en"
            else "1 Emeza impuruza, 2 Hagarika impuruza.")


def _alerts_done(opted_in, lang: str) -> str:
    if lang == "en":
        return "Alerts on. Thank you." if opted_in else "Alerts off."
    return "Wemeye impuruza. Murakoze." if opted_in else "Impuruza zihagaritswe."


def _goodbye(lang: str) -> str:
    return "Thank you for using AgriGuard." if lang == "en" \
        else "Murakoze gukoresha AgriGuard."


def _contact_support(lang: str) -> str:
    return ("This number is registered to another account type; contact support."
            if lang == "en"
            else "Umubare ushizwe ku kindi kibanziriza; hamagara iyobora.")


def _service_unavailable(lang: str) -> str:
    return ("Service unavailable, please try again later." if lang == "en"
            else "Serivisi ntabwo iboneka, ongera ugerageze nyuma.")


# --- output builders ---------------------------------------------------------

def _gather(prompt, state, lang, digits=1) -> IVROutput:
    return IVROutput(action="gather", prompt=prompt, gather_digits=digits,
                     language=lang, session_state=state)


def _say(prompt, state, lang) -> IVROutput:
    return IVROutput(action="say", prompt=prompt, gather_digits=0,
                     language=lang, session_state=state)


def _hangup(prompt, state, lang) -> IVROutput:
    return IVROutput(action="hangup", prompt=prompt, gather_digits=0,
                     language=lang, session_state=state)


# --- symptom list resolution ------------------------------------------------

def _symptom_options(crop, lang: str):
    """Return (display_list, store_list). store_list[i] is the canonical string."""
    graph = neo4j_client.query_symptoms_for_crop(crop.name_en) or []
    raw = []
    for s in graph[:8]:
        raw.append(s.get("symptom_rw") if lang == "rw" and s.get("symptom_rw")
                   else s.get("symptom_en") or s.get("symptom_rw") or "symptom")
    if not raw:
        generic = ["leaves damaged", "yellowing", "spots", "stunting"]
        raw = list(generic)
    # display_list == store_list here (store uses the same language string);
    # AI reasoner matches both en and rw symptom strings.
    return raw, raw


# --- main entry --------------------------------------------------------------

def advance(session: IVRSession, ivr_input: IVRInput, db: Session,
            is_new_session: bool) -> IVROutput:
    """Advance the IVR menu one turn; mutates session.dtmf_log/current_step."""
    log = _log(session)
    lang = _lang(session)
    digit = (ivr_input.digits or "").strip()

    if is_new_session:
        if session.current_step == "MAIN_MENU":
            return _gather(_main_menu(lang), "MAIN_MENU", lang)
        return _gather(_welcome(lang), "WELCOME", lang)

    step = session.current_step
    try:
        if step == "WELCOME":
            # WELCOME is only reached by unknown phones -> auto-register.
            if digit == "1":
                session.language = "rw"
                lang = "rw"
            elif digit == "2":
                session.language = "en"
                lang = "en"
            else:
                return _gather(_welcome(lang), "WELCOME", lang)
            try:
                farmer = self_register_farmer(
                    db, session.phone_number, "IVR Farmer", "Unknown", lang
                )
            except FarmerAlreadyRegisteredError:
                return _hangup(_contact_support(lang), "GOODBYE", lang)
            return _gather(_main_menu(lang), "MAIN_MENU", lang)

        if step == "MAIN_MENU":
            if digit == "1":
                crops = _active_crops(db)
                return _gather(_report_crop_prompt(crops, lang), "REPORT_CROP", lang)
            elif digit == "2":
                return _render_status(session, db, lang)
            elif digit == "3":
                return _gather(_alerts(lang), "ALERTS", lang)
            elif digit == "0":
                return _hangup(_goodbye(lang), "GOODBYE", lang)
            return _gather(_main_menu(lang), "MAIN_MENU", lang)

        if step == "REPORT_CROP":
            crops = _active_crops(db)
            try:
                idx = int(digit)
            except (TypeError, ValueError):
                idx = -1
            if idx < 1 or idx > len(crops):
                return _gather(_report_crop_prompt(crops, lang), "REPORT_CROP", lang)
            crop_id = crops[idx - 1].id
            log.append({"step": "REPORT_CROP", "digit": digit,
                        "crop_id": crop_id, "symptom": None})
            _set_log(session, log)
            return _gather(_report_symptom_prompt(
                *_symptom_options(crops[idx - 1], lang)), "REPORT_SYMPTOM", lang)

        if step == "REPORT_SYMPTOM":
            crop_entry = _last_entry(log, "REPORT_CROP")
            if not crop_entry:
                return _gather(_main_menu(lang), "MAIN_MENU", lang)
            crop = db.query(Crop).filter(Crop.id == crop_entry["crop_id"]).first()
            if not crop:
                return _gather(_main_menu(lang), "MAIN_MENU", lang)
            _display, store = _symptom_options(crop, lang)
            if digit == "9":
                symptom = "other"
            else:
                try:
                    idx = int(digit)
                except (TypeError, ValueError):
                    idx = -1
                if idx < 1 or idx > len(store):
                    return _gather(_report_symptom_prompt(_display, store),
                                   "REPORT_SYMPTOM", lang)
                symptom = store[idx - 1]
            log.append({"step": "REPORT_SYMPTOM", "digit": digit,
                        "crop_id": None, "symptom": symptom})
            _set_log(session, log)
            return _gather(_report_confirm(lang), "REPORT_CONFIRM", lang)

        if step == "REPORT_CONFIRM":
            if digit == "1":
                crop_entry = _last_entry(log, "REPORT_CROP")
                sym_entry = _last_entry(log, "REPORT_SYMPTOM")
                if not crop_entry or not sym_entry:
                    return _gather(_main_menu(lang), "MAIN_MENU", lang)
                farmer = identify_farmer_by_phone(db, session.phone_number)
                if not farmer:
                    return _gather(_main_menu(lang), "MAIN_MENU", lang)
                symptom = sym_entry.get("symptom") or "other"
                report = create_crop_report(
                    db, farmer,
                    crop_id=crop_entry["crop_id"],
                    channel=ReportChannel.IVR,
                    symptoms=[symptom],
                    actor_user_id=farmer.user_id,
                )
                return _hangup(_report_done(report.report_code, lang),
                                "REPORT_DONE", lang)
            elif digit == "2":
                # Redo (finding #8): drop all REPORT_CROP/REPORT_SYMPTOM entries.
                log = [e for e in log if e.get("step") not in
                       ("REPORT_CROP", "REPORT_SYMPTOM")]
                _set_log(session, log)
                crops = _active_crops(db)
                return _gather(_report_crop_prompt(crops, lang), "REPORT_CROP", lang)
            elif digit == "0":
                return _hangup(_goodbye(lang), "GOODBYE", lang)
            return _gather(_report_confirm(lang), "REPORT_CONFIRM", lang)

        if step == "ALERTS":
            if digit == "1":
                farmer = identify_farmer_by_phone(db, session.phone_number)
                if farmer:
                    set_alert_preference(farmer, True)
                return _hangup(_alerts_done(True, lang), "ALERTS_DONE", lang)
            elif digit == "2":
                farmer = identify_farmer_by_phone(db, session.phone_number)
                if farmer:
                    set_alert_preference(farmer, False)
                return _hangup(_alerts_done(False, lang), "ALERTS_DONE", lang)
            elif digit == "0":
                return _hangup(_goodbye(lang), "GOODBYE", lang)
            return _gather(_alerts(lang), "ALERTS", lang)

        # Unknown step: fall back to MAIN_MENU gracefully.
        return _gather(_main_menu(lang), "MAIN_MENU", lang)

    except Exception as exc:  # safety net: never leak a raw 500 to the caller
        logger.exception("IVR menu.advance unexpected error: %s", exc)
        return _hangup(_service_unavailable(lang), "GOODBYE", lang)


def _render_status(session: IVRSession, db: Session, lang: str) -> IVROutput:
    farmer = identify_farmer_by_phone(db, session.phone_number)
    report = None
    if farmer:
        report = (
            db.query(CropReport)
            .filter(CropReport.farmer_id == farmer.id)
            .order_by(CropReport.created_at.desc())
            .first()
        )
    if not report:
        return _hangup(_status_no_report(lang), "STATUS", lang)
    crop_name = report.crop.name_en if report.crop else "Unknown"
    status_text = report.status.value if report.status else "PENDING"
    pest = "N/A"
    conf = 0
    if report.ai_result:
        pest = report.ai_result.predicted_pest_en or "N/A"
        conf = int((report.ai_result.confidence_score or 0) * 100)
    return _hangup(_status_has_report(report.report_code, crop_name, status_text,
                                      pest, conf, lang), "STATUS", lang)
