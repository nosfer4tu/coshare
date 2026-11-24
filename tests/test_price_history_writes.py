"""price_history writes of a fresh search: the batch writer in db.py, the passenger / cabin guard,
and failure handling in search_service. Fake DB and Duffel only; nothing touches a real database."""
import contextlib
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api" / "_lib"))
sys.path.insert(0, str(ROOT))

import db  # noqa: E402
import search_service  # noqa: E402


# ---- db.save_price_history_batch ------------------------------------------------------------

ROWS = [
    ("KIX-TPE", "2027-02-22", 18600, "China Airlines", "Japan Airlines"),
    ("KIX-TPE", "2027-02-22", 21700, "EVA Air", "EVA Air"),
]


class FakeConn:
    def __init__(self):
        self.events = []

    def commit(self):
        self.events.append("commit")

    def rollback(self):
        self.events.append("rollback")

    def close(self):
        self.events.append("close")

    def cursor(self, **kwargs):
        return object()


class BatchWriterTest(unittest.TestCase):
    def setUp(self):
        self.conn = FakeConn()
        self.connects = []

        def fake_connect(*args, **kwargs):
            self.connects.append(args)
            return self.conn

        patcher = mock.patch.object(db.psycopg2, "connect", fake_connect)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.statements = []

        def fake_execute_values(cursor, sql, rows, template=None, page_size=100, fetch=False):
            self.conn.events.append("execute_values")
            self.statements.append((sql, list(rows), page_size))

        patcher = mock.patch.object(db, "execute_values", fake_execute_values)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_all_rows_go_in_one_connection_one_statement_one_commit(self):
        db.save_price_history_batch(ROWS)
        self.assertEqual(len(self.connects), 1)
        self.assertEqual(len(self.statements), 1)
        sql, rows, page_size = self.statements[0]
        self.assertEqual(rows, ROWS)
        self.assertIn("INSERT INTO price_history (route, departure_date, price_jpy, operating_airline, marketing_airline)", sql)
        self.assertTrue(sql.rstrip().endswith("VALUES %s"))
        self.assertEqual(self.conn.events, ["execute_values", "commit", "close"])

    def test_more_than_the_default_page_size_is_still_one_statement(self):
        rows = [("KIX-TPE", "2027-02-22", 20000 + i, "A", "B") for i in range(250)]
        db.save_price_history_batch(rows)
        self.assertEqual(len(self.statements), 1)
        self.assertEqual(self.statements[0][2], 250)  # page_size = len(rows), default would be 100
        self.assertEqual(self.statements[0][1], rows)

    def test_accepts_any_iterable_of_rows(self):
        db.save_price_history_batch(iter(ROWS))
        self.assertEqual(self.statements[0][1], ROWS)

    def test_no_rows_means_no_connection(self):
        db.save_price_history_batch([])
        self.assertEqual(self.connects, [])
        self.assertEqual(self.statements, [])

    def test_a_failing_statement_rolls_back_without_committing_and_raises(self):
        def failing(*args, **kwargs):
            self.conn.events.append("execute_values")
            raise RuntimeError("insert failed")

        with mock.patch.object(db, "execute_values", failing):
            with self.assertRaises(RuntimeError):
                db.save_price_history_batch(ROWS)
        self.assertEqual(self.conn.events, ["execute_values", "rollback", "close"])
        self.assertNotIn("commit", self.conn.events)

    def test_the_single_row_writer_is_still_there(self):
        cursor = mock.MagicMock()

        @contextlib.contextmanager
        def fake_get_db():
            yield self.conn, cursor

        with mock.patch.object(db, "get_db", fake_get_db):
            db.save_price_history("KIX-TPE", "2027-02-22", 18600, "China Airlines", "Japan Airlines")
        sql, params = cursor.execute.call_args[0]
        self.assertIn("INSERT INTO price_history", sql)
        self.assertEqual(params, ROWS[0])
        self.assertEqual(self.conn.events, ["commit"])


# ---- search_service -------------------------------------------------------------------------

def _carrier(iata, name):
    return {"iata_code": iata, "name": name}


