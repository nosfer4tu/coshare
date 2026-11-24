"""Demo snapshots: the loader, the search hook (search_offers / search_payload) and the routes.

Fixtures are small and synthetic; the two real snapshot files are only checked for shape.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api" / "_lib"))
sys.path.insert(0, str(ROOT))

import search_service  # noqa: E402
import snapshot_service  # noqa: E402
from codeshare_service import filter_codeshare_offers  # noqa: E402

ARGS = ("KIX", "TPE", "2027-02-22", ["adult"], "economy")


def snapshot_offer(offer_id, display, operating, *, codeshare, flight="0001", departure="2027-02-22T12:55:00"):
    return {
        "Offer ID": offer_id, "Total Amount": 50000, "Currency": "JPY",
        "Owner Airline IATA": display, "Marketing IATA": display, "Operating IATA": operating,
        "Marketing Flight Number": flight, "Departure Airport": "KIX", "Arrival Airport": "TPE",
        "Departure Time": departure, "Segment Count": 1, "is Codeshare": codeshare,
    }


def snapshot_data(**overrides):
    data = {
        "route": "KIX-TPE", "departure_date": "2027-02-22", "cabin_class": "economy",
        "passengers": ["adult"], "source": "Duffel test environment",
        "captured_at": "2026-11-23T05:55:02Z",
        "offers": [
            snapshot_offer("snap_own", "BR", "BR", codeshare=False, flight="0131"),
            snapshot_offer("snap_cs", "NH", "BR", codeshare=True, flight="5811"),
        ],
    }
    data.update(overrides)
    return data


class SnapshotDirTestCase(unittest.TestCase):
    """A temp snapshot directory; snapshot_service points at it for the duration of a test."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        patcher = mock.patch.object(snapshot_service, "SNAPSHOT_DIR", self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, name, data):
        text = data if isinstance(data, str) else json.dumps(data)
        (self.dir / name).write_text(text, encoding="utf-8")


class RepoSnapshotFilesTest(unittest.TestCase):
    def test_both_files_load_and_are_economy_one_adult(self):
        for origin, destination, count in (("KIX", "TPE", 70), ("NRT", "BOM", 116)):
            snap = snapshot_service.load_snapshot(origin, destination, "2027-02-22", ["adult"], "economy")
            self.assertIsNotNone(snap, f"{origin}-{destination}")
            self.assertEqual(len(snap["offers"]), count)
            self.assertEqual(snap["source"], "Duffel test environment")

    def test_captured_at_values(self):
        kix = snapshot_service.load_snapshot("KIX", "TPE", "2027-02-22", ["adult"], "economy")
        nrt = snapshot_service.load_snapshot("NRT", "BOM", "2027-02-22", ["adult"], "economy")
        self.assertEqual(kix["captured_at"], "2026-11-23T05:55:02Z")
        self.assertEqual(nrt["captured_at"], "2026-11-04T07:44:01Z")

    def test_files_hold_the_full_normalized_list_without_excluded_carriers(self):
        for origin, destination in (("KIX", "TPE"), ("NRT", "BOM")):
            offers = snapshot_service.load_snapshot(origin, destination, "2027-02-22", ["adult"], "economy")["offers"]
            self.assertTrue(all(o["Currency"] == "JPY" for o in offers))
            self.assertFalse(any(o["Owner Airline IATA"] in ("ZZ", "HR") for o in offers))

    def test_nrt_bom_snapshot_holds_the_ai8001_nh829_group(self):
        offers = snapshot_service.load_snapshot("NRT", "BOM", "2027-02-22", ["adult"], "economy")["offers"]
        at_1115 = [o for o in offers if o["Departure Time"].endswith("T11:15:00") and o["Segment Count"] == 1]
        self.assertEqual({(o["Marketing IATA"], o["Marketing Flight Number"]) for o in at_1115},
                         {("AI", "8001"), ("NH", "0829")})

    def test_no_secret_like_keys_in_the_files(self):
        for path in snapshot_service.SNAPSHOT_DIR.glob("*.json"):
            text = path.read_text(encoding="utf-8").lower()
            for needle in ("api_key", "apikey", "bearer", "authorization", "secret", "password", "postgres://"):
                self.assertNotIn(needle, text, f"{path.name}: {needle}")


