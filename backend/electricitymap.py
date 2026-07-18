import asyncio
import hashlib
import math
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from config import CARBON_CACHE, EM_ZONE


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


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
        anchor = synthetic_grid(station_id)
        model["carbon_intensity_gco2_kwh"] = round(clamp(model["carbon_intensity_gco2_kwh"] + CARBON_CACHE["carbon"] - anchor["carbon_intensity_gco2_kwh"], 180, 920), 0)
        if CARBON_CACHE.get("renewable") is not None:
            model["renewable_share_pct"] = round(clamp(model["renewable_share_pct"] + CARBON_CACHE["renewable"] - anchor["renewable_share_pct"], 0, 100), 1)
        source = "electricitymaps"
    else:
        source = "kerala-model"
    model.update({"source": source, "updated_at": datetime.now(timezone.utc).isoformat()})
    return model


async def refresh_electricity_maps() -> None:
    key = os.getenv("EM_API_KEY")
    if not key:
        CARBON_CACHE.update({"source": "kerala-model", "carbon": None, "renewable": None, "forecast": []})
        return
    try:
        headers = {"auth-token": key}
        async with httpx.AsyncClient(timeout=8) as client:
            responses = await asyncio.gather(
                client.get(f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={EM_ZONE}", headers=headers),
                client.get(f"https://api.electricitymap.org/v3/power-breakdown/latest?zone={EM_ZONE}", headers=headers),
                client.get(f"https://api.electricitymap.org/v3/carbon-intensity/forecast?zone={EM_ZONE}", headers=headers),
                return_exceptions=True,
            )
        carbon_res, power_res, forecast_res = responses
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
