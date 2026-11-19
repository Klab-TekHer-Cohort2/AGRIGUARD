"""Geographic utilities — Haversine distance and radius queries.

Used by the outbreak detection and 5 km alert logic. Pure functions, fully
unit-testable. Mirrors ``src/utils/geoUtils.js``.
"""

import math


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance between two lat/lng points, in kilometres.

    Returns the great-circle distance assuming a spherical Earth of radius
    6371 km.
    """

    def _to_rad(deg: float) -> float:
        return deg * math.pi / 180.0

    radius = 6371.0  # Earth radius in km
    d_lat = _to_rad(lat2 - lat1)
    d_lng = _to_rad(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) * math.sin(d_lat / 2)
        + math.cos(_to_rad(lat1)) * math.cos(_to_rad(lat2)) * math.sin(d_lng / 2) * math.sin(d_lng / 2)
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def farmers_within_radius(centre: dict, farmers: list, radius_km: float) -> list:
    """Find all registered farmers within ``radius_km`` of a centre point.

    Only farmers with location data are considered — others are skipped (we
    never expose private locations unnecessarily). Each returned farmer dict
    is a copy annotated with a ``distanceKm`` field, sorted nearest-first.

    Args:
        centre: ``{"lat": float, "lng": float}``
        farmers: list of ``{"id", "name?", "lat", "lng", "phone?", "community?"}``
        radius_km: radius in kilometres

    Returns:
        list of farmers within radius, each with an added ``distanceKm`` key.
    """
    if not centre or centre.get("lat") is None or centre.get("lng") is None:
        return []

    # 1. Keep only farmers that have coordinates.
    with_coords = [f for f in (farmers or []) if f.get("lat") is not None and f.get("lng") is not None]
    # 2. Annotate each with its distance from the centre.
    annotated = [
        {**f, "distanceKm": haversine_km(centre["lat"], centre["lng"], f["lat"], f["lng"])}
        for f in with_coords
    ]
    # 3. Keep only farmers within the radius.
    within = [f for f in annotated if f["distanceKm"] <= radius_km]
    # 4. Sort nearest-first.
    return sorted(within, key=lambda f: f["distanceKm"])
