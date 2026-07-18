from typing import Any

from grid import enrich


def rank(stations: list[dict[str, Any]], lat: float, lng: float, mode: str) -> list[dict[str, Any]]:
    if not stations:
        return []
    weights = {"fastest": {"prox": .55, "grid": .15, "carbon": .10, "avail": .20}, "greenest": {"prox": .15, "grid": .30, "carbon": .45, "avail": .10}, "balanced": {"prox": .30, "grid": .25, "carbon": .30, "avail": .15}}.get(mode, {"prox": .30, "grid": .25, "carbon": .30, "avail": .15})
    result = enrich(stations, lat, lng)
    max_dist = max(item["distance_km"] for item in result) or 1
    for item in result:
        prox = 1 - item["distance_km"] / max_dist
        grid = 1 - item["grid_load_pct"] / 100
        carbon = 1 - (item["carbon_intensity_gco2_kwh"] - 180) / 740
        avail = item.get("available", 0) / max(item.get("plugs", 1), 1)
        item["score"] = round(100 * (weights["prox"] * prox + weights["grid"] * grid + weights["carbon"] * carbon + weights["avail"] * avail), 1)
    return sorted(result, key=lambda item: item["score"], reverse=True)
