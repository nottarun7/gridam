"""Curated li-ion battery recycling / e-waste centers around Kochi.

Closes the EV lifecycle story: charge clean AND retire the battery responsibly.
Coordinates are approximate (near known Kochi localities) — a demo seed meant to
be replaced by a real recyclers registry later. Same swappable pattern as the
station data.
"""
from __future__ import annotations

RECYCLING_CENTERS: list[dict] = [
    {"id": "rec-cleankerala", "name": "Clean Kerala Company · E-waste Facility",
     "lat": 9.9970, "lng": 76.3080, "type": "E-waste + Li-ion",
     "accepts": ["Li-ion batteries", "EV packs", "Electronics"], "phone": "0471-2318189"},
    {"id": "rec-kalamassery", "name": "Cochin E-Waste Recyclers",
     "lat": 10.0640, "lng": 76.3220, "type": "E-waste", "accepts": ["Li-ion batteries", "Electronics"],
     "phone": "0484-2555000"},
    {"id": "rec-edappally", "name": "Green Era Recyclers · Edappally",
     "lat": 10.0274, "lng": 76.3080, "type": "Li-ion", "accepts": ["Li-ion batteries", "EV packs"],
     "phone": "0484-2334455"},
    {"id": "rec-keil", "name": "Kerala Enviro Infrastructure (KEIL) · Ambalamugal",
     "lat": 9.9490, "lng": 76.3900, "type": "Hazardous + battery", "accepts": ["Battery waste", "Hazardous waste"],
     "phone": "0484-2720666"},
    {"id": "rec-secondlife", "name": "EcoBirdd · Battery Second-life Hub",
     "lat": 9.9680, "lng": 76.3180, "type": "Second-life", "accepts": ["EV packs (reuse)", "Li-ion cells"],
     "phone": "0484-2999888"},
    {"id": "rec-aluva", "name": "Aluva Municipal E-waste Collection",
     "lat": 10.1080, "lng": 76.3510, "type": "E-waste", "accepts": ["Li-ion batteries", "Electronics"],
     "phone": "0484-2624001"},
]
