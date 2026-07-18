# CoShare.jp (smart-travel-companion) — CLAUDE.md

卒業制作: 同一運航便のコードシェア価格差を検出・解説する航空券比較Webアプリ。
Owner: Gabriel (4年・松村ゼミ)。中間発表 **2026-07-30**。

Product context: @PRODUCT.md / Design system: @DESIGN.md

## Priorities (until 2026-07-30)
Demo stability wins every tradeoff. Concretely, WITHOUT an explicit request do not:
- upgrade or add dependencies
- refactor: `normalizer.py`, the codeshare pairing logic, `db.py`, ResultsPage search-param handling
- change the normalized offer schema (see Data Contracts)
- run destructive DB operations (see Guardrails)
Small, reviewable diffs. Show the diff before explaining it.

## Run / Dev
- Backend: `python3 local_server.py` from repo root → Flask on **http://127.0.0.1:8000**
  - Port 5000 is macOS AirPlay — never use it. Always `127.0.0.1`, never `localhost`
    (IPv6 resolution sends requests to the wrong listener).
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
- `local_server.py` Flask routes under `/api/*`.
- `duffel_service.py` Duffel API calls (offer_requests, return_offers=true).
- `normalizer.py` raw Duffel → normalized offers. All display-carrier logic is here.
- `codeshare_service.py` exists; `get_codeshare_offers` is currently NOT called in the
  search route (commented out). TODO(Gabriel): document where pairing actually runs.
- `db.py` Neon PostgreSQL: `search_cache`, `price_history`.
- `seed_trend_data.py` populates price history for demo routes (GET loop via :8000).

## Data Contracts (do not change silently)
- **Search API**: `GET /api/flights/search?origin=KIX&destination=TPE&departureDate=YYYY-MM-DD&passengers=adult&cabinClass=economy`
  — camelCase param names. Response: `{"data": [<normalized offers>]}`.
- **Normalized offer keys are Title Case with spaces**: `'Total Amount'`, `'Currency'`,
  `'Marketing Carrier'`, `'Operating Carrier'`, … Do NOT rename to snake_case/camelCase;
  React components and `save_price_history` read these exact strings.
- **Display carrier = `slices[0].segments[0].marketing_carrier`** (name + iata_code),
  flight number from `marketing_carrier_flight_number`. Duffel's `offer.owner` is the
  *ticketing* entity, not the seller — never use it for display. Fallback to owner only
  if marketing_carrier is missing.
- **Excluded carriers**: `ZZ` (Duffel Airways, test-env synthetic) dropped in
  `normalizer.py`; `HR` (Hahn Air, ticketing broker — no consumer booking page)
  excluded from codeshare comparison pairs.
- **DB carrier columns store NAMES, not IATA codes** (`marketing_airline = 'China Airlines'`).
  Write SQL against names.
- **Trend cutoff**: price-history aggregation excludes departure dates > ~10 months out
  (airline schedule horizon skews averages). Applies to the chart AND the 最安月/最高値月
  stat cards, server-side. Search itself is not date-limited.
- Prices JPY; fixed rate ¥155/USD (real-time FX is post-demo roadmap).
- Booking links: static map `frontend/src/constants/airlineBookingUrls.js`, keyed by
  IATA code, values are official-site URLs (Japan locale where available). URLs are
  hand-verified by clicking — an agent must not "correct" them from pattern-guessing
  (that's how `/jp/ja` broke; China Airlines is `/jp/jp/`). Missing code → render no button.

## Environment
- Duffel is in **TEST MODE**: prices are synthetic; ZZ offers appear in raw responses.
  Do not present prices as real-market data.
- Secrets: `DUFFEL_ACCESS_TOKEN` via `config.py` / `.env.local`. Never print or commit tokens.

## Testing discipline
- `search_cache` may contain rows written BEFORE normalizer fixes. When testing any
  normalization/display change, use a **never-searched date** to force a fresh Duffel
  fetch; cached dates replay old data and give false results.
- Cached searches do not write price history; only fresh fetches do (JPY offers only).

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
- Do not add features before 2026-07-30 unless explicitly asked.
- When a fix depends on a Duffel response field, verify against a real raw response
  (temporary dump), not from memory of the API shape.

## Open questions (TODO — verify in repo, then delete this section)
- Where does codeshare pairing actually execute now (frontend? `/api/codeshare/detect`?)
- Exact `passengers` param format for multiple passengers (comma list? repeated param?)
- Node/npm and Python versions in use (pin them here once known)
- Is `vercel.json` deploy live? If yes, document the prod URL and env-var setup
- Does `test_db.py` still pass / what does it cover?