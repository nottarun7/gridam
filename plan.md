# GRIഢം Architecture And Build Plan

## Product Goal

Build a grid-aware EV charging web app for Kochi, Kerala that helps drivers charge at the greenest and cheapest time and place.

## Decisions

- React Vite SPA served by nginx on port `8080`.
- FastAPI backend proxied under `/api`.
- MapLibre map with MapTiler support and a public fallback style.
- Electricity Maps `IN-SO` for live carbon when `EM_API_KEY` exists.
- Kerala-calibrated synthetic grid fallback when live carbon is unavailable.
- SQLite persistence for community stations, sessions, and profile settings.
- Groq assistant integration with deterministic fallback.
- Root `.env` for secrets; backend-only access.
- One-command runtime: `docker compose up -d --build`.

## Clarifying Questions

1. Do we want account-based user profiles in v1, or local profiles until hosting is chosen?
2. Which station networks should be treated as verified partners?
3. Should Kochi city trips or Kerala highway corridors drive the first data model?
4. Do we need KSEB tariff slabs and station-specific pricing in the MVP?
5. Should operator controls remain simulated until OCPP/provider integration exists?
6. Should Malayalam localization be included in the first release?

## Build Plan

1. Backend API: configuration, grid model, Electricity Maps, station aggregation, scoring, route fallback, forecast, sessions, profile, chat, and operator summary.
2. Frontend: landing page, map app, station list/detail, Charge Right forecast, profile, assistant, and operator dashboard.
3. Deployment: nginx proxy and SPA fallback, backend Dockerfile, frontend Dockerfile, Docker Compose, and persistent volume.
4. Verification: `npm run build`, Python compile check, and backend smoke test.

## Future Expansion

- Region configuration for center, grid zone, tariff, language, and partner feeds.
- Authentication and hosted user accounts.
- Verified provider APIs and OCPP integration.
- Observability around API failures and carbon-source switching.
