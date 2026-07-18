# GRIഢം

Smart EV charging for Kochi — a unified charging map with grid-aware,
carbon-aware routing. Web frontend (MapLibre GL JS) + FastAPI backend with a
synthetic grid/carbon model and a personal carbon dashboard.

## Run it (Docker — recommended)

One command brings up both services:

```bash
docker compose up -d --build
```

Then open **http://localhost:8080**

- `frontend` (nginx) serves the web app on **:8080** and reverse-proxies API
  calls to the backend — so the browser only ever talks to one address.
- `backend` (FastAPI) runs on **:8000** (also exposed for `/docs` and direct
  API testing).

API keys are read from `.env` (already in the repo root) via `env_file` in
`docker-compose.yml`.

Stop everything:

```bash
docker compose down
```

To view on your **phone**: find your laptop's LAN IP (`ipconfig` on Windows),
make sure your phone is on the same Wi-Fi, and open `http://<laptop-IP>:8080`.

## Run without Docker (dev mode, hot reload)

The frontend is now a React (Vite) app, so run the two services in two
terminals:

```bash
# 1) backend
cd backend
python -m venv .venv && .venv\Scripts\activate     # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000

# 2) frontend (Vite dev server, proxies API calls to :8000)
cd web
npm install
npm run dev
```

Open **http://localhost:5173** for the app with hot reload.

## Project layout

```
gridam/
  docker-compose.yml     # runs both services
  .env                   # API keys (git-ignored)
  backend/               # FastAPI: OCM stations, synthetic grid, scoring,
                         # routing (ORS), carbon dashboard, community stations
    Dockerfile
  web/                   # MapLibre GL JS single-page app (neon-green theme)
    Dockerfile           # nginx: serves static + proxies API to backend
    nginx.conf
  ARCHITECTURE_PLAN.md   # full architecture write-up
```

## Keys used (in `.env`)

- `MAPTILER_API_KEY` — dark map tiles
- `OPENCHARGEMAP_API_KEY` — real charging stations
- `OPENROUTESERVER_BASIC_API_KEY` — routing / ETA (OpenRouteService)

## Features

Interactive charger map · Greenest / Fastest / Balanced routing · synthetic grid
utilization + carbon intensity per station · route + ETA · personal carbon
footprint dashboard · community station registration.