def _offer(offer_id, owner, marketing, operating, amount, currency="USD"):
    segment = {
        "marketing_carrier": marketing, "operating_carrier": operating,
        "marketing_carrier_flight_number": "1", "operating_carrier_flight_number": "1",
        "origin": {"iata_code": "KIX"}, "destination": {"iata_code": "TPE"},
        "departing_at": "2027-02-22T10:00:00", "arriving_at": "2027-02-22T12:00:00",
    }
    return {"id": offer_id, "total_amount": amount, "total_currency": currency, "owner": owner,
            "slices": [{"segments": [segment]}]}


JL, CI, BR, ZZ = _carrier("JL", "Japan Airlines"), _carrier("CI", "China Airlines"), _carrier("BR", "EVA Air"), _carrier("ZZ", "Duffel Airways")
RAW = {"data": {"offers": [
    _offer("off_cs", JL, JL, CI, "120.00"),            # 120 USD x 155 = 18,600 JPY
    _offer("off_own", BR, BR, BR, "140.00"),           # 21,700 JPY
    _offer("off_zz", ZZ, ZZ, ZZ, "10.00"),             # dropped by the normalizer
    _offer("off_eur", BR, BR, BR, "90.00", "EUR"),     # not JPY: never recorded
]}}
EXPECTED_ROWS = [
    ("KIX-TPE", "2027-02-22", 18600, "China Airlines", "Japan Airlines"),
    ("KIX-TPE", "2027-02-22", 21700, "EVA Air", "EVA Air"),
]
DUFFEL_ERROR = {"errors": [{"code": "validation_error", "title": "Bad request"}]}


class FakeDb:
    def __init__(self, cache_error=None, history_error=None):
        self.cache = {}
        self.cache_writes, self.history_batches = [], []
        self.cache_error, self.history_error = cache_error, history_error

    def get_cached_search(self, route, departure_date, cabin_class, passengers):
        key = (route, departure_date, cabin_class, passengers)
        return {"result_json": self.cache[key]} if key in self.cache else None

    def save_search_cache(self, route, departure_date, passengers, result_json, cabin_class):
        if self.cache_error:
            raise self.cache_error
        self.cache_writes.append((route, departure_date, passengers, result_json, cabin_class))
        self.cache[(route, departure_date, cabin_class, passengers)] = result_json

    def save_price_history(self, *args):
        raise AssertionError("per-row history writes are no longer used by a search")

    def save_price_history_batch(self, rows):
        rows = list(rows)
        if self.history_error:
            raise self.history_error
        self.history_batches.append(rows)


class FakeDuffel:
    def __init__(self, response):
        self.response, self.calls = response, []

    def search_flights(self, *args):
        self.calls.append(args)
        return self.response


class HistoryTestCase(unittest.TestCase):
    def use(self, response=RAW, **db_kwargs):
        self.db, self.duffel = FakeDb(**db_kwargs), FakeDuffel(response)
        for name, fake in (("db", self.db), ("duffel_service", self.duffel)):
            patcher = mock.patch.object(search_service, name, fake)
            patcher.start()
            self.addCleanup(patcher.stop)

    def search(self, passengers=("adult",), cabin_class="economy"):
        passengers = passengers if isinstance(passengers, str) else list(passengers)
        return search_service.get_normalized_offers("KIX", "TPE", "2027-02-22", passengers, cabin_class)


class BatchCallTest(HistoryTestCase):
    def test_one_batch_per_search_with_all_rows_in_offer_order(self):
        self.use()
        self.search()
        self.assertEqual(self.db.history_batches, [EXPECTED_ROWS])

    def test_only_jpy_offers_and_never_zz(self):
        self.use()
        self.search()
        flat = [row for batch in self.db.history_batches for row in batch]
        self.assertEqual(len(flat), 2)  # 4 raw offers: ZZ dropped by the normalizer, EUR not JPY

    def test_passengers_as_the_joined_string_still_count_as_one_adult(self):
        self.use()
        self.search(passengers="adult")
        self.assertEqual(self.db.history_batches, [EXPECTED_ROWS])

    def test_a_cache_hit_writes_nothing_more(self):
        self.use()
        self.search()
        self.search()
        self.assertEqual((len(self.db.cache_writes), len(self.db.history_batches)), (1, 1))

    def test_duffel_error_writes_nothing(self):
        self.use(DUFFEL_ERROR)
        with self.assertLogs("search_service", level="WARNING"):
            self.assertEqual(self.search(), [])
        self.assertEqual((self.db.cache_writes, self.db.history_batches), ([], []))


