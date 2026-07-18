# PRD — CoShare.jp: 中間発表 → 卒展 production ready

Read CLAUDE.md first. Its Data Contracts, Guardrails, and Definition of Done apply to
every task below. This PRD adds WHAT to build and in what order; CLAUDE.md governs HOW.

---

## OBJECTIVE

Take CoShare.jp from its 2026-07-30 中間発表 state (one-way search, codeshare price-gap
detection, booking links, holiday-aware trend page, Duffel test mode, local-only) to a
**publicly deployed, real-data, abuse-protected web app** presented at 卒展, adding the
四 roadmap features promised on the exhibition panel: round-trip search, flight-number
lookup, real-time FX, and LCC coverage via a second flight-data API.

Why: the product's thesis (same operated flight, different price by marketing carrier)
is proven with test data; 卒展 requires the public to use it with real fares and for
the app to survive unattended public traffic.

---

## SUCCESS — verifiable checklist (final state)

A model can verify each item mechanically:

- [ ] `curl` to the production URL returns the app (HTTP 200, HTML contains "CoShare").
- [ ] Production search KIX→TPE (fresh date) returns offers with real airline names;
      response JSON contains no "Duffel Airways" and no "Hahn Air".
- [ ] Prices come from the data source chosen in M2 (live data); the テスト環境 disclaimer
      is removed from UI and panels' successor materials.
- [ ] Round trip: a search with 復路 date returns itineraries with 2 slices; UI renders
      outbound and return; codeshare comparison works per slice.
- [ ] Flight-number lookup: entering e.g. "NH849" + date returns that flight's codeshare
      comparison directly.
- [ ] FX: JPY conversion uses a rate fetched within the last 24h (endpoint exposes rate
      + timestamp); fixed ¥155 constant no longer referenced in code.
- [ ] LCC coverage: at least one route returns offers sourced from the second API,
      merged and deduplicated against primary-source offers (no duplicate flight rows).
- [ ] Abuse protection: >N searches/minute from one client returns HTTP 429.
- [ ] `npx eslint .` clean; CLAUDE.md Definition of Done steps 1–7 all pass locally.
- [ ] CLAUDE.md "Open questions" section is empty (verified and deleted).

---

## MILESTONES (in order)

- **M0 — Demo protection (now → 7/30)**: freeze holds; only bug fixes for the demo.
- **M1 — Foundation hardening (early Aug)**: resolve unknowns, add tests, clean dead code.
- **M2 — Data-source decision (Aug)**: research spike + HUMAN GATE. Chooses the
  real-price provider and the LCC strategy. Blocks M6/M7 scope details.
- **M3 — Round-trip search (Aug)**
- **M4 — Flight-number lookup (Aug–Sep)**
- **M5 — Real-time FX + deep-link improvements (Sep)**
- **M6 — LCC second-API integration (Sep–Oct)** — shape depends on M2.
- **M7 — Production deployment + abuse protection (Oct, before 本審査)**
- **M8 — 卒展 polish (after 本審査 feedback)**

Human (non-model) tasks run in parallel and are listed in HANDOFF.

---

## TASKS

Each task: files it touches → done-when. Execute in order within a milestone.
Milestones M3–M6 may be reordered by the human if 本審査 feedback demands it.

### M0 — Demo protection
0.1 No code changes except explicit bug-fix requests from Gabriel.
    Files: n/a. Done when: 2026-07-30 has passed.

### M1 — Foundation hardening
1.1 Answer CLAUDE.md Open questions by reading the repo; update CLAUDE.md; delete the
    section. Files: CLAUDE.md. Done when: section removed, claims verified.
1.2 Locate and document (or remove) dead codeshare path: `codeshare_service.py` usage,
    `/api/codeshare/detect`. If pairing lives in frontend, document it in CLAUDE.md
    Architecture. Files: codeshare_service.py, local_server.py, CLAUDE.md.
    Done when: exactly one documented pairing implementation remains.
1.3 Add pytest with tests for `normalizer.py`: ZZ excluded; HR excluded from pairs;
    display fields come from marketing_carrier; owner fallback; Title Case keys stable.
    Use a saved raw Duffel response as fixture (scrub tokens).
    Files: tests/test_normalizer.py, tests/fixtures/duffel_sample.json, requirements.txt.
    Done when: `pytest` green; fixture contains an HR-owned and a ZZ offer.
