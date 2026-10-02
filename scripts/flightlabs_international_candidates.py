"""
Same clean-candidate-list approach as flightlabs_verification_candidates.py
(NRT->OKA), applied to an international route (NRT->LAX) so it can be manually
spot-checked against the real airline's booking site.

Reuses call_flightlabs / find_result_list from test_flightlabs.py and
select_cheapest_candidates / format_candidates_table from
flightlabs_verification_candidates.py - no filtering/table logic duplicated.

Usage:
    export FLIGHTLABS_API_KEY=...      # or put FLIGHTLABS_API_KEY=... in .env.local
    python3 scripts/flightlabs_international_candidates.py

Writes scripts/flightlabs_international_candidates.md.
"""

from pathlib import Path

from test_flightlabs import call_flightlabs, find_result_list
from flightlabs_verification_candidates import select_cheapest_candidates, format_candidates_table

SCRIPT_DIR = Path(__file__).resolve().parent

ORIGIN, DESTINATION, DATE = "NRT", "LAX", "2026-11-26"
CANDIDATE_COUNT = 5


def main():
    data = call_flightlabs(ORIGIN, DESTINATION, DATE, f"International candidates ({ORIGIN}->{DESTINATION})")
    offers = find_result_list(data)

    clean_offers, candidates = select_cheapest_candidates(offers, count=CANDIDATE_COUNT)
    header, separator, rows = format_candidates_table(candidates)

    # flightNumber sanity check: on domestic routes this is a real code like "MM105"
    # or "GK307"; on this route it may just be a small sequential integer ("1", "2",
    # "0") that isn't searchable on the airline's own site. Flag it so it's obvious
    # before anyone tries to verify against a real booking page.
    suspicious_flight_numbers = [
        o for o in candidates if o["flightNumber"].isdigit() and len(o["flightNumber"]) <= 2
    ]
    flight_number_warning = ""
    if suspicious_flight_numbers:
        flight_number_warning = (
            f"**WARNING: flightNumber looks like a placeholder index, not a real flight number** on this "
            f"route - {len(suspicious_flight_numbers)}/{len(candidates)} candidates have a bare 1-2 digit "
            f"value (e.g. \"{suspicious_flight_numbers[0]['flightNumber']}\") instead of an airline code + "
            f"digits (e.g. \"ZG001\"). These cannot be looked up by flight number on the airline's site - "
            f"verify by carrier + route + departure time/date instead."
        )

    zipair_in_candidates = any(o["marketingCarrier"] == "ZIPAIR" for o in candidates)
    zipair_in_clean = [o for o in clean_offers if o["marketingCarrier"] == "ZIPAIR"]
    zipair_note = []
    if zipair_in_candidates:
        zipair_note.append("A ZIPAIR offer is among the top 5 cheapest candidates below.")
    elif zipair_in_clean:
        cheapest_zipair = zipair_in_clean[0]
        zipair_note.append(
            f"No ZIPAIR offer ranked in the top {CANDIDATE_COUNT} cheapest, but ZIPAIR did pass the clean-offer "
            f"filter - cheapest qualifying ZIPAIR offer: flight {cheapest_zipair['flightNumber']}, "
            f"${cheapest_zipair['_price_float']:.0f} {cheapest_zipair['currency']}. Appended as a 6th row below."
        )
        candidates = candidates + [cheapest_zipair]
        header, separator, rows = format_candidates_table(candidates)
    else:
        zipair_note.append(
            "No ZIPAIR offer passed the clean-offer filter at all (it may only appear in this route's raw "
            "data as part of a codeshare/multi-carrier itinerary, which this filter deliberately excludes)."
        )

    lines = [
        "# FlightLabs International Verification Candidates",
        "",
        f"Route: {ORIGIN} -> {DESTINATION}, date: {DATE}",
        "Filter: flightNumber present, single real-airline marketingCarrier (no OTA/broker names, "
        "no comma-joined multi-carrier strings), operatingCarrier == marketingCarrier (non-codeshare only). "
        "Same filter as flightlabs_verification_candidates.py (NRT->OKA).",
        f"{len(offers)} raw offers -> {len(clean_offers)} passed the filter -> {len(candidates)} shown below.",
        "",
        flight_number_warning,
        "",
        " ".join(zipair_note),
        "",
        header,
        separator,
        *rows,
    ]

    report_path = SCRIPT_DIR / "flightlabs_international_candidates.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"\nWritten to {report_path}")


if __name__ == "__main__":
    main()
