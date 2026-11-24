"""Saved Duffel test-environment search results, for the demo.

Pure stdlib (json, logging, os, pathlib, datetime), no DB and no network, so the tests can import
it without credentials. A snapshot holds the FULL normalized offer list of one exact search
(route, date, economy, 1 adult), exactly as search_cache stores it; the mode filter is applied
by the caller afterwards, like for live data. The files live in demo_snapshots/<ORIGIN>-<DEST>_<DATE>.json.
"""
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Absolute path from __file__: Vercel's cwd is the project root, not this directory.
SNAPSHOT_DIR = Path(__file__).resolve().parent / "demo_snapshots"

ENV_VAR = "DEMO_SNAPSHOT"
_TRUTHY = {"1", "true", "yes", "on"}

CABIN_CLASS = "economy"
PASSENGERS = ["adult"]
SOURCE = "Duffel test environment"

_AIRPORT = re.compile(r"[A-Z0-9]{3}")
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def snapshot_forced(environ=None):
    """True when DEMO_SNAPSHOT is switched on. Read on every call, never at import time."""
    value = (environ if environ is not None else os.environ).get(ENV_VAR, "")
    return value.strip().lower() in _TRUTHY


def _passenger_list(passengers):
    if isinstance(passengers, str):
        passengers = passengers.split(",")
    return [p for p in passengers if p] or ["adult"]


def _parse_captured_at(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def validate_snapshot(data, origin, destination, departure_date):
    """Return a list of error strings; an empty list means the snapshot is usable."""
    if not isinstance(data, dict):
        return ["snapshot must be an object"]
    errors = []
    if data.get("route") != f"{origin}-{destination}":
        errors.append("route does not match the file name")
    if data.get("departure_date") != departure_date:
        errors.append("departure_date does not match the file name")
    if data.get("cabin_class") != CABIN_CLASS:
        errors.append(f'cabin_class must be "{CABIN_CLASS}"')
    if data.get("passengers") != PASSENGERS:
        errors.append(f"passengers must be {PASSENGERS}")
    if not isinstance(data.get("source"), str) or not data["source"].strip():
        errors.append("source is required")
    if _parse_captured_at(data.get("captured_at")) is None:
        errors.append("captured_at must be an ISO datetime")
    offers = data.get("offers")
    if not isinstance(offers, list) or not offers:
        errors.append("offers must be a non-empty list")
    elif not all(isinstance(o, dict) and "Offer ID" in o and "Total Amount" in o for o in offers):
        errors.append("every offer needs 'Offer ID' and 'Total Amount'")
    return errors


def load_snapshot(origin, destination, departure_date, passengers, cabin_class, directory=None):
    """The snapshot for exactly this search, or None.

    Returns {"offers": [...], "captured_at": str, "source": str}. None when no snapshot file
    exists for the search, the search is not economy / one adult, or the file is invalid (logged,
    never raised: a broken snapshot must not break a search).
    """
    if cabin_class != CABIN_CLASS or _passenger_list(passengers) != PASSENGERS:
        return None
    # Only well-formed codes and dates reach the file system.
    if not (isinstance(origin, str) and isinstance(destination, str) and isinstance(departure_date, str)
            and _AIRPORT.fullmatch(origin) and _AIRPORT.fullmatch(destination)
            and _ISO_DATE.fullmatch(departure_date)):
        return None
    path = Path(directory or SNAPSHOT_DIR) / f"{origin}-{destination}_{departure_date}.json"
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        logger.warning("Demo snapshot %s could not be read: %s", path.name, exc)
        return None
    errors = validate_snapshot(data, origin, destination, departure_date)
    if errors:
        logger.warning("Demo snapshot %s is invalid: %s", path.name, "; ".join(errors))
        return None
    return {"offers": data["offers"], "captured_at": data["captured_at"], "source": data["source"]}


def snapshot_meta(snapshot):
    """The response fields that mark a snapshot (live responses carry none of them)."""
    return {
        "data_source": "snapshot",
        "captured_at": snapshot["captured_at"],
        "snapshot_source": snapshot["source"],
    }
