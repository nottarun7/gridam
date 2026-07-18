# GRIഢം Agents

GRIഢം is built as a coordinated product system with clear ownership boundaries.

## Product Architect

- Owns the driver journey: discover, compare, forecast, navigate, and record impact.
- Keeps Kochi first while preserving expansion paths for more regions.
- Maintains the decision log in `plan.md`.

## Grid Intelligence Agent

- Owns Electricity Maps `IN-SO` ingestion and the Kerala synthetic fallback.
- Exposes active source clearly through health, config, grid, and forecast endpoints.
- Ensures external API failures never crash the app.

## Station Data Agent

- Combines Open Charge Map, curated Indian networks, and community stations.
- Normalizes connectors, max power, operators, availability, and source labels.

## Ranking Agent

- Owns Greenest, Fastest, and Balanced scoring.
- Scores distance, grid load, carbon intensity, and availability.

## Driver Experience Agent

- Owns React, MapLibre, search, routing, Charge Right, profile, impact, and assistant surfaces.
- Keeps API keys out of frontend code and preserves graceful degraded states.

## Operator Agent

- Owns network KPIs, station status, demand response, load curves, and operator grouping.

## AI Assistant Agent

- Owns Groq integration and the deterministic fallback assistant.
- Allows only safe UI actions: select station, change mode, or open a page.

## DevOps Agent

- Owns Docker, nginx, `.env`, health checks, and production build verification.

## Open Architecture Questions

1. Should profiles stay local/demo SQLite for v1, or move to authenticated accounts?
2. Which Indian charging networks should be verified partner feeds versus curated listings?
3. Should v1 optimize for Kochi city driving, Kerala corridors, or both?
4. Should tariff logic stay simple time-of-use, or model KSEB slabs and station pricing?
5. Should operator controls be analytics-only first, or include authenticated actions later?
6. Should the UI ship in English first, or bilingual English/Malayalam?
