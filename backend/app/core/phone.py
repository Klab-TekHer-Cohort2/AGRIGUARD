"""Shared phone-number normalization helpers (non-router module).

Layering rule: services must not import from API routers. This module owns the
single canonical phone-normalization invariant used by registration, lookup,
and the USSD/IVR channels. It is re-exported from ``app.api.v1.auth`` for
backward compatibility with existing callers.
"""


def normalize_phone_number(phone: str) -> str:
    """Normalizes Rwandan phone numbers to +250 standard."""
    cleaned = phone.replace(" ", "").replace("-", "")
    if cleaned.startswith("07") and len(cleaned) == 10:
        return "+250" + cleaned[1:]
    if cleaned.startswith("250") and len(cleaned) == 12:
        return "+" + cleaned
    return cleaned
