"""Tests: outbreak detection, community risk, and 5 km alert distance.

Mirrors ``tests/outbreak.distance.test.js``.
"""

from app.services.outbreak_detection_service import outbreak_detection_service
from app.utils import geo_utils
from app.data.prototype_dataset import prototype_dataset as dataset
from app.config import settings


# ── Outbreak detection — Fall Armyworm cluster (Kabarore) ──────────────────────
_result = None


def _cluster_result():
    global _result
    if _result is None:
        _result = outbreak_detection_service.detect_community_risk(dataset["reports"])
    return _result


def test_detects_a_non_low_risk_level():
    result = _cluster_result()
    assert result["riskLevel"] in ("MEDIUM", "HIGH", "CRITICAL")


def test_identifies_problem_as_fall_armyworm():
    result = _cluster_result()
    assert "Fall Armyworm".lower() in (result["problem"] or "").lower()


def test_identifies_crop_as_maize():
    result = _cluster_result()
    assert result["cropId"] == "maize"


def test_report_count_reflects_cluster():
    result = _cluster_result()
    assert result["reportCount"] >= settings.outbreak_min_reports_for_risk


def test_affected_area_is_kabarore():
    result = _cluster_result()
    assert "Kabarore" in (result["affectedArea"] or "")


def test_alert_recommended_for_high_or_critical():
    result = _cluster_result()
    if result["riskLevel"] in ("HIGH", "CRITICAL"):
        assert result["alertRecommended"] is True


def test_result_is_labelled_as_prototype():
    result = _cluster_result()
    assert result["prototype"] is True
    assert "prototype" in result["disclaimer"].lower()


# ── Outbreak detection — no outbreak (isolated reports) ────────────────────────
def test_isolated_single_reports_low_risk():
    isolated = [r for r in dataset["reports"] if r["community"] != "Kabarore"]
    result = outbreak_detection_service.detect_community_risk(isolated)
    assert result["riskLevel"] == "LOW"
    assert result["alertRecommended"] is False


def test_empty_report_list_low_risk_no_alert():
    result = outbreak_detection_service.detect_community_risk([])
    assert result["riskLevel"] == "LOW"
    assert result["alertRecommended"] is False


# ── 5 km alert logic — distance ────────────────────────────────────────────────
# Kabarore centroid ~ (-1.479, 30.419)
_CENTER = {"lat": -1.4790, "lng": 30.4190}


def _nearby_ids():
    nearby = geo_utils.farmers_within_radius(_CENTER, dataset["farmers"], 5)
    return [f["id"] for f in nearby]


def test_farmer_within_5km_eligible_for_alert():
    ids = _nearby_ids()
    # F001–F005 are all within ~1 km of the Kabarore centroid
    assert "F001" in ids
    assert "F002" in ids
    assert "F003" in ids
    assert "F004" in ids
    assert "F005" in ids


def test_farmer_outside_5km_not_eligible():
    ids = _nearby_ids()
    # F007 in Nyagatare (~-1.56, 30.33) is > 10 km away
    assert "F007" not in ids


def test_farmer_without_location_excluded():
    ids = _nearby_ids()
    # F009 has no coordinates
    assert "F009" not in ids


def test_find_alertable_farmers_returns_farmers_with_distance():
    risk = outbreak_detection_service.detect_community_risk(dataset["reports"])
    alertable = outbreak_detection_service.find_alertable_farmers(risk, dataset["farmers"], 5)
    if alertable:
        assert "distanceKm" in alertable[0]
        assert "id" in alertable[0]


# ── Haversine distance ────────────────────────────────────────────────────────
def test_distance_between_identical_points_is_zero():
    assert geo_utils.haversine_km(1.0, 30.0, 1.0, 30.0) == 0


def test_distance_is_symmetric():
    d1 = geo_utils.haversine_km(-1.479, 30.419, -1.56, 30.33)
    d2 = geo_utils.haversine_km(-1.56, 30.33, -1.479, 30.419)
    assert abs(d1 - d2) < 1e-5


def test_distance_is_positive_for_distinct_points():
    d = geo_utils.haversine_km(-1.479, 30.419, -1.56, 30.33)
    assert d > 0
