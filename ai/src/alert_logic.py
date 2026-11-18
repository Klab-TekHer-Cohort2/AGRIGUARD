"""Alert logic — agronomist escalation (section 11) and 5 km radius alerts (sections 21/22).

Two separate "alert" concerns live here:

1. Agronomist escalation: when should a human expert review the report instead of
   relying on the AI? Responsible-AI logic — the system never claims to replace
   agronomists.

2. 5 km radius alert: which registered farmers should receive a personalised
   prototype outbreak alert? Uses the Haversine great-circle distance.

Both are pure functions, fully unit-testable.
"""

import math
from dataclasses import dataclass
from typing import List, Optional

from ai.src.models import AlertableFarmer, EscalationResult
from ai.src.severity import ESCALATE_SEVERITIES


# ── Agronomist escalation (section 11) ────────────────────────────────────────
@dataclass
class EscalationConfig:
    """Configurable escalation thresholds."""
    confidence_threshold: float = 0.50      # below this -> escalate
    escalate_severities: tuple = ("High", "Critical")
    escalate_categories: tuple = ("Unknown",)


DEFAULT_ESCALATION_CONFIG = EscalationConfig()


def needs_agronomist(
    confidence: float,
    severity: Optional[str],
    category: Optional[str],
    farmer_requested_help: bool = False,
    config: EscalationConfig = None,
) -> EscalationResult:
    """Decide whether a report must be escalated to an agronomist.

    Escalate when ANY of:
        - the farmer explicitly requested human help
        - confidence < threshold (low confidence -> don't pretend to know)
        - severity is High or Critical (serious problem -> expert review)
        - category is Unknown (we couldn't identify the problem)

    Returns an ``EscalationResult`` with a list of triggered reasons and a
    comma-joined ``reason`` string for compact logging/USSD.
    """
    config = config or DEFAULT_ESCALATION_CONFIG
    reasons = []

    if farmer_requested_help:
        reasons.append("farmer_requested_help")

    if confidence is None or confidence < config.confidence_threshold:
        reasons.append("low_confidence")

    if severity in config.escalate_severities:
        reasons.append(f"severity_{(severity or '').lower()}")

    if category in config.escalate_categories:
        reasons.append("unknown_category")

    return EscalationResult(
        needs_agronomist=bool(reasons),
        reasons=reasons,
        reason=",".join(reasons) if reasons else "none",
    )


# ── Geographic distance + 5 km alert (sections 21/22) ──────────────────────────
def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in kilometres (Haversine).

    Assumes a spherical Earth (radius 6371 km). Accurate enough for community
    radius alerts at this scale.
    """
    radius = 6371.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def farmers_within_radius(
    outbreak_lat: float,
    outbreak_lon: float,
    farmers: List[dict],
    radius_km: float = 5.0,
) -> List[AlertableFarmer]:
    """Find registered farmers within ``radius_km`` of an outbreak centre.

    Eligibility (section 22): a farmer is eligible for a personalised alert when
        registered == True  AND  location available == True  AND  distance <= radius.

    Farmers without coordinates are skipped (we never expose/estimate private
    locations). Returns ``AlertableFarmer`` objects sorted nearest-first.
    """
    eligible = []
    for f in farmers or []:
        lat = f.get("lat") if "lat" in f else f.get("latitude")
        lon = f.get("lng") if "lng" in f else f.get("longitude")
        if lat is None or lon is None:
            continue
        dist = calculate_distance_km(outbreak_lat, outbreak_lon, lat, lon)
        if dist <= radius_km:
            eligible.append(
                AlertableFarmer(
                    farmer_id=f.get("id") or f.get("farmer_id") or "unknown",
                    name=f.get("name"),
                    community=f.get("community"),
                    distance_km=round(dist, 2),
                )
            )
    eligible.sort(key=lambda a: a.distance_km)
    return eligible


def is_alert_eligible(farmer: dict, outbreak_lat: float, outbreak_lon: float, radius_km: float = 5.0) -> bool:
    """Convenience: is a single farmer within the alert radius?"""
    lat = farmer.get("lat") if "lat" in farmer else farmer.get("latitude")
    lon = farmer.get("lng") if "lng" in farmer else farmer.get("longitude")
    if lat is None or lon is None:
        return False
    return calculate_distance_km(outbreak_lat, outbreak_lon, lat, lon) <= radius_km
