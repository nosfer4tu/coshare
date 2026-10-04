# CoShare.jp (smart-travel-companion) — CLAUDE.md

卒業制作: 同一運航便のコードシェア価格差を検出・解説する航空券比較Webアプリ。
Owner: Gabriel (4年・松村ゼミ)。Interim presentation 2026-07-30 (done). Final assessment: January 2027.

Product context: @PRODUCT.md / Design system: @DESIGN.md

## Priorities (target: January 2027 final assessment)
The 2026-07-30 mid-term demo has passed. Still off-limits WITHOUT an explicit request:
- renaming normalized offer keys (see Data Contracts)
- changing the codeshare pairing logic (grouping by `Departure Time` + `Operating IATA`, see Architecture)
- removing the ZZ / HR exclusions
- DB DELETE/DDL (see Guardrails)
Small, reviewable diffs. Show the diff before explaining it.

## Run / Dev
- Backend: `python3 local_server.py` from repo root → Flask on **http://127.0.0.1:8000**
  - Port 5000 is macOS AirPlay — never use it. Scripts and `curl` must use `127.0.0.1`,
    not `localhost` (IPv6 resolution sends requests to the wrong listener). The Vite proxy
    targets `localhost:8000` and works for the browser in dev (see Known issues).
- Frontend: `cd frontend && npm run dev` → Vite on :5173, proxies `/api` → :8000
  (see `frontend/vite.config.js`; no path rewrite).
- Both servers must run for the app to work. If `/api/*` returns ECONNREFUSED in the
  browser console, Flask is down — restart it before debugging anything else.
- After any agent session that spawned test servers (e.g. Playwright), assume dev
  servers are dead; restart both before manual testing.

## Architecture
- `frontend/` React + Vite SPA. Pages: HomePage, ResultsPage, TrendPage, DestinationPage.
  ResultsPage state lives in **URL search params** (useSearchParams) — a new search
  updates the query string, and the fetch effect depends on it. Do not move search
  state back to location.state (breaks re-search on the results page).
- `local_server.py` (repo root) Flask routes under `/api/*` for local dev.
- `api/<area>/*.py` Vercel serverless handlers; shared backend modules live in `api/_lib/`.
- `api/_lib/duffel_service.py` Duffel API calls (offer_requests, return_offers=true).
- `api/_lib/normalizer.py` raw Duffel → normalized offers. All display-carrier logic is here.
- `api/_lib/codeshare_service.py` `get_codeshare_offers`: keeps offers with `is Codeshare`
  and drops `Owner Airline IATA` in `{"HR"}`. Called only by `/api/codeshare/detect`
  (ResultsPage mode `codeshare`); in `/api/flights/search` (mode `both`) the call is commented
  out, so that route does no server-side HR filtering.
- **Pairing runs in the frontend**: `frontend/src/pages/ResultsPage.jsx` groups offers by
  `` `${Departure Time}_${Operating IATA}` ``; groups with >1 offer are codeshare groups
  (gap logic in `frontend/src/utils/codeshareGap.js`).
- `api/_lib/db.py` Neon PostgreSQL: `search_cache`, `price_history`.
- `seed_trend_data.py` (repo root) populates price history for demo routes (GET loop via :8000).

## Data Contracts (do not change silently)
- **Search API**: `GET /api/flights/search?origin=KIX&destination=TPE&departureDate=YYYY-MM-DD&passengers=adult&cabinClass=economy`
  — camelCase param names. Response: `{"data": [<normalized offers>]}`.
  `passengers` is ONE comma-separated param, one entry per traveller
  (`passengers=adult,adult,child`; default `adult`); each entry becomes a Duffel
  `{"type": ...}` passenger and the joined string is the cache key.
- **Normalized offer keys are Title Case with spaces**: `'Total Amount'`, `'Currency'`,
  `'Marketing Carrier'`, `'Operating Carrier'`, … Do NOT rename to snake_case/camelCase;
  React components and `save_price_history` read these exact strings.
- **Which segment each key reflects.** The normalizer's segment loop overwrites the same
  keys on every segment, so for connecting itineraries the last segment wins for some keys
  and the first segment for others:
  - *Last segment* (overwritten per segment): `'Operating Carrier'`, `'Operating IATA'`,
    `'Marketing Carrier'`, `'Marketing IATA'`, `'Departure Time'`, `'Arrival Time'`,
    `'is Codeshare'` (also compares `offer.owner` to the operating carrier),
    `'is Marketing Codeshare'` (Marketing IATA != Operating IATA only; `offer.owner` is ignored;
    absent on `search_cache` rows written before it existed).
  - *First segment* (`slices[0].segments[0]`, set before the loop): `'Owner Airline'`,
    `'Owner Airline IATA'`, and the additive detail keys `'Marketing Flight Number'`,
    `'Operating Flight Number'` (may be null), `'Departure Airport'`, `'Arrival Airport'`,
    `'Segment Count'` (segments in slice 0). Detail keys are absent on `search_cache` rows
    written before they existed — the UI omits absent fields and only offers expandable
    details when `Segment Count === 1`.
  - So on a connection the display carrier (first leg) and the pairing key
    (`Departure Time` + `Operating IATA`, last leg) describe different legs.
