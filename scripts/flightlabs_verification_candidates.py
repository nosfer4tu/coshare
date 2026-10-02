"""
Build a clean, manually-verifiable candidate list from FlightLabs' /retrieveFlights
for one route, to spot-check against the real airline's booking site.

Reuses call_flightlabs / find_result_list / _extract_price / USD_TO_JPY from
test_flightlabs.py - no core polling/parsing logic duplicated here.

Usage:
    export FLIGHTLABS_API_KEY=...      # or put FLIGHTLABS_API_KEY=... in .env.local
    python3 scripts/flightlabs_verification_candidates.py

Writes scripts/flightlabs_verification_candidates.md (does not touch flightlabs_report.md).
"""

from pathlib import Path

from test_flightlabs import call_flightlabs, find_result_list, _extract_price, USD_TO_JPY

SCRIPT_DIR = Path(__file__).resolve().parent

# Known OTA / ticketing-broker names seen in FlightLabs' marketingCarrier field so far
# (Expedia, FlightHub on other routes; Hahn Air is a ticketing broker, not an operating
# airline - same exclusion this project already applies to Duffel's `HR` carrier).
NON_AIRLINE_NAMES = {"expedia", "flighthub", "hahn air systems", "hahn air"}

ORIGIN, DESTINATION, DATE = "NRT", "OKA", "2026-11-26"
CANDIDATE_COUNT = 5


def is_clean_single_carrier_offer(offer):
    flight_number = offer.get("flightNumber")
    if not flight_number or flight_number == "null":
        return False

    marketing = offer.get("marketingCarrier")
    operating = offer.get("operatingCarrier")
    if not marketing or not operating:
        return False
    if "," in marketing or "," in operating:  # comma-joined multi-carrier itinerary
        return False
    if marketing.strip().lower() in NON_AIRLINE_NAMES:
        return False
    if marketing != operating:  # codeshare - excluded per this task's scope
        return False

    return True


def select_cheapest_candidates(offers, count=CANDIDATE_COUNT):
    """Filter offers to clean single-carrier, non-codeshare offers with a real
    flight number, then return the `count` cheapest, each carrying a `_price_float`
    key. Shared by any route-specific verification-candidates script."""
    clean_offers = [o for o in offers if is_clean_single_carrier_offer(o)]
    for o in clean_offers:
        o["_price_float"] = _extract_price(o)
    clean_offers = [o for o in clean_offers if o["_price_float"] is not None]
    clean_offers.sort(key=lambda o: o["_price_float"])
    return clean_offers, clean_offers[:count]


def format_candidates_table(candidates):
    header = "| Flight # | Marketing Carrier | Departure | Arrival | Price (orig.) | Price (JPY) |"
    separator = "|---|---|---|---|---|---|"
    rows = []
    for o in candidates:
        price_jpy = o["_price_float"] * USD_TO_JPY
        rows.append(
            f"| {o['flightNumber']} | {o['marketingCarrier']} | {o['departure']} | {o['arrival']} | "
            f"{o['_price_float']:.0f} {o['currency']} | ¥{price_jpy:,.0f} |"
        )
    return header, separator, rows


def main():
    data = call_flightlabs(ORIGIN, DESTINATION, DATE, f"Verification candidates ({ORIGIN}->{DESTINATION})")
    offers = find_result_list(data)

    clean_offers, candidates = select_cheapest_candidates(offers)
    header, separator, rows = format_candidates_table(candidates)

    lines = [
        "# FlightLabs Verification Candidates",
        "",
        f"Route: {ORIGIN} -> {DESTINATION}, date: {DATE}",
        f"Filter: flightNumber present, single real-airline marketingCarrier (no OTA/broker names, "
        "no comma-joined multi-carrier strings), operatingCarrier == marketingCarrier (non-codeshare only).",
        f"{len(offers)} raw offers -> {len(clean_offers)} passed the filter -> top {len(candidates)} shown below.",
        "",
        header,
        separator,
        *rows,
    ]

    report_path = SCRIPT_DIR / "flightlabs_verification_candidates.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"\nWritten to {report_path}")


if __name__ == "__main__":
    main()
