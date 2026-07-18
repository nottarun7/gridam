"""Nominatim (OpenStreetMap) geocoding — search a place name, get coordinates.

Server-side so we can set a proper User-Agent (Nominatim's usage policy
requires one) and, later, swap in a self-hosted instance for heavy use.
"""
from __future__ import annotations

import httpx

SEARCH_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "GRIDAM/0.1 (hackathon; EV charging)"}


async def geocode(q: str, limit: int = 6) -> list[dict]:
    params = {
        "q": q,
        "format": "json",
        "limit": limit,
        "countrycodes": "in",     # bias to India for the demo
        "addressdetails": 0,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(SEARCH_URL, params=params, headers=HEADERS)
        r.raise_for_status()
        rows = r.json()
    return [
        {
            "name": row.get("display_name", "").split(",")[0],
            "full_name": row.get("display_name", ""),
            "lat": float(row["lat"]),
            "lng": float(row["lon"]),
        }
        for row in rows
    ]