- **Display carrier = `slices[0].segments[0].marketing_carrier`** (name + iata_code),
  flight number from `marketing_carrier_flight_number`. Duffel's `offer.owner` is the
  *ticketing* entity, not the seller — never use it for display. Fallback to owner only
  if marketing_carrier is missing.
  **`'Owner Airline'` / `'Owner Airline IATA'` hold this display carrier, not `offer.owner`** —
  the names are misleading but renaming is off-limits (see Priorities).
- **Excluded carriers**: `ZZ` (Duffel Airways, test-env synthetic) dropped in
  `api/_lib/normalizer.py` (checked on the display carrier); `HR` (Hahn Air, ticketing broker —
  no consumer booking page) excluded from codeshare comparison pairs in
  `api/_lib/codeshare_service.py` (checked on `Owner Airline IATA`).
- **DB carrier columns store NAMES, not IATA codes** (`marketing_airline = 'China Airlines'`).
  Write SQL against names.
- **Trend cutoff**: price-history aggregation excludes rows where `departure_date >
  recorded_at + 10 months` (airline schedule horizon skews averages; relative to when the row
  was recorded, not to today). Rows with NULL `recorded_at` are excluded. Applies to the chart
  AND the 最安月/最高値月 stat cards, server-side, in `api/_lib/trend_service.py` (the only place;
  `local_server.py` and the Vercel handlers call it). Search itself is not date-limited.
