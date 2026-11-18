"""Language Service.

Detects the language of a user message (English vs Kinyarwanda) and provides
localised text lookups. Prototype detection uses a keyword heuristic — not a
production language model. It is intentionally conservative: when unsure it
falls back to the default language (English) rather than guessing wrong.

Mirrors ``src/services/languageService.js``.
"""

from app.config import settings

# Kinyarwanda indicator words / stems (subset — prototype only).
# These are high-signal words unlikely to appear in English agricultural
# questions. Kept identical to the JavaScript marker list.
KINYARWANDA_MARKERS = [
    "ibigori", "ibishyimbo", "imyumbati", "ibirayi", "inyanya",  # crops
    "amababi", "ibimenyetso", "indwara", "udokoko", "inzoka",  # symptoms/pests
    "guhindura", "umuhondo", "umukara", "icyatsi",  # colours
    "kubura", "ifumbire", "amapfa", "amazi", "ubutaka",  # conditions
    "umuhinzi", "umurima", "gutera", "gusarura", "guhinga",  # farming actions
    "umugati", "imbuto", "ibiribwa", "nshuti", "murakoze",  # common words
    "cyangwa", "kandi", "ariko", "none", "umunsi", "n'",  # connectors
    "byanjye", "byawe", "ubu", "iki", "meze",
    "ndikwizera", "mwigisha", "mbwira", "mbwiro",
]


class LanguageService:
    """Detect language and localise strings/arrays."""

    def detect_language(self, text):
        """Return ``'en'`` or ``'rw'`` for a message.

        Requires at least one strong Kinyarwanda marker to switch language;
        otherwise falls back to the default (English).
        """
        if not text or not isinstance(text, str):
            return settings.default_language

        lower = text.lower()
        rw_hits = sum(1 for marker in KINYARWANDA_MARKERS if marker in lower)
        if rw_hits >= 1:
            return "rw"
        return "en"

    def localise(self, localised_obj, lang):
        """Get a localised string from a ``{"en", "rw"}`` dict.

        Falls back to English if the requested language is missing. Strings
        are returned as-is.
        """
        if not localised_obj:
            return ""
        if isinstance(localised_obj, str):
            return localised_obj
        return localised_obj.get(lang) or localised_obj.get("en") or ""

    def localise_list(self, localised_arr, lang):
        """Get a localised list from a ``{"en": [...], "rw": [...]}`` dict.

        If a plain list of strings is passed, it is returned unchanged.
        """
        if not localised_arr:
            return []
        if isinstance(localised_arr, list) and localised_arr and isinstance(localised_arr[0], str):
            return localised_arr
        return localised_arr.get(lang) or localised_arr.get("en") or []

    # Standard UI messages used across channels.
    messages = {
        "en": {
            "confidenceHigh": "High confidence",
            "confidenceMedium": "Medium confidence — more information required",
            "confidenceLow": "Unable to confidently identify the problem",
            "needsAgronomist": "Agronomist review recommended",
            "agronomistNotRequired": "Agronomist review not required",
            "unknownProblem": "We could not identify the problem confidently.",
            "reportSentForReview": "Your report has been sent for agronomist review.",
            "askMoreInfo": "Please upload another photo or describe the symptoms in more detail.",
            "possibleProblem": "Possible problem",
            "confidence": "Confidence",
            "severity": "Severity",
            "recommendation": "Recommendation",
            "advice": "Advice",
            "status": "Status",
            "risk": "Risk",
            "alert": "Alert",
            "radius": "Radius",
            "moreInfoTitle": "More information required",
            "escalationTitle": "Agronomist review required",
            "disclaimer": "Prototype AI assessment — not a substitute for professional agronomist advice.",
        },
        "rw": {
            "confidenceHigh": "Iwizera rya hejuru",
            "confidenceMedium": "Iwizera riringaniye — hakenewe amakuru arenga",
            "confidenceLow": "Ntibishobora kwitabwaho neza ikibazo",
            "needsAgronomist": "Gusaba kurebwa n'umuhinzi",
            "agronomistNotRequired": "Ntibisabwa kurebwa n'umuhinzi",
            "unknownProblem": "Ntitwabashije kumenya neza ikibazo.",
            "reportSentForReview": "Raporo yawe yoherejwe kugira ngo irebwe n'umuhinzi.",
            "askMoreInfo": "Tafiye ifoto irindi cyangwa sobanura ibimenyetso byinshi.",
            "possibleProblem": "Ikibazo gishoboka",
            "confidence": "Iwizera",
            "severity": "Ubukomeye",
            "recommendation": "Inama",
            "advice": "Inama",
            "status": "Imiterere",
            "risk": "Byaga",
            "alert": "Kurhura",
            "radius": "Kilometero",
            "moreInfoTitle": "Hakenewe amakuru arenga",
            "escalationTitle": "Gusaba kurebwa n'umuhinzi",
            "disclaimer": "Ibibazo bya prototype AI — si ibisimikangurwa by'umuhinzi w'ubuhinzi.",
        },
    }

    def get_message(self, key, lang):
        """Get a UI message in a given language, falling back to English then the key."""
        return self.messages.get(lang, {}).get(key) or self.messages["en"].get(key) or key


# Module-level singleton, matching the JS `languageService` object.
language_service = LanguageService()
