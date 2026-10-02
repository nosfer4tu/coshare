"""
Investigate FlightLabs' missing-flightNumber problem: on NRT->OKA, 18/22 offers
(82%) came back with flightNumber: null. Is this fixable (a param we're not
passing) or structural (a backend data-quality gap)?

Reuses call_flightlabs / find_result_list from test_flightlabs.py - no core
polling/parsing logic duplicated here. This script only adds analysis on top.

Usage:
    export FLIGHTLABS_API_KEY=...      # or put FLIGHTLABS_API_KEY=... in .env.local
    python3 scripts/flightlabs_null_flightnumber_investigation.py

Prints findings directly; does not write a report file (this is throwaway
investigation, not a candidate list to keep around).
"""

from test_flightlabs import call_flightlabs, find_result_list

ROUTES = [
    ("NRT", "OKA", "2026-11-26", "Domestic (previously tested, 18/22 null)"),
    ("KIX", "LAX", "2026-11-26", "International (new)"),
    ("HND", "FUK", "2026-11-26", "Domestic (new)"),
]


def is_null_flight_number(offer):
    fn = offer.get("flightNumber")
    return not fn or fn == "null"


def analyze_route(origin, destination, date, label, offers):
    null_offers = [o for o in offers if is_null_flight_number(o)]
    nonnull_offers = [o for o in offers if not is_null_flight_number(o)]

    print(f"\n=== {label}: {origin}->{destination} {date} ===")
    total = len(offers)
    null_count = len(null_offers)
    pct = (null_count / total * 100) if total else 0
    print(f"Total offers: {total} | null flightNumber: {null_count} ({pct:.0f}%)")

    null_carriers = sorted({o.get("marketingCarrier") for o in null_offers})
    nonnull_carriers = sorted({o.get("marketingCarrier") for o in nonnull_offers})
    print(f"Carriers among NULL-flightNumber offers: {null_carriers}")
    print(f"Carriers among NON-null offers:          {nonnull_carriers}")

    null_key_sets = {frozenset(o.keys()) for o in null_offers}
    nonnull_key_sets = {frozenset(o.keys()) for o in nonnull_offers}
    print(f"Distinct field-sets among null offers: {len(null_key_sets)}")
    print(f"Distinct field-sets among non-null offers: {len(nonnull_key_sets)}")
    if null_key_sets and nonnull_key_sets:
        only_in_nonnull = frozenset.union(*nonnull_key_sets) - frozenset.union(*null_key_sets)
        only_in_null = frozenset.union(*null_key_sets) - frozenset.union(*nonnull_key_sets)
        print(f"Fields present in non-null offers but never in null offers: {sorted(only_in_nonnull) or 'none'}")
        print(f"Fields present in null offers but never in non-null offers: {sorted(only_in_null) or 'none'}")

    # Origin/destination mismatch check: do any offers (in either group) have an
    # origin/destination that doesn't match what we actually queried?
    mismatched = [
        o for o in offers
        if o.get("origin", {}).get("code") != origin or o.get("destination", {}).get("code") != destination
    ]
    if mismatched:
        print(f"** {len(mismatched)}/{total} offers have origin/destination != the queried {origin}->{destination}: **")
        for o in mismatched:
            print(
                f"   {o.get('origin', {}).get('code')}->{o.get('destination', {}).get('code')} "
                f"| flightNumber={o.get('flightNumber')} | marketingCarrier={o.get('marketingCarrier')} "
                f"| price={o.get('price')} {o.get('currency')} | departure={o.get('departure')}"
            )

    if null_offers:
        null_prices = sorted(float(o["price"]) for o in null_offers if o.get("price"))
        print(f"Null-offer price range: {null_prices[0]:.0f}-{null_prices[-1]:.0f} {null_offers[0].get('currency')}"
              if null_prices else "Null-offer price range: n/a")
    if nonnull_offers:
        nonnull_prices = sorted(float(o["price"]) for o in nonnull_offers if o.get("price"))
        print(f"Non-null price range: {nonnull_prices[0]:.0f}-{nonnull_prices[-1]:.0f} {nonnull_offers[0].get('currency')}"
              if nonnull_prices else "Non-null price range: n/a")

    # Duplicate-underlying-flight check: does a null offer share carrier+departure+
    # arrival with a non-null offer (same flight, just missing its number in this row)?
    nonnull_signatures = {
        (o.get("marketingCarrier"), o.get("departure"), o.get("arrival")) for o in nonnull_offers
    }
    dupe_matches = [
        o for o in null_offers
        if (o.get("marketingCarrier"), o.get("departure"), o.get("arrival")) in nonnull_signatures
    ]
    print(f"Null offers matching a non-null offer's carrier+departure+arrival: {len(dupe_matches)}/{null_count}")

    # Templated-schedule check: group ALL offers (null + non-null) by (departure,
    # arrival, durationInMinutes, price) ignoring origin/carrier - reveals whether
    # the same schedule/price is being stamped out under multiple origins/carriers.
    from collections import defaultdict
    groups = defaultdict(list)
    for o in offers:
        key = (o.get("departure"), o.get("arrival"), o.get("durationInMinutes"), o.get("price"))
        groups[key].append(o)
    templated_groups = {k: v for k, v in groups.items() if len(v) > 1}
    if templated_groups:
        print(f"{len(templated_groups)} schedule+price combos appear more than once across different origin/carrier:")
        for key, group in templated_groups.items():
            variants = [(o.get("origin", {}).get("code"), o.get("marketingCarrier"), o.get("flightNumber")) for o in group]
            print(f"   departure={key[0]} price={key[3]}: {variants}")

    return {
        "total": total,
        "null_count": null_count,
        "pct": pct,
        "null_carriers": null_carriers,
        "nonnull_carriers": nonnull_carriers,
    }


def main():
    results = []
    for origin, destination, date, label in ROUTES:
        data = call_flightlabs(origin, destination, date, f"Null-flightNumber check ({label})")
        offers = find_result_list(data)
        results.append((label, analyze_route(origin, destination, date, label, offers)))

    print("\n=== Cross-route summary ===")
    for label, r in results:
        print(f"- {label}: {r['null_count']}/{r['total']} null ({r['pct']:.0f}%)")


if __name__ == "__main__":
    main()
