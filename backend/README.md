# GRIഢം Backend

FastAPI service for the GRIഢം EV-charging demo. Provides real charging stations
(via Open Charge Map), a synthetic grid/carbon model for Kochi, the
recommendation ranking (Greenest / Fastest / Balanced), and the user carbon
footprint dashboard.

## Setup

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate     |  macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

Keys are read from the project-root `.env` (`../.env`) — no need to duplicate them.

## Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Interactive docs: http://localhost:8000/docs
- From your phone, use your laptop's LAN IP, e.g. `http://192.168.1.20:8000`
  (phone + laptop on the same Wi-Fi/hotspot).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET  | `/` | Health + region info |
| GET  | `/charging-stations?lat=&lng=&distance=` | OCM + community stations, grid-enriched |
| GET  | `/stations` | Community stations |
| POST | `/stations` | Add a community station |
| GET  | `/grid/{station_id}` | Synthetic grid load + carbon intensity |
| POST | `/score` | Rank candidates by mode (fastest/greenest/balanced) |
| POST | `/sessions` | Log a charging session (drives the dashboard) |
| GET  | `/sessions` | List sessions |
| GET  | `/footprint/summary` | Dashboard totals, CO₂ saved, series, equivalents |
| GET  | `/map-style` | MapTiler style URL (or MapLibre demo fallback) |

## Swapping in real grid data later

Replace `grid_state()` in `grid.py` with a call to India Energy Atlas /
Electricity Maps. Nothing else changes — scoring and the carbon dashboard only
depend on that function's return shape.

## Notes

- `gridam.db` (SQLite) is created on first run and seeded with 3 demo stations
  and 5 past charging sessions so the map and dashboard look alive immediately.
- Delete `gridam.db` to reset the demo state.
