"""Curated 'partner network' charging stations for Kochi.

Open Charge Map misses most Indian operators (ChargeMOD, Zeon, etc.), so this
is a seed dataset of representative Kochi locations across the major networks —
enough to make the map feel real for the demo. Coordinates are approximate
(near well-known Kochi hubs) and this list is intended to be REPLACED by real
operator APIs later: the app merges it exactly like any other source, so
swapping in a live feed changes nothing downstream.
"""
from __future__ import annotations

PARTNER_STATIONS: list[dict] = [
    {"station_id": "chargemod-lulu", "name": "ChargeMOD · Lulu Mall Edappally",
     "lat": 10.0274, "lng": 76.3080, "connectors": ["CCS2", "Type 2"], "power_kw": 60,
     "operator": "ChargeMOD", "source": "partner"},
    {"station_id": "chargemod-vyttila", "name": "ChargeMOD · Vyttila Mobility Hub",
     "lat": 9.9670, "lng": 76.3180, "connectors": ["CCS2", "CHAdeMO"], "power_kw": 50,
     "operator": "ChargeMOD", "source": "partner"},
    {"station_id": "chargemod-fortkochi", "name": "ChargeMOD · Fort Kochi",
     "lat": 9.9658, "lng": 76.2421, "connectors": ["Type 2"], "power_kw": 22,
     "operator": "ChargeMOD", "source": "partner"},
    {"station_id": "zeon-marinedrive", "name": "Zeon · Marine Drive",
     "lat": 9.9800, "lng": 76.2760, "connectors": ["CCS2", "Type 2"], "power_kw": 30,
     "operator": "Zeon Charging", "source": "partner"},
    {"station_id": "zeon-kakkanad", "name": "Zeon · Infopark Kakkanad",
     "lat": 10.0074, "lng": 76.3600, "connectors": ["CCS2"], "power_kw": 60,
     "operator": "Zeon Charging", "source": "partner"},
    {"station_id": "zeon-panampilly", "name": "Zeon · Panampilly Nagar",
     "lat": 9.9636, "lng": 76.2969, "connectors": ["Type 2", "Bharat AC-001"], "power_kw": 22,
     "operator": "Zeon Charging", "source": "partner"},
    {"station_id": "tata-kaloor", "name": "Tata Power · Kaloor Stadium",
     "lat": 9.9970, "lng": 76.2980, "connectors": ["CCS2", "CHAdeMO"], "power_kw": 50,
     "operator": "Tata Power EZ Charge", "source": "partner"},
    {"station_id": "tata-palarivattom", "name": "Tata Power · Palarivattom",
     "lat": 10.0060, "lng": 76.3050, "connectors": ["CCS2"], "power_kw": 25,
     "operator": "Tata Power EZ Charge", "source": "partner"},
    {"station_id": "statiq-aluva", "name": "Statiq · Aluva Metro",
     "lat": 10.1080, "lng": 76.3510, "connectors": ["CCS2", "Type 2"], "power_kw": 60,
     "operator": "Statiq", "source": "partner"},
    {"station_id": "statiq-kalamassery", "name": "Statiq · Kalamassery",
     "lat": 10.0640, "lng": 76.3220, "connectors": ["Type 2"], "power_kw": 22,
     "operator": "Statiq", "source": "partner"},
    {"station_id": "kseb-thripunithura", "name": "KSEB · Thripunithura",
     "lat": 9.9430, "lng": 76.3470, "connectors": ["Bharat DC-001", "Bharat AC-001"], "power_kw": 15,
     "operator": "KSEB", "source": "partner"},
    {"station_id": "kseb-mgroad", "name": "KSEB · MG Road",
     "lat": 9.9760, "lng": 76.2840, "connectors": ["Bharat AC-001"], "power_kw": 10,
     "operator": "KSEB", "source": "partner"},
]