class EnvVarTest(unittest.TestCase):
    def test_truthy_values(self):
        for value in ("1", "true", "TRUE", " yes ", "on"):
            self.assertTrue(snapshot_service.snapshot_forced({"DEMO_SNAPSHOT": value}), value)

    def test_everything_else_is_off(self):
        for value in ("", "0", "false", "off", "no", "2"):
            self.assertFalse(snapshot_service.snapshot_forced({"DEMO_SNAPSHOT": value}), value)
        self.assertFalse(snapshot_service.snapshot_forced({}))

    def test_reads_the_process_environment_at_call_time(self):
        with mock.patch.dict(os.environ, {"DEMO_SNAPSHOT": "1"}):
            self.assertTrue(snapshot_service.snapshot_forced())
        with mock.patch.dict(os.environ, {"DEMO_SNAPSHOT": ""}):
            self.assertFalse(snapshot_service.snapshot_forced())


class LoadSnapshotTest(SnapshotDirTestCase):
    def load(self, *args):
        return snapshot_service.load_snapshot(*(args or ARGS))

    def test_exact_search_loads(self):
        self.write("KIX-TPE_2027-02-22.json", snapshot_data())
        snap = self.load()
        self.assertEqual([o["Offer ID"] for o in snap["offers"]], ["snap_own", "snap_cs"])
        self.assertEqual(snap["captured_at"], "2026-11-23T05:55:02Z")

    def test_passengers_as_the_comma_string_also_match(self):
        self.write("KIX-TPE_2027-02-22.json", snapshot_data())
        self.assertIsNotNone(self.load("KIX", "TPE", "2027-02-22", "adult", "economy"))

    def test_only_the_exact_search_matches(self):
        self.write("KIX-TPE_2027-02-22.json", snapshot_data())
        for args in (
            ("KIX", "TPE", "2027-02-23", ["adult"], "economy"),
            ("KIX", "TPE", "2027-02-22", ["adult"], "business"),
            ("KIX", "TPE", "2027-02-22", ["adult", "adult"], "economy"),
            ("KIX", "TPE", "2027-02-22", ["adult", "child"], "economy"),
            ("KIX", "TPE", "2027-02-22", ["child"], "economy"),
            ("TPE", "KIX", "2027-02-22", ["adult"], "economy"),
            ("kix", "tpe", "2027-02-22", ["adult"], "economy"),
        ):
            self.assertIsNone(self.load(*args), args)

    def test_unsafe_values_never_reach_the_file_system(self):
        self.write("KIX-TPE_2027-02-22.json", snapshot_data())
        for args in (
            ("../KIX", "TPE", "2027-02-22", ["adult"], "economy"),
            ("KIX", "TPE", "../2027-02-22", ["adult"], "economy"),
            ("KIX", "TPE", "2027-02-22/../x", ["adult"], "economy"),
            (None, "TPE", "2027-02-22", ["adult"], "economy"),
            ("KIX", "TPE", None, ["adult"], "economy"),
        ):
            self.assertIsNone(self.load(*args), args)

    def test_invalid_files_are_ignored_not_raised(self):
        bad = {
            "corrupt": "{not json",
            "wrong route": snapshot_data(route="NRT-BOM"),
            "wrong date": snapshot_data(departure_date="2027-03-01"),
            "wrong cabin": snapshot_data(cabin_class="business"),
            "two adults": snapshot_data(passengers=["adult", "adult"]),
            "no source": snapshot_data(source=""),
            "bad captured_at": snapshot_data(captured_at="yesterday"),
            "empty offers": snapshot_data(offers=[]),
            "offers not offers": snapshot_data(offers=[{"x": 1}]),
            "not an object": [],
        }
        for label, data in bad.items():
            self.write("KIX-TPE_2027-02-22.json", data)
            with self.assertLogs("snapshot_service", level="WARNING"):
                self.assertIsNone(self.load(), label)

    def test_missing_file_is_none(self):
        self.assertIsNone(self.load())


