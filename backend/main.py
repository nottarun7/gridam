import asyncio
import hashlib
import json
import math
import os
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

KOCHI = {"lat": 9.9312, "lng": 76.2673}
DB_PATH = Path(os.getenv("GRIDAM_DB_PATH", ROOT / "data" / "gridam.db"))
EM_ZONE = os.getenv("EM_ZONE", "IN-SO")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
CARBON_CACHE: dict[str, Any] = {"source": "kerala-model", "carbon": None, "renewable": None, "forecast": []}

app = FastAPI(title="GRIഢം API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ScoreRequest(BaseModel):
    stations: list[dict[str, Any]]
    lat: float = KOCHI["lat"]
    lng: float = KOCHI["lng"]
    mode: str = "balanced"


class RouteRequest(BaseModel):
    start: dict[str, float]
    end: dict[str, float]


class StationCreate(BaseModel):
    name: str
    lat: float
    lng: float
    operator: str = "Community"
    connector: str = "Type 2"
    power_kw: float = 22


class SessionCreate(BaseModel):
    station_id: str
    station_name: str = "Selected charger"
    kwh: float = 18
    carbon_intensity: float = 520
    cost_inr: float = 144


class ChatRequest(BaseModel):
    message: str
    context: dict[str, Any] = {}


def db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.execute("create table if not exists stations (id text primary key, payload text not null)")
        conn.execute("create table if not exists sessions (id integer primary key autoincrement, payload text not null, created_at text not null)")
        conn.execute("create table if not exists settings (id integer primary key check (id=1), payload text not null)")
        if not conn.execute("select count(*) from stations").fetchone()[0]:
            for station in community_seed():
                conn.execute("insert into stations values (?, ?)", (station["id"], json.dumps(station)))
        if not conn.execute("select count(*) from sessions").fetchone()[0]:
            rng = random.Random(42)
            stations = partner_stations()[:5]
            for idx in range(24):
                when = datetime.now(timezone.utc) - timedelta(days=rng.randint(1, 42), hours=rng.randint(0, 23))
                kwh = round(rng.uniform(8, 38), 1)
                carbon = grid_state(stations[idx % len(stations)]["id"], when)["carbon_intensity_gco2_kwh"]
                payload = {
                    "station_id": stations[idx % len(stations)]["id"],
                    "station_name": stations[idx % len(stations)]["name"],
                    "kwh": kwh,
                    "carbon_intensity": carbon,
                    "cost_inr": round(kwh * tou_price(when.hour), 0),
                }
                conn.execute("insert into sessions (payload, created_at) values (?, ?)", (json.dumps(payload), when.isoformat()))
        if not conn.execute("select count(*) from settings").fetchone()[0]:
            profile = {"name": "Kochi driver", "vehicle": "Tata Nexon EV", "battery_kwh": 40.5, "efficiency_km_kwh": 6.5}
            conn.execute("insert into settings values (1, ?)", (json.dumps(profile),))


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def haversine(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    radius = 6371
    d_lat = math.radians(b_lat - a_lat)
    d_lng = math.radians(b_lng - a_lng)
    x = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * math.sin(d_lng / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(x), math.sqrt(1 - x))


def tou_price(hour: int | float) -> float:
    if hour >= 22 or hour < 6:
        return 6
    if 10 <= hour < 16:
        return 6.5
    if 18 <= hour < 22:
        return 11
    return 8


def synthetic_grid(station_id: str, when: datetime | None = None) -> dict[str, Any]:
    now = when or datetime.now(timezone.utc).astimezone()
    hour = now.hour + now.minute / 60
    solar = math.exp(-((hour - 12.5) ** 2) / 8)
    evening = math.exp(-((hour - 20.5) ** 2) / 6.5)
    morning = math.exp(-((hour - 10) ** 2) / 7)
    load = clamp(35 + 58 * evening + 18 * morning, 15, 98)
    renewable = clamp(12 + 60 * solar - 22 * evening, 3, 90)
    digest = hashlib.md5(station_id.encode()).hexdigest()
    clean_char = (int(digest[:2], 16) / 127.5) - 1
    load_char = (int(digest[2:4], 16) / 127.5) - 1
    phase = int(digest[4:6], 16) / 255 * math.pi
    wobble = math.sin(now.timestamp() / 780 + phase) + 0.5 * math.sin(now.timestamp() / 300 + phase)
    load = clamp(load + load_char * 10 + wobble * 4, 8, 99)
    renewable = clamp(renewable + clean_char * 15 + wobble * 3, 2, 94)
    carbon = clamp(820 - 5.5 * renewable + 0.4 * (load - 50), 240, 820)
    return {"grid_load_pct": round(load, 1), "renewable_share_pct": round(renewable, 1), "carbon_intensity_gco2_kwh": round(carbon, 0)}


def grid_state(station_id: str, when: datetime | None = None) -> dict[str, Any]:
    model = synthetic_grid(station_id, when)
    if CARBON_CACHE.get("source") == "electricitymaps" and CARBON_CACHE.get("carbon"):
        anchor_now = synthetic_grid(station_id)
        model["carbon_intensity_gco2_kwh"] = round(clamp(model["carbon_intensity_gco2_kwh"] + CARBON_CACHE["carbon"] - anchor_now["carbon_intensity_gco2_kwh"], 180, 920), 0)
        if CARBON_CACHE.get("renewable") is not None:
            model["renewable_share_pct"] = round(clamp(model["renewable_share_pct"] + CARBON_CACHE["renewable"] - anchor_now["renewable_share_pct"], 0, 100), 1)
        source = "electricitymaps"
    else:
        source = "kerala-model"
    model["source"] = source
    model["updated_at"] = datetime.now(timezone.utc).isoformat()
    return model


async def refresh_electricity_maps() -> None:
    key = os.getenv("EM_API_KEY")
    if not key:
        CARBON_CACHE.update({"source": "kerala-model", "carbon": None, "renewable": None, "forecast": []})
        return
    headers = {"auth-token": key}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            carbon_req = client.get(f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={EM_ZONE}", headers=headers)
            power_req = client.get(f"https://api.electricitymap.org/v3/power-breakdown/latest?zone={EM_ZONE}", headers=headers)
            forecast_req = client.get(f"https://api.electricitymap.org/v3/carbon-intensity/forecast?zone={EM_ZONE}", headers=headers)
            carbon_res, power_res, forecast_res = await asyncio.gather(carbon_req, power_req, forecast_req, return_exceptions=True)
        carbon = carbon_res.json().get("carbonIntensity") if not isinstance(carbon_res, Exception) and carbon_res.status_code < 400 else None
        renewable = power_res.json().get("renewablePercentage") if not isinstance(power_res, Exception) and power_res.status_code < 400 else None
        forecast = forecast_res.json().get("forecast", []) if not isinstance(forecast_res, Exception) and forecast_res.status_code < 400 else []
        if carbon:
            CARBON_CACHE.update({"source": "electricitymaps", "carbon": carbon, "renewable": renewable, "forecast": forecast})
        else:
            CARBON_CACHE.update({"source": "kerala-model", "carbon": None, "renewable": None, "forecast": []})
    except Exception:
        CARBON_CACHE.update({"source": "kerala-model", "carbon": None, "renewable": None, "forecast": []})


async def carbon_loop() -> None:
    while True:
        await refresh_electricity_maps()
        await asyncio.sleep(600)


@app.on_event("startup")
async def startup() -> None:
    init_db()
    await refresh_electricity_maps()
    asyncio.create_task(carbon_loop())


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


def station(id_: str, name: str, lat: float, lng: float, operator: str, connector: str, power: float, plugs: int) -> dict[str, Any]:
    return {"id": id_, "name": name, "lat": lat, "lng": lng, "operator": operator, "connector": connector, "power_kw": power, "plugs": plugs, "available": max(1, plugs - (len(id_) % 2)), "source": "partner"}


def community_seed() -> list[dict[str, Any]]:
    return [
        station("community-infopark", "Community Charger - Infopark Gate", 10.0139, 76.3627, "Community", "Type 2", 11, 1),
        station("community-thevara", "Community Charger - Thevara", 9.9351, 76.2996, "Community", "Bharat AC001", 7.4, 1),
        station("community-kalamassery", "Community Charger - Kalamassery", 10.0526, 76.3341, "Community", "Type 2", 22, 2),
    ]


def read_community() -> list[dict[str, Any]]:
    try:
        with db() as conn:
            return [json.loads(row["payload"]) for row in conn.execute("select payload from stations")]
    except sqlite3.OperationalError:
        init_db()
        with db() as conn:
            return [json.loads(row["payload"]) for row in conn.execute("select payload from stations")]


async def open_charge_map(lat: float, lng: float, distance: float) -> list[dict[str, Any]]:
    key = os.getenv("OPENCHARGEMAP_API_KEY")
    if not key:
        return []
    try:
        params = {"output": "json", "latitude": lat, "longitude": lng, "distance": distance, "distanceunit": "KM", "maxresults": 50}
        async with httpx.AsyncClient(timeout=8) as client:
            res = await client.get("https://api.openchargemap.io/v3/poi/", params=params, headers={"X-API-Key": key})
            res.raise_for_status()
        stations = []
        for item in res.json():
            connections = item.get("Connections") or []
            power = max([c.get("PowerKW") or 0 for c in connections] or [7.4])
            connector = connections[0].get("ConnectionType", {}).get("Title", "EV connector") if connections else "EV connector"
            addr = item.get("AddressInfo") or {}
            stations.append(station(f"ocm-{item.get('ID')}", item.get("Title") or addr.get("Title") or "Open Charge Map station", addr.get("Latitude"), addr.get("Longitude"), item.get("OperatorInfo", {}).get("Title", "Open Charge Map"), connector, power or 7.4, len(connections) or 1) | {"source": "openchargemap"})
        return [s for s in stations if s.get("lat") and s.get("lng")]
    except Exception:
        return []


def enrich(stations: list[dict[str, Any]], lat: float, lng: float) -> list[dict[str, Any]]:
    result = []
    for item in stations:
        grid = grid_state(item["id"])
        merged = item | grid
        merged["distance_km"] = round(haversine(lat, lng, item["lat"], item["lng"]), 2)
        result.append(merged)
    return result


def rank(stations: list[dict[str, Any]], lat: float, lng: float, mode: str) -> list[dict[str, Any]]:
    if not stations:
        return []
    weights = {
        "fastest": {"prox": .55, "grid": .15, "carbon": .10, "avail": .20},
        "greenest": {"prox": .15, "grid": .30, "carbon": .45, "avail": .10},
        "balanced": {"prox": .30, "grid": .25, "carbon": .30, "avail": .15},
    }.get(mode, {"prox": .30, "grid": .25, "carbon": .30, "avail": .15})
    enriched = enrich(stations, lat, lng)
    max_dist = max(s["distance_km"] for s in enriched) or 1
    for s in enriched:
        prox = 1 - s["distance_km"] / max_dist
        grid = 1 - s["grid_load_pct"] / 100
        carbon = 1 - (s["carbon_intensity_gco2_kwh"] - 180) / 740
        avail = s.get("available", 0) / max(s.get("plugs", 1), 1)
        s["score"] = round(100 * (weights["prox"] * prox + weights["grid"] * grid + weights["carbon"] * carbon + weights["avail"] * avail), 1)
    return sorted(enriched, key=lambda x: x["score"], reverse=True)


async def all_stations(lat: float, lng: float, distance: float) -> list[dict[str, Any]]:
    combined = partner_stations() + read_community() + await open_charge_map(lat, lng, distance)
    by_id = {item["id"]: item for item in combined if haversine(lat, lng, item["lat"], item["lng"]) <= distance}
    return list(by_id.values())


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "service": "gridam", "carbon_source": CARBON_CACHE["source"], "zone": EM_ZONE}


@app.get("/config")
async def config() -> dict[str, Any]:
    key = os.getenv("MAPTILER_API_KEY")
    style = f"https://api.maptiler.com/maps/streets-v2-dark/style.json?key={key}" if key else "https://demotiles.maplibre.org/style.json"
    return {"center": KOCHI, "map_style_url": style, "carbon_source": CARBON_CACHE["source"], "zone": EM_ZONE}


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
    with db() as conn:
        conn.execute("insert or replace into stations values (?, ?)", (item["id"], json.dumps(item)))
    return item


@app.get("/grid/{station_id}")
async def grid(station_id: str) -> dict[str, Any]:
    return grid_state(station_id)


@app.post("/grid/batch")
async def grid_batch(payload: dict[str, list[str]]) -> dict[str, Any]:
    return {id_: grid_state(id_) for id_ in payload.get("station_ids", [])}


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
                res = await client.post("https://api.openrouteservice.org/v2/directions/driving-car/geojson", json=body, headers={"Authorization": key})
                res.raise_for_status()
            data = res.json()
            feature = data["features"][0]
            return {"source": "openrouteservice", "geometry": feature["geometry"], "summary": feature["properties"].get("summary", {}), "steps": feature["properties"].get("segments", [{}])[0].get("steps", [])}
        except Exception:
            pass
    distance = haversine(payload.start["lat"], payload.start["lng"], payload.end["lat"], payload.end["lng"])
    return {"source": "fallback", "geometry": {"type": "LineString", "coordinates": [[payload.start["lng"], payload.start["lat"]], [payload.end["lng"], payload.end["lat"]]]}, "summary": {"distance": distance * 1000, "duration": distance / 35 * 3600}, "steps": [{"instruction": "Follow local roads toward the selected charger.", "distance": distance * 1000}]}


@app.get("/geocode")
async def geocode(q: str) -> list[dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=8, headers={"User-Agent": "GRIDAM/1.0"}) as client:
            res = await client.get("https://nominatim.openstreetmap.org/search", params={"q": q, "format": "json", "limit": 5, "countrycodes": "in"})
            res.raise_for_status()
        return [{"name": item.get("name") or item.get("display_name", "").split(",")[0], "full_name": item.get("display_name"), "lat": float(item["lat"]), "lng": float(item["lon"])} for item in res.json()]
    except Exception:
        return [{"name": "Kochi", "full_name": "Kochi, Kerala, India", "lat": KOCHI["lat"], "lng": KOCHI["lng"]}]


@app.get("/forecast")
async def forecast(station_id: str = "partner-kseb-mgroad", charge_hours: float = 2.5) -> dict[str, Any]:
    now = datetime.now(timezone.utc).astimezone()
    points = []
    for idx in range(24):
        when = now + timedelta(hours=idx)
        carbon = grid_state(station_id, when)["carbon_intensity_gco2_kwh"]
        if CARBON_CACHE["source"] == "electricitymaps" and idx < len(CARBON_CACHE.get("forecast", [])):
            carbon = CARBON_CACHE["forecast"][idx].get("carbonIntensity", carbon)
        price = tou_price(when.hour)
        points.append({"time": when.isoformat(), "hour": when.hour, "carbon": carbon, "price": price, "load": grid_state(station_id, when)["grid_load_pct"]})
    min_c, max_c = min(p["carbon"] for p in points), max(p["carbon"] for p in points)
    min_p, max_p = min(p["price"] for p in points), max(p["price"] for p in points)
    for p in points:
        c_norm = (p["carbon"] - min_c) / max(max_c - min_c, 1)
        p_norm = (p["price"] - min_p) / max(max_p - min_p, 1)
        p["recommendation_score"] = round(0.6 * c_norm + 0.4 * p_norm, 3)
    greenest = min(points, key=lambda p: p["carbon"])
    cheapest = min(points, key=lambda p: p["price"])
    recommended = min(points, key=lambda p: p["recommendation_score"])
    return {"source": CARBON_CACHE["source"], "charge_hours": charge_hours, "points": points, "greenest": greenest, "cheapest": cheapest, "recommended": recommended}


@app.get("/recycling")
async def recycling() -> list[dict[str, Any]]:
    return [
        {"name": "Kochi E-Waste Collection Centre", "lat": 9.9835, "lng": 76.2999, "type": "e-waste"},
        {"name": "Clean Kerala Company Hub", "lat": 10.0150, "lng": 76.3410, "type": "battery and e-waste"},
        {"name": "Kalamassery Recycling Point", "lat": 10.0521, "lng": 76.3330, "type": "li-ion intake"},
        {"name": "Fort Kochi Civic Collection", "lat": 9.9650, "lng": 76.2440, "type": "e-waste"},
        {"name": "Aluva Second Life Partner", "lat": 10.1080, "lng": 76.3510, "type": "battery second life"},
        {"name": "Vyttila Mobility Hub Collection", "lat": 9.9680, "lng": 76.3180, "type": "e-waste"},
    ]


@app.post("/sessions")
async def add_session(payload: SessionCreate) -> dict[str, Any]:
    item = payload.model_dump()
    with db() as conn:
        cur = conn.execute("insert into sessions (payload, created_at) values (?, ?)", (json.dumps(item), datetime.now(timezone.utc).isoformat()))
        item["id"] = cur.lastrowid
    return item


@app.get("/sessions")
async def sessions() -> list[dict[str, Any]]:
    try:
        with db() as conn:
            rows = conn.execute("select id, payload, created_at from sessions order by created_at desc").fetchall()
    except sqlite3.OperationalError:
        init_db()
        with db() as conn:
            rows = conn.execute("select id, payload, created_at from sessions order by created_at desc").fetchall()
    return [json.loads(r["payload"]) | {"id": r["id"], "created_at": r["created_at"]} for r in rows]


def impact_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    total_kwh = sum(i.get("kwh", 0) for i in items)
    avg_carbon = sum(i.get("kwh", 0) * i.get("carbon_intensity", 520) for i in items) / max(total_kwh, 1)
    ev_km = total_kwh * 6.5
    session_co2 = total_kwh * avg_carbon / 1000
    petrol_co2 = ev_km * 140 / 1000
    money_saved = ev_km / 18 * 105 - total_kwh * 8
    return {"total_kwh": round(total_kwh, 1), "avg_carbon": round(avg_carbon, 0), "ev_km": round(ev_km, 0), "co2_emitted_kg": round(session_co2, 1), "co2_saved_kg": round(max(0, petrol_co2 - session_co2), 1), "money_saved_inr": round(money_saved, 0), "sessions": len(items)}


@app.get("/footprint/summary")
async def footprint() -> dict[str, Any]:
    items = await sessions()
    return impact_summary(items) | {"recent": items[:8]}


@app.get("/profile")
async def profile() -> dict[str, Any]:
    try:
        with db() as conn:
            row = conn.execute("select payload from settings where id=1").fetchone()
    except sqlite3.OperationalError:
        init_db()
        with db() as conn:
            row = conn.execute("select payload from settings where id=1").fetchone()
    return json.loads(row["payload"]) | {"analytics": await footprint()}


@app.put("/profile")
async def update_profile(payload: dict[str, Any]) -> dict[str, Any]:
    current = await profile()
    current.update(payload)
    current.pop("analytics", None)
    with db() as conn:
        conn.execute("insert or replace into settings values (1, ?)", (json.dumps(current),))
    return await profile()


@app.post("/chat")
async def chat(payload: ChatRequest) -> dict[str, Any]:
    key = os.getenv("GROQ_API_KEY")
    context = payload.context
    if key:
        try:
            system = "You are GRIഢം, a concise grid-aware EV charging assistant for Kochi. Ground answers in the supplied JSON context. Optional final line may be ACTION: JSON with select_station, set_mode, or open."
            body = {"model": GROQ_MODEL, "messages": [{"role": "system", "content": system + "\nContext: " + json.dumps(context)[:6000]}, {"role": "user", "content": payload.message}], "temperature": 0.3}
            async with httpx.AsyncClient(timeout=12) as client:
                res = await client.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json=body)
                res.raise_for_status()
            text = res.json()["choices"][0]["message"]["content"]
            action = None
            if "ACTION:" in text:
                text, raw = text.rsplit("ACTION:", 1)
                action = json.loads(raw.strip())
            return {"reply": text.strip(), "action": action, "source": "groq"}
        except Exception:
            pass
    best = (context.get("stations") or [{}])[0]
    reply = f"The best current pick is {best.get('name', 'the top-ranked charger')} with {best.get('carbon_intensity_gco2_kwh', 'modelled')} gCO2/kWh. Midday and late night usually beat Kochi's evening peak."
    return {"reply": reply, "action": None, "source": "fallback"}


@app.get("/operator/summary")
async def operator_summary() -> dict[str, Any]:
    stations_ranked = rank(partner_stations() + read_community(), KOCHI["lat"], KOCHI["lng"], "balanced")
    curve = []
    now = datetime.now(timezone.utc).astimezone()
    for idx in range(24):
        when = now + timedelta(hours=idx)
        grid = synthetic_grid("operator-network", when)
        curve.append({"hour": when.hour, "load": grid["grid_load_pct"], "carbon": grid["carbon_intensity_gco2_kwh"], "price": tou_price(when.hour)})
    by_operator: dict[str, int] = {}
    for s in stations_ranked:
        by_operator[s["operator"]] = by_operator.get(s["operator"], 0) + 1
    return {"carbon_source": CARBON_CACHE["source"], "network_load_pct": round(sum(p["load"] for p in curve[:1]), 1), "station_count": len(stations_ranked), "available_plugs": sum(s.get("available", 0) for s in stations_ranked), "curve": curve, "stations": stations_ranked, "by_operator": by_operator}


@app.get("/map-style")
async def map_style() -> dict[str, Any]:
    return await config()
