"""Hand-collected "real prices" reference dataset: loader, validator and lookup.

Pure functions only (stdlib: json, pathlib, datetime), no DB, no network, no config
import, so the tests can import this without credentials. The data lives in
real_prices.json next to this file. The Flask route in local_server.py and the Vercel
handler in api/real-prices/index.py both call `lookup_response`.
"""
import json
from datetime import date
from pathlib import Path

# Absolute path from __file__: Vercel's cwd is the project root, not this directory.
DATA_FILE = Path(__file__).resolve().parent / "real_prices.json"

KINDS = ("full_service", "lcc")
CABIN = "economy"
PASSENGERS = 1
TRIP = "one-way"

AIRPORT_CODE_LENGTH = 3
AIRLINE_CODE_LENGTH = 2

ROUTE_REQUIRED_FIELDS = (
    "origin", "destination", "flight_date", "captured_on", "source",
    "cabin", "passengers", "trip", "entries",
)
ENTRY_REQUIRED_FIELDS = ("kind", "airline", "dep", "arr", "stops", "price_jpy", "seller")


class RealPricesError(ValueError):
    """The data file holds invalid routes; the message lists every error."""


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_positive_int(value):
    return _is_int(value) and value > 0


def _is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _is_iso_date(value):
    if not isinstance(value, str) or len(value) != 10:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _is_hhmm(value):
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        return False
    hours, minutes = value[:2], value[3:]
    if not (hours.isascii() and hours.isdigit() and minutes.isascii() and minutes.isdigit()):
        return False
    return int(hours) <= 23 and int(minutes) <= 59


def _is_code(value, length):
    return (
        isinstance(value, str) and len(value) == length
        and value.isascii() and value.isalnum() and value == value.upper()
    )


def validate_entry(entry):
    """Return a list of error strings for one entry's own fields; an empty list means valid.

    The same_flight_as cross-reference needs the whole route, so validate_route checks it.
    """
    if not isinstance(entry, dict):
        return ["entry must be an object"]

    errors = []
    for field in ENTRY_REQUIRED_FIELDS:
        if entry.get(field) in (None, ""):
            errors.append(f"{field} is required")

    kind = entry.get("kind")
    if kind not in (None, "") and kind not in KINDS:
        errors.append(f"kind must be one of {list(KINDS)}")

    for field in ("airline", "seller"):
        value = entry.get(field)
        if value not in (None, "") and not _is_nonempty_string(value):
            errors.append(f"{field} must be a non-empty string")

    for field in ("marketing_code", "operating_code"):
        value = entry.get(field)
        if value is not None and not _is_code(value, AIRLINE_CODE_LENGTH):
            errors.append(f"{field} must be {AIRLINE_CODE_LENGTH} uppercase letters or digits")

    for field in ("flight_number", "note"):
        value = entry.get(field)
        if value is not None and not _is_nonempty_string(value):
            errors.append(f"{field} must be a non-empty string when present")

    for field in ("dep", "arr"):
        value = entry.get(field)
        if value not in (None, "") and not _is_hhmm(value):
            errors.append(f"{field} must be HH:MM (00:00-23:59)")

    arr_next_day = entry.get("arr_next_day")
    if arr_next_day is not None and not isinstance(arr_next_day, bool):
        errors.append("arr_next_day must be a boolean when present")

    stops = entry.get("stops")
    if stops not in (None, "") and not (_is_int(stops) and stops >= 0):
        errors.append("stops must be an integer >= 0")

    price = entry.get("price_jpy")
    if price not in (None, "") and not _is_positive_int(price):
        errors.append("price_jpy must be a positive integer")

    site_price = entry.get("airline_site_price_jpy")
    if site_price is not None and not _is_positive_int(site_price):
        errors.append("airline_site_price_jpy must be a positive integer when present")

    same = entry.get("same_flight_as")
    if same is not None and not _is_nonempty_string(same):
        errors.append("same_flight_as must be a non-empty string when present")

    return errors


def validate_route(route, today=None):
    """Return a list of error strings for one route; an empty list means valid.

    `today` (a date) defaults to date.today(); tests pass a fixed value.
    """
    if not isinstance(route, dict):
        return ["route must be an object"]
    today = today or date.today()

    errors = []
    for field in ROUTE_REQUIRED_FIELDS:
        if route.get(field) in (None, ""):
            errors.append(f"{field} is required")

    for field in ("origin", "destination"):
        value = route.get(field)
        if value not in (None, "") and not _is_code(value, AIRPORT_CODE_LENGTH):
            errors.append(f"{field} must be {AIRPORT_CODE_LENGTH} uppercase letters or digits")

    source = route.get("source")
    if source not in (None, "") and not _is_nonempty_string(source):
        errors.append("source must be a non-empty string")

    flight_date = route.get("flight_date")
    captured_on = route.get("captured_on")
    flight_ok = flight_date in (None, "") or _is_iso_date(flight_date)
    captured_ok = captured_on in (None, "") or _is_iso_date(captured_on)
    if not flight_ok:
        errors.append("flight_date must be an ISO date (YYYY-MM-DD)")
    if not captured_ok:
        errors.append("captured_on must be an ISO date (YYYY-MM-DD)")
    if captured_ok and captured_on not in (None, ""):
        captured = date.fromisoformat(captured_on)
        if captured > today:
            errors.append(f"captured_on must not be in the future (today is {today.isoformat()})")
        if flight_ok and flight_date not in (None, "") and captured > date.fromisoformat(flight_date):
            errors.append("captured_on must be on or before flight_date")

    if route.get("cabin") not in (None, "") and route.get("cabin") != CABIN:
        errors.append(f'cabin must be "{CABIN}"')
    passengers = route.get("passengers")
    if passengers not in (None, "") and not (_is_int(passengers) and passengers == PASSENGERS):
        errors.append(f"passengers must be {PASSENGERS}")
    if route.get("trip") not in (None, "") and route.get("trip") != TRIP:
        errors.append(f'trip must be "{TRIP}"')

    entries = route.get("entries")
    if entries is None:
        return errors
    if not isinstance(entries, list) or not entries:
        errors.append("entries must be a non-empty list")
        return errors

    flight_numbers = {}
    for index, entry in enumerate(entries):
        label = f"entries[{index}]"
        if isinstance(entry, dict) and isinstance(entry.get("flight_number"), str):
            label += f" ({entry['flight_number']})"
        errors += [f"{label}: {e}" for e in validate_entry(entry)]
        number = entry.get("flight_number") if isinstance(entry, dict) else None
        if _is_nonempty_string(number):
            if number in flight_numbers:
                errors.append(f"{label}: duplicate flight_number (first used by entries[{flight_numbers[number]}])")
            else:
                flight_numbers[number] = index

    for index, entry in enumerate(entries):
        same = entry.get("same_flight_as") if isinstance(entry, dict) else None
        if not _is_nonempty_string(same):
            continue
        label = f"entries[{index}]"
        if same == entry.get("flight_number"):
            errors.append(f"{label}: same_flight_as must not reference itself")
        elif same not in flight_numbers:
            errors.append(f"{label}: same_flight_as {same!r} is not a flight_number in this route")

    return errors


