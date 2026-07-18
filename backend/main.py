import asyncio
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CARBON_CACHE, EM_ZONE, KOCHI, map_style_url
from electricitymap import carbon_loop, grid_state, refresh_electricity_maps, synthetic_grid, tou_price
from grid import all_stations
from nomatim import geocode
from partner_stations import community_seed, partner_stations, station
from recycling_centers import centers
from schemas import ChatRequest, RouteRequest, ScoreRequest, SessionCreate, StationCreate
from scoring import rank
from store import add_session, get_profile, init_db, read_community, save_profile, save_station, sessions

app = FastAPI(title="GRIഢം API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup() -> None:
    init_db()
    await refresh_electricity_maps()
    asyncio.create_task(carbon_loop())


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "service": "gridam", "carbon_source": CARBON_CACHE["source"], "zone": EM_ZONE}


@app.get("/config")
async def config() -> dict[str, Any]:
    return {"center": KOCHI, "map_style_url": map_style_url(), "carbon_source": CARBON_CACHE["source"], "zone": EM_ZONE}


@app.get("/charging-stations")
async def charging_stations(lat: float = KOCHI["lat"], lng: float = KOCHI["lng"], distance: float = 35, mode: str = "balanced") -> list[dict[str, Any]]:
    return rank(await all_stations(lat, lng, distance), lat, lng, mode)


@app.get("/stations")
async def stations() -> list[dict[str, Any]]:
    return read_community()


@app.post("/stations")
async def add_station(payload: StationCreate) -> dict[str, Any]:
    item = station("community-" + hashlib.md5(f"{payload.name}{payload.lat}{payload.lng}".encode()).hexdigest()[:10], payload.name, payload.lat, payload.lng, payload.operator, payload.connector, payload.power_kw, 1)
    item["source"] = "community"
    save_station(item)
    return item


@app.get("/grid/{station_id}")
async def grid(station_id: str) -> dict[str, Any]:
    return grid_state(station_id)


@app.post("/grid/batch")
async def grid_batch(payload: dict[str, list[str]]) -> dict[str, Any]:
    return {station_id: grid_state(station_id) for station_id in payload.get("station_ids", [])}


@app.post("/score")
async def score(payload: ScoreRequest) -> list[dict[str, Any]]:
    return rank(payload.stations, payload.lat, payload.lng, payload.mode)


@app.post("/route")
async def route(payload: RouteRequest) -> dict[str, Any]:
    key = os.getenv("OPENROUTESERVER_BASIC_API_KEY")
    if key:
        try:
            body = {"coordinates": [[payload.start["lng"], payload.start["lat"]], [payload.end["lng"], payload.end["lat"]]]}
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.post("https://api.openrouteservice.org/v2/directions/driving-car/geojson", json=body, headers={"Authorization": key})
                response.raise_for_status()
            feature = response.json()["features"][0]
            return {"source": "openrouteservice", "geometry": feature["geometry"], "summary": feature["properties"].get("summary", {}), "steps": feature["properties"].get("segments", [{}])[0].get("steps", [])}
        except Exception:
            pass
    from grid import haversine
    distance = haversine(payload.start["lat"], payload.start["lng"], payload.end["lat"], payload.end["lng"])
    return {"source": "fallback", "geometry": {"type": "LineString", "coordinates": [[payload.start["lng"], payload.start["lat"]], [payload.end["lng"], payload.end["lat"]]]}, "summary": {"distance": distance * 1000, "duration": distance / 35 * 3600}, "steps": [{"instruction": "Follow local roads toward the selected charger.", "distance": distance * 1000}]}


@app.get("/geocode")
async def geocode_route(q: str) -> list[dict]:
    return await geocode(q)


@app.get("/forecast")
async def forecast(station_id: str = "partner-kseb-mgroad", charge_hours: float = 2.5) -> dict[str, Any]:
    now = datetime.now(timezone.utc).astimezone()
    points = []
    for index in range(24):
        when = now + timedelta(hours=index)
        state = grid_state(station_id, when)
        carbon = state["carbon_intensity_gco2_kwh"]
        if CARBON_CACHE["source"] == "electricitymaps" and index < len(CARBON_CACHE.get("forecast", [])):
            carbon = CARBON_CACHE["forecast"][index].get("carbonIntensity", carbon)
        points.append({"time": when.isoformat(), "hour": when.hour, "carbon": carbon, "price": tou_price(when.hour), "load": state["grid_load_pct"]})
    min_c, max_c = min(item["carbon"] for item in points), max(item["carbon"] for item in points)
    min_p, max_p = min(item["price"] for item in points), max(item["price"] for item in points)
    for item in points:
        item["recommendation_score"] = round(.6 * (item["carbon"] - min_c) / max(max_c - min_c, 1) + .4 * (item["price"] - min_p) / max(max_p - min_p, 1), 3)
    return {"source": CARBON_CACHE["source"], "charge_hours": charge_hours, "points": points, "greenest": min(points, key=lambda item: item["carbon"]), "cheapest": min(points, key=lambda item: item["price"]), "recommended": min(points, key=lambda item: item["recommendation_score"])}


