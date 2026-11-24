# CoShare.jp (smart-travel-companion) — CLAUDE.md

卒業制作: 同一運航便のコードシェア価格差を検出・解説する航空券比較Webアプリ。
Owner: Gabriel (4年・松村ゼミ)。Interim presentation 2026-07-30 (done). Final assessment: January 2027.

Product context: @PRODUCT.md / Design system: @DESIGN.md

## Priorities (target: January 2027 final assessment)
The 2026-07-30 mid-term demo has passed. Still off-limits WITHOUT an explicit request:
- renaming normalized offer keys (see Data Contracts)
- changing the codeshare pairing logic (`groupOffers`: nonstop grouping by `Departure Time` + `Operating IATA`, see Architecture)
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
- **Check before starting a server**: run `lsof -nP -iTCP:8000 -sTCP:LISTEN` and
  `lsof -nP -iTCP:5173 -sTCP:LISTEN`. If a server is already running and responds, reuse it
  for verification instead of starting another.
- **Only stop processes you started in this session.** Never kill a process you did not
  start. If the port is held by something else, report it and ask the owner.
- **If you start Flask or Vite for a check, stop it before you finish** (stop the parent
  process first; Flask debug mode runs a reloader parent and child). State in your report
  which servers you started and that they are stopped.
- The Flask debug reloader picks up code edits, so a restart is usually not needed. If you
  think one is, ask the owner.

## Architecture
- `frontend/` React + Vite SPA. Pages: HomePage, ResultsPage, TrendPage, DestinationPage.
  ResultsPage state lives in **URL search params** (useSearchParams) — a new search
  updates the query string, and the fetch effect depends on it. Do not move search
  state back to location.state (breaks re-search on the results page).
- `local_server.py` (repo root) Flask routes under `/api/*` for local dev.
- `api/<area>/*.py` Vercel serverless handlers; shared backend modules live in `api/_lib/`.
- `api/_lib/duffel_service.py` Duffel API calls (offer_requests, return_offers=true).
- `api/_lib/normalizer.py` raw Duffel → normalized offers. All display-carrier logic is here.
- `api/_lib/search_service.py` `get_normalized_offers(origin, destination, departure_date,
  passengers, cabin_class)`: the one search path. Used by `/api/flights/search` and
  `/api/codeshare/detect` in both `local_server.py` and the Vercel handlers. Cache read, else
  Duffel fetch → normalize (ZZ dropped) → `search_cache` write + `price_history`. **The cache
  always holds the FULL normalized list**, under the key `cache_route()` =
  `f"{SEARCH_CACHE_VERSION}:{origin}-{destination}"` (`"v2:KIX-TPE"`; `route` is varchar(20) in
  both tables). Bump `SEARCH_CACHE_VERSION` when the cached payload changes; old rows are left
  to expire (the 24h TTL), never deleted. A Duffel error (`errors` or no `data`) or an empty
  normalized list writes nothing and returns `[]`, so the next request retries Duffel.
  `price_history` keeps the unprefixed route (`KIX-TPE`), which `trend_service` reads. The history
  rows of one search go in as a single batch (`db.save_price_history_batch`: one connection, one
  INSERT, one transaction) and **only for economy with exactly one adult** (`passengers == ["adult"]`,
  JPY offers only): the table has no cabin or passenger column, and a 2-adult total is double.
  A failed `search_cache` or history write is logged as a warning and never breaks the response
  (a failed batch rolls back that search's history rows). `db.save_price_history` (one row) remains.
- `api/_lib/snapshot_service.py` + `api/_lib/demo_snapshots/<ORIGIN>-<DEST>_<DATE>.json` (stdlib only):
  saved Duffel test-environment results for the demo, one file per exact search (full normalized
  list + `route`, `departure_date`, `cabin_class`, `passengers`, `source`, `captured_at`). Hook:
  `search_service.search_offers()` wraps `get_normalized_offers` (unchanged) and `search_payload()`
  builds the response body; `local_server.py` and both Vercel search handlers call `search_payload`.
  A snapshot is served only for an exact match (economy, one adult, a file for that route and date)
  and only when `DEMO_SNAPSHOT` is on (returns before any cache, Duffel or DB access) or when the
  live search raised or returned no offers. It then goes through the same mode filter as live data
  and is never written to `search_cache` / `price_history`. See "Demo mode" below.
- `api/_lib/codeshare_service.py` `filter_codeshare_offers(normalized)`: the keep rule for codeshare
  mode. An offer is kept if (a) it passes the original rule, `is Codeshare` and `Owner Airline IATA`
  not in `{"HR"}` (an *anchor*), or (b) it is a non-HR nonstop offer in the same pairing group as
  an anchor. The group key is the one `groupOffers` uses: `Departure Airport`, `Arrival Airport`,
  `Departure Time`, `Operating IATA`. So the operating carrier's own-code offer (BR131 next to
  NH5811, NH829 next to AI8001) stays beside the codeshare offer it is compared with. Connecting
  offers (`'Segment Count' > 1`, their key describes only the last leg) and rows lacking
  `Departure Time` or `Operating IATA` are never grouped, so they pass only on rule (a) and never
  anchor a group. HR-displayed offers are always dropped and never anchor. `get_codeshare_offers(raw)`
  is the same rule on a raw Duffel response. Only `/api/codeshare/detect` (ResultsPage mode
  `codeshare`) applies it, **after** the cache read on every request; `/api/flights/search`
  (mode `both`) returns the full list, so it does no server-side HR filtering. It changes only
  which offers are returned: the cache, `price_history` and the trend tab never see the filter.
