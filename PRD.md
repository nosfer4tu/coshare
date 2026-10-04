# PRD — CoShare.jp: interim → final assessment (January 2027)

Read CLAUDE.md first. Its Data Contracts, Guardrails, Known issues, and Definition of Done
apply to every task below. This PRD adds WHAT to build and in what order; CLAUDE.md governs HOW.

Status as of 2026-10-04. Dates not known yet are marked TODO(Gabriel); do not invent them.

---

## OBJECTIVE

Take CoShare.jp from its post-interim state (one-way search, codeshare price-gap detection,
booking links, holiday-aware trend page, expandable flight details, price-difference
explainer; Duffel test mode) to an **honest, publicly demonstrable app** for the final
assessment (January 2027, exact date TODO(Gabriel)), with its data limitations disclosed
in the UI and documented.

The interim presentation promised a public release with a QR code by the 卒展 (graduation
exhibition); that promise stands. TODO(Gabriel): confirm the 卒展 date and whether it is the
same event as the January final assessment.

"Production ready" means exactly that: a deployed, abuse-protected app whose users can see
where each number comes from and what it is not. It does NOT require live market prices.

Why: the thesis (same operated flight, different price by marketing carrier) is shown with
real codeshare relationships. Duffel live mode is unavailable (Japan is not selectable in
Duffel's team-registration country dropdown), so prices stay synthetic. The credible path
is to say so plainly, cross-check what can be cross-checked, and show manually verified
price checks as trust evidence.

### Data strategy (decision record)

Multi-source, not one live API. Each source has a defined role and a defined limit:

| Source | Role | Limits |
|---|---|---|
| Duffel, test mode | Primary: real codeshare relationships | Prices are synthetic. Never present them as market data. |
| FlightLabs (Starter plan) | Secondary price source | No owner/issuer field; inconsistent LCC coverage; `flightNumber` unreliable in three route-dependent failure modes (TODO(Gabriel): list them; the repo only shows null `flightNumber` and OTA names in carrier fields, see `scripts/flightlabs_report.md`). **Not wired into the backend yet**: only exploration scripts in `scripts/`. |
| ODPT | Cross-check for pairing | Free JAL/ANA schedule and codeshare data; no prices. Registration status: TODO(Gabriel). |
| `verified_checks` | Trust badges | Manually verified route/carrier price checks. In progress: schema file exists (`database/schemas/seed_verified_checks.sql`), no code uses it yet. |
| Norba (NDC aggregator) | Optional upgrade | JAL/ANA/LATAM support expected, unconfirmed. Not a dependency. |

**Ruled out** (outcome only): Skyscanner, Amadeus Self-Service, Google Flights (no official
API; scrapers out of scope), Travelpayouts, TripStack, NUUA, SerpApi, Airlabs, LetsFG,
NAVITIME. Verteil: IATA-accredited agencies only. Mystifly: terms incompatible with the
project. Duffel live mode: unavailable (see above). TODO(Gabriel): one-line reasons for
the others if the final report needs them.

---

## SUCCESS — verifiable checklist (final state)

A model can verify each item mechanically:

- [ ] `curl` to the production URL returns the app (HTTP 200, HTML contains "CoShare").
- [ ] Production search KIX→TPE (fresh date), in both ResultsPage modes (`codeshare`,
      `both`): real airline names; the displayed results contain no "Duffel Airways" and
      no "Hahn Air".
- [ ] Disclosure: ResultsPage and TrendPage show a visible, non-dismissible notice that
      prices are synthetic test data (Duffel test mode); the notice text appears in the
      rendered page of both. The テスト環境 disclaimer is NOT removed.
- [ ] A 「データについて」 page (or equivalent) is linked from the navbar and lists, per
      source in the table above, what it provides and what it does not.
- [ ] `docs/data-verification.md` exists and matches the Data strategy table (sources, roles,
      limits, ruled-out list), with no commercial terms or correspondence details.
- [ ] Verified badges: a route/carrier with a `verified_checks` row shows a badge with the
      check date, linking to the verification page; a route/carrier without a row shows none.
      At least TODO(Gabriel) checks are recorded.
- [ ] ODPT cross-check (if registration succeeds): a script compares ODPT JAL/ANA codeshare
      data with the app's pairs for chosen routes and prints agreements and mismatches.
      If registration does not happen, this item is marked "not pursued" with the reason.
- [ ] Round trip: a search with 復路 date returns itineraries with 2 slices; UI renders
      outbound and return; codeshare comparison works per slice.
- [ ] Flight-number lookup (scope per M7 flag): entering e.g. "NH849" + date returns that
      flight's codeshare comparison directly.
- [ ] FX: JPY conversion uses a rate fetched within the last 24h (endpoint exposes rate +
      timestamp); the fixed ¥155 constant is no longer referenced in code.
- [ ] Abuse protection: >N searches/minute from one client returns HTTP 429.
- [ ] Known issues in CLAUDE.md are each either fixed (entry removed) or explicitly
      accepted (entry reworded as accepted, with the reason).
- [ ] `npx eslint .` clean; CLAUDE.md Definition of Done steps 1–7 all pass locally.
- [ ] CLAUDE.md "Open questions" section is empty (verified and deleted).

Removed from the earlier checklist: "Prices come from live data / test disclaimer removed"
and "LCC offers from a second API merged" (their premise, live mode, is gone).

---

## MILESTONES (in order)

Dates: TODO(Gabriel) for every milestone. Order is a default; Gabriel may reorder M5–M8.

- **M0 — Demo protection — DONE.** The 2026-07-30 interim presentation is done; the freeze
  is lifted.
- **M1 — Foundation hardening — PARTLY DONE.** Docs done; tests, error handling, pins open.
- **M2 — Data-source decision — COMPLETED, outcome recorded** (Data strategy above).
- **M3 — Known-issue fixes** (from CLAUDE.md "Known issues").
- **M4 — Disclosure + verified badges.**
- **M5 — Multi-source plan** (FlightLabs handling, ODPT cross-check, optional Norba).
- **M6 — Round-trip search.**
- **M7 — Flight-number lookup.** Flagged: dependency changed.
- **M8 — FX + deep-link improvements.**
- **M9 — Deployment + abuse protection.** Targets the 卒展 public release (QR code to the
  production URL); date TODO(Gabriel).
- **M10 — Final-assessment polish.**

Human (non-model) tasks run in parallel and are listed in HANDOFF.

---

## TASKS

Each task: files it touches → done-when. Execute in order within a milestone.
Any task touching the codeshare pairing logic, normalized key names, or the ZZ/HR
exclusions needs Gabriel's explicit go-ahead first (CLAUDE.md Priorities).

### M0 — Demo protection — DONE
Evidence: interim presentation held; CLAUDE.md Priorities rewritten (commit cc27d79).

### M1 — Foundation hardening
- 1.1 DONE (partly) — CLAUDE.md Open questions answered by reading the repo (cc27d79).
      Remaining: the section still holds 3 entries (versions, Vercel live status,
      `test_db.py`). Files: CLAUDE.md. Done when: section removed, claims verified.
- 1.2 DONE (partly) — pairing is documented in CLAUDE.md Architecture (frontend grouping in
      `ResultsPage.jsx`; server-side filter in `get_codeshare_offers`). Both paths remain
      live; collapsing them is not planned. Done when: CLAUDE.md states which path each
      ResultsPage mode uses (already true) and Known issues tracks the differences (M3).
- 1.3 NOT DONE — add pytest tests for `api/_lib/normalizer.py`: ZZ excluded; HR excluded
      from pairs; display fields from marketing_carrier; owner fallback; Title Case keys
      stable; a connecting-itinerary fixture documenting which keys reflect the last vs
      first segment (see 3.5). Use a saved raw Duffel response as fixture (scrub tokens;
      do not commit dump files). Files: tests/test_normalizer.py,
      tests/fixtures/duffel_sample.json, requirements.txt. Done when: `pytest` green;
      fixture contains an HR-owned offer, a ZZ offer, and a 2-segment offer.
- 1.4 NOT DONE — error handling on `/api/flights/search` and `/api/codeshare/detect`:
      Duffel non-200 → clean JSON error + HTTP 502; frontend shows the existing error
      state. Files: local_server.py, api/_lib/duffel_service.py. Done when: simulated
      Duffel failure (invalid token in a test run) renders the エラー UI, no traceback.
- 1.5 PARTLY DONE — `requirements.txt` is pinned but contains unrelated packages
      (e.g. firebase_admin, flet, openai, yt-dlp). Prune only after confirming each is
      unused (dependency changes need Gabriel's go-ahead); pin the Node version in
      CLAUDE.md once the Vercel runtime is known. Files: requirements.txt, CLAUDE.md.
      Done when: fresh `pip install -r requirements.txt` + `npm ci` boots both servers.

### M2 — Data-source decision: completed, outcome recorded
The decision and the ruled-out list are recorded in OBJECTIVE → Data strategy. No further
research task. Evidence of the FlightLabs investigation: `scripts/flightlabs_report.md`,
`scripts/flightlabs_*_candidates.*`, `scripts/flightlabs_null_flightnumber_investigation.py`
(commit 9b9ad4d).
- 2.1 `docs/data-verification.md` is the single document for data sources and verification.
      A separate task writes it; this PRD only references it (no second document). Done
      when: that file includes the Data strategy table and the ruled-out list, with no
      commercial terms and no correspondence details.

### M3 — Known-issue fixes (CLAUDE.md "Known issues")
- 3.1 Shared `search_cache` key. Make the two routes stop replaying each other's stored
      result. Approach TODO(Gabriel): store unfiltered normalized offers on both routes and
      apply `get_codeshare_offers` after reading, OR separate the key. Do not change the
      schema without approval (DDL is human-run). Files: local_server.py, api/_lib/db.py
      (only if the key changes). Done when: with a fresh date, `codeshare` then `both`
      searches (and the reverse) each return their own correct result within the 24h TTL.
- 3.2 HR filtering consistency. Decide where HR is excluded so both routes behave the same
      (CLAUDE.md DoD item 2 says no "Hahn Air" anywhere in results). Removing the exclusion
      is not allowed; extending it to `/api/flights/search` is the intent. Files:
      local_server.py, api/_lib/codeshare_service.py. Done when: a fresh-date KIX→TPE search
      in `both` mode returns no Hahn Air offers.
- 3.3 Vercel handlers vs contract. `api/flights/search.py` and `api/codeshare/detect.py`
      read snake_case params; the contract is camelCase. Align the handlers to the
      contract (or accept both). Files: api/flights/search.py, api/codeshare/detect.py.
      Done when: the same query string works against `local_server.py` and the handlers
      (run via `vercel dev` or equivalent; TODO(Gabriel) which).
- 3.4 `is Codeshare` semantics. The flag is set per segment (last wins) and is true when
      operating IATA != marketing IATA OR `offer.owner` IATA != operating IATA, so a solo
      flight ticketed through an intermediary gets the コードシェア便 badge. FIRST
      investigate: run a fresh-date `/api/codeshare/detect` search and record which
      offers `get_codeshare_offers` keeps because of the second clause (e.g. own-code
      offers from HR-ticketed carriers such as CI), and where `ResultsPage.jsx` reads the
      flag. Only then propose a rule change, for Gabriel's approval. Files (investigation):
      none changed; findings go in CLAUDE.md Known issues. Done when: findings are
      recorded and Gabriel has decided (change / keep and relabel the badge).
- 3.5 Segment-overwrite behavior. For connecting itineraries, Operating Carrier,
      Marketing Carrier, Operating/Marketing IATA, Departure/Arrival Time and
      `is Codeshare` reflect the last segment; Owner Airline and the detail keys reflect
      the first. Decide: keep and keep documenting, or change. Any change to key semantics
      needs approval. Minimum deliverable: the 1.3 connecting-itinerary fixture and test
      pin the current behavior. Files: tests/. Done when: the test passes and CLAUDE.md
      matches it.
- 3.6 `price_history` is economy-only in practice. The table has no `cabin_class` column,
      so non-economy searches contaminate trend data. Guard the writes: only save price
      history when `cabinClass` is economy. Do not add a column (DDL is human-run).
      Cleanup of rows already written by non-economy test searches: output SQL for manual
      review in the Neon console, never executed by the model. Files: local_server.py
      (both search routes). Done when: a fresh-date non-economy search writes no
      `price_history` rows (checked by Gabriel in Neon) and an economy search still does.
      TODO(Gabriel): which route/dates were searched with non-economy cabins.
- 3.7 Vite proxy target. `frontend/vite.config.js` proxies to `localhost:8000`, which works
      for the browser in dev. No change planned. Done when: either a proxy failure is
      reproduced (then change the target to `127.0.0.1:8000` and update CLAUDE.md) or the
      Known issue is reworded as accepted.

### M4 — Disclosure + verified badges
- 4.1 Persistent test-data notice on ResultsPage and TrendPage (text TODO(Gabriel), Japanese
      first; plain and factual, per PRODUCT.md and DESIGN.md; no new accent usage beyond
      the One Signal Rule). Files: frontend/src/pages/ResultsPage.jsx, TrendPage.jsx,
      a small shared component. Done when: SUCCESS disclosure item passes; eslint clean.
- 4.2 「データについて」 page, linked from the navbar: per source, what it provides and
      what it does not (from the Data strategy table). Files: frontend/src/pages/,
      App.jsx routes, Navbar.jsx. Done when: SUCCESS data-page item passes.
- 4.3 `verified_checks` backend read path: a read-only endpoint returning checks for a
      route (and carrier). The table exists as a schema file only; confirming it exists in
      Neon, and creating it if not, is a human step (DDL: output SQL, do not run).
      Files: api/_lib/db.py (read function), local_server.py (+ matching `api/` handler).
      Done when: curl returns a seeded row; empty list for an unverified route.
      Status: done (api/_lib/db.py, local_server.py, api/_lib/verified_checks.py; Vercel handler skipped by decision)
- 4.4 Verified badge on CodeShareCard: shows check date and source link when a row matches
      route + carrier; nothing otherwise. Files: frontend/src/components/results/
      CodeShareCard.jsx (+ css). Done when: SUCCESS verified-badge item passes.
      Status: done (frontend/src/components/results/VerifiedBadge.jsx, CodeShareCard.jsx, FlightCard.jsx, frontend/src/utils/verifiedChecks.js, frontend/src/pages/VerificationPage.jsx)
- 4.5 Human task: record the manual checks (see HANDOFF).

### M5 — Multi-source plan
- 5.1 FlightLabs `flightNumber` handling. Before any wiring, document the three
      route-dependent failure modes (TODO(Gabriel) list them) and define the rule the app
      follows when `flightNumber` is null or untrustworthy (e.g. never show a flight number
      from FlightLabs; match to Duffel offers only on carrier + departure time). Files:
      docs/data-verification.md. Done when: each failure mode has a documented example route and
      handling rule.
- 5.2 Decide FlightLabs's role: wired secondary price source vs offline verification aid
      for `verified_checks`. Decision TODO(Gabriel). If wired: new service module (key
      loaded via `api/_lib/config.py`, never printed), output conforming to the normalized
      offer schema (Title Case keys; the additive `'Source'` key is added ONLY if FlightLabs is
      actually wired into the backend; if it is not wired, no `'Source'` key is added), merged and
      deduplicated against Duffel (duplicate = same operating carrier + departure datetime;
      flight number NOT used as a key while unreliable), cheaper offer kept, FlightLabs
      prices labelled as such in the UI. Files: new service module, api/_lib/normalizer.py
      or a separate adapter, local_server.py, tests/. Done when: fixture with an
      overlapping flight yields one row, source labelled; if not wired: the decision is
      recorded in docs/data-verification.md.
- 5.3 ODPT cross-check. Prerequisite: registration (status TODO(Gabriel)). Script that
      loads ODPT JAL/ANA schedule/codeshare data for chosen routes and compares it with
      the app's pairs; no prices. Files: scripts/odpt_crosscheck.py, docs/data-verification.md.
      Done when: SUCCESS ODPT item passes, or is recorded as "not pursued" with a reason.
      Does not change the pairing logic.
- 5.4 Norba (optional, not a dependency). Revisit only if JAL/ANA/LATAM access is available
      (expected around October 2026; TODO(Gabriel) status). Done when: a go/no-go line is
      written in docs/data-verification.md. No other task may depend on this.

### M6 — Round-trip search
Dependency unchanged (Duffel supports multi-slice in test mode). FlightLabs round-trip is
out of scope.
- 6.1 Backend: accept optional `returnDate`; when present, request two slices; normalizer
      emits per-slice data without renaming existing keys (additive: new key `'Slices'`
      alongside existing flat fields for slice 0). Note the segment-overwrite behavior (3.5)
      applies per slice loop; the current loop spans all slices. Files: local_server.py,
      api/_lib/duffel_service.py, api/_lib/normalizer.py, tests/. Done when: curl with
      returnDate returns 2-slice offers; one-way response unchanged in structure; pytest
      green.
- 6.2 Frontend: optional 復路 date field; ResultsPage renders 往路/復路 sections; URL param
      `returnDate` round-trips. Files: frontend/src/components/search/*,
      frontend/src/pages/ResultsPage.jsx. Done when: DoD #3 passes with and without
      returnDate; eslint clean.
- 6.3 Codeshare comparison per slice. Files: wherever pairing runs (ResultsPage grouping).
      This task changes the pairing logic's inputs and needs Gabriel's explicit go-ahead.
      Done when: a round-trip KIX→TPE search shows CodeShareCards for both directions.

### M7 — Flight-number lookup (FLAG: dependency changed)
The original design resolved a flight number to a route via a second flight API's schedule
data. FlightLabs `flightNumber` is unreliable, so it cannot be that source. Options:
Duffel offers (flight numbers present per segment) for a user-supplied route, or ODPT
schedule data for JAL/ANA flights (depends on 5.3). TODO(Gabriel): choose scope before
starting.
- 7.1 Backend: `GET /api/flights/lookup?flightNumber=NH849&date=YYYY-MM-DD` using the chosen
      source; unknown flight → clean 404 JSON. Files: local_server.py, new service function,
      tests/. Done when: curl for a known codeshare flight returns its comparison.
- 7.2 Frontend: 「便名で調べる」 entry on HomePage reusing CodeShareCard. Files:
      HomePage.jsx, ResultsPage.jsx or a new page. Done when: NH849 + date shows the
      comparison; invalid input shows a validation message.

### M8 — FX + deep-link improvements
FX dependency strengthened: FlightLabs returns USD prices (per the exploration report), as
does Duffel; `EXCHANGE_API_KEY` is already in `.env.local` and `config.py` but unused.
- 8.1 FX service: fetch JPY rates daily, cache in DB table `fx_rates` (currency, rate,
      fetched_at; table creation is human-run DDL, output SQL for review); fall back to the
      last cached rate on failure; remove the ¥155 constant (in `normalizer.py`; the
      constant's removal is a behavior change, not a key rename). Files: new fx service,
      api/_lib/db.py, local_server.py, api/_lib/normalizer.py, tests/. Done when: SUCCESS
      FX item passes; killing the network still serves the cached rate.
- 8.2 Deep links where documented: only for airlines with publicly documented URL params
      (research each; do NOT pattern-guess); add `deepLink: true/false` per entry. Files:
      frontend/src/constants/airlineBookingUrls.js. Done when: each upgraded URL is
      click-verified by Gabriel (list them for him); no URL is constructed by guessing.
      Changing existing URL values needs Gabriel's go-ahead (HANDOFF).

### M9 — Deployment + abuse protection (live-mode migration removed)
Target: the 卒展 public release, with a QR code pointing to the production URL (date and
event relationship to the January final assessment: TODO(Gabriel)). Dependency changed: production runs Duffel TEST mode; the app ships with the disclosure
(M4). Do 3.3 (Vercel param mismatch) before 9.2.
- 9.1 Rate limiting: per-IP limit on `/api/*` (e.g. 10 searches/min) returning 429 with a
      friendly JSON message; frontend shows 「少し待ってから再検索してください」. Files:
      local_server.py (or Vercel middleware), one frontend error branch. Done when:
      scripted 20 rapid requests → 429s after the limit; UI message shows.
- 9.2 Deploy: Vercel production project, env vars set, Neon production branch, seed trend
      data for the demo routes via `seed_trend_data.py` (economy only, see 3.6). Whether the
      current Vercel deploy is live: TODO(Gabriel). Files: vercel.json, docs/deploy.md.
      Done when: SUCCESS item 1 passes; deploy steps reproducible from docs/deploy.md.
- 9.3 Observability minimum: log each search (route, date, source, duration, status) to a
      DB table (human-run DDL) or Vercel logs; document where to look. Files:
      local_server.py, docs/deploy.md. Done when: one prod search is findable in logs by
      route string.

### M10 — Final-assessment polish
- 10.1 Incorporate feedback from the interim presentation and later reviews (tasks TBD —
       human writes them into this file).
- 10.2 QR/link target check: prod URL stable; OGP tags (title/description/image) set (none
       exist today). Files: frontend/index.html. Done when: an OGP validator shows title +
       image.
- 10.3 Final pass: CLAUDE.md Definition of Done + this file's SUCCESS list, all green,
       documented in docs/release-checklist.md with date.

---

## HANDOFF — work order and conventions

**Work order rules**
1. One milestone at a time, tasks in order (Gabriel may reorder M5–M8).
2. Before each task: re-read CLAUDE.md Data Contracts and Known issues. After each task:
   run CLAUDE.md Definition of Done (steps relevant to what you touched) + the task's
   done-when.
3. Show diffs before explanations. Small PRs/commits per task, message `M3.2: ...`.
4. STOP and ask a human before: spending money, changing the normalized schema (additive is
   OK, renames are not), any DB DDL/DELETE/UPDATE (output SQL instead), removing any
   exclusion filter (ZZ/HR), changing the codeshare pairing logic or the `is Codeshare`
   rule, touching `airlineBookingUrls.js` values, or presenting synthetic prices as
   market data.

**Gotchas**: see CLAUDE.md (Run / Dev, Data Contracts, Testing discipline, Known issues).
They are kept there only, so there is one copy to keep current.

**Human-only tasks (not for the model, tracked here for completeness)**
- Exact final-assessment date and any milestone dates: TODO(Gabriel).
- ODPT registration (status TODO(Gabriel)); Norba status check (optional).
- Run manual route/carrier price checks and record them for `verified_checks`; confirm the
  table exists in Neon and run any DDL/cleanup SQL the model outputs.
- Click-verification of all booking/deep-link URLs.
- Decisions flagged above: 3.1 approach, 3.4 `is Codeshare`, 5.2 FlightLabs role, M7 scope.
- Final-assessment feedback → write M10.1 tasks into this file.
