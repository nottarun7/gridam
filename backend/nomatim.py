import httpx

from config import KOCHI


async def geocode(query: str) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=8, headers={"User-Agent": "GRI-1.0"}) as client:
            response = await client.get("https://nominatim.openstreetmap.org/search", params={"q": query, "format": "json", "limit": 5, "countrycodes": "in"})
            response.raise_for_status()
        return [{"name": item.get("name") or item.get("display_name", "").split(",")[0], "full_name": item.get("display_name"), "lat": float(item["lat"]), "lng": float(item["lon"])} for item in response.json()]
    except Exception:
        return [{"name": "Kochi", "full_name": "Kochi, Kerala, India", "lat": KOCHI["lat"], "lng": KOCHI["lng"]}]