@app.get("/recycling")
async def recycling() -> list[dict]:
    return centers()


def impact_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    total_kwh = sum(item.get("kwh", 0) for item in items)
    avg_carbon = sum(item.get("kwh", 0) * item.get("carbon_intensity", 520) for item in items) / max(total_kwh, 1)
    ev_km = total_kwh * 6.5
    session_co2 = total_kwh * avg_carbon / 1000
    petrol_co2 = ev_km * 140 / 1000
    return {"total_kwh": round(total_kwh, 1), "avg_carbon": round(avg_carbon, 0), "ev_km": round(ev_km, 0), "co2_emitted_kg": round(session_co2, 1), "co2_saved_kg": round(max(0, petrol_co2 - session_co2), 1), "money_saved_inr": round(ev_km / 18 * 105 - total_kwh * 8, 0), "sessions": len(items)}


@app.post("/sessions")
async def create_session(payload: SessionCreate) -> dict[str, Any]:
    return add_session(payload.model_dump())


@app.get("/sessions")
async def list_sessions() -> list[dict[str, Any]]:
    return sessions()


@app.get("/footprint/summary")
async def footprint() -> dict[str, Any]:
    items = sessions()
    return impact_summary(items) | {"recent": items[:8]}


@app.get("/profile")
async def profile() -> dict[str, Any]:
    return get_profile() | {"analytics": await footprint()}


@app.put("/profile")
async def update_profile(payload: dict[str, Any]) -> dict[str, Any]:
    current = get_profile()
    current.update(payload)
    save_profile(current)
    return await profile()


@app.post("/chat")
async def chat(payload: ChatRequest) -> dict[str, Any]:
    key = os.getenv("GROQ_API_KEY")
    if key:
        try:
            system = "You are GRIഢം, a concise grid-aware EV charging assistant for Kochi. Ground answers in the supplied JSON context. Optional final line may be ACTION: JSON with select_station, set_mode, or open."
            body = {"model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"), "messages": [{"role": "system", "content": system + "\nContext: " + json.dumps(payload.context)[:6000]}, {"role": "user", "content": payload.message}], "temperature": .3}
            async with httpx.AsyncClient(timeout=12) as client:
                response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json=body)
                response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
            action = None
            if "ACTION:" in text:
                text, raw = text.rsplit("ACTION:", 1)
                action = json.loads(raw.strip())
            return {"reply": text.strip(), "action": action, "source": "groq"}
        except Exception:
            pass
    best = (payload.context.get("stations") or [{}])[0]
    return {"reply": f"The best current pick is {best.get('name', 'the top-ranked charger')} with {best.get('carbon_intensity_gco2_kwh', 'modelled')} gCO2/kWh. Midday and late night usually beat Kochi's evening peak.", "action": None, "source": "fallback"}


@app.get("/operator/summary")
async def operator_summary() -> dict[str, Any]:
    stations_ranked = rank(partner_stations() + read_community(), KOCHI["lat"], KOCHI["lng"], "balanced")
    now = datetime.now(timezone.utc).astimezone()
    curve = [{"hour": (now + timedelta(hours=index)).hour, "load": synthetic_grid("operator-network", now + timedelta(hours=index))["grid_load_pct"], "carbon": synthetic_grid("operator-network", now + timedelta(hours=index))["carbon_intensity_gco2_kwh"], "price": tou_price((now + timedelta(hours=index)).hour)} for index in range(24)]
    by_operator: dict[str, int] = {}
    for item in stations_ranked:
        by_operator[item["operator"]] = by_operator.get(item["operator"], 0) + 1
    return {"carbon_source": CARBON_CACHE["source"], "network_load_pct": round(curve[0]["load"], 1), "station_count": len(stations_ranked), "available_plugs": sum(item.get("available", 0) for item in stations_ranked), "curve": curve, "stations": stations_ranked, "by_operator": by_operator}


@app.get("/map-style")
async def map_style() -> dict[str, Any]:
    return await config()
