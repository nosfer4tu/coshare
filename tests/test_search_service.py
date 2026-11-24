import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api" / "_lib"))
sys.path.insert(0, str(ROOT))

import search_service  # noqa: E402
from codeshare_service import filter_codeshare_offers  # noqa: E402


def _carrier(iata, name):
    return {"iata_code": iata, "name": name}


def _segment(marketing, operating, number):
    return {
        "marketing_carrier": marketing,
        "operating_carrier": operating,
        "marketing_carrier_flight_number": number,
        "operating_carrier_flight_number": number,
        "origin": {"iata_code": "KIX"},
        "destination": {"iata_code": "TPE"},
        "departing_at": "2026-12-02T10:00:00",
        "arriving_at": "2026-12-02T12:00:00",
    }


JL = _carrier("JL", "Japan Airlines")
CI = _carrier("CI", "China Airlines")
BR = _carrier("BR", "EVA Air")
ZZ = _carrier("ZZ", "Duffel Airways")


def _offer(offer_id, owner, marketing, operating, usd="100.00"):
    return {"id": offer_id, "total_amount": usd, "total_currency": "USD", "owner": owner,
            "slices": [{"segments": [_segment(marketing, operating, "1")]}]}


# off_cs: JL sells a CI flight (codeshare). off_own: BR sells its own flight. off_zz: synthetic.
RAW = {"data": {"offers": [
    _offer("off_cs", JL, JL, CI, "120.00"),
    _offer("off_own", BR, BR, BR, "140.00"),
    _offer("off_zz", ZZ, ZZ, ZZ, "10.00"),
]}}
ALL_IDS = ["off_cs", "off_own"]
CODESHARE_IDS = ["off_cs"]
DUFFEL_ERROR = {"errors": [{"code": "validation_error", "title": "Bad request"}]}
EMPTY = {"data": {"offers": []}}


class FakeDb:
    """In-memory stand-in for the db module; counts and records every write."""

    def __init__(self):
        self.cache = {}  # (route, date, cabin, passengers) -> result_json (as stored: a str)
        self.cache_writes = []
        self.history_writes = []  # every history row, however it arrived
        self.history_batches = []  # one entry per save_price_history_batch call: the rows it received

    def get_cached_search(self, route, departure_date, cabin_class, passengers):
        key = (route, departure_date, cabin_class, passengers)
        if key not in self.cache:
            return None
        return {"result_json": self.cache[key]}

    def save_search_cache(self, route, departure_date, passengers, result_json, cabin_class):
        self.cache_writes.append((route, departure_date, passengers, result_json, cabin_class))
        self.cache[(route, departure_date, cabin_class, passengers)] = result_json

    def save_price_history(self, route, departure_date, price_jpy, operating_airline, marketing_airline):
        self.history_writes.append((route, departure_date, price_jpy, operating_airline, marketing_airline))

    def save_price_history_batch(self, rows):
        rows = list(rows)
        self.history_batches.append(rows)
        self.history_writes.extend(rows)


class FakeDuffel:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def search_flights(self, origin, destination, departure_date, passengers, cabin_class):
        self.calls.append((origin, destination, departure_date, passengers, cabin_class))
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]


class ServiceTestCase(unittest.TestCase):
    def use(self, *duffel_responses):
        self.db = FakeDb()
        self.duffel = FakeDuffel(*duffel_responses)
        for name, fake in (("db", self.db), ("duffel_service", self.duffel)):
            patcher = mock.patch.object(search_service, name, fake)
            patcher.start()
            self.addCleanup(patcher.stop)

    def search(self, passengers=("adult",), cabin_class="economy"):
        return search_service.get_normalized_offers("KIX", "TPE", "2026-12-02", list(passengers), cabin_class)


def ids(offers):
    return [o["Offer ID"] for o in offers]


class CacheRouteTest(unittest.TestCase):
    def test_versioned_route(self):
        self.assertEqual(search_service.SEARCH_CACHE_VERSION, "v2")
        self.assertEqual(search_service.cache_route("KIX", "TPE"), "v2:KIX-TPE")

    def test_fits_varchar_20_for_iata_codes(self):
        self.assertLessEqual(len(search_service.cache_route("KIX", "TPE")), search_service.ROUTE_MAX_LENGTH)

    def test_overlong_route_is_rejected_before_any_db_write(self):
        with self.assertRaises(ValueError):
            search_service.cache_route("KIXKIXKIX", "TPETPETPE")


class FilterCodeshareOffersTest(unittest.TestCase):
    def test_existing_rule(self):
        offers = [
            {"Offer ID": "a", "is Codeshare": True, "Owner Airline IATA": "JL"},
            {"Offer ID": "b", "is Codeshare": False, "Owner Airline IATA": "BR"},
            {"Offer ID": "c", "is Codeshare": True, "Owner Airline IATA": "HR"},
            {"Offer ID": "d", "Owner Airline IATA": "CI"},
        ]
        self.assertEqual(ids(filter_codeshare_offers(offers)), ["a"])


