"""Multilingual support — English & Kinyarwanda (sections 15/16).

Language detection here is a conservative keyword heuristic, NOT a production
language model. When unsure it falls back to English (the default) rather than
guessing wrong. The frontend/USSD/IVR layer (Person 3) can also pass the language
explicitly to override detection — recommended for very short USSD inputs.

Honest limitation (section 27): Kinyarwanda AI performance must be validated;
this prototype does not claim perfect Kinyarwanda understanding.
"""

# High-signal Kinyarwanda indicator words (subset — prototype only).
KINYARWANDA_MARKERS = [
    "ibigori", "ibishyimbo", "imyumbati", "ibirayi", "inyanya",  # crops
    "amababi", "ibimenyetso", "indwara", "udokoko", "inzoka",   # symptoms/pests
    "guhindura", "umuhondo", "umukara", "icyatsi",              # colours/states
    "kubura", "ifumbire", "amapfa", "amazi", "ubutaka",         # conditions
    "umuhinzi", "umurima", "gutera", "gusarura", "guhinga",      # farming actions
    "umugati", "imbuto", "ibiribwa", "nshuti", "murakoze",       # common words
    "cyangwa", "kandi", "ariko", "none", "umunsi", "n'",         # connectors
    "byanjye", "byawe", "ubu", "iki", "meze",
    "mbwira", "inama", "ninama",
]

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ["en", "rw"]


def detect_language(text: str) -> str:
    """Detect 'en' or 'rw'. Requires >=1 strong Kinyarwanda marker to switch."""
    if not text or not isinstance(text, str):
        return DEFAULT_LANGUAGE
    lower = text.lower()
    if any(marker in lower for marker in KINYARWANDA_MARKERS):
        return "rw"
    return DEFAULT_LANGUAGE


def resolve_language(explicit: str = None, text: str = None) -> str:
    """Resolve the effective language: explicit override wins, else detect."""
    if explicit and explicit in SUPPORTED_LANGUAGES:
        return explicit
    return detect_language(text) if text else DEFAULT_LANGUAGE


# Standard UI/advice messages used across channels.
MESSAGES = {
    "en": {
        "possible_problem": "Possible problem",
        "confidence": "Confidence",
        "severity": "Severity",
        "advice": "Advice",
        "status": "Status",
        "needs_agronomist": "Agronomist review recommended",
        "agronomist_not_required": "Agronomist review not required",
        "unknown_problem": "We could not confidently identify the problem.",
        "report_sent_for_review": "Your report has been sent for agronomist review.",
        "disclaimer": "Prototype AI assessment — not a substitute for professional agronomist advice.",
    },
    "rw": {
        "possible_problem": "Ikibazo gishoboka",
        "confidence": "Iwizera",
        "severity": "Ubukomeye",
        "advice": "Inama",
        "status": "Imiterere",
        "needs_agronomist": "Gusaba kurebwa n'umuhinzi",
        "agronomist_not_required": "Ntibisabwa kurebwa n'umuhinzi",
        "unknown_problem": "Ntitwabashije kumenya neza ikibazo.",
        "report_sent_for_review": "Raporo yawe yoherejwe kugira ngo irebwe n'umuhinzi.",
        "disclaimer": "Ibibazo bya prototype AI — si ibisimikangurwa by'umuhinzi w'ubuhinzi.",
    },
}


def get_message(key: str, lang: str = "en") -> str:
    """Get a localised UI message, falling back to English then the key."""
    return MESSAGES.get(lang, {}).get(key) or MESSAGES["en"].get(key) or key


def localise(localised_obj, lang: str = "en") -> str:
    """Get a localised string from a ``{"en": ..., "rw": ...}`` dict (fallback en)."""
    if not localised_obj:
        return ""
    if isinstance(localised_obj, str):
        return localised_obj
    return localised_obj.get(lang) or localised_obj.get("en") or ""


def localise_list(localised_arr, lang: str = "en") -> list:
    """Get a localised list from ``{"en": [...], "rw": [...]}``. Plain lists pass through."""
    if not localised_arr:
        return []
    if isinstance(localised_arr, list):
        return localised_arr
    return localised_arr.get(lang) or localised_arr.get("en") or []
