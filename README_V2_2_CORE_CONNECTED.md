# QuantSport AI Web v2.2 — v10.8 Core Connected

This build removes the demo analysis from Command Center. The browser now sends raw pasted fixtures to the bundled Python API, which imports the frozen v10.8 football, basketball and tennis parsers/engines and historical datasets.

## Local test
1. Double-click `START QUANTSPORT CORE.bat` and leave that window open.
2. Double-click `START WEBSITE.bat` and leave it open.
3. Open http://localhost:3001/admin
4. Paste the same raw feed used in desktop v10.8 and Analyse.

The analysis screen distinguishes `TOP PICKS` (one top fingerprint per qualifying fixture) from `QUALIFIED MARKETS` (all qualifying markets across those fixtures), so a desktop All Qualified Markets count should be compared with the web Qualified Markets count, not the public card count.

Publishing remains browser-local in this test build. Production deployment requires hosting the Python API and replacing localStorage with a shared database/authenticated publishing service.
