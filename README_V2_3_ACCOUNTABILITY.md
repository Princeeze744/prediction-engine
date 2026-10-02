# QuantSport AI Web v2.3 — Accountability Edition

Built on v2.2 CORE CONNECTED. The v10.8 mathematical engine is unchanged.

## Added
- Public navigation no longer exposes Command Center.
- Highly visible market chips on Intelligence: Top Fingerprint, Home 1+, Away 1+, Over 1.5, Over 2.5, Under 3.5, 1X, X2.
- Private Results Center inside /admin.
- Paste partial final scores; only matched finished fixtures update. Missing fixtures stay PENDING and can be settled by later pastes.
- Immutable prediction architecture: scores are stored separately; original publication is not rewritten.
- Public Results & History with sport, market, status and time-window filters.
- Automatic WON/LOST/PENDING settlement for supported football markets; baseline basketball/tennis settlement included for current public market shapes.
- Public hit-rate KPI = WON / (WON + LOST); pending/void excluded.

## Result paste format
One fixture per line, e.g.
Hong Kong 2 - 1 Laos
Denmark 1 - 0 Wales
Germany 2 - 2 Greece

Unmatched or unparseable lines are reported and do not alter history.

## Prototype persistence
Publications/results still use browser localStorage in this local build. Production deployment must move them to authenticated server/database storage before multi-device/public launch.
