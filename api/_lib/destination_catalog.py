"""Hand-curated destination catalog: loader and validator.

Pure functions only (stdlib: json, pathlib, datetime, urllib), no DB, no network, no
config import, so the tests can import this without credentials. The data lives in
destination_catalog.json next to this file. Nothing in the app reads it yet.
"""
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

# Absolute path from __file__: Vercel's cwd is the project root, not this directory.
DATA_FILE = Path(__file__).resolve().parent / "destination_catalog.json"

ALLOWED_TAGS = {"food", "city", "culture", "nature", "beach", "shopping", "nightlife", "relax"}

IATA_COUNT = 3
HIGHLIGHT_COUNT = (3, 5)
HOTEL_AREA_COUNT = (2, 3)

REQUIRED_FIELDS = (
    "iata", "city", "country", "bestMonths", "budgetLevel", "tags",
    "highlights", "hotelAreas", "mapQuery", "lastChecked",
)


class CatalogError(ValueError):
    """The catalog file holds invalid entries; the message lists every error."""


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


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


def _is_https_url(value):
    return isinstance(value, str) and value.startswith("https://") and bool(urlparse(value).netloc)


def _validate_items(entry, field, title_field, count_range):
    """Errors for a list of {<title_field>, note, sourceUrl} items with a size range."""
    items = entry.get(field)
    if items is None:
        return []  # already reported as missing
    low, high = count_range
    if not isinstance(items, list):
        return [f"{field} must be a list"]
    errors = []
    if not low <= len(items) <= high:
        errors.append(f"{field} must have {low} to {high} items (got {len(items)})")
    for i, item in enumerate(items):
        label = f"{field}[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        for key in (title_field, "note"):
            if not _is_nonempty_string(item.get(key)):
                errors.append(f"{label}.{key} must be a non-empty string")
        if not _is_https_url(item.get("sourceUrl")):
            errors.append(f"{label}.sourceUrl must be an https:// URL")
    return errors


def validate_entry(entry):
    """Return a list of error strings for one catalog entry; an empty list means valid."""
    if not isinstance(entry, dict):
        return ["entry must be an object"]

    errors = []
    for field in REQUIRED_FIELDS:
        if entry.get(field) in (None, ""):
            errors.append(f"{field} is required")

    iata = entry.get("iata")
    if iata not in (None, "") and not (
        isinstance(iata, str) and len(iata) == IATA_COUNT and iata.isascii() and iata.isalpha() and iata.isupper()
    ):
        errors.append("iata must be 3 uppercase letters")

    for field in ("city", "country"):
        value = entry.get(field)
        if value not in (None, "") and not _is_nonempty_string(value):
            errors.append(f"{field} must be a non-empty string")

    months = entry.get("bestMonths")
    if months not in (None, ""):
        if not isinstance(months, list) or not months:
            errors.append("bestMonths must be a non-empty list of months 1-12")
        elif not all(_is_int(m) and 1 <= m <= 12 for m in months):
            errors.append("bestMonths must only contain integers from 1 to 12")

    budget = entry.get("budgetLevel")
    if budget not in (None, "") and not (_is_int(budget) and 1 <= budget <= 3):
        errors.append("budgetLevel must be an integer from 1 to 3")

    tags = entry.get("tags")
    if tags not in (None, ""):
        if not isinstance(tags, list) or not tags:
            errors.append("tags must be a non-empty list")
        else:
            unknown = sorted({str(t) for t in tags if t not in ALLOWED_TAGS})
            if unknown:
                errors.append(f"unknown tag(s) {unknown}; allowed: {sorted(ALLOWED_TAGS)}")

    errors += _validate_items(entry, "highlights", "title", HIGHLIGHT_COUNT)
    errors += _validate_items(entry, "hotelAreas", "name", HOTEL_AREA_COUNT)

    map_query = entry.get("mapQuery")
    if map_query is not None and not _is_nonempty_string(map_query):
        errors.append("mapQuery must be a non-empty string")

    caution = entry.get("caution")
    if caution is not None and not _is_nonempty_string(caution):
        errors.append("caution must be a non-empty string when present")

    last_checked = entry.get("lastChecked")
    if last_checked not in (None, "") and not _is_iso_date(last_checked):
        errors.append("lastChecked must be an ISO date (YYYY-MM-DD)")

    return errors


def validate_catalog(entries):
    """Validate a list of entries (examples already removed) and reject duplicate iata.

    Returns a list of error strings, each prefixed with the entry's position and iata.
    """
    if not isinstance(entries, list):
        return ["destinations must be a list"]

    errors = []
    seen = {}
    for index, entry in enumerate(entries):
        label = f"destinations[{index}]"
        if isinstance(entry, dict) and isinstance(entry.get("iata"), str):
            label += f" ({entry['iata']})"
        errors += [f"{label}: {e}" for e in validate_entry(entry)]
        iata = entry.get("iata") if isinstance(entry, dict) else None
        if isinstance(iata, str) and iata:
            if iata in seen:
                errors.append(f"{label}: duplicate iata (first used by destinations[{seen[iata]}])")
            else:
                seen[iata] = index
    return errors


def load_catalog(path=DATA_FILE):
    """Return the catalog entries: the 'destinations' list without "example": true entries.

    Raises CatalogError listing every problem if any remaining entry is invalid.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    entries = [e for e in data.get("destinations", []) if not (isinstance(e, dict) and e.get("example") is True)]
    errors = validate_catalog(entries)
    if errors:
        raise CatalogError("invalid destination catalog:\n" + "\n".join(errors))
    return entries