- Prices JPY; fixed rate ¥155/USD (real-time FX is post-demo roadmap).
- Booking links: static map `frontend/src/constants/airlineBookingUrls.js`, keyed by
  IATA code, values are official-site URLs (Japan locale where available). URLs are
  hand-verified by clicking — an agent must not "correct" them from pattern-guessing
  (that's how `/jp/ja` broke; China Airlines is `/jp/jp/`). Missing code → render no button.

## Environment
- Duffel is in **TEST MODE**: prices are synthetic; ZZ offers appear in raw responses.
  Do not present prices as real-market data.
- ResultsPage and TrendPage show a non-dismissible `TestDataNotice`; gated by
  `SHOW_TEST_DATA_NOTICE` in `frontend/src/constants/testDataNotice.js` (set false only when real prices are wired in and verified).
- Secrets: `DUFFEL_ACCESS_TOKEN` via `api/_lib/config.py` / `.env.local`. Never print or commit tokens.

## Testing discipline
- `search_cache` may contain rows written BEFORE normalizer fixes. When testing any
  normalization/display change, use a **never-searched date** to force a fresh Duffel
  fetch; cached dates replay old data and give false results.
- Cached searches do not write price history; only fresh fetches do (JPY offers only).
- `price_history` has NO `cabin_class` column, so non-economy test searches contaminate the
  trend data. Use economy for test searches, or note the route + departure dates you searched
  so cleanup SQL can be written (output it for review; never execute — see Guardrails).
- `database/schemas/*.sql` may be stale: `search_cache.passengers` is declared `INTEGER` but
  the code writes strings like `'adult'` / `'adult,adult'`. Check the live Neon schema before
  writing SQL against it.

## verified_checks (manual ground-truth price checks)
- Table (Neon, created by hand; never write to it from code except `seed_verified_checks.py`, which
  the owner runs): `id, route, check_date, flight_date, carrier_checked, sandbox_source,
  sandbox_price_jpy, real_price_jpy, real_source_url, verdict, notes, created_at`.
  `carrier_checked` is the airline NAME (the card's display carrier), not an IATA code.
- Values: `sandbox_source` = `duffel` | `flightlabs`; `verdict` = `match` | `mismatch` |
  `not_comparable`. `match` means `abs(sandbox - real) / real <= 5%`
  (`MATCH_TOLERANCE` in `api/_lib/verified_checks.py`, mirrored by `MATCH_TOLERANCE_PERCENT` in
  `frontend/src/utils/verifiedChecks.js`; change both). It does NOT mean identical.
  `not_comparable` = the itinerary could not be matched on the official site (prices may be null/0).
- Data in via `verified_checks_data.json` + `python3 seed_verified_checks.py [--dry-run]`;
  `validate_check` in `api/_lib/verified_checks.py` is the single validator. No real check data
  is committed except what the owner adds to that JSON.
- Read path: `GET /api/verified-checks?route=KIX-TPE&flightDate=YYYY-MM-DD` (both optional, camelCase)
  → `{"data": [...]}` with the table's column names. `local_server.py` only; there is NO Vercel
  handler (`/api/places/suggestions` has none either).
- Verification page `/verification` (linked from the navbar) lists every check, mismatches included.
- Card badge (`VerifiedBadge`, on CodeShareCard rows and FlightCard): shown only when
  route + `flight_date == searched departure date` + carrier name (trimmed, case-insensitive,
  exact; never flight number) match, `sandbox_source === CARD_SANDBOX_SOURCE`
  (`frontend/src/utils/verifiedChecks.js`, `'duffel'`; **change it when another price source is
  wired into the cards**) and the latest matching check has verdict `match`.
  Badges are date-specific records ("{check_date}に公式サイトと照合"), not a claim about the
  current price. Checks are fetched once per results search in `ResultsPage.jsx`.

## Definition of Done — run before reporting success
1. Both servers restart cleanly; no tracebacks on boot.
2. Fresh-date search KIX→TPE renders CodeShareCards with real airline names —
   no "Duffel Airways", no "Hahn Air" anywhere in results.
3. On ResultsPage, editing the form and clicking 検索 fires a new request
   (URL query string updates) and re-renders.
4. TrendPage loads; chart ends ≈10 months out; stat cards populated.
5. Booking button appears on the cheaper carrier and opens the correct airline
   site in a new tab (spot-check one).
6. `npx eslint .` clean in `frontend/`; browser console free of errors on the
   pages you touched.
7. Quick API smoke test:
   `curl -s "http://127.0.0.1:8000/api/flights/search?origin=KIX&destination=TPE&departureDate=<fresh date>&passengers=adult&cabinClass=economy" | head -c 300`
   → expect `{"data": [...]`.

## Guardrails
- Never execute DB DELETE/UPDATE/DDL. Output the SQL for manual review in the Neon
  console instead (this repo's convention; deletes are reviewed by a human).
- Never commit dump files (`duffel_raw_dump.json`) or tokens.
- Do not add features beyond the task you were given; milestone work is listed in PRD.md.
- When a fix depends on a Duffel response field, verify against a real raw response
  (temporary dump), not from memory of the API shape.

## Known issues (not yet fixed)
- **Shared `search_cache` key.** `/api/flights/search` and `/api/codeshare/detect` read and
  write the same key (route, date, cabin, passengers) but store different content: the first
  stores all normalized offers, the second only `get_codeshare_offers` output. Within the 24h
  TTL, a search on one route replays the other's stored result, in both directions.
- **HR is filtered only on `/api/codeshare/detect`** (`get_codeshare_offers`, on
  `Owner Airline IATA`). `/api/flights/search` returns HR offers unfiltered.
- **Vercel handlers vs contract.** `api/flights/search.py` and `api/codeshare/detect.py` read
  snake_case params (`departure_date`, `cabin_class`); the contract and `local_server.py` use
  camelCase (`departureDate`, `cabinClass`).
- **Vite proxy target.** `frontend/vite.config.js` proxies `/api` to `http://localhost:8000`,
  which works for the browser in dev. The 127.0.0.1 rule applies to scripts and `curl`.
- **`is Codeshare` is unchanged on purpose.** Its `offer.owner` clause makes it `True` for
  HR-ticketed own-code offers (e.g. owner `HR`, marketing = operating = `7C`). That is what
  keeps HR-ticketed own-code offers such as `CI` and `KE` in the codeshare pairs
  (`get_codeshare_offers`; checked in the analysis). `ResultsPage.jsx` also reads it
  (singleton groups are dropped in codeshare mode unless it is true). Do not change the rule
  without checking `/api/codeshare/detect` first.
- **The コードシェア便 badge reads `'is Marketing Codeshare'`**, not `'is Codeshare'`, so solo
  flights ticketed through an intermediary no longer get a false badge. Rows cached before the
  key existed show no badge.

## Open questions (TODO — verify, then delete this section)
- Versions observed locally (not pinned in the repo: no `.nvmrc`, no `engines`): Node v24.14.0,
  npm 11.9.0, Python 3.11.3. Confirm what Vercel runs, then pin.
- Is the Vercel deploy live? The repo has `vercel.json` and a linked `.vercel/project.json`, but no
  prod URL or env-var setup is documented (see also the Vercel param mismatch under Known issues).
- `test_db.py` is not a test: it prints the table names in Neon's `public` schema (read-only). It has
  no assertions, and `python3 test_db.py` from the repo root currently fails with
  `ModuleNotFoundError: No module named 'config'` (`api/_lib/db.py` imports `config` as a top-level
  module; `api/_lib` is not on the path).