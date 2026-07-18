"""Recommendation ranking: combine proximity, grid load, carbon and availability.

The three UI modes (Greenest / Fastest / Balanced) simply change the weights.
Higher score = better recommendation.
"""
from __future__ import annotations

import math

WEIGHTS = {
    "fastest":  {"proximity": 0.55, "grid": 0.15, "carbon": 0.10, "availability": 0.20},
    "greenest": {"proximity": 0.15, "grid": 0.30, "carbon": 0.45, "availability": 0.10},
    "balanced": {"proximity": 0.30, "grid": 0.25, "carbon": 0.30, "availability": 0.15},
}


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def _norm(value: float, lo: float, hi: float) -> float:
    if hi - lo < 1e-9:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def rank(candidates: list[dict], user_lat: float, user_lng: float,
         mode: str = "balanced") -> list[dict]:
    """Score and sort candidate stations.

    Each candidate must have: station_id, lat, lng, grid_load_pct,
    carbon_intensity_gco2_kwh, availability (0-1). Returns the same list with
    `distance_km` and `score` added, sorted best-first.
    """
    weights = WEIGHTS.get(mode, WEIGHTS["balanced"])
    if not candidates:
        return []

    for c in candidates:
        c["distance_km"] = round(
            haversine_km(user_lat, user_lng, c["lat"], c["lng"]), 2
        )

    dists = [c["distance_km"] for c in candidates]
    loads = [c["grid_load_pct"] for c in candidates]
    carbons = [c["carbon_intensity_gco2_kwh"] for c in candidates]
    dmin, dmax = min(dists), max(dists)
    lmin, lmax = min(loads), max(loads)
    cmin, cmax = min(carbons), max(carbons)

    for c in candidates:
        proximity = 1 - _norm(c["distance_km"], dmin, dmax)     # closer = better
        low_load = 1 - _norm(c["grid_load_pct"], lmin, lmax)    # emptier grid = better
        low_carbon = 1 - _norm(c["carbon_intensity_gco2_kwh"], cmin, cmax)
        availability = float(c.get("availability", 0.5))

        c["score"] = round(
            weights["proximity"] * proximity
            + weights["grid"] * low_load
            + weights["carbon"] * low_carbon
            + weights["availability"] * availability,
            4,
        )

    return sorted(candidates, key=lambda x: x["score"], reverse=True)