1.4 Add error handling to `/api/flights/search`: Duffel non-200 → clean JSON error +
    HTTP 502; frontend shows the existing error state (no crash).
    Files: local_server.py, duffel_service.py. Done when: simulated Duffel failure
    (invalid token in a test run) renders エラー UI, no traceback in response.
1.5 Pin versions: create/verify requirements.txt with exact versions; note Node version
    in CLAUDE.md. Files: requirements.txt, CLAUDE.md. Done when: fresh
    `pip install -r requirements.txt` + `npm ci` boots both servers.

### M2 — Data-source decision (research spike; produces a doc, not code)
2.1 Research current (2026) pricing/terms, with sources, for: Duffel live mode
    (per-search cost, activation requirements), Amadeus Self-Service (free production
    quota per endpoint, LCC coverage, JP market coverage), and one fallback
    (e.g. Kiwi/Travelpayouts if still open to individuals). Explicitly note: no official
    Google Flights API exists; scrapers are out of scope.
    Files: docs/data-source-research.md. Done when: doc has a comparison table with
    costs, quotas, LCC coverage, and citation URLs.
2.2 Recommend: primary real-price source + LCC strategy (same API vs second API) +
    est. monthly cost at 100/500/2000 searches. Files: same doc, RECOMMENDATION section.
    Done when: recommendation written. **STOP — HUMAN GATE: Gabriel approves before
    any M6/M7 task referencing the choice.**

### M3 — Round-trip search
3.1 Backend: accept optional `returnDate` param; when present, request two slices from
    the flight API; normalizer emits per-slice data without renaming existing keys
    (additive schema only: new key `'Slices'` alongside existing flat fields for slice 0).
    Files: local_server.py, duffel_service.py, normalizer.py, tests/.
    Done when: curl with returnDate returns 2-slice offers; old one-way response
    unchanged byte-for-byte in structure; pytest green.
