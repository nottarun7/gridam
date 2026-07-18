"""Open Charge Map client — fetches real EV charging stations near a point.

Kept server-side so the API key never ships inside the Android app. The Android
app can call GET /charging-stations on this backend instead of OCM directly,
which also lets us merge in community-added stations.
"""
from __future__ import annotations

import httpx

from config import OPENCHARGEMAP_API_KEY

OCM_URL = "https://api.openchargemap.io/v3/poi/"


def _connector_names(poi: dict) -> list[str]:
    out = []
    for conn in poi.get("Connections") or []:
        ct = (conn.get("ConnectionType") or {}).get("Title")
        if ct and ct not in out:
            out.append(ct)
    return out


def _max_power_kw(poi: dict) -> float:
    powers = [c.get("PowerKW") for c in (poi.get("Connections") or []) if c.get("PowerKW")]
    return float(max(powers)) if powers else 0.0


async def nearby(lat: float, lng: float, distance_km: float = 15,
                 max_results: int = 40) -> list[dict]:
    params = {
        "output": "json",
        "latitude": lat,
        "longitude": lng,
        "distance": distance_km,
        "distanceunit": "KM",
        "maxresults": max_results,
        "compact": "true",
        "verbose": "false",
        "key": OPENCHARGEMAP_API_KEY,
    }
    headers = {"X-API-Key": OPENCHARGEMAP_API_KEY, "User-Agent": "GRIDAM/0.1 (hackathon)"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(OCM_URL, params=params, headers=headers)
        r.raise_for_status()
        pois = r.json()

    stations = []
    for p in pois:
        addr = p.get("AddressInfo") or {}
        if addr.get("Latitude") is None:
            continue
        stations.append({
            "station_id": f"ocm-{p.get('ID')}",
            "name": addr.get("Title") or "Unnamed station",
            "lat": addr.get("Latitude"),
            "lng": addr.get("Longitude"),
            "address": addr.get("AddressLine1"),
            "town": addr.get("Town"),
            "connectors": _connector_names(p),
            "power_kw": _max_power_kw(p),
            "operator": (p.get("OperatorInfo") or {}).get("Title"),
            "source": "ocm",
        })
    return stations