- **Pairing runs in the frontend**: `groupOffers(offers, mode)` in
  `frontend/src/utils/groupOffers.js` (pure; tests in `groupOffers.test.mjs`), called from
  `ResultsPage.jsx`. Nonstop offers are grouped by
  `` `${Departure Airport}_${Arrival Airport}_${Departure Time}_${Operating IATA}` `` (airports
  keep e.g. HND and NRT departures at the same time from pairing);
  groups with >1 offer are codeshare groups (gap logic in `frontend/src/utils/codeshareGap.js`).
  Display order (order only, not pairing): groups with a real gap, largest gap first (stable, so equal
  gaps keep their arrival order), then tied groups, then single offers (then connecting offers in 両方 mode);
  tests in `groupOffers.order.test.mjs`.
  An offer with `'Segment Count' > 1` never joins a group (its key describes only the last leg);
  offers with `'Segment Count'` 1 or absent (older cache rows) group as before. Codeshare mode
  drops connecting offers (and single nonstop offers whose `is Codeshare` is false); 両方 mode
  renders each connecting offer as its own FlightCard, after the nonstop groups.
- `api/_lib/db.py` Neon PostgreSQL: `search_cache`, `price_history`.
- `seed_trend_data.py` (repo root) populates price history for demo routes (GET loop via :8000).

## Data Contracts (do not change silently)
- **Search API**: `GET /api/flights/search?origin=KIX&destination=TPE&departureDate=YYYY-MM-DD&passengers=adult&cabinClass=economy`
  — camelCase param names. Response: `{"data": [<normalized offers>]}`. When a saved demo snapshot
  is served, three more top-level fields appear: `data_source` (`"snapshot"`), `captured_at` (ISO UTC)
  and `snapshot_source`; live responses carry none of them.
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
    `'Owner Airline IATA'`, `'First Departure Time'` (the departure to DISPLAY; absent on
    `search_cache` rows written before it existed, so the UI reads it via `displayDeparture` in
    `frontend/src/utils/flightDetails.js`, which falls back to `'Departure Time'`), and the
    additive detail keys `'Marketing Flight Number'`, `'Operating Flight Number'` (may be null),
    `'Departure Airport'`, `'Arrival Airport'`,
    `'Segment Count'` (segments in slice 0). Detail keys are absent on `search_cache` rows
    written before they existed — the UI omits absent fields and only offers expandable
    details when `Segment Count === 1`.
  - `'Departure Time'` stays the LAST leg: grouping/pairing and verified-checks code keep using
    it, but it must NOT be used to display a departure (use `displayDeparture`). For
    `'Segment Count' > 1` the cards show 「乗り継ぎ{n-1}回」 and 「乗り継ぎ便」 instead of the
    last leg's operator.
  - So on a connection the display carrier (first leg) and the pairing key
    (`Departure Time` + `Operating IATA`, last leg) describe different legs; for that reason
    connecting offers are excluded from pairing (see Architecture).
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

## Real prices dataset (hand-curated)
- Data: `api/_lib/real_prices.json`; loader/validator/lookup: `api/_lib/real_prices.py`
  (`lookup_response`, shared by `local_server.py` and `api/real-prices/index.py`); tests:
  `tests/test_real_prices.py`. Shown on ResultsPage as 「実測価格との比較」, nonstop flights only,
  apart from the Duffel cards. One record per (origin, destination, flight_date).
- The owner verifies and maintains the data. A scraper run (`scripts/fetch_real_prices.py`, not
  committed) only produces a candidate; hand-verified overrides are applied before merging, and
  the record's `source` says so (「…・一部手動確認」).
- **Outlier rule:** when the lowest listed price is more than 30% below the official site price,
  store the official price (`seller` = the official site, `airline_site_price_jpy` = same value)
  and say why in the entry's `note`. Tested in `Feb2027RecordsTest`.
- `same_flight_as` goes on the pricier flight. Set `operating_code` and `same_flight_as` only for
  codeshares whose operating carrier is confirmed; otherwise keep the flights as plain entries.

## Demo mode (saved test data)
So the demo does not depend on what Duffel returns that day, two searches can be served from saved
Duffel test-environment results (`api/_lib/demo_snapshots/`). The results page then shows
「保存済みのDuffelテストデータを表示しています(取得日 YYYY-MM-DD)」 (the UTC date of `captured_at`)
next to the usual test-data notice.
- Run the backend in demo mode (after the `lsof` check above): `DEMO_SNAPSHOT=1 python3 local_server.py`
  (or put `DEMO_SNAPSHOT=1` in `.env.local`; values `1`, `true`, `yes`, `on` count). The variable is
  read on every request. On Vercel it is a project environment variable.
