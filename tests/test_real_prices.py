import copy
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# real_prices.py is pure (stdlib only), so no env vars or DB access are needed.
sys.path.insert(0, str(ROOT / "api" / "_lib"))
sys.path.insert(0, str(ROOT))

from real_prices import (  # noqa: E402
    DATA_FILE, RealPricesError, build_summary, load_routes, lookup_response,
    validate_entry, validate_route, validate_routes,
)

TODAY = date(2026, 11, 4)


def make_entry(**overrides):
    entry = {
        "kind": "full_service", "airline": "Sample Air", "flight_number": "SA100",
        "dep": "09:00", "arr": "11:15", "stops": 0, "price_jpy": 30000, "seller": "Sample",
    }
    entry.update(overrides)
    return entry


def make_route(**overrides):
    route = {
        "origin": "AAA", "destination": "BBB", "flight_date": "2026-12-03",
        "captured_on": "2026-10-19", "source": "manual", "cabin": "economy",
        "passengers": 1, "trip": "one-way", "entries": [make_entry()],
    }
    route.update(overrides)
    return route


class SeedDataTest(unittest.TestCase):
    def test_seed_file_is_valid(self):
        routes = load_routes(DATA_FILE, today=TODAY)
        self.assertEqual(len(routes), 1)
        route = routes[0]
        self.assertEqual((route["origin"], route["destination"], route["flight_date"]),
                         ("KIX", "TPE", "2026-12-03"))
        self.assertEqual(route["captured_on"], "2026-10-19")
        self.assertEqual(len(route["entries"]), 13)

    def test_seed_validates_with_validate_routes(self):
        with open(DATA_FILE, encoding="utf-8") as f:
            self.assertEqual(validate_routes(json.load(f)["routes"], today=TODAY), [])


class ValidateRouteTest(unittest.TestCase):
    def assertInvalid(self, route, fragment):
        errors = validate_route(route, today=TODAY)
        self.assertTrue(any(fragment in e for e in errors), f"expected '{fragment}' in {errors}")

    def test_valid_route(self):
        self.assertEqual(validate_route(make_route(), today=TODAY), [])

    def test_negative_or_bad_price_rejected(self):
        for bad in (-1, 0, 1.5, "100", True, None):
            with self.subTest(bad=bad):
                self.assertInvalid(make_route(entries=[make_entry(price_jpy=bad)]), "price_jpy")

    def test_airline_site_price_must_be_positive_int(self):
        self.assertEqual(validate_route(make_route(entries=[make_entry(airline_site_price_jpy=31000)]), today=TODAY), [])
        for bad in (-5, 0, "1"):
            with self.subTest(bad=bad):
                self.assertInvalid(make_route(entries=[make_entry(airline_site_price_jpy=bad)]),
                                   "airline_site_price_jpy")

    def test_dangling_same_flight_as_rejected(self):
        route = make_route(entries=[make_entry(same_flight_as="XX999")])
        self.assertInvalid(route, "same_flight_as 'XX999' is not a flight_number in this route")

    def test_same_flight_as_must_not_reference_itself(self):
        self.assertInvalid(make_route(entries=[make_entry(same_flight_as="SA100")]), "reference itself")

    def test_same_flight_as_resolves_within_route(self):
        entries = [make_entry(), make_entry(flight_number="SB200", same_flight_as="SA100")]
        self.assertEqual(validate_route(make_route(entries=entries), today=TODAY), [])

    def test_duplicate_flight_number_rejected(self):
        self.assertInvalid(make_route(entries=[make_entry(), make_entry()]), "duplicate flight_number")

    def test_future_captured_on_rejected(self):
        self.assertInvalid(make_route(captured_on="2026-11-05"), "captured_on must not be in the future")

    def test_captured_on_today_accepted(self):
        self.assertEqual(validate_route(make_route(captured_on="2026-11-04"), today=TODAY), [])

    def test_captured_on_after_flight_date_rejected(self):
        self.assertInvalid(make_route(flight_date="2026-10-01", captured_on="2026-10-19"),
                           "captured_on must be on or before flight_date")

    def test_captured_on_equal_to_flight_date_accepted(self):
        self.assertEqual(validate_route(make_route(flight_date="2026-10-19"), today=TODAY), [])

    def test_bad_dates_rejected(self):
        for bad in ("2026-13-01", "2026/12/03", "20261203", "", None, 20261203):
            with self.subTest(bad=bad):
                self.assertInvalid(make_route(flight_date=bad), "flight_date")
                self.assertInvalid(make_route(captured_on=bad), "captured_on")

    def test_route_fixed_fields(self):
        self.assertInvalid(make_route(cabin="business"), "cabin")
        self.assertInvalid(make_route(passengers=2), "passengers")
        self.assertInvalid(make_route(passengers=True), "passengers")
        self.assertInvalid(make_route(trip="round-trip"), "trip")

    def test_entries_must_be_nonempty(self):
        self.assertInvalid(make_route(entries=[]), "entries")

    def test_duplicate_route_rejected(self):
        errors = validate_routes([make_route(), make_route()], today=TODAY)
        self.assertTrue(any("duplicate route" in e for e in errors), errors)


