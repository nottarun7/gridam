import json
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from config import DB_PATH
from electricitymap import grid_state, tou_price
from partner_stations import community_seed, partner_stations


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
            conn.executemany("insert into stations values (?, ?)", [(item["id"], json.dumps(item)) for item in community_seed()])
        if not conn.execute("select count(*) from sessions").fetchone()[0]:
            rng, stations = random.Random(42), partner_stations()[:5]
            for idx in range(24):
                when = datetime.now(timezone.utc) - timedelta(days=rng.randint(1, 42), hours=rng.randint(0, 23))
                station_item = stations[idx % len(stations)]
                kwh = round(rng.uniform(8, 38), 1)
                payload = {"station_id": station_item["id"], "station_name": station_item["name"], "kwh": kwh, "carbon_intensity": grid_state(station_item["id"], when)["carbon_intensity_gco2_kwh"], "cost_inr": round(kwh * tou_price(when.hour), 0)}
                conn.execute("insert into sessions (payload, created_at) values (?, ?)", (json.dumps(payload), when.isoformat()))
        if not conn.execute("select count(*) from settings").fetchone()[0]:
            conn.execute("insert into settings values (1, ?)", (json.dumps({"name": "Kochi driver", "vehicle": "Tata Nexon EV", "battery_kwh": 40.5, "efficiency_km_kwh": 6.5}),))


def read_community() -> list[dict[str, Any]]:
    try:
        with db() as conn:
            return [json.loads(row["payload"]) for row in conn.execute("select payload from stations")]
    except sqlite3.OperationalError:
        init_db()
        return read_community()


def save_station(item: dict[str, Any]) -> None:
    with db() as conn:
        conn.execute("insert or replace into stations values (?, ?)", (item["id"], json.dumps(item)))


def add_session(item: dict[str, Any]) -> dict[str, Any]:
    with db() as conn:
        cur = conn.execute("insert into sessions (payload, created_at) values (?, ?)", (json.dumps(item), datetime.now(timezone.utc).isoformat()))
        return item | {"id": cur.lastrowid}


def sessions() -> list[dict[str, Any]]:
    try:
        with db() as conn:
            rows = conn.execute("select id, payload, created_at from sessions order by created_at desc").fetchall()
    except sqlite3.OperationalError:
        init_db()
        return sessions()
    return [json.loads(row["payload"]) | {"id": row["id"], "created_at": row["created_at"]} for row in rows]


def get_profile() -> dict[str, Any]:
    try:
        with db() as conn:
            row = conn.execute("select payload from settings where id=1").fetchone()
    except sqlite3.OperationalError:
        init_db()
        return get_profile()
    return json.loads(row["payload"])


def save_profile(profile: dict[str, Any]) -> None:
    with db() as conn:
        conn.execute("insert or replace into settings values (1, ?)", (json.dumps(profile),))