class ModeSwitchTest(ServiceTestCase):
    def test_codeshare_request_then_both_request_one_duffel_call(self):
        self.use(RAW)
        self.assertEqual(ids(filter_codeshare_offers(self.search())), CODESHARE_IDS)
        self.assertEqual(ids(self.search()), ALL_IDS)
        self.assertEqual(len(self.duffel.calls), 1)

    def test_both_request_then_codeshare_request_one_duffel_call(self):
        self.use(RAW)
        self.assertEqual(ids(self.search()), ALL_IDS)
        self.assertEqual(ids(filter_codeshare_offers(self.search())), CODESHARE_IDS)
        self.assertEqual(len(self.duffel.calls), 1)

    def test_cache_holds_the_full_list_under_the_v2_key(self):
        self.use(RAW)
        filter_codeshare_offers(self.search())  # a codeshare request must not narrow the cache
        self.assertEqual(len(self.db.cache_writes), 1)
        route, departure_date, passengers, result_json, cabin_class = self.db.cache_writes[0]
        self.assertEqual(route, "v2:KIX-TPE")
        self.assertEqual((departure_date, passengers, cabin_class), ("2026-12-02", "adult", "economy"))
        self.assertEqual(ids(json.loads(result_json)), ALL_IDS)  # ZZ dropped, nothing else

    def test_passengers_key_is_the_joined_string(self):
        self.use(RAW)
        self.search(passengers=("adult", "adult", "child"))
        self.assertEqual(self.db.cache_writes[0][2], "adult,adult,child")
        self.assertEqual(self.duffel.calls[0][3], ["adult", "adult", "child"])
        self.search(passengers=("adult", "adult", "child"))
        self.assertEqual(len(self.duffel.calls), 1)

    def test_old_unversioned_rows_are_ignored(self):
        self.use(RAW)
        old_key = ("KIX-TPE", "2026-12-02", "economy", "adult")
        self.db.cache[old_key] = json.dumps([{"Offer ID": "stale"}])
        self.assertEqual(ids(self.search()), ALL_IDS)
        self.assertEqual(len(self.duffel.calls), 1)
        self.assertEqual(self.db.cache[old_key], json.dumps([{"Offer ID": "stale"}]))  # untouched


class FailureTest(ServiceTestCase):
    def test_duffel_error_writes_nothing_and_retry_goes_back_to_duffel(self):
        self.use(DUFFEL_ERROR, RAW)
        self.assertEqual(self.search(), [])
        self.assertEqual((self.db.cache_writes, self.db.history_writes), ([], []))
        self.assertEqual(ids(self.search()), ALL_IDS)
        self.assertEqual(len(self.duffel.calls), 2)

    def test_empty_result_writes_nothing_and_retry_goes_back_to_duffel(self):
        self.use(EMPTY, RAW)
        self.assertEqual(self.search(), [])
        self.assertEqual((self.db.cache_writes, self.db.history_writes), ([], []))
        self.assertEqual(ids(self.search()), ALL_IDS)
        self.assertEqual(len(self.duffel.calls), 2)

    def test_only_zz_offers_counts_as_empty(self):
        self.use({"data": {"offers": [_offer("off_zz", ZZ, ZZ, ZZ)]}})
        self.assertEqual(self.search(), [])
        self.assertEqual((self.db.cache_writes, self.db.history_writes), ([], []))

    def test_response_without_data_is_a_failure(self):
        self.use({"meta": {}})
        self.assertEqual(self.search(), [])
        self.assertEqual(self.db.cache_writes, [])


class SuccessWritesTest(ServiceTestCase):
    def test_successful_fetch_writes_cache_and_price_history(self):
        self.use(RAW)
        self.search()
        self.assertEqual(len(self.db.cache_writes), 1)
        # USD offers are converted to JPY (x155) by the normalizer; both non-ZZ offers are recorded.
        self.assertEqual(
            self.db.history_batches,
            [[("KIX-TPE", "2026-12-02", 18600, "China Airlines", "Japan Airlines"),
              ("KIX-TPE", "2026-12-02", 21700, "EVA Air", "EVA Air")]],
        )

    def test_cache_hit_writes_nothing(self):
        self.use(RAW)
        self.search()
        self.search()
        self.assertEqual((len(self.db.cache_writes), len(self.db.history_batches), len(self.db.history_writes)), (1, 1, 2))

    def test_non_economy_caches_but_records_no_price_history(self):
        self.use(RAW)
        self.search(cabin_class="business")
        self.assertEqual(len(self.db.cache_writes), 1)
        self.assertEqual(self.db.history_batches, [])


class RoutesTest(ServiceTestCase):
    """The Flask routes in local_server.py, through the same fakes."""

    def setUp(self):
        import local_server
        self.client = local_server.app.test_client()

    def get(self, path):
        response = self.client.get(path + "?origin=KIX&destination=TPE&departureDate=2026-12-02&passengers=adult&cabinClass=economy")
        self.assertEqual(response.status_code, 200)
        return response.get_json()["data"]

    def test_codeshare_then_search_and_back(self):
        self.use(RAW)
        self.assertEqual(ids(self.get("/api/codeshare/detect")), CODESHARE_IDS)
        self.assertEqual(ids(self.get("/api/flights/search")), ALL_IDS)
        self.assertEqual(ids(self.get("/api/codeshare/detect")), CODESHARE_IDS)
        self.assertEqual(len(self.duffel.calls), 1)

    def test_missing_params_is_400(self):
        self.use(RAW)
        self.assertEqual(self.client.get("/api/flights/search?origin=KIX").status_code, 400)
        self.assertEqual(self.duffel.calls, [])


if __name__ == "__main__":
    unittest.main()