class ValidateEntryTest(unittest.TestCase):
    def assertInvalid(self, entry, fragment):
        errors = validate_entry(entry)
        self.assertTrue(any(fragment in e for e in errors), f"expected '{fragment}' in {errors}")

    def test_valid_entry(self):
        self.assertEqual(validate_entry(make_entry()), [])

    def test_kind_must_be_valid(self):
        for good in ("full_service", "lcc"):
            self.assertEqual(validate_entry(make_entry(kind=good)), [])
        for bad in ("premium", "LCC", "", None):
            with self.subTest(bad=bad):
                self.assertInvalid(make_entry(kind=bad), "kind")

    def test_time_format(self):
        for good in ("00:00", "09:05", "23:59"):
            self.assertEqual(validate_entry(make_entry(dep=good, arr=good)), [])
        for bad in ("9:05", "24:00", "12:60", "1205", "12:5", "ab:cd", "12:00:00", None, 1205):
            with self.subTest(bad=bad):
                self.assertInvalid(make_entry(dep=bad), "dep")
                self.assertInvalid(make_entry(arr=bad), "arr")

    def test_airline_codes_are_two_characters(self):
        for field in ("marketing_code", "operating_code"):
            for good in ("CI", "7C", "D7"):
                self.assertEqual(validate_entry(make_entry(**{field: good})), [])
            for bad in ("C", "CIA", "", "ci", "C ", 12):
                with self.subTest(field=field, bad=bad):
                    self.assertInvalid(make_entry(**{field: bad}), field)

    def test_stops_must_be_nonnegative_int(self):
        self.assertEqual(validate_entry(make_entry(stops=1)), [])
        for bad in (-1, 0.5, "0", True):
            with self.subTest(bad=bad):
                self.assertInvalid(make_entry(stops=bad), "stops")

    def test_arr_next_day_must_be_bool(self):
        self.assertEqual(validate_entry(make_entry(arr_next_day=True)), [])
        self.assertInvalid(make_entry(arr_next_day="yes"), "arr_next_day")

    def test_required_fields(self):
        for field in ("kind", "airline", "dep", "arr", "stops", "price_jpy", "seller"):
            entry = make_entry()
            del entry[field]
            with self.subTest(field=field):
                self.assertInvalid(entry, f"{field} is required")

    def test_optional_fields_may_be_absent(self):
        entry = make_entry()
        del entry["flight_number"]
        self.assertEqual(validate_entry(entry), [])


class LoadRoutesTest(unittest.TestCase):
    def test_invalid_file_raises_with_all_errors(self):
        bad = make_route(captured_on="2027-01-01", entries=[make_entry(price_jpy=-1, same_flight_as="NOPE")])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "real_prices.json"
            path.write_text(json.dumps({"routes": [bad]}), encoding="utf-8")
            with self.assertRaises(RealPricesError) as ctx:
                load_routes(path, today=TODAY)
        message = str(ctx.exception)
        self.assertIn("captured_on", message)
        self.assertIn("price_jpy", message)
        self.assertIn("same_flight_as", message)