# ---- search hook ----------------------------------------------------------------------------

class FakeDb:
    """Records every write; any read or write after `strict` is set fails the test."""

    def __init__(self):
        self.reads, self.cache_writes, self.history_writes = [], [], []
        self.strict = False

    def get_cached_search(self, *args):
        self.reads.append(args)
        if self.strict:
            raise AssertionError("the DB must not be read")
        return None

    def save_search_cache(self, *args):
        self.cache_writes.append(args)
        if self.strict:
            raise AssertionError("the DB must not be written")

    def save_price_history(self, *args):
        self.history_writes.append(args)
        if self.strict:
            raise AssertionError("the DB must not be written")

    def save_price_history_batch(self, rows):
        self.history_writes.extend(rows)
        if self.strict:
            raise AssertionError("the DB must not be written")


class FakeDuffel:
    def __init__(self, response=None, exc=None):
        self.response, self.exc, self.calls = response, exc, []

    def search_flights(self, *args):
        self.calls.append(args)
        if self.exc:
            raise self.exc
        return self.response


def _carrier(iata, name):
    return {"iata_code": iata, "name": name}


def _live_raw():
    seg = {
        "marketing_carrier": _carrier("CI", "China Airlines"), "operating_carrier": _carrier("CI", "China Airlines"),
        "marketing_carrier_flight_number": "157", "operating_carrier_flight_number": "157",
        "origin": {"iata_code": "KIX"}, "destination": {"iata_code": "TPE"},
        "departing_at": "2027-02-22T12:45:00", "arriving_at": "2027-02-22T15:00:00",
    }
    return {"data": {"offers": [{"id": "off_live", "total_amount": "120.00", "total_currency": "USD",
                                 "owner": _carrier("CI", "China Airlines"), "slices": [{"segments": [seg]}]}]}}


DUFFEL_ERROR = {"errors": [{"code": "validation_error", "title": "Bad request"}]}


class SearchHookTestCase(SnapshotDirTestCase):
    def use(self, duffel, snapshot=True):
        self.db, self.duffel = FakeDb(), duffel
        for name, fake in (("db", self.db), ("duffel_service", self.duffel)):
            patcher = mock.patch.object(search_service, name, fake)
            patcher.start()
            self.addCleanup(patcher.stop)
        if snapshot:
            self.write("KIX-TPE_2027-02-22.json", snapshot_data())

    def force(self, value="1"):
        patcher = mock.patch.dict(os.environ, {"DEMO_SNAPSHOT": value})
        patcher.start()
        self.addCleanup(patcher.stop)

    def assertNoSnapshotWrites(self):
        self.assertEqual(self.db.cache_writes, [])
        self.assertEqual(self.db.history_writes, [])

    @staticmethod
    def ids(offers):
        return [o["Offer ID"] for o in offers]


