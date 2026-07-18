# GRIഢം — Charge right. Drive clean.

GRIഢം is a grid-aware EV charging web app for Kochi, Kerala. It helps a driver
choose a charger *and* a better time to charge by combining charger discovery,
regional grid-carbon data, routing, a 24-hour charging forecast and personal
impact tracking.

The application is built with a React/Vite frontend, a FastAPI backend and an
nginx reverse proxy. The browser always calls `/api/*`; API keys stay on the
server.

## What it does

- Finds charging stations around a selected location using Open Charge Map,
  curated Kochi partner-network data and community additions.
- Ranks stations as **Greenest**, **Fastest** or **Balanced**.
- Uses Electricity Maps' Southern India (`IN-SO`) signal for live regional
  carbon intensity and renewable share when available.
- Falls back automatically to a Kerala-calibrated model when live carbon data
  is unavailable.
- Shows a **Charge Right** 24-hour forecast and recommends a lower-carbon,
  lower-price charging window.
- Provides routing and turn-by-turn instructions, a personal charging/impact
  dashboard, battery-health coaching, recycling locations and a grounded AI
  assistant.
- Includes an operator console for illustrating peak-demand and
  demand-response scenarios.

## Data honesty

Not every value is a live measurement. This distinction is intentional and
visible in the application.

| Data | Status |
| --- | --- |
| Charger POIs, connectors and operators | Open Charge Map where available; curated partner-network seed data; community additions stored locally |
| Carbon intensity and renewable share | Live regional Electricity Maps data when configured and available; otherwise a Kerala-calibrated fallback model |
| Grid load, station busy status and tariff | Modelled; India does not publish a live per-station feeder-load or plug-availability feed used by this app |
| Charge Right forecast | Electricity Maps forecast when available; otherwise modelled and live-carbon-anchored forecast |
| Charging history and profile analytics | Local SQLite records; a first run is seeded with demo history |
| Demand-response and battery-health results | Transparent scenario/estimate calculations, not live operator telemetry or vehicle BMS diagnostics |

Read [DATA_SOURCES.md](DATA_SOURCES.md) for source-by-source detail and
[GRID_DATA.md](GRID_DATA.md) for Kerala calibration figures and citations.

## Run with Docker

From the project root:

```bash
docker compose up -d --build
```

Open [http://localhost:8080](http://localhost:8080).

- The `frontend` container builds `web/`, serves the static application with
  nginx, and proxies `/api/*` to the backend.
- The `backend` container runs FastAPI on port `8000`; interactive API docs are
  available at [http://localhost:8000/docs](http://localhost:8000/docs).
- SQLite data persists in the `gridam-data` Docker volume.

After any code change, rebuild and hard-refresh the browser (`Ctrl+Shift+R`):

```bash
docker compose up -d --build
```

Stop the stack:

```bash
docker compose down
```

Reset the persisted demo database (destructive):

```bash
docker compose down -v
```

## Local development

Use two terminals.

```bash
# Terminal 1 — backend
cd backend
python -m venv .venv
.venv\Scripts\activate     # Windows; macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload
```

```bash
# Terminal 2 — frontend
cd web
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` to the
local FastAPI process.

## Configuration

Create a root `.env` file using plain `KEY=value` lines. It is git-ignored and
must never be committed.

| Variable | Used for | Required? |
| --- | --- | --- |
| `OPENCHARGEMAP_API_KEY` | Nearby real charger POIs | Recommended |
| `OPENROUTESERVER_BASIC_API_KEY` | Driving routes, ETA and instructions | Optional |
| `MAPTILER_API_KEY` | Production map style | Optional |
| `EM_API_KEY` | Live regional carbon, renewable share and forecast | Optional; the fallback model works without it |
| `EM_ZONE` | Electricity Maps zone | Defaults to `IN-SO` |
| `GROQ_API_KEY` | AI assistant | Optional |
| `GROQ_MODEL` | Assistant model selection | Optional |

## Verify the app

```bash
# Frontend production build
cd web
npm run build
```

With the backend running, open these endpoints:

- [http://localhost:8000/health](http://localhost:8000/health) — includes
  `carbon_source`, either `electricitymaps` or `model`.
- [http://localhost:8000/config](http://localhost:8000/config) — client-safe
  configuration and map settings.
- [http://localhost:8000/charging-stations](http://localhost:8000/charging-stations)
  — stations near the default Kochi centre.

## Project layout

```text
gridam/
├── backend/                  # FastAPI APIs, data integrations, SQLite store
│   ├── main.py               # endpoints and aggregation
│   ├── grid.py               # live-carbon anchoring + calibrated fallback
│   ├── electricitymap.py     # Electricity Maps client/cache
│   ├── scoring.py            # station ranking weights
│   └── store.py              # community stations, sessions and profile data
├── web/                      # React/Vite application served by nginx
│   └── src/                  # landing page, map, dashboards and components
├── docker-compose.yml        # full local stack
├── DATA_SOURCES.md           # source, fallback and calculation reference
├── DEMO_WORKFLOW.md          # 7–10 minute presentation walkthrough
├── GRID_DATA.md              # Kerala grid data and citations
├── EXPLAINER.md              # product explainer
└── PITCH.md                  # pitch material
```

## Demonstrating GRIഢം

Start at the landing page, explain why charging time matters, then launch the
app and walk through the map, ranking modes, Charge Right, Impact/Profile and
Operator Console. [DEMO_WORKFLOW.md](DEMO_WORKFLOW.md) provides the exact talk
track, formulas, Kerala grid statistics, dashboard explanations and clear
guidance on what is live versus modelled.

## Current limitations and next steps

- Plug availability is a placeholder score until operator OCPP/status feeds are
  integrated.
- Time-of-use price is a model, not an official parsed KSERC tariff schedule.
- Partner-network and recycling locations are curated approximate seed data.
- The app currently uses a local, single-user SQLite profile rather than
  authentication and multi-user storage.

See [PLAN.md](PLAN.md) for the roadmap.
