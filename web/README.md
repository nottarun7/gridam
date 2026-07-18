# GRIഢം — Web App (React + Vite)

Responsive single-page app for GRIഢം in the neon-green dark theme. **MapLibre
GL JS** map, live grid/carbon polling, ranked routing, live navigation
simulation, and a carbon dashboard. Talks to the FastAPI backend.

Adapts to the window: a two-pane **sidebar + map** layout on desktop, a
map-with-bottom-sheet layout on phones.

## Run (Docker — recommended)

From the repo root:

```bash
docker compose up -d --build
```

Open **http://localhost:8080**. nginx serves the built app and proxies API
calls to the backend container — one origin, no CORS.

## Run (dev mode, hot reload)

Two terminals:

```bash
# 1) backend
cd backend && uvicorn main:app --port 8000

# 2) frontend (Vite dev server on :5173, proxies /api paths to :8000)
cd web && npm install && npm run dev
```

Open **http://localhost:5173**. (In dev, the backend no longer serves the app
directly — Vite does, with hot reload.)

## Features

- **Map** — OCM stations near Kochi as pins colored by live carbon intensity;
  your location as a blue dot.
- **Search** — type any place in Kerala (Nominatim); picking it recenters the
  map, reloads nearby stations, and sets it as your start point.
- **Greenest / Fastest / Balanced** — re-ranks via the backend, marks the best
  station.
- **Filters** — connector type, search radius, and your battery size.
- **Live grid** — carbon/load/renewable values poll every 6s and drift in real
  time (a "live" pulse shows it's updating).
- **Station detail** — connectors, live stats, and a **charge time + cost
  estimate** for your battery.
- **Navigate + turn-by-turn** — draws the ORS route with step-by-step
  directions, and a **Start drive** button animates a car along the route with a
  live ETA countdown.
- **Impact** — carbon dashboard (CO₂ saved, weekly chart, clean-charging %).
- **Add station** — register a community station (type coords or pick on map).

## Structure

```
web/
  index.html · package.json · vite.config.js
  Dockerfile          # node build → nginx serve
  nginx.conf          # static + API reverse-proxy
  src/
    main.jsx · App.jsx · api.js · index.css
    lib/estimate.js
    components/  MapView, SearchBar, ModeToggle, Filters, StationList,
                 StationDetail, NavPanel, ImpactPanel, AddStationModal, Toast, Icon
```

## Notes

- Map tiles, station data, geocoding, and routing all need internet + the keys
  in the root `.env` — verified with a production `vite build`; live data works
  on your machine.
- The production bundle warns about size (MapLibre is ~1 MB) — harmless for a
  hackathon; code-split later if you want.