class LookupResponseTest(unittest.TestCase):
    def lookup(self, origin="KIX", destination="TPE", departure_date="2026-12-03"):
        return lookup_response(origin, destination, departure_date, today=TODAY)

    def test_unknown_route_not_found(self):
        self.assertEqual(self.lookup("KIX", "ICN"), (200, {"found": False}))

    def test_exact_match_on_date_and_direction(self):
        self.assertEqual(self.lookup(departure_date="2026-12-04"), (200, {"found": False}))
        self.assertEqual(self.lookup("TPE", "KIX"), (200, {"found": False}))

    def test_missing_or_bad_params_are_400(self):
        self.assertEqual(self.lookup(origin=None)[0], 400)
        self.assertEqual(self.lookup(destination="")[0], 400)
        self.assertEqual(self.lookup(departure_date=None)[0], 400)
        self.assertEqual(self.lookup(departure_date="2026/12/03")[0], 400)

    def test_found_shape_and_sorting(self):
        status, body = self.lookup()
        self.assertEqual(status, 200)
        self.assertTrue(body["found"])
        self.assertEqual(
            set(body), {"found", "flight_date", "captured_on", "source", "entries", "summary"})
        self.assertEqual(body["flight_date"], "2026-12-03")
        self.assertEqual(body["captured_on"], "2026-10-19")
        self.assertEqual(body["source"], "Skyscanner (manual check)")
        prices = [e["price_jpy"] for e in body["entries"]]
        self.assertEqual(prices, sorted(prices))
        self.assertEqual(len(prices), 13)

    def test_summary_cheapest_lcc(self):
        _, body = self.lookup()
        lcc = body["summary"]["cheapest_lcc"]
        self.assertEqual(lcc["price_jpy"], 20718)
        self.assertEqual(lcc["airline"], "Jetstar Japan")
        self.assertEqual(lcc["kind"], "lcc")

    def test_summary_cheapest_full_service(self):
        _, body = self.lookup()
        full = body["summary"]["cheapest_full_service"]
        self.assertEqual(full["price_jpy"], 36849)
        self.assertEqual(full["flight_number"], "CI157")

    def test_summary_br131_nh5811_gap(self):
        _, body = self.lookup()
        pairs = {p["cheaper"]["flight_number"]: p for p in body["summary"]["codeshare_pairs"]}
        pair = pairs["BR131"]
        self.assertEqual(pair["gap_jpy"], 154899)
        self.assertEqual(pair["pricier"]["flight_number"], "NH5811")
        self.assertEqual(pair["cheaper"]["price_jpy"], 40828)
        self.assertEqual(pair["pricier"]["price_jpy"], 195727)

    def test_summary_lists_both_seed_pairs(self):
        _, body = self.lookup()
        gaps = {p["cheaper"]["flight_number"]: p["gap_jpy"] for p in body["summary"]["codeshare_pairs"]}
        self.assertEqual(gaps, {"BR131": 154899, "BR177": 222588})

    def test_invalid_data_file_is_500(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "real_prices.json"
            path.write_text(json.dumps({"routes": [make_route(entries=[make_entry(price_jpy=-1)])]}),
                            encoding="utf-8")
            status, body = lookup_response("AAA", "BBB", "2026-12-03", path=path, today=TODAY)
        self.assertEqual(status, 500)
        self.assertIn("error", body)


class BuildSummaryTest(unittest.TestCase):
    def test_no_lcc_or_pairs(self):
        summary = build_summary([make_entry()])
        self.assertIsNone(summary["cheapest_lcc"])
        self.assertEqual(summary["cheapest_full_service"]["price_jpy"], 30000)
        self.assertEqual(summary["codeshare_pairs"], [])

    def test_link_written_in_both_directions_counts_once(self):
        a = make_entry(flight_number="AA1", price_jpy=100, same_flight_as="BB2")
        b = make_entry(flight_number="BB2", price_jpy=250, same_flight_as="AA1")
        pairs = build_summary([a, b])["codeshare_pairs"]
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["gap_jpy"], 150)

    def test_cheaper_side_is_the_lower_price_regardless_of_link_direction(self):
        # The link is written on the cheaper entry here.
        a = make_entry(flight_number="AA1", price_jpy=100, same_flight_as="BB2")
        b = make_entry(flight_number="BB2", price_jpy=250)
        pair = build_summary([a, b])["codeshare_pairs"][0]
        self.assertEqual(pair["cheaper"]["flight_number"], "AA1")
        self.assertEqual(pair["pricier"]["flight_number"], "BB2")

    def test_does_not_mutate_input(self):
        entries = [make_entry(flight_number="AA1", price_jpy=100), make_entry(flight_number="BB2", price_jpy=250)]
        snapshot = copy.deepcopy(entries)
        build_summary(entries)
        self.assertEqual(entries, snapshot)


class FlaskEndpointTest(unittest.TestCase):
    """Route wiring in local_server.py (query-string names, status codes, JSON)."""

    @classmethod
    def setUpClass(cls):
        import local_server
        cls.client = local_server.app.test_client()

    def test_unknown_route(self):
        res = self.client.get("/api/real-prices?origin=NRT&destination=ICN&departureDate=2026-12-03")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"found": False})

    def test_seed_route_summary(self):
        res = self.client.get("/api/real-prices?origin=KIX&destination=TPE&departureDate=2026-12-03")
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["found"])
        self.assertEqual(body["summary"]["cheapest_lcc"]["price_jpy"], 20718)
        gaps = {p["cheaper"]["flight_number"]: p["gap_jpy"] for p in body["summary"]["codeshare_pairs"]}
        self.assertEqual(gaps["BR131"], 154899)

    def test_missing_params_400(self):
        res = self.client.get("/api/real-prices?origin=KIX&destination=TPE")
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
