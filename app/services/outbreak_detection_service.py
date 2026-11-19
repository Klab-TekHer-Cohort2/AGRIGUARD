"""Community Outbreak Detection Service.

PROTOTYPE risk detector — NOT a scientifically validated disease forecasting
model. Clearly labelled as such in all output.

Concept:
    Multiple reports + same/similar problem + nearby locations + recent time
    window → community risk analysis → potential outbreak.

Risk score inputs (transparent, configurable):
    - Number of reports
    - Severity of reports
    - AI confidence of reports
    - Geographic concentration (within alert radius)
    - Recency (within the time window)

Outputs:
    detect_community_risk(reports, opts) → CommunityRiskResult
    find_alertable_farmers(outbreak, farmers, radius_km) → farmer list

The risk score is a transparent heuristic 0–100, not a probability.

Mirrors ``src/services/outbreakDetectionService.js``.
"""

import time
from datetime import datetime, timezone

from app.config import settings
from app.utils import geo_utils

SEVERITY_WEIGHT = {
    "Low": 1,
    "Moderate": 2,
    "High": 3,
    "Critical": 4,
}

_DAY_SECONDS = 24 * 60 * 60


def _parse_ts(timestamp):
    """Parse an ISO 8601 timestamp (with optional trailing 'Z') to a UTC datetime."""
    if isinstance(timestamp, datetime):
        return timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
    ts = timestamp
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