- Run the frontend as usual: `cd frontend && npm run dev`, then open http://localhost:5173.
- Only these searches match a snapshot (route, date, economy, 1 adult; any other search is live):
  - KIX → TPE, 2027-02-22 (captured 2026-11-23, 70 offers)
  - NRT → BOM, 2027-02-22 (captured 2026-11-04, 116 offers; holds the AI8001 / NH829 pair at 11:15)
- Without `DEMO_SNAPSHOT`, a snapshot appears only as a fallback, when the live search raised an
  exception or returned no offers (a Duffel error, or only ZZ offers). A fresh cache hit still wins.
  Duffel calls have no timeout, so a hanging Duffel never reaches the fallback; use `DEMO_SNAPSHOT=1`
  for the demo.
- Forced mode needs no database for the offers. The verified-check badges, real prices and trend
  pages still read their own sources.
- Updating a snapshot: replace the file with a newer full normalized list for the same search and a new
  `captured_at`; `snapshot_service.validate_snapshot` rejects a malformed file (the search then runs live).
  Tests: `tests/test_snapshot_service.py`, `frontend/src/utils/snapshotNotice.test.mjs`.

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
- `price_history` has NO `cabin_class` or passenger column. Since the batch writer only records
  economy + one adult, other searches no longer add rows, but rows written before that guard may be
  2-adult or non-economy. If you must test other searches, note the route + departure dates so cleanup
  SQL can be written (output it for review; never execute — see Guardrails).
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

## Destination catalog (hand-curated)
- Data: `api/_lib/destination_catalog.json` (`{"destinations": [...]}`, a list, one entry per
  `iata`). Loader/validator: `api/_lib/destination_catalog.py` (`load_catalog`, `validate_entry`,
  `validate_catalog`; stdlib only). Tests: `tests/test_destination_catalog.py`.
- Entry fields: `iata`, `city` / `country` (Japanese), `bestMonths` (1-12), `budgetLevel` (1-3,
  1 low), `tags` (only: food, city, culture, nature, beach, shopping, nightlife, relax),
  `highlights` (3-5 of title/note/sourceUrl), `hotelAreas` (2-3 of name/note/sourceUrl),
  `mapQuery` (non-empty), optional `caution`, `lastChecked` (ISO date).
- **The owner writes and maintains every real entry.** An agent must not invent entries or facts.
  Every highlight and hotel area needs a source link (`https://`). The file holds one
  `"example": true` placeholder, which the loader skips.
- Planned source for the destination and trip pages, read through a future API endpoint (the
  frontend must not import the file). **Nothing reads it yet.** It is separate from
  `destination_cache` / `recommendation_service.py`, which are unchanged.

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
- **HR is filtered only on `/api/codeshare/detect`** (`filter_codeshare_offers`, on
  `Owner Airline IATA`). `/api/flights/search` returns HR offers unfiltered.
- **Vercel handlers vs contract.** `api/flights/search.py` and `api/codeshare/detect.py` read
  snake_case params (`departure_date`, `cabin_class`); the contract and `local_server.py` use
  camelCase (`departureDate`, `cabinClass`).
- **Vite proxy target.** `frontend/vite.config.js` proxies `/api` to `http://localhost:8000`,
  which works for the browser in dev. The 127.0.0.1 rule applies to scripts and `curl`.
- **`is Codeshare` is unchanged on purpose, and it is not a reliable "is a codeshare" flag.** The
  normalizer sets it when marketing != operating carrier **or** when `offer.owner` (the ticketing
  entity, not stored in the cached row) != the operating carrier. Two consequences. An own-code
  offer ticketed by HR (e.g. owner `HR`, marketing = operating = `CI`/`KE`/`7C`) is `True`, so it
  always passed the filter. An own-code offer ticketed by the airline itself (`BR131`, `NH829`,
  owner = marketing = operating) is `False`. Before the group keep rule, that made codeshare mode
  drop the operating carrier's own offer and leave only a lone ANA / Air India card, while CI/JAL
  pairs survived by accident of who ticketed the CI fare. The keep rule above fixes that in the
  filter; the flag itself still behaves as described. `groupOffers` also reads it (single nonstop
  offers are dropped in codeshare mode unless it is true). Do not change the rule without
  checking `/api/codeshare/detect` first.
- **Connecting itineraries are never paired.** Codeshare price gaps are detected for nonstop
  offers only (`'Segment Count'` 1 or absent); codeshare mode hides connecting offers entirely
  and 両方 mode lists them as single FlightCards. Offers cached before `'Segment Count'` existed
  still group by the old last-leg key, so a connection cached that way can still be paired
  falsely until its `search_cache` row expires (24h). A proper itinerary key (all legs) would
  be needed to pair connections; not done.
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