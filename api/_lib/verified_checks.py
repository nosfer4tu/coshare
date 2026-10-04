"""Validation for manual ground-truth price checks (the `verified_checks` table).

Pure functions only: no DB, no network, so the seed script and the unit tests can
import this without credentials.
"""
import re
from datetime import date

ALLOWED_SANDBOX_SOURCES = {"duffel", "flightlabs"}
ALLOWED_VERDICTS = {"match", "mismatch", "not_comparable"}

# 'match' means abs(sandbox - real) / real <= MATCH_TOLERANCE. The frontend mirrors this
# in frontend/src/utils/verifiedChecks.js (MATCH_TOLERANCE_PERCENT); change both together.
MATCH_TOLERANCE = 0.05

ROUTE_PATTERN = re.compile(r"^[A-Z]{3}-[A-Z]{3}$")
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# A 'not_comparable' row says the itinerary could not be matched, so its note must not
# claim the prices agreed or differed. Heuristic substring check, case-insensitive.
VERDICT_IMPLYING_PHRASES = (
    "一致", "相違", "差異", "同額", "同じ価格", "照合済",
    "mismatch", "identical", "same price", "prices match", "verified", "within 5",
)

REQUIRED_FIELDS = (
    "route", "check_date", "flight_date", "carrier_checked",
    "sandbox_source", "real_source_url", "verdict",
)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_iso_date(value):
    if not isinstance(value, str) or not ISO_DATE_PATTERN.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def price_difference_ratio(sandbox_price, real_price):
    """abs(sandbox - real) / real. The caller guarantees real_price > 0."""
    return abs(sandbox_price - real_price) / real_price


def validate_check(record):
    """Return a list of error strings for one check record; an empty list means valid."""
    if not isinstance(record, dict):
        return ["record must be an object"]

    errors = []
    for field in REQUIRED_FIELDS:
        if record.get(field) in (None, ""):
            errors.append(f"{field} is required")

    route = record.get("route")
    if route not in (None, "") and not (isinstance(route, str) and ROUTE_PATTERN.match(route)):
        errors.append("route must match AAA-AAA (uppercase IATA codes)")

    for field in ("check_date", "flight_date"):
        value = record.get(field)
        if value not in (None, "") and not _is_iso_date(value):
            errors.append(f"{field} must be an ISO date (YYYY-MM-DD)")

    carrier = record.get("carrier_checked")
    if carrier not in (None, ""):
        if not isinstance(carrier, str) or not carrier.strip():
            errors.append("carrier_checked must be a non-empty string")
        elif len(carrier) > 100:
            errors.append("carrier_checked must be at most 100 characters")

    source = record.get("sandbox_source")
    if source not in (None, "") and source not in ALLOWED_SANDBOX_SOURCES:
        errors.append(f"sandbox_source must be one of {sorted(ALLOWED_SANDBOX_SOURCES)}")

    url = record.get("real_source_url")
    if url not in (None, ""):
        if not isinstance(url, str) or not url.startswith("https://"):
            errors.append("real_source_url must start with https://")
        elif len(url) > 255:
            errors.append("real_source_url must be at most 255 characters")

    notes = record.get("notes")
    if notes is not None and not isinstance(notes, str):
        errors.append("notes must be a string or null")

    verdict = record.get("verdict")
    if verdict not in (None, "") and verdict not in ALLOWED_VERDICTS:
        errors.append(f"verdict must be one of {sorted(ALLOWED_VERDICTS)}")

    sandbox_price = record.get("sandbox_price_jpy")
    real_price = record.get("real_price_jpy")

    if verdict in ("match", "mismatch"):
        prices_ok = True
        for field, value in (("sandbox_price_jpy", sandbox_price), ("real_price_jpy", real_price)):
            if not _is_int(value) or value <= 0:
                errors.append(f"{field} must be a positive integer for verdict '{verdict}'")
                prices_ok = False
        if prices_ok:
            within = price_difference_ratio(sandbox_price, real_price) <= MATCH_TOLERANCE
            if verdict == "match" and not within:
                errors.append(f"verdict 'match' requires a difference of at most {MATCH_TOLERANCE:.0%}")
            if verdict == "mismatch" and within:
                errors.append(f"verdict 'mismatch' requires a difference above {MATCH_TOLERANCE:.0%}")
    elif verdict == "not_comparable":
        # Prices may be null or 0 (nothing to compare); any other value must be a positive integer.
        for field, value in (("sandbox_price_jpy", sandbox_price), ("real_price_jpy", real_price)):
            if value is not None and (not _is_int(value) or value < 0):
                errors.append(f"{field} must be null, 0 or a positive integer for verdict 'not_comparable'")
        if isinstance(notes, str):
            lowered = notes.lower()
            if any(phrase in lowered for phrase in VERDICT_IMPLYING_PHRASES):
                errors.append("notes for 'not_comparable' must not imply a verdict (match/mismatch)")
    else:
        # Unknown or missing verdict is already reported; still reject malformed prices.
        for field, value in (("sandbox_price_jpy", sandbox_price), ("real_price_jpy", real_price)):
            if value is not None and (not _is_int(value) or value < 0):
                errors.append(f"{field} must be a non-negative integer or null")

    return errors
