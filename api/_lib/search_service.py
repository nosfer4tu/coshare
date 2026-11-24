"""Cached flight search shared by every search route.

The cache always holds the FULL normalized offer list (ZZ already dropped). Mode filtering
(e.g. codeshare-only) is applied by the caller after this returns, on every request, so one
cache row serves every mode.
"""
import json
import logging

import db
import duffel_service
import snapshot_service
from normalizer import normalize_offers

logger = logging.getLogger(__name__)

# Bump when the shape or meaning of the cached payload changes. Old rows keep their old
# prefix, are never read again, and expire on their own; they are not deleted.
SEARCH_CACHE_VERSION = "v2"

# search_cache.route and price_history.route are VARCHAR(20) in the live schema.
ROUTE_MAX_LENGTH = 20


def cache_route(origin, destination):
    route = f"{SEARCH_CACHE_VERSION}:{origin}-{destination}"
    if len(route) > ROUTE_MAX_LENGTH:
        raise ValueError(f"cache route {route!r} exceeds {ROUTE_MAX_LENGTH} characters")
    return route


def _passenger_list(passengers):
    if isinstance(passengers, str):
        passengers = passengers.split(",")
    return [p for p in passengers if p] or ["adult"]


def _cached_offers(cached_row):
    """The stored offer list, or None when there is no usable row (miss, corrupt, or empty)."""
    if not cached_row:
        return None
    payload = cached_row["result_json"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload if isinstance(payload, list) and payload else None


def _duffel_failed(raw_response):
    return (
        not isinstance(raw_response, dict)
        or bool(raw_response.get("errors"))
        or "data" not in raw_response
    )


def _price_history_rows(origin, destination, departure_date, passenger_list, cabin_class, normalized):
    """The price_history rows of a fresh search: JPY offers only, and only for economy with exactly
    one adult. price_history has no cabin or passenger column, so any other search (a total for
    two adults is double, business fares are higher) would skew the trend averages."""
    if cabin_class != "economy" or passenger_list != ["adult"]:
        return []
    history_route = f"{origin}-{destination}"
    return [
        (history_route, departure_date, offer["Total Amount"], offer["Operating Carrier"], offer["Marketing Carrier"])
        for offer in normalized
        if offer["Currency"] == "JPY"
    ]


def get_normalized_offers(origin, destination, departure_date, passengers, cabin_class):
    """Return the full normalized offer list for a search.

    Cache hit: the stored list. Miss: fetch from Duffel, normalize (ZZ dropped), then write
    search_cache and price_history. A Duffel error or an empty normalized list writes nothing
    and returns [], so the next request goes back to Duffel.
    """
    passenger_list = _passenger_list(passengers)
    passengers_key = ",".join(passenger_list)
    route = cache_route(origin, destination)

    cached = _cached_offers(db.get_cached_search(route, departure_date, cabin_class, passengers_key))
    if cached is not None:
        return cached

    raw_response = duffel_service.search_flights(origin, destination, departure_date, passenger_list, cabin_class)
    if _duffel_failed(raw_response):
        errors = raw_response.get("errors") if isinstance(raw_response, dict) else None
        logger.warning(
            "Duffel search failed for %s-%s on %s: %s",
            origin, destination, departure_date,
            [(e.get("code"), e.get("title")) for e in errors if isinstance(e, dict)] if errors else "no data",
        )
        return []

    normalized = normalize_offers(raw_response)
    if not normalized:
        return []

    # The offers are already in hand: a failed write is logged and never breaks the response.
    try:
        db.save_search_cache(route, departure_date, passengers_key, json.dumps(normalized), cabin_class)
    except Exception:
        logger.warning("search_cache write failed for %s on %s; serving the live offers", route, departure_date, exc_info=True)

    history_rows = _price_history_rows(origin, destination, departure_date, passenger_list, cabin_class, normalized)
    if history_rows:
        try:
            db.save_price_history_batch(history_rows)  # one connection, one transaction
        except Exception:
            logger.warning(
                "price_history write failed for %s-%s on %s (%d rows rolled back); serving the live offers",
                origin, destination, departure_date, len(history_rows), exc_info=True,
            )
    return normalized


def _snapshot_for(origin, destination, departure_date, passengers, cabin_class):
    return snapshot_service.load_snapshot(origin, destination, departure_date, passengers, cabin_class)


def search_offers(origin, destination, departure_date, passengers, cabin_class):
    """Return (offers, snapshot_meta). snapshot_meta is None for live data.

    Live data is whatever get_normalized_offers returns, unchanged. A saved snapshot (see
    snapshot_service) replaces it only for the exact searches that have one, and only when
    DEMO_SNAPSHOT is on (checked first: no cache, Duffel or DB access) or when the live search
    raised or came back empty. A snapshot is never written to search_cache or price_history.
    """
    args = (origin, destination, departure_date, passengers, cabin_class)

    if snapshot_service.snapshot_forced():
        snapshot = _snapshot_for(*args)
        if snapshot is not None:
            return snapshot["offers"], snapshot_service.snapshot_meta(snapshot)

    try:
        offers = get_normalized_offers(*args)
    except Exception:
        snapshot = _snapshot_for(*args)
        if snapshot is None:
            raise
        logger.warning("Live search failed for %s-%s on %s; serving the saved snapshot", origin, destination, departure_date)
        return snapshot["offers"], snapshot_service.snapshot_meta(snapshot)

    if not offers:
        snapshot = _snapshot_for(*args)
        if snapshot is not None:
            logger.warning("No usable live offers for %s-%s on %s; serving the saved snapshot", origin, destination, departure_date)
            return snapshot["offers"], snapshot_service.snapshot_meta(snapshot)
    return offers, None


def search_payload(origin, destination, departure_date, passengers, cabin_class, filter_offers=None):
    """The JSON body of a search response: {"data": [...]}, plus the snapshot fields when a
    snapshot was served. `filter_offers` is the mode filter, applied after the offers are chosen."""
    offers, meta = search_offers(origin, destination, departure_date, passengers, cabin_class)
    if filter_offers:
        offers = filter_offers(offers)
    body = {"data": offers}
    if meta:
        body.update(meta)
    return body