class PassengerAndCabinGuardTest(HistoryTestCase):
    def assertCachedButNoHistory(self, **search_kwargs):
        self.use()
        self.search(**search_kwargs)
        self.assertEqual(len(self.db.cache_writes), 1, search_kwargs)  # the cache row is written as before
        self.assertEqual(self.db.history_batches, [], search_kwargs)

    def test_two_adults_write_no_history(self):
        self.assertCachedButNoHistory(passengers=("adult", "adult"))

    def test_an_adult_and_a_child_write_no_history(self):
        self.assertCachedButNoHistory(passengers=("adult", "child"))

    def test_a_child_alone_writes_no_history(self):
        self.assertCachedButNoHistory(passengers=("child",))

    def test_three_passengers_write_no_history(self):
        self.assertCachedButNoHistory(passengers=("adult", "adult", "child"))

    def test_the_joined_two_adult_string_writes_no_history(self):
        self.assertCachedButNoHistory(passengers="adult,adult")

    def test_non_economy_writes_no_history(self):
        for cabin in ("business", "premium_economy", "first"):
            self.assertCachedButNoHistory(cabin_class=cabin)

    def test_one_adult_economy_writes_history(self):
        self.use()
        self.search(passengers=("adult",), cabin_class="economy")
        self.assertEqual(len(self.db.history_batches), 1)

    def test_the_cache_key_keeps_the_full_passenger_string(self):
        self.use()
        self.search(passengers=("adult", "adult"))
        self.assertEqual(self.db.cache_writes[0][2], "adult,adult")


class WriteFailureTest(HistoryTestCase):
    def test_a_failing_cache_write_still_returns_the_offers_and_still_tries_history(self):
        self.use(cache_error=RuntimeError("cache down"))
        with self.assertLogs("search_service", level="WARNING") as logs:
            offers = self.search()
        self.assertEqual([o["Offer ID"] for o in offers], ["off_cs", "off_own", "off_eur"])
        self.assertTrue(any("search_cache write failed" in line for line in logs.output))
        self.assertEqual(self.db.history_batches, [EXPECTED_ROWS])

    def test_a_failing_history_batch_still_returns_the_offers_and_keeps_the_cache_row(self):
        self.use(history_error=RuntimeError("history down"))
        with self.assertLogs("search_service", level="WARNING") as logs:
            offers = self.search()
        self.assertEqual([o["Offer ID"] for o in offers], ["off_cs", "off_own", "off_eur"])
        self.assertEqual(len(self.db.cache_writes), 1)
        message = next(line for line in logs.output if "price_history write failed" in line)
        self.assertIn("KIX-TPE", message)
        self.assertIn("2 rows rolled back", message)

    def test_both_writes_failing_still_returns_the_offers(self):
        self.use(cache_error=RuntimeError("cache down"), history_error=RuntimeError("history down"))
        with self.assertLogs("search_service", level="WARNING") as logs:
            offers = self.search()
        self.assertEqual(len(offers), 3)
        self.assertEqual(len([line for line in logs.output if "write failed" in line]), 2)

    def test_a_lost_history_write_is_not_retried_by_a_later_cache_hit(self):
        self.use(history_error=RuntimeError("history down"))
        with self.assertLogs("search_service", level="WARNING"):
            self.search()
        self.db.history_error = None
        self.search()  # served from the cache row that was written: no Duffel call, no history write
        self.assertEqual(len(self.duffel.calls), 1)
        self.assertEqual(self.db.history_batches, [])

    def test_a_search_without_history_rows_does_not_call_the_batch_writer(self):
        self.use(history_error=RuntimeError("must not be called"))
        self.search(passengers=("adult", "adult"))  # no rows -> no call -> no failure to log
        self.assertEqual(len(self.db.cache_writes), 1)

    def test_the_flask_route_answers_200_with_the_offers_when_both_writes_fail(self):
        import local_server
        self.use(cache_error=RuntimeError("cache down"), history_error=RuntimeError("history down"))
        client = local_server.app.test_client()
        with mock.patch.dict(os.environ, {"DEMO_SNAPSHOT": ""}), self.assertLogs("search_service", level="WARNING"):
            response = client.get("/api/flights/search?origin=KIX&destination=TPE&departureDate=2027-02-22"
                                  "&passengers=adult&cabinClass=economy")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([o["Offer ID"] for o in response.get_json()["data"]], ["off_cs", "off_own", "off_eur"])


if __name__ == "__main__":
    unittest.main()
