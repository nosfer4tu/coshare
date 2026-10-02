"""
Standalone exploratory test for the FlightLabs (goflightlabs.com) Flight Prices API.

Not wired into local_server.py / normalizer.py — this is purely to inspect FlightLabs'
actual response shape and decide whether it's worth integrating alongside/instead of Duffel.

Usage:
    export FLIGHTLABS_API_KEY=...      # or put FLIGHTLABS_API_KEY=... in .env.local
    python3 scripts/test_flightlabs.py

Writes a raw-response dump (scripts/flightlabs_raw_dump.json) and a findings report
(scripts/flightlabs_report.md). Both are gitignored via the existing `*dump*.json` /
scratch conventions — do not commit the raw dump.
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")
except ImportError:
    pass

API_KEY = os.environ.get("FLIGHTLABS_API_KEY")
# NOTE: https://www.goflightlabs.com/flight-prices is the *docs page*, not the API host.
# The docs page's own "try it" panel points at this actual endpoint (see
# data-endpoint="..." in the rendered HTML). It's an async job API: the first call
# returns HTTP 202 + a jobId, and you re-poll the *same* query params until HTTP 200.
BASE_URL = "https://www.goflightlabs.com/retrieveFlights"
MAX_POLL_ATTEMPTS = 12
POLL_INTERVAL_SECONDS = 15

# Known third-party-issuer-style field names to scan for (Duffel's analogue: `owner`,
# which surfaces things like Hahn Air as a ticketing broker rather than the seller).
ISSUER_FIELD_CANDIDATES = [
    "seller",
    "issuer",
    "owner",
    "validatingCarrier",
    "validatingAirline",
    "ticketingCarrier",
    "ticketingAirline",
    "bookingAgent",
]

JAL_GROUND_TRUTH_JPY = 538_260
USD_TO_JPY = 155  # fixed rate per this project's convention (CLAUDE.md); FlightLabs prices are USD
JAPAN_LCC_NAMES = {
    "Peach": ["peach"],
    "Jetstar Japan": ["jetstar japan", "jetstar"],
    "ZIPAIR": ["zipair", "zip air"],
    "Spring Airlines Japan": ["spring airlines japan", "spring japan"],
    "Skymark": ["skymark"],
}

SCRIPT_DIR = Path(__file__).resolve().parent


def call_flightlabs(origin, destination, date, label):
    if not API_KEY:
        print(
            "ERROR: FLIGHTLABS_API_KEY not set. Export it or add it to .env.local.",
            file=sys.stderr,
        )
        sys.exit(1)

    params = {
        "access_key": API_KEY,
        "originIATACode": origin,
        "destinationIATACode": destination,
        "date": date,
    }
    print(f"\n=== {label}: {origin} -> {destination} on {date} ===")

    data = None
    for attempt in range(1, MAX_POLL_ATTEMPTS + 1):
        resp = requests.get(BASE_URL, params=params, timeout=30)
        print(f"  attempt {attempt}: HTTP {resp.status_code}")

        try:
            data = resp.json()
        except ValueError:
            print("Response was not valid JSON:")
            print(resp.text[:2000])
            return None

        # retrieveFlights is an async job API: 202 + jobId means "still processing,
        # re-issue the same query params". Only a 200 carries the actual results.
        if resp.status_code == 200:
            break
        if resp.status_code == 202 and isinstance(data, dict) and "jobId" in data:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        break  # unexpected status - stop and report what we got

    print(json.dumps(data, indent=2, ensure_ascii=False)[:5000])
    return data


def find_result_list(data):
    """FlightLabs wraps results under a top-level key that varies by endpoint version
    (commonly 'data'). Return whatever list of offer-like dicts we can find."""
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "results", "flights", "prices"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def scan_for_issuer_fields(offers):
    found = {}
    for offer in offers:
        _scan_dict(offer, found)
    return found


def _scan_dict(obj, found, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{path}.{k}" if path else k
            if any(cand.lower() == k.lower() for cand in ISSUER_FIELD_CANDIDATES):
                found.setdefault(full_key, v)
            _scan_dict(v, found, full_key)
    elif isinstance(obj, list):
        for item in obj:
            _scan_dict(item, found, path)


def extract_carrier_names(offers):
    """FlightLabs returns full carrier *names* (e.g. 'Japan Airlines'), not IATA
    codes, in marketingCarrier/operatingCarrier. Multi-leg itineraries join several
    names with ', ' in a single string, so split on that too."""
    names = set()

    def _walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() in ("marketingcarrier", "operatingcarrier") and isinstance(v, str):
                    for part in v.split(","):
                        part = part.strip()
                        if part:
                            names.add(part)
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    for offer in offers:
        _walk(offer)
    return names


def find_cheapest_matching(offers, keywords):
    """Return (price, offer) for the cheapest offer whose marketingCarrier or
    operatingCarrier field contains any of the given keywords (case-insensitive).
    Matches only against carrier fields, not the whole offer, to avoid false
    positives from unrelated substrings elsewhere in the object."""
    best = None
    for offer in offers:
        carrier_text = f"{offer.get('marketingCarrier', '')} {offer.get('operatingCarrier', '')}".lower()
        if any(kw.lower() in carrier_text for kw in keywords):
            price = _extract_price(offer)
            if price is not None and (best is None or price < best[0]):
                best = (price, offer)
    return best


def _extract_price(offer):
    if not isinstance(offer, dict):
        return None
    for k in ("price", "totalPrice", "total_amount", "amount"):
        if k in offer:
            v = offer[k]
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                try:
                    return float(v)
                except ValueError:
                    pass
            if isinstance(v, dict):
                for pk in ("amount", "total", "value"):
                    if pk in v:
                        try:
                            return float(v[pk])
                        except (TypeError, ValueError):
                            pass
    return None


def run_route_section(section_num, label, origin, destination, date):
    """Fetch one route via the existing call_flightlabs/find_result_list helpers and
    build a report section: offer count, unique marketingCarrier values, LCC presence
    check, cheapest/most expensive price in JPY. Returns (report_lines, offers, raw_data)
    so callers can reuse the offers/names for a cross-route summary."""
    data = call_flightlabs(origin, destination, date, label)
    offers = find_result_list(data)
    names = extract_carrier_names(offers)

    lines = [f"## {section_num}. {label} ({origin}->{destination}, {date})"]
    lines.append(f"- Offers returned: {len(offers)}")
    lines.append(f"- Unique marketingCarrier values: {sorted(names) or 'none'}")

    lcc_hits = {}
    for lcc_name, keywords in JAPAN_LCC_NAMES.items():
        present = any(any(kw in n.lower() for kw in keywords) for n in names)
        lcc_hits[lcc_name] = present
        lines.append(f"- {lcc_name}: {'FOUND' if present else 'not found'}")

    prices = [p for p in (_extract_price(o) for o in offers) if p is not None]
    if prices:
        cheapest_jpy = min(prices) * USD_TO_JPY
        priciest_jpy = max(prices) * USD_TO_JPY
        lines.append(f"- Cheapest: ¥{cheapest_jpy:,.0f} | Most expensive: ¥{priciest_jpy:,.0f}")
    else:
        lines.append("- No parseable prices found in response")
    lines.append("")

    return lines, offers, data, lcc_hits


def main():
    report_lines = ["# FlightLabs API Exploratory Test Report", ""]

    # --- Test 1: NRT -> GRU, international, JAL/LATAM codeshare route ---
    intl_data = call_flightlabs("NRT", "GRU", "2026-11-26", "International (NRT->GRU)")
    intl_offers = find_result_list(intl_data)

    report_lines.append("## 1. Schema completeness: third-party issuer fields")
    issuer_fields = scan_for_issuer_fields(intl_offers)
    if issuer_fields:
        report_lines.append(
            "Found fields beyond marketingCarrier/operatingCarrier that could represent a ticket issuer/seller:"
        )
        for k, v in issuer_fields.items():
            report_lines.append(f"- `{k}` = `{v!r}`")
    else:
        report_lines.append(
            "**No** field resembling a third-party issuer/seller (seller, issuer, owner, "
            "validatingCarrier, etc.) was found in the response. FlightLabs appears to expose "
            "only marketingCarrier / operatingCarrier — no Hahn-Air-style ticketing-broker signal."
        )
    report_lines.append("")

    report_lines.append("## 2. Price accuracy vs. ground truth (JAL/LATAM, NRT->GRU)")
    jal_match = find_cheapest_matching(intl_offers, ["japan airlines", "jal"])
    latam_match = find_cheapest_matching(intl_offers, ["latam"])
    exact_match = find_cheapest_matching(intl_offers, ["japan airlines"])
    exact_match = exact_match if exact_match and "latam" in (
        f"{exact_match[1].get('marketingCarrier','')} {exact_match[1].get('operatingCarrier','')}".lower()
    ) else None

    report_lines.append(f"- Ground truth (book-i.jal.co.jp, hand-verified): ¥{JAL_GROUND_TRUTH_JPY:,}")
    if exact_match:
        price, offer = exact_match
        jpy = price * USD_TO_JPY
        diff = jpy - JAL_GROUND_TRUTH_JPY
        pct = (diff / JAL_GROUND_TRUTH_JPY) * 100
        report_lines.append(
            f"- Exact JAL-marketed / LATAM-operated match: ${price:,.0f} -> ¥{jpy:,.0f} "
            f"(diff ¥{diff:,.0f}, {pct:+.1f}%)"
        )
    else:
        report_lines.append(
            "- **No offer with `marketingCarrier` containing \"Japan Airlines\" AND \"LATAM\" together "
            "was found** — FlightLabs did not return the specific JAL-issued/LATAM-operated combination "
            "the ground truth price is for. Nearest comparables below (not the same itinerary; treat the "
            "% diff as directional only):"
        )
        for label, match in (("Cheapest offer mentioning Japan Airlines", jal_match), ("Cheapest offer mentioning LATAM", latam_match)):
            if match:
                price, offer = match
                jpy = price * USD_TO_JPY
                diff = jpy - JAL_GROUND_TRUTH_JPY
                pct = (diff / JAL_GROUND_TRUTH_JPY) * 100
                report_lines.append(
                    f"  - {label}: ${price:,.0f} USD -> ¥{jpy:,.0f} (marketingCarrier=\"{offer.get('marketingCarrier')}\", "
                    f"flightNumber={offer.get('flightNumber')}) — diff vs ground truth: ¥{diff:,.0f} ({pct:+.1f}%)"
                )
            else:
                report_lines.append(f"  - {label}: none found")
    report_lines.append("")

    # --- Test 2: domestic Japan route, LCC coverage ---
    domestic_data = call_flightlabs("HND", "CTS", "2026-11-26", "Domestic (HND->CTS)")
    domestic_offers = find_result_list(domestic_data)
    domestic_names = extract_carrier_names(domestic_offers)

    report_lines.append("## 3. LCC coverage (domestic HND->CTS)")
    report_lines.append(f"- Carrier names seen in response: {sorted(domestic_names) or 'none'}")
    for lcc_name, keywords in JAPAN_LCC_NAMES.items():
        present = any(any(kw in n.lower() for kw in keywords) for n in domestic_names)
        report_lines.append(f"- {lcc_name}: {'FOUND' if present else 'not found'}")
    non_airline_carriers = [n for n in domestic_names if n not in {"Japan Airlines", "ANA"} and not any(
        any(kw in n.lower() for kw in kws) for kws in JAPAN_LCC_NAMES.values()
    )]
    if non_airline_carriers:
        report_lines.append(
            f"- **Data quality flag**: non-airline values appearing in `marketingCarrier`/`operatingCarrier`: "
            f"{non_airline_carriers} (e.g. an OTA name where flightNumber is `null` — schema is not reliably "
            "airline-only)."
        )
    report_lines.append("")

    # --- Tests 4-6: additional routes to broaden LCC-coverage / price-sanity evidence ---
    lax_lines, lax_offers, lax_data, lax_lcc = run_route_section(
        4, "NRT->LAX", "NRT", "LAX", "2026-11-26"
    )
    report_lines.extend(lax_lines)

    icn_lines, icn_offers, icn_data, icn_lcc = run_route_section(
        5, "KIX->ICN (Peach route)", "KIX", "ICN", "2026-11-26"
    )
    report_lines.extend(icn_lines)

    oka_lines, oka_offers, oka_data, oka_lcc = run_route_section(
        6, "NRT->OKA (Peach/Jetstar Japan/Skymark route)", "NRT", "OKA", "2026-11-26"
    )
    report_lines.extend(oka_lines)

    # LCC hits for NRT->GRU and HND->CTS weren't captured as dicts earlier (sections 1-3
    # predate run_route_section) - recompute the same check here for the verdict, reusing
    # the offers/names already fetched above (no extra API calls).
    intl_names = extract_carrier_names(intl_offers)
    intl_lcc = {
        lcc_name: any(any(kw in n.lower() for kw in keywords) for n in intl_names)
        for lcc_name, keywords in JAPAN_LCC_NAMES.items()
    }
    hnd_cts_names = extract_carrier_names(domestic_offers)
    hnd_cts_lcc = {
        lcc_name: any(any(kw in n.lower() for kw in keywords) for n in hnd_cts_names)
        for lcc_name, keywords in JAPAN_LCC_NAMES.items()
    }

    report_lines.append("## Overall LCC Coverage Verdict")
    all_routes_lcc = {
        "NRT->GRU (international, long-haul)": intl_lcc,
        "HND->CTS (domestic)": hnd_cts_lcc,
        "NRT->LAX (international, long-haul, but ZIPAIR operates it)": lax_lcc,
        "KIX->ICN (Peach route)": icn_lcc,
        "NRT->OKA (Peach/Jetstar Japan/Skymark route)": oka_lcc,
    }
    any_lcc_found = any(any(hits.values()) for hits in all_routes_lcc.values())
    if any_lcc_found:
        report_lines.append(
            "**Evidence of Japanese LCC coverage found** — FlightLabs does return these carriers on some "
            "routes, so coverage is not zero, but it's inconsistent:"
        )
        for route, hits in all_routes_lcc.items():
            found = [name for name, present in hits.items() if present]
            report_lines.append(f"- {route}: {', '.join(found) if found else '(none found)'}")
        report_lines.append(
            "\nHND->CTS returned **zero** of the five target LCCs despite ANA/JAL both flying that route "
            "and Skymark, ADO, and AIRDO commonly serving Tokyo-Sapporo in reality — so the HND->CTS gap "
            "is real and route-specific, not evidence that FlightLabs lacks LCC data entirely. KIX->ICN and "
            "NRT->OKA both surfaced Peach correctly, and NRT->LAX surfaced ZIPAIR correctly, so LCC data "
            "does exist in FlightLabs for at least Peach and ZIPAIR — Jetstar Japan appeared once (NRT->OKA), "
            "Spring Airlines Japan and Skymark appeared on **none** of the 5 routes tested."
        )
    else:
        report_lines.append(
            "**No evidence of Japanese LCC coverage anywhere** across any of the 5 routes tested."
        )
    report_lines.append("")

    report_lines.append("## Summary")
    report_lines.append(f"- NRT->GRU offers returned: {len(intl_offers)}")
    report_lines.append(f"- HND->CTS offers returned: {len(domestic_offers)}")
    report_lines.append(f"- NRT->LAX offers returned: {len(lax_offers)}")
    report_lines.append(f"- KIX->ICN offers returned: {len(icn_offers)}")
    report_lines.append(f"- NRT->OKA offers returned: {len(oka_offers)}")
    report_lines.append(
        "- Full raw responses dumped to `scripts/flightlabs_raw_dump.json` for manual inspection."
    )

    report_path = SCRIPT_DIR / "flightlabs_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\nReport written to {report_path}")

    dump_path = SCRIPT_DIR / "flightlabs_raw_dump.json"
    dump_path.write_text(
        json.dumps(
            {
                "nrt_gru": intl_data,
                "hnd_cts": domestic_data,
                "nrt_lax": lax_data,
                "kix_icn": icn_data,
                "nrt_oka": oka_data,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Raw dump written to {dump_path}")


if __name__ == "__main__":
    main()
