"""Grounded assistant powered by Groq (OpenAI-compatible API).

The model never sees raw databases — the backend injects a compact, live
snapshot of what the user is looking at (nearby stations, the best pick, the
Charge Right window, the user's vehicle) into the system prompt. The model can
also request ONE ui action, which the frontend executes.
"""
from __future__ import annotations

import json
import re

import httpx

from config import GROQ_API_KEY, GROQ_MODEL

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

ALLOWED_ACTIONS = (
    'select_station (needs "id"), set_mode (needs "mode": greenest|fastest|balanced), '
    'open (needs "page": charge|impact|profile|operator)'
)


def build_system(ctx: dict, rec: dict | None) -> str:
    mode = ctx.get("mode", "greenest")
    profile = ctx.get("profile") or {}
    best = ctx.get("best") or {}
    stations = (ctx.get("stations") or [])[:8]

    lines = []
    lines.append(
        "You are the GRIഢം assistant — a friendly, concise EV-charging guide for Kochi, Kerala. "
        "GRIഢം helps drivers charge at the greenest and cheapest time and place. Use ₹ for money and "
        "metric units. Keep answers to 2–4 short sentences. Only use the data given below; if you don't "
        "have something, say so briefly."
    )
    lines.append(f"\nCurrent ranking mode: {mode}.")
    if profile:
        lines.append(
            f"User vehicle: {profile.get('vehicle','?')}, {profile.get('battery_kwh','?')} kWh battery, "
            f"{profile.get('efficiency_km_kwh','?')} km/kWh, tariff ₹{profile.get('tariff','?')}/kWh."
        )
    if best:
        lines.append(
            f"Best station right now ({mode}): {best.get('name')} — {best.get('distance_km','?')} km away, "
            f"{round(best.get('carbon_intensity_gco2_kwh',0))} gCO₂/kWh, grid load {round(best.get('grid_load_pct',0))}%."
        )
    if stations:
        lines.append("Nearby stations (id · name · km · gCO₂/kWh · load% · connectors · kW):")
        for s in stations:
            lines.append(
                f"  - {s.get('station_id')} · {s.get('name')} · {s.get('distance_km','?')} · "
                f"{round(s.get('carbon_intensity_gco2_kwh',0))} · {round(s.get('grid_load_pct',0))} · "
                f"{','.join(s.get('connectors') or [])} · {round(s.get('power_kw',0))}"
            )
    if rec:
        lines.append(
            f"Charge Right window (next 24h): best to charge around {rec['start_hour']}:00 for {rec['hours']}h "
            f"— ~{round(rec['carbon'])} gCO₂/kWh at ₹{rec['price']}/kWh. Evening 18–22h is the dirty/expensive peak; "
            f"midday and overnight are cleaner."
        )
    lines.append(
        "\nMetric help: carbon intensity = gCO₂ per kWh now (lower is greener); grid load = how busy the feeder is; "
        "the recommendation score blends proximity, low load, low carbon and availability."
    )
    lines.append(
        "\nIf — and only if — the user clearly wants you to DO something in the app, add a FINAL line exactly like "
        'ACTION: {"type":"..."} using one of: ' + ALLOWED_ACTIONS + ". "
        "Use select_station only with an id from the list above. Otherwise add no ACTION line."
    )
    return "\n".join(lines)


def parse_action(text: str):
    """Split an optional trailing ACTION: {json} line from the reply."""
    action = None
    m = re.search(r"ACTION:\s*(\{.*\})\s*$", text.strip(), re.S | re.I)
    if m:
        try:
            action = json.loads(m.group(1))
        except Exception:
            action = None
        text = text[:m.start()].strip()
    # strip any stray code fences
    text = re.sub(r"^```[a-z]*\n?|\n?```$", "", text.strip())
    return action, text.strip()


async def chat_complete(messages: list[dict]) -> str:
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    body = {"model": GROQ_MODEL, "messages": messages, "temperature": 0.4, "max_tokens": 700}
    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.post(GROQ_URL, json=body, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
