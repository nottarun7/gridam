"""OpenRouteService client — driving route + ETA between two points.

Kept server-side so the ORS key never ships to the browser. Returns a GeoJSON
LineString the frontend can drop straight onto the MapLibre map, plus a summary
(distance / duration).
"""
from __future__ import annotations

import httpx

from config import OPENROUTESERVICE_API_KEY

ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"


async def route(start_lat: float, start_lng: float,
                end_lat: float, end_lng: float) -> dict:
    body = {"coordinates": [[start_lng, start_lat], [end_lng, end_lat]]}
    headers = {
        "Authorization": OPENROUTESERVICE_API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "GRIDAM/0.1 (hackathon)",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(ORS_URL, json=body, headers=headers)
        r.raise_for_status()
        data = r.json()

    feat = (data.get("features") or [{}])[0]
    props = feat.get("properties") or {}
    summary = props.get("summary") or {}

    # Flatten turn-by-turn steps across route segments.
    steps: list[dict] = []
    for seg in props.get("segments") or []:
        for st in seg.get("steps") or []:
            steps.append({
                "instruction": st.get("instruction", ""),
                "name": st.get("name", ""),
                "distance_m": round(st.get("distance", 0)),
                "duration_s": round(st.get("duration", 0)),
                "way_points": st.get("way_points", []),
            })

    return {
        "geometry": feat.get("geometry"),          # GeoJSON LineString
        "distance_km": round(summary.get("distance", 0) / 1000.0, 2),
        "duration_min": round(summary.get("duration", 0) / 60.0, 1),
        "steps": steps,
    }
