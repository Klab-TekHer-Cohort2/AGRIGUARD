"""Community outbreak detection (sections 19, 20).

PROTOTYPE detector — NOT a scientifically validated disease forecasting model.
All results carry ``is_prototype = True`` and a disclaimer.

Concept:
    Multiple reports + same/similar problem + nearby locations + recent time
    -> transparent risk analysis -> potential outbreak.

The risk score is a transparent 0–100 heuristic (section 20), explicitly NOT a
probability. Factors:
    - number of reports          (0–40)
    - average severity           (0–25)
    - average AI confidence       (0–15)
    - geographic concentration   (0–10, bonus if clustered within 2× radius)
    - recency (last 3 days)      (0–10)

``detect_outbreak(reports)`` groups reports by (problem, crop) within a time
window, scores each group, and returns the most concerning one.
``farmers_within_radius`` (in alert_logic.py) then finds alertable farmers.
"""

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ai.src.alert_logic import calculate_distance_km
from ai.src.models import OutbreakRiskResult

_DAY_SECONDS = 24 * 60 * 60
SEVERITY_WEIGHT = {"Low": 1, "Moderate": 2, "High": 3, "Critical": 4}

# Configurable defaults (also overridable per call).
MIN_REPORTS_FOR_RISK = 3
HIGH_RISK_REPORT_COUNT = 7
CRITICAL_RISK_REPORT_COUNT = 12
DEFAULT_TIME_WINDOW_DAYS = 7
DEFAULT_ALERT_RADIUS_KM = 5.0


def _parse_ts(ts) -> datetime:
    """Parse an ISO 8601 timestamp (with optional trailing 'Z') to a UTC datetime."""
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    s = ts
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _centroid(reports: List[Dict]) -> Optional[Dict[str, float]]:
    pts = [r for r in reports if r.get("latitude") is not None and r.get("longitude") is not None]
    if not pts:
        return None
    lat = sum(r["latitude"] for r in pts) / len(pts)
    lon = sum(r["longitude"] for r in pts) / len(pts)
    return {"lat": lat, "lng": lon}


def _is_geo_concentrated(reports: List[Dict], radius_km: float) -> bool:
    if len(reports) < 2:
        return False
    c = _centroid(reports)
    if not c:
        return False
    return all(
        r.get("latitude") is not None
        and r.get("longitude") is not None
        and calculate_distance_km(c["lat"], c["lng"], r["latitude"], r["longitude"]) <= radius_km * 2
        for r in reports
    )


def _summarise_area(reports: List[Dict]) -> Optional[str]:
    communities = []
    for r in reports:
        c = r.get("community")
        if c and c not in communities:
            communities.append(c)
    if len(communities) == 1:
        return communities[0]
    if len(communities) > 1:
        return ", ".join(communities)
    return None


def _score_group(reports: List[Dict], geo_concentrated: bool, now_epoch: float) -> float:
    """Transparent prototype risk score (0–100). NOT a probability."""
    count = len(reports)
    count_score = min((count / CRITICAL_RISK_REPORT_COUNT) * 40, 40)
    avg_sev = sum(SEVERITY_WEIGHT.get(r.get("severity"), 1) for r in reports) / count
    severity_score = (avg_sev / 4) * 25
    avg_conf = sum((r.get("confidence") or 0) for r in reports) / count
    confidence_score = avg_conf * 15
    geo_score = 10 if geo_concentrated else 0
    recent_count = sum(
        1 for r in reports
        if (now_epoch - _parse_ts(r["timestamp"]).timestamp()) / _DAY_SECONDS <= 3
    )
    recency_score = (recent_count / count) * 10
    return count_score + severity_score + confidence_score + geo_score + recency_score


def _risk_level(score: float, report_count: int) -> str:
    if score >= 70 or report_count >= CRITICAL_RISK_REPORT_COUNT:
        return "CRITICAL"
    if score >= 50 or report_count >= HIGH_RISK_REPORT_COUNT:
        return "HIGH"
    if score >= 30 or report_count >= MIN_REPORTS_FOR_RISK:
        return "MEDIUM"
    return "LOW"


