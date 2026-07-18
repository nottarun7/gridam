"""Electricity Maps client — REAL grid carbon intensity for Kerala (zone IN-SO).

Fetches live carbon intensity + renewable share (and a 24h forecast when the
plan allows) for the Southern India zone, caches it in memory, and exposes a
synchronous snapshot that grid.py reads. Refreshed by a background task in
main.py. If the API is unreachable / rate-limited / the zone is denied, the
snapshot stays empty and grid.py falls back to the calibrated synthetic model.
"""
from __future__ import annotations

import time

import httpx

from config import EM_API_KEY, EM_ZONE

BASE = "https://api.electricitymap.org/v3"

_state = {
    "carbon": None,        # gCO2eq/kWh (live)
    "renewable": None,     # %
    "datetime": None,      # ISO string of the live reading
    "forecast": None,      # list of {datetime, carbonIntensity} or None
    "ok": False,           # True if we have a usable live carbon value
    "ts": 0.0,             # unix time of last successful refresh
    "error": None,
}


async def refresh() -> dict:
    """Pull latest carbon + power breakdown (+ forecast) for the zone."""
    if not EM_API_KEY:
        _state["error"] = "no EM_API_KEY"
        return dict(_state)
    headers = {"auth-token": EM_API_KEY}
    params = {"zone": EM_ZONE}
    got_carbon = False
    # Broad guard: a refresh failure (network, proxy, bad zone, rate limit) must
    # NEVER crash the app — grid.py just falls back to the model.
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            try:
                r = await c.get(f"{BASE}/carbon-intensity/latest", params=params, headers=headers)
                if r.status_code == 200:
                    d = r.json()
                    _state["carbon"] = d.get("carbonIntensity")
                    _state["datetime"] = d.get("datetime")
                    got_carbon = _state["carbon"] is not None
                else:
                    _state["error"] = f"carbon {r.status_code}"
            except Exception as e:
                _state["error"] = f"carbon {e}"
            try:
                r = await c.get(f"{BASE}/power-breakdown/latest", params=params, headers=headers)
                if r.status_code == 200:
                    _state["renewable"] = r.json().get("renewablePercentage")
            except Exception:
                pass
            try:
                r = await c.get(f"{BASE}/carbon-intensity/forecast", params=params, headers=headers)
                if r.status_code == 200:
                    _state["forecast"] = r.json().get("forecast")
            except Exception:
                pass
    except Exception as e:
        _state["error"] = f"client {e}"
    _state["ok"] = got_carbon
    if got_carbon:
        _state["ts"] = time.time()
        _state["error"] = None
    return dict(_state)


def snapshot() -> dict:
    return dict(_state)
