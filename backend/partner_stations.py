import os
from typing import Any

import httpx


def station(id_: str, name: str, lat: float, lng: float, operator: str, connector: str, power: float, plugs: int) -> dict[str, Any]:
    return {"id": id_, "name": name, "lat": lat, "lng": lng, "operator": operator, "connector": connector, "power_kw": power, "plugs": plugs, "available": max(1, plugs - (len(id_) % 2)), "source": "partner"}


def partner_stations() -> list[dict[str, Any]]:
    return [
        station("partner-zeon-lulu", "Zeon Charging - Lulu Mall", 10.0279, 76.3083, "Zeon", "CCS2", 60, 4),
        station("partner-tata-vyttila", "Tata Power EZ Charge - Vyttila", 9.9673, 76.3185, "Tata Power", "CCS2", 30, 2),
        station("partner-kseb-mgroad", "KSEB EV Hub - MG Road", 9.9761, 76.2824, "KSEB", "Type 2", 22, 3),
        station("partner-chargemod-fortkochi", "ChargeMOD - Fort Kochi", 9.9658, 76.2420, "ChargeMOD", "Bharat AC001", 10, 2),
        station("partner-statiq-edappally", "Statiq - Edappally", 10.0260, 76.3124, "Statiq", "CCS2", 50, 3),
        station("partner-kseb-kakkanad", "KSEB Fast Charge - Kakkanad", 10.0159, 76.3419, "KSEB", "CCS2", 60, 4),
        station("partner-ather-panampilly", "Ather Grid - Panampilly", 9.9617, 76.2999, "Ather", "Ather/Type 2", 7.4, 2),
        station("partner-tata-maradu", "Tata Power - Maradu", 9.9399, 76.3202, "Tata Power", "CCS2", 25, 2),
        station("partner-zeon-airport", "Zeon Corridor - CIAL", 10.1518, 76.3927, "Zeon", "CCS2", 60, 4),
        station("partner-chargemod-aluva", "ChargeMOD - Aluva", 10.1076, 76.3516, "ChargeMOD", "Type 2", 22, 2),
        station("partner-kseb-tripunitura", "KSEB - Tripunithura", 9.9479, 76.3496, "KSEB", "Bharat DC001", 15, 2),
        station("partner-statiq-marine", "Statiq - Marine Drive", 9.9816, 76.2765, "Statiq", "CCS2", 30, 2),
    ]


def community_seed() -> list[dict[str, Any]]:
    return [
        station("community-infopark", "Community Charger - Infopark Gate", 10.0139, 76.3627, "Community", "Type 2", 11, 1),
        station("community-thevara", "Community Charger - Thevara", 9.9351, 76.2996, "Community", "Bharat AC001", 7.4, 1),
        station("community-kalamassery", "Community Charger - Kalamassery", 10.0526, 76.3341, "Community", "Type 2", 22, 2),
    ]


async def open_charge_map(lat: float, lng: float, distance: float) -> list[dict[str, Any]]:
    key = os.getenv("OPENCHARGEMAP_API_KEY")
    if not key:
        return []
    try:
        params = {"output": "json", "latitude": lat, "longitude": lng, "distance": distance, "distanceunit": "KM", "maxresults": 50}
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get("https://api.openchargemap.io/v3/poi/", params=params, headers={"X-API-Key": key})
            response.raise_for_status()
        result = []
        for item in response.json():
            connections = item.get("Connections") or []
            address = item.get("AddressInfo") or {}
            power = max([c.get("PowerKW") or 0 for c in connections] or [7.4])
            connector = connections[0].get("ConnectionType", {}).get("Title", "EV connector") if connections else "EV connector"
            result.append(station(f"ocm-{item.get('ID')}", item.get("Title") or address.get("Title") or "Open Charge Map station", address.get("Latitude"), address.get("Longitude"), item.get("OperatorInfo", {}).get("Title", "Open Charge Map"), connector, power or 7.4, len(connections) or 1) | {"source": "openchargemap"})
        return [item for item in result if item.get("lat") and item.get("lng")]
    except Exception:
        return []