def _empty_result(reason: str, time_window_days: int, radius_km: float) -> OutbreakRiskResult:
    return OutbreakRiskResult(
        risk_level="LOW", risk_score=0.0, problem=None, crop=None, crop_id=None,
        problem_id=None, category=None, report_count=0, affected_area=None,
        affected_area_center=None, geo_concentrated=False, alert_recommended=False,
        reason=reason, radius_km=radius_km, time_window_days=time_window_days,
    )


def detect_outbreak(
    reports: List[Dict],
    time_window_days: int = DEFAULT_TIME_WINDOW_DAYS,
    alert_radius_km: float = DEFAULT_ALERT_RADIUS_KM,
) -> OutbreakRiskResult:
    """Analyse a set of farmer reports for community outbreak risk.

    Args:
        reports: list of report dicts (see ``knowledge.reports_as_dicts``).
        time_window_days: only consider reports within this many days.
        alert_radius_km: radius for the geo-concentration bonus + later alerts.

    Returns:
        OutbreakRiskResult (call ``.to_dict()`` for JSON). PROTOTYPE scoring.
    """
    now_epoch = time.time()
    window_start = now_epoch - time_window_days * _DAY_SECONDS

    recent = [
        r for r in reports
        if window_start <= _parse_ts(r["timestamp"]).timestamp() <= now_epoch
    ]
    if not recent:
        return _empty_result("no_recent_reports", time_window_days, alert_radius_km)

    # Group by (problem_id|crop_id).
    groups: Dict[str, List[Dict]] = {}
    for r in recent:
        key = f"{r.get('problem_id') or r.get('problem') or 'unknown'}|{r.get('crop_id') or r.get('crop') or 'unknown'}"
        groups.setdefault(key, []).append(r)

    best = None
    best_score = 0.0
    for key, grp in groups.items():
        problem_id, crop_id = key.split("|", 1)
        geo = _is_geo_concentrated(grp, alert_radius_km)
        score = _score_group(grp, geo, now_epoch)
        if score > best_score:
            best_score = score
            best = {
                "problem_id": problem_id, "crop_id": crop_id,
                "problem": grp[0].get("problem"), "crop": grp[0].get("crop"),
                "category": grp[0].get("category"), "reports": grp,
                "report_count": len(grp), "geo_concentrated": geo, "score": score,
            }

    if not best or best["report_count"] < MIN_REPORTS_FOR_RISK:
        return OutbreakRiskResult(
            risk_level="LOW",
            risk_score=round(best["score"]) if best else 0,
            problem=best["problem"] if best else None,
            crop=best["crop"] if best else None,
            crop_id=best["crop_id"] if best else None,
            problem_id=best["problem_id"] if best else None,
            category=best["category"] if best else None,
            report_count=best["report_count"] if best else len(recent),
            affected_area=_summarise_area(best["reports"]) if best else None,
            affected_area_center=_centroid(best["reports"]) if best else None,
            geo_concentrated=False, alert_recommended=False,
            reason="below_threshold", radius_km=alert_radius_km,
            time_window_days=time_window_days,
        )

    risk_level = _risk_level(best["score"], best["report_count"])
    return OutbreakRiskResult(
        risk_level=risk_level,
        risk_score=round(best["score"]),
        problem=best["problem"],
        crop=best["crop"],
        crop_id=best["crop_id"],
        problem_id=best["problem_id"],
        category=best["category"],
        report_count=best["report_count"],
        affected_area=_summarise_area(best["reports"]),
        affected_area_center=_centroid(best["reports"]),
        geo_concentrated=best["geo_concentrated"],
        alert_recommended=risk_level in ("HIGH", "CRITICAL"),
        reason="cluster_detected" if risk_level in ("HIGH", "CRITICAL") else "no_significant_cluster",
        radius_km=alert_radius_km,
        time_window_days=time_window_days,
    )
