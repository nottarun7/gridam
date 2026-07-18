"""SQLite persistence for community-added stations and charging sessions.

Uses the stdlib sqlite3 module (no extra deps). Tables are created on import
and seeded with a few demo rows so the map and carbon dashboard look alive on
first run.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from config import DB_PATH, EV_EFFICIENCY_KM_PER_KWH, PETROL_GCO2_PER_KM
from grid import grid_state


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                connector TEXT,
                source TEXT DEFAULT 'community',
                created_at TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id TEXT,
                station_name TEXT,
                kwh REAL NOT NULL,
                carbon_intensity_gco2_kwh REAL,
                session_co2_kg REAL,
                co2_saved_kg REAL,
                created_at TEXT
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data TEXT NOT NULL
            )"""
        )
    _seed_if_empty()


# ------------------------------- settings ---------------------------------
DEFAULT_SETTINGS = {
    "name": "EV Driver",
    "vehicle": "Tata Nexon EV",
    "battery_kwh": 40.0,
    "efficiency_km_kwh": 6.5,   # range per kWh
    "mileage_kmpl": 18.0,       # equivalent petrol car
    "petrol_price": 105.0,      # ₹ per litre
    "tariff": 8.0,              # ₹ per kWh charged
    "connector_pref": "CCS2",
}


def get_settings() -> dict:
    with _conn() as c:
        row = c.execute("SELECT data FROM settings WHERE id=1").fetchone()
    if not row:
        return dict(DEFAULT_SETTINGS)
    import json
    saved = json.loads(row["data"])
    return {**DEFAULT_SETTINGS, **saved}


def save_settings(patch: dict) -> dict:
    import json
    merged = {**get_settings(), **{k: v for k, v in patch.items() if v is not None}}
    with _conn() as c:
        c.execute(
            "INSERT INTO settings (id, data) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET data=excluded.data",
            (json.dumps(merged),),
        )
    return merged


# --------------------------- community stations ---------------------------
def add_station(name: str, lat: float, lng: float, connector: str) -> dict:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO stations (name, lat, lng, connector, source, created_at)"
            " VALUES (?,?,?,?, 'community', ?)",
            (name, lat, lng, connector, datetime.now().isoformat(timespec="seconds")),
        )
        sid = cur.lastrowid
    return get_station(sid)


def get_station(sid: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM stations WHERE id=?", (sid,)).fetchone()
    return dict(row) if row else None


def list_stations() -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT * FROM stations ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


# ------------------------------- sessions ---------------------------------
def log_session(station_id: str, station_name: str, kwh: float,
                when: datetime | None = None) -> dict:
    when = when or datetime.now()
    gs = grid_state(station_id, when)
    ci = gs["carbon_intensity_gco2_kwh"]

    session_co2_kg = kwh * ci / 1000.0
    petrol_km = kwh * EV_EFFICIENCY_KM_PER_KWH
    petrol_co2_kg = petrol_km * PETROL_GCO2_PER_KM / 1000.0
    co2_saved_kg = petrol_co2_kg - session_co2_kg

    with _conn() as c:
        cur = c.execute(
            """INSERT INTO sessions
               (station_id, station_name, kwh, carbon_intensity_gco2_kwh,
                session_co2_kg, co2_saved_kg, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (str(station_id), station_name, kwh, ci,
             round(session_co2_kg, 3), round(co2_saved_kg, 3),
             when.isoformat(timespec="seconds")),
        )
        sid = cur.lastrowid
    return get_session(sid)


def get_session(sid: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    return dict(row) if row else None


def list_sessions() -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT * FROM sessions ORDER BY created_at").fetchall()
    return [dict(r) for r in rows]


# ------------------------------- seeding ----------------------------------
def _seed_if_empty() -> None:
    with _conn() as c:
        n_st = c.execute("SELECT COUNT(*) FROM stations").fetchone()[0]
        n_se = c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

    if n_st == 0:
        demo = [
            ("Panampilly Nagar Fast Charger", 9.9636, 76.2969, "CCS2"),
            ("Kakkanad InfoPark Hub", 10.0074, 76.3600, "Type 2"),
            ("Fort Kochi Community Point", 9.9658, 76.2421, "Bharat AC-001"),
        ]
        for name, lat, lng, conn_t in demo:
            add_station(name, lat, lng, conn_t)

    if n_se == 0:
        # Seed ~6 weeks of charging history at varied times/stations so the
        # profile charts (CO2 trend, energy mix, weekly kWh) look real.
        import random
        rng = random.Random(42)
        now = datetime.now()
        stations = [
            "Panampilly Nagar Fast Charger", "Kakkanad InfoPark Hub",
            "Fort Kochi Community Point", "ChargeMOD · Lulu Mall Edappally",
            "Zeon · Marine Drive",
        ]
        # roughly every ~2 days over 42 days
        for days_ago in range(41, 0, -2):
            hour = rng.choice([8, 9, 12, 13, 14, 19, 20, 22])  # mix clean/dirty
            kwh = round(rng.uniform(12, 32), 1)
            name = rng.choice(stations)
            ts = (now - timedelta(days=days_ago)).replace(hour=hour, minute=0, second=0)
            log_session(name, name, kwh, ts)
