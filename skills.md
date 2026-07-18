# GRIഢം Skills

## Grid-Aware Charging Recommendation

Ranks nearby chargers using distance, carbon intensity, grid load, charger speed, and availability. Modes are Greenest, Fastest, and Balanced.

## Charge Right Forecast

Builds a 24-hour carbon and tariff forecast, then identifies the greenest, cheapest, and recommended charging windows.

## Station Discovery

Aggregates Open Charge Map, curated Kochi network data, and community SQLite stations into normalized charger records.

## Route Planning

Uses OpenRouteService when configured and falls back to straight-line guidance when routing is unavailable.

## Impact Accounting

Calculates energy used, CO2 emitted, CO2 saved versus petrol, estimated petrol money saved, and recent charging trends.

## Operator Monitoring

Provides network load, station status, availability, operator grouping, and demand-response timing.

## Grounded AI Assistant

Answers driver questions using current station, forecast, profile, and ranking context. Groq is used when configured; otherwise a local fallback keeps the UX alive.
