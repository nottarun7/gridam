"""GRIഢം backend — EV charging + synthetic grid/carbon + carbon dashboard.

Run:  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

from datetime import datetime

from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import store
from config import (DEFAULT_RADIUS_KM, KOCHI_LAT, KOCHI_LNG, MAPTILER_API_KEY,
                    TREE_KG_CO2_PER_YEAR)
import asyncio

import electricitymap as em
from chat import build_system, chat_complete, parse_action
from grid import grid_state
from nominatim import geocode as nominatim_geocode
from ocm import nearby
from ors import route as ors_route
from partner_stations import PARTNER_STATIONS
from recycling_centers import RECYCLING_CENTERS
from scoring import haversine_km, rank
from schemas import (ChatRequest, GridBatchRequest, ProfileIn, RouteRequest,
                     ScoreRequest, SessionIn, StationIn)

app = FastAPI(title="GRIDAM Backend", version="0.1.0")

# Allow the Android app (any origin on the LAN) to call us during the demo.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
async def _startup() -> None:
    store.init_db()
    try:
        await em.refresh()                  # first real carbon pull
    except Exception:
        pass
    async def _loop():
        while True:
            await asyncio.sleep(600)        # refresh every 10 min
            try:
                await em.refresh()
            except Exception:
                pass
    asyncio.create_task(_loop())


@app.get("/health")
def health() -> dict:
    return {
        "app": "GRIDAM backend",
        "status": "ok",
        "region": "Kochi, Kerala",
        "center": {"lat": KOCHI_LAT, "lng": KOCHI_LNG},
        "maptiler_key_loaded": bool(MAPTILER_API_KEY),
        "carbon_source": "electricitymaps" if em.snapshot().get("ok") else "model",
        "electricitymap": {k: em.snapshot().get(k) for k in ("ok", "carbon", "renewable", "datetime", "error")},
    }


# ----------------------------- charging map -------------------------------
@app.get("/charging-stations")
async def charging_stations(
    lat: float = Query(KOCHI_LAT),
    lng: float = Query(KOCHI_LNG),
    distance: float = Query(DEFAULT_RADIUS_KM),
) -> dict:
    """Real OCM stations + community stations, each enriched with grid state."""
    try:
        ocm_stations = await nearby(lat, lng, distance)
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"Open Charge Map error: {e.response.status_code}")
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Open Charge Map unreachable: {e}")

    community = [
        {
            "station_id": f"community-{s['id']}",
            "name": s["name"],
            "lat": s["lat"],
            "lng": s["lng"],
            "connectors": [s["connector"]] if s.get("connector") else [],
            "power_kw": 50.0,
            "operator": "Community",
            "source": "community",
        }
        for s in store.list_stations()
    ]

    # Partner networks (ChargeMOD, Zeon, Tata, …) + community, filtered to the
    # requested radius so far-away ones don't appear when searching elsewhere.
    extra = [
        s for s in ([dict(p) for p in PARTNER_STATIONS] + community)
        if haversine_km(lat, lng, s["lat"], s["lng"]) <= distance
    ]

    all_stations = ocm_stations + extra
    for s in all_stations:
        gs = grid_state(s["station_id"])
        s["grid_load_pct"] = gs["grid_load_pct"]
        s["carbon_intensity_gco2_kwh"] = gs["carbon_intensity_gco2_kwh"]
        s["renewable_share_pct"] = gs["renewable_share_pct"]

    return {"count": len(all_stations), "stations": all_stations}


# --------------------------- community stations ---------------------------
@app.get("/stations")
def get_stations() -> dict:
    return {"stations": store.list_stations()}


@app.post("/stations", status_code=201)
def create_station(payload: StationIn) -> dict:
    return store.add_station(payload.name, payload.lat, payload.lng, payload.connector)


# ------------------------------ grid state --------------------------------
@app.get("/grid/{station_id}")
def grid(station_id: str) -> dict:
    return grid_state(station_id)


@app.post("/grid/batch")
def grid_batch(req: GridBatchRequest) -> dict:
    """Current (live) grid state for many stations — polled by the frontend."""
    return {"grid": [grid_state(sid) for sid in req.station_ids]}


def _tou_price(hour: int) -> float:
    """Time-of-use tariff (₹/kWh): cheap overnight + solar midday, dear at peak."""
    if hour >= 22 or hour < 6:
        return 6.0            # off-peak night
    if 10 <= hour < 16:
        return 6.5            # solar daytime
    if 18 <= hour < 22:
        return 11.0           # evening peak
    return 8.0               # shoulder


@app.get("/forecast")
def forecast(station_id: str = "ocm-1", hours: int = 24, charge_hours: int = 2) -> dict:
    """24h grid-carbon + price forecast and the best window to 'charge right'."""
    from datetime import timedelta
    now = datetime.now().replace(minute=0, second=0, microsecond=0)

    # Real Electricity Maps forecast (carbon per hour), keyed by hour, if available.
    em_fc = {}
    for row in (em.snapshot().get("forecast") or []):
        ci = row.get("carbonIntensity")
        dt = row.get("datetime", "")
        try:
            hh = int(dt[11:13])
            if ci is not None and hh not in em_fc:
                em_fc[hh] = ci
        except (ValueError, IndexError):
            pass
    source = "electricitymaps" if em_fc else ("electricitymaps" if em.snapshot().get("ok") else "model")

    pts = []
    for h in range(hours):
        t = now + timedelta(hours=h)
        gs = grid_state(station_id, t)
        carbon = em_fc.get(t.hour, gs["carbon_intensity_gco2_kwh"])  # real forecast when present
        pts.append({
            "hour": t.hour, "iso": t.isoformat(timespec="minutes"),
            "carbon": round(carbon, 1), "load": gs["grid_load_pct"],
            "renewable": gs["renewable_share_pct"], "price": _tou_price(t.hour),
        })

    carbons = [p["carbon"] for p in pts]
    prices = [p["price"] for p in pts]
    cmin, cmax = min(carbons), max(carbons)
    pmin, pmax = min(prices), max(prices)

    def norm(v, lo, hi):
        return 0.0 if hi - lo < 1e-9 else (v - lo) / (hi - lo)

    charge_hours = max(1, min(charge_hours, hours))
    best = None
    for i in range(len(pts) - charge_hours + 1):
        window = pts[i:i + charge_hours]
        cost = sum(0.6 * norm(w["carbon"], cmin, cmax) + 0.4 * norm(w["price"], pmin, pmax)
                   for w in window) / charge_hours
        if best is None or cost < best[0]:
            best = (cost, i)

    gi = min(range(len(pts)), key=lambda i: pts[i]["carbon"])
    pi = min(range(len(pts)), key=lambda i: pts[i]["price"])
    ri = best[1]
    return {
        "points": pts,
        "source": source,
        "greenest": {"hour": pts[gi]["hour"], "carbon": pts[gi]["carbon"]},
        "cheapest": {"hour": pts[pi]["hour"], "price": pts[pi]["price"]},
        "recommended": {
            "start_hour": pts[ri]["hour"], "iso": pts[ri]["iso"], "hours": charge_hours,
            "carbon": pts[ri]["carbon"], "price": pts[ri]["price"],
        },
    }


@app.get("/recycling")
def recycling() -> dict:
    """Curated Kochi li-ion recycling / e-waste / second-life centers."""
    return {"centers": RECYCLING_CENTERS}


@app.post("/chat")
async def chat(req: ChatRequest) -> dict:
    """Grounded assistant: injects live app context, calls Groq, returns reply + optional action."""
    ctx = req.context or {}
    sid = (ctx.get("best") or {}).get("station_id") or "ocm-1"
    try:
        rec = forecast(station_id=sid)["recommended"]
    except Exception:
        rec = None
    system = build_system(ctx, rec)
    msgs = [{"role": "system", "content": system}] + [{"role": m.role, "content": m.content} for m in req.messages]
    try:
        content = await chat_complete(msgs)
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"Assistant error: {e.response.status_code}")
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Assistant unreachable: {e}")
    action, text = parse_action(content)
    return {"reply": text, "action": action}


@app.get("/operator/summary")
def operator_summary() -> dict:
    """Aggregate network view for a charging operator / fleet: load, carbon, demand-response."""
    from datetime import timedelta
    stns = [dict(p) for p in PARTNER_STATIONS]
    for s in store.list_stations():
        stns.append({"station_id": f"community-{s['id']}", "name": s["name"], "operator": "Community"})

    rows = []
    for s in stns:
        gs = grid_state(s["station_id"])
        load, carbon = gs["grid_load_pct"], gs["carbon_intensity_gco2_kwh"]
        status = "busy" if load > 70 else "moderate" if load > 45 else "free"
        rows.append({"name": s["name"], "operator": s.get("operator", "—"),
                     "load": round(load), "carbon": round(carbon), "status": status})

    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    hourly = []
    for h in range(24):
        t = now + timedelta(hours=h)
        states = [grid_state(s["station_id"], t) for s in stns]
        hourly.append({
            "hour": t.hour,
            "load": round(sum(x["grid_load_pct"] for x in states) / len(states), 1),
            "carbon": round(sum(x["carbon_intensity_gco2_kwh"] for x in states) / len(states)),
            "price": _tou_price(t.hour),
        })
    peak = max(hourly, key=lambda x: x["load"])
    off = min(hourly, key=lambda x: x["load"])

    ops: dict[str, int] = {}
    for r in rows:
        ops[r["operator"]] = ops.get(r["operator"], 0) + 1

    return {
        "network": {
            "stations": len(rows), "operators": len(ops),
            "avg_load": round(sum(r["load"] for r in rows) / len(rows), 1),
            "avg_carbon": round(sum(r["carbon"] for r in rows) / len(rows)),
            "peak_hour": peak["hour"], "offpeak_hour": off["hour"],
            "busy": sum(1 for r in rows if r["status"] == "busy"),
        },
        "hourly": hourly,
        "stations": sorted(rows, key=lambda r: -r["load"]),
        "by_operator": [{"operator": k, "count": v} for k, v in sorted(ops.items())],
    }


def _build_profile() -> dict:
    """Vehicle settings + full analytics for the profile page."""
    s = store.get_settings()
    sessions = store.list_sessions()
    n = len(sessions)
    total_kwh = sum(x["kwh"] for x in sessions)
    total_co2 = sum(x["session_co2_kg"] for x in sessions)
    total_saved = sum(x["co2_saved_kg"] for x in sessions)
    clean_kwh = sum(x["kwh"] for x in sessions if x["carbon_intensity_gco2_kwh"] < 600)
    clean_pct = (clean_kwh / total_kwh * 100) if total_kwh else 0.0

    km_driven = total_kwh * s["efficiency_km_kwh"]
    petrol_litres = km_driven / s["mileage_kmpl"] if s["mileage_kmpl"] else 0
    petrol_cost = petrol_litres * s["petrol_price"]
    energy_cost = total_kwh * s["tariff"]
    money_saved = petrol_cost - energy_cost

    # per-day aggregation + cumulative saved
    by_date: dict[str, dict] = {}
    for x in sessions:
        d = x["created_at"][:10]
        e = by_date.setdefault(d, {"date": d, "kwh": 0.0, "co2_kg": 0.0, "saved_kg": 0.0})
        e["kwh"] += x["kwh"]; e["co2_kg"] += x["session_co2_kg"]; e["saved_kg"] += x["co2_saved_kg"]
    daily = sorted(by_date.values(), key=lambda e: e["date"])
    cum = 0.0
    cumulative = []
    for e in daily:
        cum += e["saved_kg"]
        cumulative.append({"date": e["date"], "kg": round(cum, 1)})

    # energy cleanliness mix
    mix = {"clean": 0.0, "mixed": 0.0, "dirty": 0.0}
    for x in sessions:
        c = x["carbon_intensity_gco2_kwh"]
        key = "clean" if c < 550 else "mixed" if c < 720 else "dirty"
        mix[key] += x["kwh"]

    counts: dict[str, int] = {}
    for x in sessions:
        counts[x["station_name"]] = counts.get(x["station_name"], 0) + 1
    most_used = max(counts, key=counts.get) if counts else "—"
    cleanest = min(sessions, key=lambda x: x["carbon_intensity_gco2_kwh"], default=None)

    return {
        "profile": s,
        "stats": {
            "sessions": n,
            "kwh_charged": round(total_kwh, 1),
            "co2_emitted_kg": round(total_co2, 1),
            "co2_saved_kg": round(total_saved, 1),
            "clean_charging_pct": round(clean_pct, 1),
            "km_driven": round(km_driven, 0),
            "petrol_cost_avoided_inr": round(petrol_cost, 0),
            "energy_cost_inr": round(energy_cost, 0),
            "money_saved_inr": round(max(0.0, money_saved), 0),
            "avg_co2_per_charge_kg": round(total_co2 / n, 1) if n else 0,
            "avg_kwh_per_charge": round(total_kwh / n, 1) if n else 0,
            "days_active": len(by_date),
            "cleanest_charge_gco2": round(cleanest["carbon_intensity_gco2_kwh"], 0) if cleanest else 0,
            "most_used_station": most_used,
            "trees_planted": round(total_saved / TREE_KG_CO2_PER_YEAR, 1),
        },
        "series": {
            "daily": [{"date": e["date"], "kwh": round(e["kwh"], 1), "co2_kg": round(e["co2_kg"], 2), "saved_kg": round(e["saved_kg"], 2)} for e in daily],
            "cumulative_saved": cumulative,
            "energy_mix": {k: round(v, 1) for k, v in mix.items()},
        },
    }


@app.get("/profile")
def get_profile() -> dict:
    return _build_profile()


@app.put("/profile")
def put_profile(payload: ProfileIn) -> dict:
    store.save_settings(payload.model_dump(exclude_none=True))
    return _build_profile()


@app.get("/geocode")
async def geocode(q: str) -> dict:
    """Place-name search (Nominatim) for the search bar + location entry."""
    if not q or len(q) < 2:
        return {"results": []}
    try:
        return {"results": await nominatim_geocode(q)}
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Geocoding unavailable: {e}")


# ----------------------------- recommendation -----------------------------
@app.post("/score")
def score(req: ScoreRequest) -> dict:
    candidates = []
    for c in req.candidates:
        gs = grid_state(c.station_id)
        candidates.append({
            "station_id": c.station_id,
            "name": c.name,
            "lat": c.lat,
            "lng": c.lng,
            "availability": c.availability,
            "grid_load_pct": gs["grid_load_pct"],
            "carbon_intensity_gco2_kwh": gs["carbon_intensity_gco2_kwh"],
            "renewable_share_pct": gs["renewable_share_pct"],
        })
    ranked = rank(candidates, req.user_lat, req.user_lng, req.mode)
    return {
        "mode": req.mode,
        "best": ranked[0] if ranked else None,
        "ranked": ranked,
    }


# --------------------------- carbon dashboard -----------------------------
@app.post("/sessions", status_code=201)
def create_session(payload: SessionIn) -> dict:
    return store.log_session(payload.station_id, payload.station_name, payload.kwh)


@app.get("/sessions")
def get_sessions() -> dict:
    return {"sessions": store.list_sessions()}


@app.get("/footprint/summary")
def footprint_summary() -> dict:
    sessions = store.list_sessions()
    total_kwh = sum(s["kwh"] for s in sessions)
    total_co2 = sum(s["session_co2_kg"] for s in sessions)
    total_saved = sum(s["co2_saved_kg"] for s in sessions)

    # "Clean" = charged when carbon intensity was below 600 gCO2/kWh.
    clean_kwh = sum(s["kwh"] for s in sessions
                    if s["carbon_intensity_gco2_kwh"] < 600)
    clean_pct = (clean_kwh / total_kwh * 100) if total_kwh else 0.0

    series = [
        {
            "date": s["created_at"][:10],
            "kwh": s["kwh"],
            "co2_kg": s["session_co2_kg"],
            "saved_kg": s["co2_saved_kg"],
            "station": s["station_name"],
        }
        for s in sessions
    ]

    # --- extended stats (for the profile + impact pages) -------------------
    n = len(sessions)
    avg_co2 = (total_co2 / n) if n else 0.0
    cleanest = min(sessions, key=lambda s: s["carbon_intensity_gco2_kwh"], default=None)
    # most-used station
    counts: dict[str, int] = {}
    for s in sessions:
        counts[s["station_name"]] = counts.get(s["station_name"], 0) + 1
    most_used = max(counts, key=counts.get) if counts else "—"
    # money saved: petrol fuel cost avoided minus EV energy cost
    petrol_km = total_kwh * 6.5
    money_saved = petrol_km * 6.7 - total_kwh * 8.0   # ~₹6.7/km petrol vs ~₹8/kWh
    days_active = len({s["created_at"][:10] for s in sessions})

    extended = {
        "avg_co2_per_charge_kg": round(avg_co2, 1),
        "most_used_station": most_used,
        "cleanest_charge_gco2": round(cleanest["carbon_intensity_gco2_kwh"], 0) if cleanest else 0,
        "money_saved_inr": round(max(0.0, money_saved), 0),
        "days_active": days_active,
        "avg_kwh_per_charge": round((total_kwh / n), 1) if n else 0,
    }

    return {
        "totals": {
            "sessions": len(sessions),
            "kwh_charged": round(total_kwh, 1),
            "co2_emitted_kg": round(total_co2, 1),
            "co2_saved_vs_petrol_kg": round(total_saved, 1),
            "clean_charging_pct": round(clean_pct, 1),
        },
        "extended": extended,
        "equivalents": {
            "trees_planted": round(total_saved / TREE_KG_CO2_PER_YEAR, 1),
            "petrol_km_avoided": round(sum(s["kwh"] for s in sessions) * 6.5, 0),
        },
        "series": series,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


# ------------------------- map style (convenience) ------------------------
@app.get("/map-style")
def map_style() -> dict:
    """Returns a MapTiler style URL if a key is loaded, else MapLibre demo tiles.

    Handy so the app can fall back gracefully; the app can also read the key
    from BuildConfig directly.
    """
    if MAPTILER_API_KEY:
        return {
            "provider": "maptiler",
            "style_url": f"https://api.maptiler.com/maps/streets-v2-dark/style.json?key={MAPTILER_API_KEY}",
        }
    return {
        "provider": "maplibre-demo",
        "style_url": "https://demotiles.maplibre.org/style.json",
    }


@app.get("/config")
def config() -> dict:
    """Everything the web frontend needs to boot in one call."""
    style = map_style()
    return {
        "region": "Kochi, Kerala",
        "center": {"lat": KOCHI_LAT, "lng": KOCHI_LNG},
        "default_radius_km": DEFAULT_RADIUS_KM,
        "map_style_url": style["style_url"],
        "map_provider": style["provider"],
        "carbon_source": "electricitymaps" if em.snapshot().get("ok") else "model",
    }


@app.post("/route")
async def route(req: RouteRequest) -> dict:
    """Driving route + ETA from user to a station (proxied ORS, key stays server-side)."""
    try:
        return await ors_route(req.start_lat, req.start_lng, req.end_lat, req.end_lng)
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"OpenRouteService error: {e.response.status_code}")
    except httpx.HTTPError as e:
        raise HTTPException(502, f"OpenRouteService unreachable: {e}")


# --------------------------- serve the web app ----------------------------
# Mounted LAST so it doesn't shadow the API routes above. Serves ../web at "/"
# so the whole demo runs from a single `uvicorn` process.
_WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if _WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_WEB_DIR), html=True), name="web")