def validate_routes(routes, today=None):
    """Validate a list of routes and reject duplicate (origin, destination, flight_date).

    Returns a list of error strings, each prefixed with the route's position and key.
    """
    if not isinstance(routes, list):
        return ["routes must be a list"]

    errors = []
    seen = {}
    for index, route in enumerate(routes):
        label = f"routes[{index}]"
        key = None
        if isinstance(route, dict):
            parts = (route.get("origin"), route.get("destination"), route.get("flight_date"))
            if all(isinstance(p, str) and p for p in parts):
                key = parts
                label += f" ({parts[0]}-{parts[1]} {parts[2]})"
        errors += [f"{label}: {e}" for e in validate_route(route, today=today)]
        if key is not None:
            if key in seen:
                errors.append(f"{label}: duplicate route (first used by routes[{seen[key]}])")
            else:
                seen[key] = index
    return errors


def load_routes(path=DATA_FILE, today=None):
    """Return the 'routes' list from the data file.

    Raises RealPricesError listing every problem if any route is invalid.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    routes = data.get("routes", []) if isinstance(data, dict) else data
    errors = validate_routes(routes, today=today)
    if errors:
        raise RealPricesError("invalid real prices data:\n" + "\n".join(errors))
    return routes


def _pair_side(entry):
    return {
        "airline": entry["airline"],
        "flight_number": entry.get("flight_number"),
        "price_jpy": entry["price_jpy"],
        "seller": entry["seller"],
    }


def build_summary(entries):
    """Server-side summary of a route's entries.

    cheapest_lcc / cheapest_full_service: the cheapest entry of that kind, or None.
    codeshare_pairs: one item per same_flight_as link (a link written in both directions
    counts once), with cheaper/pricier sides and gap_jpy = pricier - cheaper.
    """
    def cheapest(kind):
        of_kind = [e for e in entries if e["kind"] == kind]
        return min(of_kind, key=lambda e: e["price_jpy"]) if of_kind else None

    by_number = {e["flight_number"]: e for e in entries if e.get("flight_number")}
    pairs = []
    seen = set()
    for entry in entries:
        other = by_number.get(entry.get("same_flight_as"))
        if other is None:
            continue
        key = frozenset((entry["flight_number"], other["flight_number"]))
        if key in seen:
            continue
        seen.add(key)
        low, high = sorted((entry, other), key=lambda e: e["price_jpy"])
        pairs.append({
            "cheaper": _pair_side(low),
            "pricier": _pair_side(high),
            "gap_jpy": high["price_jpy"] - low["price_jpy"],
        })

    return {
        "cheapest_lcc": cheapest("lcc"),
        "cheapest_full_service": cheapest("full_service"),
        "codeshare_pairs": pairs,
    }


def find_route(routes, origin, destination, flight_date):
    """Exact match on origin, destination and flight_date; None if absent."""
    for route in routes:
        if (route["origin"], route["destination"], route["flight_date"]) == (origin, destination, flight_date):
            return route
    return None


def lookup_response(origin, destination, departure_date, path=DATA_FILE, today=None):
    """Shared endpoint logic. Returns (http_status, body_dict).

    400 for missing params or a non-ISO date; 500 if the data file is invalid;
    200 {"found": False} when no route matches exactly.
    """
    if not origin or not destination or not departure_date:
        return 400, {"error": "origin、destination、departureDateは必須項目です"}
    if not _is_iso_date(departure_date):
        return 400, {"error": "departureDateはYYYY-MM-DD形式で指定してください"}

    try:
        routes = load_routes(path, today=today)
    except (OSError, ValueError):  # RealPricesError and json.JSONDecodeError are ValueErrors
        return 500, {"error": "実価格データの読み込みに失敗しました"}

    route = find_route(routes, origin, destination, departure_date)
    if route is None:
        return 200, {"found": False}

    entries = sorted(route["entries"], key=lambda e: e["price_jpy"])
    return 200, {
        "found": True,
        "flight_date": route["flight_date"],
        "captured_on": route["captured_on"],
        "source": route["source"],
        "entries": entries,
        "summary": build_summary(entries),
    }
