"""Provider-neutral USSD menu state machine (Africa's-Talking CON/END convention).

Accepts the neutral ``USSDInput`` (from the adapter) + the ``USSDSession`` row
+ ``db`` and returns a neutral ``USSDOutput``. Server-side session state (the
``USSDSession`` row keyed by ``sessionId``) is the source of truth, so the menu
is robust to either gateway convention (full trail echoed, or only the latest
segment). The last ``*``-delimited segment of ``text`` is the input for the
current step (computed by the adapter into ``USSDInput.current_input``).

Error handling: no ``HTTPException`` is raised inside this module (that would
break the CON/END text contract). ``self_register_farmer`` is idempotent and
raises the typed ``FarmerAlreadyRegisteredError``, caught here -> friendly END.
"""
import json
import logging
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.session import USSDSession
from app.models.crop import Crop
from app.models.report import CropReport, ReportChannel, ReportSeverity, ReportStatus
from app.schemas.ussd import USSDOutput
from app.services.farmer_service import (
    identify_farmer_by_phone,
    self_register_farmer,
    FarmerAlreadyRegisteredError,
)
from app.services.report_service import create_crop_report
from app.services.alert_service import set_alert_preference

logger = logging.getLogger("agriguard.ussd.menu")


@dataclass
class USSDInput:
    """Neutral input the adapter produces from validated form values."""

    session_id: str
    service_code: str
    phone_number: str
    text: str            # full accumulated trail
    current_input: str   # last *-delimited segment ("" on first dial)


# --- payload helpers ---------------------------------------------------------

def _payload(session: USSDSession) -> dict:
    try:
        return json.loads(session.temp_payload or "{}")
    except Exception:
        return {}


def _set_payload(session: USSDSession, payload: dict) -> None:
    session.temp_payload = json.dumps(payload)


def _active_crops(db: Session):
    return db.query(Crop).filter(Crop.is_active == True).order_by(Crop.id.asc()).all()


# --- prompt builders (language-aware; no CON/END prefix — the adapter adds it) --

def _lang(session: USSDSession) -> str:
    return session.language or "rw"


def _lang_select(lang: str) -> str:
    if lang == "en":
        return "Welcome to AgriGuard. Choose language:\n1. Kinyarwanda\n2. English"
    return "Murakaza neza kuri AgriGuard. Hiturilimi:\n1. Kinyarwanda\n2. English"


def _reg_name(lang: str) -> str:
    return "Enter your full name:" if lang == "en" else "Andika izina ryawe:"


def _reg_district(lang: str) -> str:
    return ("Enter your district (e.g. Musanze):" if lang == "en"
            else "Andika akarere (urugero: Musanze):")


def _reg_lang(lang: str) -> str:
    return "Choose language:\n1. Kinyarwanda\n2. English" if lang == "en" \
        else "Hiturilimi:\n1. Kinyarwanda\n2. English"


def _main_menu_prompt(name: str, lang: str) -> str:
    if lang == "en":
        return (f"Welcome, {name}. Choose:\n1. Report a problem\n"
                f"2. Report status\n3. Alerts\n0. Exit")
    return (f"Murakaza neza, {name}. Hitamo:\n1. Kumenyesha ikibazo\n"
            f"2. Ibyavuye kuri raporo\n3. Impuruza\n0. Sohoka")


def _report_crop_prompt(crops, lang: str) -> str:
    lines = []
    for i, crop in enumerate(crops, start=1):
        if lang == "en":
            lines.append(f"{i}. {crop.name_en} ({crop.name_rw})")
        else:
            lines.append(f"{i}. {crop.name_rw} ({crop.name_en})")
    head = "Choose crop:" if lang == "en" else "Hitamo igihingwa:"
    return head + "\n" + "\n".join(lines)


def _report_symptoms(lang: str) -> str:
    return ("Describe the problem (e.g. holes in leaves):" if lang == "en"
            else "Sobanura ikibazo (urugero: imyobo mu mababi):")