class LiveSearchUnaffectedTest(SearchHookTestCase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(os.environ, {"DEMO_SNAPSHOT": ""})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_working_live_search_returns_live_offers_with_no_snapshot_meta(self):
        self.use(FakeDuffel(_live_raw()))
        offers, meta = search_service.search_offers(*ARGS)
        self.assertEqual(self.ids(offers), ["off_live"])
        self.assertIsNone(meta)

    def test_live_search_still_writes_cache_and_history(self):
        self.use(FakeDuffel(_live_raw()))
        search_service.search_offers(*ARGS)
        self.assertEqual(len(self.db.cache_writes), 1)
        self.assertEqual(len(self.db.history_writes), 1)

    def test_live_search_never_loads_a_snapshot(self):
        self.use(FakeDuffel(_live_raw()))
        with mock.patch.object(snapshot_service, "load_snapshot") as loader:
            search_service.search_offers(*ARGS)
        loader.assert_not_called()

    def test_live_payload_has_only_the_data_key(self):
        self.use(FakeDuffel(_live_raw()))
        body = search_service.search_payload(*ARGS)
        self.assertEqual(set(body), {"data"})
        self.assertEqual(self.ids(body["data"]), ["off_live"])

    def test_a_search_without_a_snapshot_behaves_exactly_as_before(self):
        # Other date: Duffel error -> [] (get_normalized_offers' own behaviour), no snapshot meta.
        self.use(FakeDuffel(DUFFEL_ERROR))
        with self.assertLogs("search_service", level="WARNING"):
            offers, meta = search_service.search_offers("KIX", "TPE", "2027-03-01", ["adult"], "economy")
        self.assertEqual((offers, meta), ([], None))

    def test_an_exception_without_a_matching_snapshot_is_re_raised(self):
        self.use(FakeDuffel(exc=ConnectionError("down")))
        with self.assertRaises(ConnectionError):
            search_service.search_offers("KIX", "TPE", "2027-03-01", ["adult"], "economy")

    def test_a_non_matching_search_ignores_the_snapshot_even_when_forced(self):
        self.use(FakeDuffel(_live_raw()))
        self.force()
        offers, meta = search_service.search_offers("KIX", "TPE", "2027-02-22", ["adult", "child"], "economy")
        self.assertEqual((self.ids(offers), meta), (["off_live"], None))
        self.assertEqual(len(self.duffel.calls), 1)


class FallbackTest(SearchHookTestCase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(os.environ, {"DEMO_SNAPSHOT": ""})
        patcher.start()
        self.addCleanup(patcher.stop)

    def served(self):
        with self.assertLogs("search_service", level="WARNING"):
            offers, meta = search_service.search_offers(*ARGS)
        self.assertEqual(self.ids(offers), ["snap_own", "snap_cs"])
        self.assertEqual(meta, {"data_source": "snapshot", "captured_at": "2026-11-23T05:55:02Z",
                                "snapshot_source": "Duffel test environment"})
        self.assertNoSnapshotWrites()

    def test_duffel_error_response_serves_the_snapshot(self):
        self.use(FakeDuffel(DUFFEL_ERROR))
        self.served()

    def test_duffel_exception_serves_the_snapshot(self):
        self.use(FakeDuffel(exc=ConnectionError("down")))
        self.served()

    def test_empty_live_result_serves_the_snapshot(self):
        self.use(FakeDuffel({"data": {"offers": []}}))
        self.served()

    def test_only_zz_offers_count_as_empty(self):
        raw = _live_raw()
        raw["data"]["offers"][0]["slices"][0]["segments"][0]["marketing_carrier"] = _carrier("ZZ", "Duffel Airways")
        self.use(FakeDuffel(raw))
        self.served()

    def test_a_fresh_cache_hit_wins_over_the_snapshot(self):
        self.use(FakeDuffel(DUFFEL_ERROR))
        self.db.get_cached_search = lambda *a: {"result_json": json.dumps([{"Offer ID": "cached", "Total Amount": 1}])}
        offers, meta = search_service.search_offers(*ARGS)
        self.assertEqual((self.ids(offers), meta), (["cached"], None))


class ForcedModeTest(SearchHookTestCase):
    def test_forced_serves_the_snapshot_before_any_cache_duffel_or_db_access(self):
        self.use(FakeDuffel(_live_raw()))
        self.db.strict = True
        self.force()
        offers, meta = search_service.search_offers(*ARGS)
        self.assertEqual(self.ids(offers), ["snap_own", "snap_cs"])
        self.assertEqual(meta["data_source"], "snapshot")
        self.assertEqual(self.duffel.calls, [])
        self.assertEqual(self.db.reads, [])
        self.assertNoSnapshotWrites()

    def test_forced_without_a_matching_snapshot_runs_the_live_path(self):
        self.use(FakeDuffel(_live_raw()), snapshot=False)
        self.force()
        offers, meta = search_service.search_offers(*ARGS)
        self.assertEqual((self.ids(offers), meta), (["off_live"], None))
        self.assertEqual(len(self.duffel.calls), 1)

    def test_forced_off_values_do_not_force(self):
        self.use(FakeDuffel(_live_raw()))
        self.force("0")
        offers, meta = search_service.search_offers(*ARGS)
        self.assertEqual((self.ids(offers), meta), (["off_live"], None))


class PayloadFilterTest(SearchHookTestCase):
    def test_the_mode_filter_runs_on_the_snapshot(self):
        self.use(FakeDuffel(DUFFEL_ERROR))
        self.force()
        full = search_service.search_payload(*ARGS)
        filtered = search_service.search_payload(*ARGS, filter_offers=filter_codeshare_offers)
        self.assertEqual(self.ids(full["data"]), ["snap_own", "snap_cs"])
        # The own-code offer stays next to the codeshare offer it is compared with.
        self.assertEqual(self.ids(filtered["data"]), ["snap_own", "snap_cs"])
        self.assertEqual(filtered["data_source"], "snapshot")

    def test_an_unanchored_snapshot_group_is_filtered_out(self):
        data = snapshot_data(offers=[snapshot_offer("only_own", "BR", "BR", codeshare=False)])
        self.use(FakeDuffel(DUFFEL_ERROR), snapshot=False)
        self.write("KIX-TPE_2027-02-22.json", data)
        self.force()
        body = search_service.search_payload(*ARGS, filter_offers=filter_codeshare_offers)
        self.assertEqual(body["data"], [])
        self.assertEqual(body["data_source"], "snapshot")


# ---- routes (Flask test client, real snapshot files) -----------------------------------------

class RouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import local_server
        cls.client = local_server.app.test_client()

    def setUp(self):
        self.db, self.duffel = FakeDb(), FakeDuffel(exc=AssertionError("Duffel must not be called"))
        self.db.strict = True
        for name, fake in (("db", self.db), ("duffel_service", self.duffel)):
            patcher = mock.patch.object(search_service, name, fake)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.dict(os.environ, {"DEMO_SNAPSHOT": "1"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def get(self, path, origin, destination, date="2027-02-22", passengers="adult", cabin="economy"):
        response = self.client.get(
            f"{path}?origin={origin}&destination={destination}&departureDate={date}"
            f"&passengers={passengers}&cabinClass={cabin}")
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def test_flights_search_returns_the_full_snapshot_with_the_marker_fields(self):
        kix = self.get("/api/flights/search", "KIX", "TPE")
        self.assertEqual(len(kix["data"]), 70)
        self.assertEqual((kix["data_source"], kix["captured_at"]), ("snapshot", "2026-11-23T05:55:02Z"))
        nrt = self.get("/api/flights/search", "NRT", "BOM")
        self.assertEqual(len(nrt["data"]), 116)
        self.assertEqual(nrt["captured_at"], "2026-11-04T07:44:01Z")

    def test_codeshare_detect_applies_the_filter_to_the_snapshot(self):
        body = self.get("/api/codeshare/detect", "NRT", "BOM")
        self.assertEqual(body["data_source"], "snapshot")
        at_1115 = {(o["Marketing IATA"], o["Marketing Flight Number"]) for o in body["data"]
                   if o["Departure Time"].endswith("T11:15:00") and o["Segment Count"] == 1}
        self.assertEqual(at_1115, {("AI", "8001"), ("NH", "0829")})
        kix = self.get("/api/codeshare/detect", "KIX", "TPE")
        flights = {(o["Marketing IATA"], o["Marketing Flight Number"]) for o in kix["data"]}
        self.assertIn(("BR", "0131"), flights)
        self.assertIn(("NH", "5811"), flights)

    def test_snapshot_responses_never_touch_the_db_or_duffel(self):
        self.get("/api/flights/search", "KIX", "TPE")
        self.get("/api/codeshare/detect", "NRT", "BOM")
        self.assertEqual(self.db.reads, [])
        self.assertEqual(self.db.cache_writes, [])
        self.assertEqual(self.db.history_writes, [])
        self.assertEqual(self.duffel.calls, [])

    def test_a_different_date_is_not_served_from_a_snapshot(self):
        self.duffel.exc = None
        self.duffel.response = DUFFEL_ERROR
        self.db.strict = False
        with self.assertLogs("search_service", level="WARNING"):
            body = self.get("/api/flights/search", "KIX", "TPE", date="2027-02-23")
        self.assertEqual(body, {"data": []})
        self.assertEqual(len(self.duffel.calls), 1)


if __name__ == "__main__":
    unittest.main()
