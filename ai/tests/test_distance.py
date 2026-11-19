"""Tests: 5 km distance + alert eligibility (section 26)."""

from ai.src.alert_logic import calculate_distance_km, farmers_within_radius, is_alert_eligible

KABARORE = (-1.4790, 30.4190)  # outbreak centre


def _farmer(lat, lon, fid="F"):
    return {"id": fid, "name": fid, "lat": lat, "lng": lon, "community": "Kabarore"}


def test_3km_is_eligible():
    assert is_alert_eligible(_farmer(-1.469, 30.419), *KABARORE, radius_km=5.0) is True


def test_4_9km_is_eligible():
    # ~4.4 km south of centre — within 5 km
    assert is_alert_eligible(_farmer(-1.519, 30.419), *KABARORE, radius_km=5.0) is True


def test_far_over_5km_not_eligible():
    # ~11+ km away (Nyagatare area) — not eligible
    assert is_alert_eligible(_farmer(-1.56, 30.33), *KABARORE, radius_km=5.0) is False


def test_farmer_without_location_not_eligible():
    assert is_alert_eligible({"id": "X", "lat": None, "lng": None}, *KABARORE) is False


def test_farmers_within_radius_excludes_outside():
    farmers = [
        _farmer(-1.479, 30.419, "A"),   # ~0 km
        _farmer(-1.482, 30.422, "B"),   # ~0.4 km
        _farmer(-1.56, 30.33, "C"),     # ~13 km
    ]
    eligible = farmers_within_radius(*KABARORE, farmers=farmers, radius_km=5.0)
    ids = [f.farmer_id for f in eligible]
    assert "A" in ids and "B" in ids and "C" not in ids
    # Sorted nearest-first
    assert eligible[0].distance_km <= eligible[1].distance_km


def test_distance_zero_for_same_point():
    assert calculate_distance_km(1.0, 30.0, 1.0, 30.0) == 0


def test_distance_symmetric():
    d1 = calculate_distance_km(-1.479, 30.419, -1.56, 30.33)
    d2 = calculate_distance_km(-1.56, 30.33, -1.479, 30.419)
    assert abs(d1 - d2) < 1e-6