3.2 Frontend: add 復路 date field (optional) to search forms; ResultsPage renders
    往路/復路 sections; URL param `returnDate` round-trips.
    Files: frontend/src/components/search/*, pages/ResultsPage.jsx.
    Done when: DoD #3 passes with and without returnDate; eslint clean.
3.3 Codeshare comparison works per slice (outbound and return compared independently).
    Files: wherever 1.2 documented pairing. Done when: a round-trip search shows
    CodeShareCards for both directions on a route with codeshares (KIX→TPE).

### M4 — Flight-number lookup
4.1 Backend: `GET /api/flights/lookup?flightNumber=NH849&date=YYYY-MM-DD` — parse
    carrier code + number; search the carrier's route(s) for that date; return the
    matching operated flight's full codeshare comparison. If the API cannot search by
    flight number directly, implement as: resolve flight → origin/destination via the
    flight API's schedule data, then reuse existing search + filter.
    Files: local_server.py, new service function, tests/.
    Done when: curl for a known codeshare flight returns its comparison; unknown
    flight returns clean 404 JSON.
4.2 Frontend: 「便名で調べる」 entry on HomePage (tab or secondary form) → results view
    reusing CodeShareCard. Files: HomePage.jsx, ResultsPage.jsx or new page.
    Done when: typing NH849 + date shows the comparison; invalid input shows
    validation message.

### M5 — Real-time FX + deep-link improvements
5.1 FX service: fetch JPY rates daily from a free API (e.g. exchangerate.host or the
    one Gabriel's exchangerate account covers), cache in DB table `fx_rates`
    (currency, rate, fetched_at); fall back to last cached rate on failure; remove the
    ¥155 constant. Files: new fx_service.py, db.py, local_server.py, tests/.
    Done when: SUCCESS FX item passes; killing network still serves cached rate.
5.2 Deep links where documented: for airlines with publicly documented URL params
    (research each; do NOT pattern-guess), upgrade booking links to pre-filled search
    URLs; others keep top-page links. Add `deepLink: true/false` per entry.
    Files: airlineBookingUrls.js. Done when: each upgraded URL manually click-verified
    by Gabriel (list them for him); no URL constructed by guessing.

### M6 — LCC second API (shape set by M2 decision)
6.1 Adapter: new service module for the chosen second source, output conforming to the
    SAME normalized offer schema (Title Case keys). Files: new service module,
    normalizer.py (shared normalize entry), tests with fixture.
    Done when: adapter unit tests green; schema identical to Duffel path.
6.2 Merge + dedupe: combine sources; duplicate = same operating carrier + flight number
    + departure datetime; prefer the cheaper offer, tag `'Source'` key.
    Files: local_server.py or new merge module, tests/.
    Done when: fixture with an overlapping flight yields one row, cheaper price kept.
6.3 LCC display: solo LCC offers render as standalone cards (existing behavior for
    non-codeshare offers); LCC prices join trend history writes.
    Files: minimal frontend, db write path. Done when: a known LCC route (e.g.
    KIX→ICN) shows LCC offers with correct names.

### M7 — Production deployment + protection
7.1 Migrate to the M2-chosen live data source (token, env vars in Vercel, remove
    test-mode disclaimers from UI). Files: config, duffel_service.py or successor,
    UI text. Done when: prod search returns real fares; SUCCESS items 2–3 pass.
7.2 Rate limiting: per-IP limit on /api/* (e.g. 10 searches/min) returning 429 with a
    friendly JSON message; frontend shows 「少し待ってから再検索してください」.
    Files: local_server.py (or Vercel middleware), one frontend error branch.
    Done when: scripted 20 rapid requests → 429s after the limit; UI message shows.
7.3 Deploy: Vercel production project, env vars set, Neon production branch, seed
    trend data for 3 demo routes via seed_trend_data.py against prod.
    Files: vercel.json, docs/deploy.md. Done when: SUCCESS item 1 passes; deploy
    steps reproducible from docs/deploy.md.
7.4 Observability minimum: log each search (route, date, source, duration, status) to
    a DB table or Vercel logs; document where to look when the app misbehaves at 卒展.
    Files: local_server.py, docs/deploy.md. Done when: one prod search is findable
    in logs by route string.

### M8 — 卒展 polish
8.1 Incorporate 本審査 feedback (tasks TBD — human writes them into this file).
8.2 QR code target check: prod URL stable, OGP tags (title/description/image) set so
    the link previews well. Files: frontend/index.html. Done when: OGP validator
    shows title + image.
8.3 Final pass: CLAUDE.md Definition of Done + this file's SUCCESS list, all green,
    documented in docs/release-checklist.md with date.

---

## HANDOFF — conventions, gotchas, work order

**Work order rules**
1. One milestone at a time, tasks in order. Do not start M6/M7 specifics before the
   M2 human gate is approved.
2. Before each task: re-read CLAUDE.md Data Contracts. After each task: run CLAUDE.md
   Definition of Done (steps relevant to what you touched) + the task's done-when.
3. Show diffs before explanations. Small PRs/commits per task, message `M3.2: ...`.
4. STOP and ask a human before: spending money, changing the normalized schema
   (additive is OK, renames are not), any DB DDL/DELETE (output SQL instead),
   removing any exclusion filter (ZZ/HR), touching airlineBookingUrls.js values.

**Gotchas (these have all actually happened)**
- Flask is :8000, use 127.0.0.1. Port 5000 is macOS AirPlay and answers 403.
- Test with never-searched dates; the cache replays pre-fix data.
- `offer.owner` is the ticketing entity — display uses segment marketing_carrier.
- DB carrier columns hold NAMES ("China Airlines"), not IATA codes.
- Normalized keys are Title Case with spaces ('Total Amount') — do not "fix".
- Airline URLs break on pattern-guessing (China Airlines is /jp/jp/, not /jp/ja).
- Airline schedules exist ~11 months out; date-horizon effects skew any price stats.
- After agent test runs, dev servers are dead; restart before manual verification.

**Human-only tasks (not for the model, tracked here for completeness)**
- 中間発表 physical prep: A4 test prints, 入稿 by the ゼミ deadline, iPad 操作説明動画.
- M2 gate decision + budget approval; Duffel/Amadeus account/verification steps.
- Click-verification of all booking/deep-link URLs (5 min per batch).
- 本審査 feedback → write M8.1 tasks into this file.
- Fill real dates: 本審査 = ____ , 卒展 = ____ (update M6–M8 pacing once known).
