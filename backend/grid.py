import math
from typing import Any

from electricitymap import grid_state
from partner_stations import open_charge_map, partner_stations
from store import read_community


def haversine(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    radius = 6371
    d_lat = math.radians(b_lat - a_lat)
    d_lng = math.radians(b_lng - a_lng)
    x = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * math.sin(d_lng / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(x), math.sqrt(1 - x))


async def all_stations(lat: float, lng: float, distance: float) -> list[dict[str, Any]]:
    combined = partner_stations() + read_community() + await open_charge_map(lat, lng, distance)
    return list({item["id"]: item for item in combined if haversine(lat, lng, item["lat"], item["lng"]) <= distance}.values())


def enrich(stations: list[dict[str, Any]], lat: float, lng: float) -> list[dict[str, Any]]:
    return [item | grid_state(item["id"]) | {"distance_km": round(haversine(lat, lng, item["lat"], item["lng"]), 2)} for item in stations]
