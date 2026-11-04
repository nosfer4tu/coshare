"""Cached flight search shared by every search route.

The cache always holds the FULL normalized offer list (ZZ already dropped). Mode filtering
(e.g. codeshare-only) is applied by the caller after this returns, on every request, so one
cache row serves every mode.
"""
import json
import logging

import db
import duffel_service
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

    db.save_search_cache(route, departure_date, passengers_key, json.dumps(normalized), cabin_class)
    history_route = f"{origin}-{destination}"
    for offer in normalized:
        if offer["Currency"] == "JPY" and cabin_class == "economy":
            db.save_price_history(
                history_route, departure_date, offer["Total Amount"],
                offer["Operating Carrier"], offer["Marketing Carrier"],
            )
    return normalized
