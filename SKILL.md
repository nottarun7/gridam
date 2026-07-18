---
name: build-gridam
description: Build or extend GRIഢം, a grid-aware EV charging app for Kochi with FastAPI, React, nginx, Docker, carbon-aware ranking, forecasts, routing, profiles, AI assistance, and operator analytics.
---

# Build GRIഢം

Use this skill when building or extending GRIഢം.

## Mission

Ship a production-shaped full-stack app:

- FastAPI backend.
- React Vite frontend.
- nginx serving the SPA and proxying `/api`.
- One command: `docker compose up -d --build`.
- Frontend: `http://localhost:8080`.
- Root `.env` secrets read only by the backend.

## Required Features

- Charger map for Kochi using Open Charge Map, curated Indian networks, and community stations.
- Greenest, Fastest, and Balanced ranking.
- Electricity Maps `IN-SO` live carbon with Kerala model fallback.
- Visible active carbon source.
- Charge Right 24-hour forecast.
- Routing and navigation with graceful fallback.
- Search, dashboard, profile, Groq assistant, and operator dashboard.
- Professional dark neon-green UI.
- Graceful handling for all external API failures.

## Kerala Fallback

- Midday is cleaner due to solar shape.
- Evening peak from 19:00 to 23:00 is dirtier.
- Carbon range is roughly 240 to 820 gCO2/kWh.
- Tariff curve:
  - 22:00-06:00: INR 6/kWh.
  - 10:00-16:00: INR 6.5/kWh.
  - 18:00-22:00: INR 11/kWh.
  - Other hours: INR 8/kWh.

## Scoring

- Fastest: proximity 0.55, grid 0.15, carbon 0.10, availability 0.20.
- Greenest: proximity 0.15, grid 0.30, carbon 0.45, availability 0.10.
- Balanced: proximity 0.30, grid 0.25, carbon 0.30, availability 0.15.

## Verification

Run:

```bash
npm run build
python -m compileall backend
```

When dependencies are installed, smoke-test `/health`, `/charging-stations`, `/forecast`, and `/operator/summary`.