def _report_confirm_prompt(crop_name, desc, lang: str) -> str:
    if lang == "en":
        return (f"You selected: Crop: {crop_name}. Problem: {desc}.\n"
                f"1. Confirm\n2. Redo\n0. Exit")
    return (f"Wahisemo: Igihingwa: {crop_name}. Ikibazo: {desc}.\n"
            f"1. Emeza\n2. Ongera\n0. Sohoka")


def _report_done_prompt(code, lang: str) -> str:
    return (f"Report {code} submitted. Advice will follow by SMS. Thank you!"
            if lang == "en"
            else f"Raporo {code} yatorewe. Azahabwa inama muri SMS. Murakoze!")


def _status_has_report_prompt(code, crop_name, status_text, pest, conf, lang: str) -> str:
    if lang == "en":
        return (f"Your last report: {code} ({crop_name}). Status: {status_text}. "
                f"AI: {pest} ({conf}%).\n1. Menu\n0. Exit")
    return (f"Raporo yawe yanyuma: {code} ({crop_name}). Status: {status_text}. "
            f"AI: {pest} ({conf}%).\n1. Menu nyamara\n0. Sohoka")


def _status_no_report(lang: str) -> str:
    return "No reports yet." if lang == "en" else "Nta raporo uhari."


def _alerts_prompt(lang: str) -> str:
    return ("Alerts:\n1. Enable alerts\n2. Disable alerts\n0. Exit" if lang == "en"
            else "Impuruza:\n1. Emeza impuruza\n2. Hagarika impuruza\n0. Sohoka")


def _alerts_done_prompt(opted_in, lang: str) -> str:
    if lang == "en":
        return "Alerts on. Thank you." if opted_in else "Alerts off."
    return "Wemeye impuruza. Murakoze." if opted_in else "Impuruza zihagaritswe."


def _exit_prompt(lang: str) -> str:
    return ("Thank you for using AgriGuard." if lang == "en"
            else "Murakoze gukoresha AgriGuard.")


def _already_registered_note(lang: str) -> str:
    return "Already registered." if lang == "en" else "Wiyandikishije." if False else "Wiyandikishije."


def _contact_support(lang: str) -> str:
    return ("This number is registered to another account type; contact support."
            if lang == "en"
            else "Umubare ushizwe ku kindi kibanziriza; hamagara iyobora.")


def _service_unavailable(lang: str) -> str:
    return ("Service unavailable, please try again later." if lang == "en"
            else "Serivisi ntabwo iboneka, ongera ugerageze nyuma.")


# --- output builders ---------------------------------------------------------

def _con(text, new_menu, lang) -> USSDOutput:
    return USSDOutput(continue_session=True, text=text, new_menu=new_menu, language=lang)


def _end(text, new_menu, lang) -> USSDOutput:
    return USSDOutput(continue_session=False, text=text, new_menu=new_menu, language=lang)


def _render_main_menu(farmer, lang) -> USSDOutput:
    name = (farmer.user.full_name if farmer and farmer.user else "Farmer")
    return _con(_main_menu_prompt(name, lang), "MAIN_MENU", lang)


# --- main entry --------------------------------------------------------------