class OutbreakDetectionService:
    """Prototype community outbreak risk detector."""

    def detect_community_risk(self, reports, opts=None):
        """Analyse a set of farmer reports for community risk.

        Args:
            reports: list of report dicts (see prototype dataset for shape).
            opts: optional dict with ``timeWindowDays`` and ``alertRadiusKm``.

        Returns:
            CommunityRiskResult dict.
        """
        opts = opts or {}
        time_window_days = opts.get("timeWindowDays") or settings.outbreak_time_window_days
        alert_radius_km = opts.get("alertRadiusKm") or settings.outbreak_alert_radius_km
        now = time.time()
        window_start = now - time_window_days * _DAY_SECONDS

        # 1. Filter to recent reports.
        recent = [
            r
            for r in reports
            if window_start <= _parse_ts(r["timestamp"]).timestamp() <= now
        ]

        if not recent:
            return self._empty_result("no_recent_reports", time_window_days, alert_radius_km)

        # 2. Group by (problemId, cropId) — the core signal.
        groups = self._group_by_problem(recent)

        # 3. Score each group; pick the most concerning.
        best_group = None
        best_score = 0
        for key, group_reports in groups.items():
            problem_id, crop_id = self._parse_group_key(key)
            geo_concentrated = self._is_geo_concentrated(group_reports, alert_radius_km)
            score = self._score_group(group_reports, geo_concentrated, time_window_days, now)

            if score > best_score:
                best_score = score
                best_group = {
                    "problemId": problem_id,
                    "cropId": crop_id,
                    "problem": group_reports[0].get("problem"),
                    "crop": group_reports[0].get("crop"),
                    "category": group_reports[0].get("category"),
                    "reports": group_reports,
                    "reportCount": len(group_reports),
                    "geoConcentrated": geo_concentrated,
                    "score": score,
                }

        # 4. No group meets the minimum report threshold → low risk.
        if not best_group or best_group["reportCount"] < settings.outbreak_min_reports_for_risk:
            return {
                "riskLevel": "LOW",
                "riskScore": best_group["score"] if best_group else 0,
                "problem": best_group["problem"] if best_group else None,
                "crop": best_group["crop"] if best_group else None,
                "cropId": best_group["cropId"] if best_group else None,
                "problemId": best_group["problemId"] if best_group else None,
                "reportCount": best_group["reportCount"] if best_group else len(recent),
                "affectedArea": self._summarise_area(best_group["reports"]) if best_group else None,
                "affectedAreaCenter": self._centroid(best_group["reports"]) if best_group else None,
                "alertRecommended": False,
                "reason": "below_threshold",
                "radiusKm": alert_radius_km,
                "timeWindowDays": time_window_days,
                "prototype": True,
                "disclaimer": "Prototype risk detector — not a validated forecasting model.",
            }

        # 5. Determine risk level from score + report count.
        risk_level = self._risk_level_from_score(best_group["score"], best_group["reportCount"])
        alert_recommended = risk_level in ("HIGH", "CRITICAL")

        return {
            "riskLevel": risk_level,
            "riskScore": round(best_group["score"]),
            "problem": best_group["problem"],
            "crop": best_group["crop"],
            "cropId": best_group["cropId"],
            "problemId": best_group["problemId"],
            "category": best_group["category"],
            "reportCount": best_group["reportCount"],
            "affectedArea": self._summarise_area(best_group["reports"]),
            "affectedAreaCenter": self._centroid(best_group["reports"]),
            "geoConcentrated": best_group["geoConcentrated"],
            "alertRecommended": alert_recommended,
            "reason": "cluster_detected" if alert_recommended else "no_significant_cluster",
            "radiusKm": alert_radius_km,
            "timeWindowDays": time_window_days,
            "prototype": True,
            "disclaimer": "Prototype risk detector — not a validated forecasting model.",
        }

    def find_alertable_farmers(self, outbreak, farmers, radius_km=None):
        """Find registered farmers within the alert radius of an outbreak centre.

        Used to send personalised prototype alerts.
        """
        if not outbreak or not outbreak.get("affectedAreaCenter"):
            return []
        return geo_utils.farmers_within_radius(
            outbreak["affectedAreaCenter"],
            farmers,
            radius_km or settings.outbreak_alert_radius_km,
        )

    # ── Internal helpers ─────────────────────────────────────────────────────
    def _group_by_problem(self, reports):
        groups = {}
        for r in reports:
            key = f"{r.get('problemId') or r.get('problem') or 'unknown'}|{r.get('cropId') or r.get('crop') or 'unknown'}"
            groups.setdefault(key, []).append(r)
        return groups

    def _parse_group_key(self, key):
        parts = key.split("|", 1)
        problem_id = parts[0]
        crop_id = parts[1] if len(parts) > 1 else "unknown"
        return problem_id, crop_id

    def _score_group(self, reports, geo_concentrated, time_window_days, now):
        """Transparent prototype risk score (0–100). NOT a probability."""
        count = len(reports)

        # Report-count component (0–40): more reports → higher score.
        count_score = min((count / settings.outbreak_critical_risk_report_count) * 40, 40)

        # Severity component (0–25): average severity weight.
        avg_severity = sum(SEVERITY_WEIGHT.get(r.get("severity"), 1) for r in reports) / count
        severity_score = (avg_severity / 4) * 25

        # Confidence component (0–15): average AI confidence.
        avg_confidence = sum((r.get("confidence") or 0) for r in reports) / count
        confidence_score = avg_confidence * 15

        # Geographic concentration (0–10): bonus if reports cluster within radius.
        geo_score = 10 if geo_concentrated else 0

        # Recency (0–10): bonus if all reports are in the last 3 days.
        recent_count = sum(
            1
            for r in reports
            if (now - _parse_ts(r["timestamp"]).timestamp()) / _DAY_SECONDS <= 3
        )
        recency_score = (recent_count / count) * 10

        return count_score + severity_score + confidence_score + geo_score + recency_score

    def _risk_level_from_score(self, score, report_count):
        if score >= 70 or report_count >= settings.outbreak_critical_risk_report_count:
            return "CRITICAL"
        if score >= 50 or report_count >= settings.outbreak_high_risk_report_count:
            return "HIGH"
        if score >= 30 or report_count >= settings.outbreak_min_reports_for_risk:
            return "MEDIUM"
        return "LOW"

    def _is_geo_concentrated(self, reports, radius_km):
        if len(reports) < 2:
            return False
        center = self._centroid(reports)
        if not center:
            return False
        return all(
            r.get("lat") is not None
            and r.get("lng") is not None
            and geo_utils.haversine_km(center["lat"], center["lng"], r["lat"], r["lng"]) <= radius_km * 2
            for r in reports
        )

    def _centroid(self, reports):
        with_coords = [r for r in reports if r.get("lat") is not None and r.get("lng") is not None]
        if not with_coords:
            return None
        lat = sum(r["lat"] for r in with_coords) / len(with_coords)
        lng = sum(r["lng"] for r in with_coords) / len(with_coords)
        return {"lat": lat, "lng": lng}

    def _summarise_area(self, reports):
        communities = []
        for r in reports:
            c = r.get("community")
            if c and c not in communities:
                communities.append(c)
        if len(communities) == 1:
            return communities[0]
        if len(communities) > 1:
            return ", ".join(communities)
        return "unknown"

    def _empty_result(self, reason, time_window_days, alert_radius_km):
        return {
            "riskLevel": "LOW",
            "riskScore": 0,
            "problem": None,
            "crop": None,
            "cropId": None,
            "problemId": None,
            "reportCount": 0,
            "affectedArea": None,
            "affectedAreaCenter": None,
            "alertRecommended": False,
            "reason": reason,
            "radiusKm": alert_radius_km,
            "timeWindowDays": time_window_days,
            "prototype": True,
            "disclaimer": "Prototype risk detector — not a validated forecasting model.",
        }


# Module-level singleton.
outbreak_detection_service = OutbreakDetectionService()
