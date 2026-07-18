"""Grid + carbon-intensity signal for Kochi / Kerala.

Two layers:
  1. REAL carbon — when Electricity Maps has a live reading for the zone (IN-SO,
     Southern India), the carbon intensity and renewable share are anchored to
     that live value, so the app shows real, day-to-day-varying data.
  2. Synthetic model — the fallback (and the shape used to spread a single
     regional reading across the 24h forecast). Calibrated to real Kerala
     figures: ~5,600 MW peak, 7–11pm evening peak, 90% hydro / 10% solar own
     generation, ~70% coal imports, Southern-grid CEA factor ≈ 809 gCO₂/kWh.
     (See GRID_DATA.md.)

`source` in the return says which was used: "electricitymaps" or "model".
Grid *load %* is always modelled — Electricity Maps doesn't publish it.
"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime

import electricitymap as em

CARBON_DIRTY_CEILING = 820.0
CARBON_CLEAN_FLOOR = 240.0


def _seed(key: str) -> float:
    h = hashlib.md5(key.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _shape(hour: float):
    """Neutral-feeder daily shape (no per-station offset, no wobble)."""
    solar = math.exp(-((hour - 12.5) ** 2) / 8.0)
    evening = math.exp(-((hour - 20.5) ** 2) / 6.5)
    morning = math.exp(-((hour - 10.0) ** 2) / 7.0)
    load = max(15.0, min(98.0, 35 + 58 * evening + 18 * morning))
    ren = max(3.0, min(90.0, 12 + 60 * solar - 22 * evening))
    carbon = max(CARBON_CLEAN_FLOOR, min(CARBON_DIRTY_CEILING, 820 - 5.5 * ren + 0.4 * (load - 50)))
    return load, ren, carbon


def grid_state(station_id: str, when: datetime | None = None) -> dict:
    when = when or datetime.now()
    hour = when.hour + when.minute / 60.0

    sid = str(station_id)
    clean_char = (_seed(sid + "|clean") - 0.5) * 2.0
    load_char = (_seed(sid + "|load") - 0.5) * 2.0
    ts = when.timestamp()
    phase = _seed(sid + "|phase") * 6.2832
    wobble = math.sin(ts / 13.0 + phase) + 0.5 * math.sin(ts / 5.0 + phase)

    # modelled values (station-adjusted)
    base_load, base_ren, _ = _shape(hour)
    load = max(15.0, min(98.0, base_load + load_char * 10 + wobble * 4.0))
    ren = max(3.0, min(90.0, base_ren + clean_char * 15 + wobble * 3.0))
    carbon = max(CARBON_CLEAN_FLOOR, min(CARBON_DIRTY_CEILING, 820 - 5.5 * ren + 0.4 * (load - 50)))
    source = "model"

    # anchor to the live Electricity Maps reading if we have one: shift the
    # whole curve so "now" matches reality, preserving per-station spread and
    # giving a real-anchored 24h forecast.
    snap = em.snapshot()
    if snap.get("ok") and snap.get("carbon") is not None:
        now = datetime.now()
        nh = now.hour + now.minute / 60.0
        _, ren_now, carbon_now = _shape(nh)
        carbon = max(80.0, min(1000.0, carbon + (snap["carbon"] - carbon_now)))
        if snap.get("renewable") is not None:
            ren = max(0.0, min(100.0, ren + (snap["renewable"] - ren_now)))
        source = "electricitymaps"

    return {
        "station_id": sid,
        "timestamp": when.isoformat(timespec="minutes"),
        "grid_load_pct": round(load, 1),
        "carbon_intensity_gco2_kwh": round(carbon, 1),
        "renewable_share_pct": round(ren, 1),
        "source": source,
    }