def advance(session: USSDSession, ussd_input: USSDInput, db: Session,
            is_new_session: bool) -> USSDOutput:
    """Advance the menu one turn; mutates session.temp_payload/language as needed."""
    payload = _payload(session)
    trail = payload.get("trail", [])
    lang = _lang(session)
    inp = ussd_input.current_input

    if is_new_session:
        # First dial: render the initial screen, consume no input.
        if session.current_menu == "MAIN_MENU":
            farmer = identify_farmer_by_phone(db, session.phone_number)
            return _render_main_menu(farmer, lang)
        return _con(_lang_select(lang), session.current_menu, lang)

    # Record this turn's input on the audit trail.
    trail.append({"menu": session.current_menu, "input": inp})
    payload["trail"] = trail

    menu = session.current_menu
    try:
        if menu == "LANG_SELECT":
            if inp == "1":
                session.language = "rw"
                payload["preferred_language"] = "rw"
                _set_payload(session, payload)
                return _con(_reg_name("rw"), "REG_NAME", "rw")
            elif inp == "2":
                session.language = "en"
                payload["preferred_language"] = "en"
                _set_payload(session, payload)
                return _con(_reg_name("en"), "REG_NAME", "en")
            _set_payload(session, payload)
            return _con(_lang_select(lang), "LANG_SELECT", lang)

        if menu == "REG_NAME":
            name = inp.strip()
            if not name:
                _set_payload(session, payload)
                return _con(_reg_name(lang), "REG_NAME", lang)
            payload["full_name"] = name
            _set_payload(session, payload)
            return _con(_reg_district(lang), "REG_DISTRICT", lang)

        if menu == "REG_DISTRICT":
            district = inp.strip()
            if not district:
                _set_payload(session, payload)
                return _con(_reg_district(lang), "REG_DISTRICT", lang)
            payload["district"] = district
            _set_payload(session, payload)
            return _con(_reg_lang(lang), "REG_LANG", lang)

        if menu == "REG_LANG":
            if inp == "1":
                payload["preferred_language"] = "rw"
                session.language = "rw"
                lang = "rw"
            elif inp == "2":
                payload["preferred_language"] = "en"
                session.language = "en"
                lang = "en"
            else:
                _set_payload(session, payload)
                return _con(_reg_lang(lang), "REG_LANG", lang)
            try:
                farmer = self_register_farmer(
                    db,
                    session.phone_number,
                    payload.get("full_name", "Farmer"),
                    payload.get("district", "Unknown"),
                    payload.get("preferred_language", "rw"),
                )
            except FarmerAlreadyRegisteredError:
                _set_payload(session, payload)
                return _end(_contact_support(lang), "EXIT", lang)
            payload["farmer_id"] = farmer.id
            _set_payload(session, payload)
            return _render_main_menu(farmer, lang)

        if menu == "MAIN_MENU":
            if inp == "1":
                _set_payload(session, payload)
                crops = _active_crops(db)
                return _con(_report_crop_prompt(crops, lang), "REPORT_CROP", lang)
            elif inp == "2":
                _set_payload(session, payload)
                return _render_status(session, db, lang)
            elif inp == "3":
                _set_payload(session, payload)
                return _con(_alerts_prompt(lang), "ALERTS", lang)
            elif inp == "0":
                _set_payload(session, payload)
                return _end(_exit_prompt(lang), "EXIT", lang)
            farmer = identify_farmer_by_phone(db, session.phone_number)
            _set_payload(session, payload)
            return _render_main_menu(farmer, lang)

        if menu == "REPORT_CROP":
            crops = _active_crops(db)
            try:
                idx = int(inp)
            except (TypeError, ValueError):
                idx = -1
            if idx < 1 or idx > len(crops):
                _set_payload(session, payload)
                return _con(_report_crop_prompt(crops, lang), "REPORT_CROP", lang)
            payload["crop_id"] = crops[idx - 1].id
            _set_payload(session, payload)
            return _con(_report_symptoms(lang), "REPORT_SYMPTOMS", lang)

        if menu == "REPORT_SYMPTOMS":
            desc = inp.strip()
            if not desc:
                _set_payload(session, payload)
                return _con(_report_symptoms(lang), "REPORT_SYMPTOMS", lang)
            payload["description"] = desc
            _set_payload(session, payload)
            crop = db.query(Crop).filter(Crop.id == payload.get("crop_id")).first()
            crop_name = crop.name_en if crop else "Unknown"
            return _con(_report_confirm_prompt(crop_name, desc, lang),
                        "REPORT_CONFIRM", lang)

        if menu == "REPORT_CONFIRM":
            if inp == "1":
                farmer = identify_farmer_by_phone(db, session.phone_number)
                crop_id = payload.get("crop_id")
                desc = payload.get("description", "") or ""
                if not farmer or not crop_id:
                    _set_payload(session, payload)
                    return _con(_service_unavailable(lang), "MAIN_MENU", lang)
                report = create_crop_report(
                    db,
                    farmer,
                    crop_id=crop_id,
                    channel=ReportChannel.USSD,
                    description=desc,
                    symptoms=[desc] if desc else [],
                    severity=ReportSeverity.LOW,
                    actor_user_id=farmer.user_id,
                )
                payload["last_report_code"] = report.report_code
                _set_payload(session, payload)
                return _end(_report_done_prompt(report.report_code, lang),
                            "REPORT_DONE", lang)
            elif inp == "2":
                payload.pop("crop_id", None)
                payload.pop("description", None)
                _set_payload(session, payload)
                crops = _active_crops(db)
                return _con(_report_crop_prompt(crops, lang), "REPORT_CROP", lang)
            elif inp == "0":
                _set_payload(session, payload)
                return _end(_exit_prompt(lang), "EXIT", lang)
            _set_payload(session, payload)
            return _con(_report_confirm_prompt(
                db.query(Crop).filter(Crop.id == payload.get("crop_id")).first().name_en
                if payload.get("crop_id") else "Unknown",
                payload.get("description", ""), lang), "REPORT_CONFIRM", lang)

        if menu == "STATUS":
            if inp == "1":
                _set_payload(session, payload)
                farmer = identify_farmer_by_phone(db, session.phone_number)
                return _render_main_menu(farmer, lang)
            elif inp == "0":
                _set_payload(session, payload)
                return _end(_exit_prompt(lang), "EXIT", lang)
            _set_payload(session, payload)
            return _render_status(session, db, lang)

        if menu == "ALERTS":
            if inp == "1":
                farmer = identify_farmer_by_phone(db, session.phone_number)
                if farmer:
                    set_alert_preference(farmer, True)
                payload["alerts_opted_in"] = True
                _set_payload(session, payload)
                return _end(_alerts_done_prompt(True, lang), "ALERTS_DONE", lang)
            elif inp == "2":
                farmer = identify_farmer_by_phone(db, session.phone_number)
                if farmer:
                    set_alert_preference(farmer, False)
                payload["alerts_opted_in"] = False
                _set_payload(session, payload)
                return _end(_alerts_done_prompt(False, lang), "ALERTS_DONE", lang)
            elif inp == "0":
                _set_payload(session, payload)
                return _end(_exit_prompt(lang), "EXIT", lang)
            _set_payload(session, payload)
            return _con(_alerts_prompt(lang), "ALERTS", lang)

        # Unknown menu: fall back to MAIN_MENU gracefully.
        _set_payload(session, payload)
        farmer = identify_farmer_by_phone(db, session.phone_number)
        return _render_main_menu(farmer, lang)

    except Exception as exc:  # safety net: never leak a 500 to the farmer
        logger.exception("USSD menu.advance unexpected error: %s", exc)
        _set_payload(session, payload)
        return _end(_service_unavailable(lang), "EXIT", lang)


def _render_status(session: USSDSession, db: Session, lang: str) -> USSDOutput:
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
        return _end(_status_no_report(lang), "STATUS", lang)
    crop_name = report.crop.name_en if report.crop else "Unknown"
    status_text = report.status.value if report.status else "PENDING"
    pest = "N/A"
    conf = 0
    if report.ai_result:
        pest = report.ai_result.predicted_pest_en or "N/A"
        conf = int((report.ai_result.confidence_score or 0) * 100)
    return _con(
        _status_has_report_prompt(report.report_code, crop_name, status_text, pest, conf, lang),
        "STATUS",
        lang,
    )
