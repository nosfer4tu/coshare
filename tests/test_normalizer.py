import sys
import unittest
from pathlib import Path

# api/_lib modules import each other as top-level modules (`from normalizer import ...`),
# so that directory has to be on the path. `config`/`db` are not imported by the modules
# under test here, so no env vars or DB access are needed.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api" / "_lib"))

from normalizer import normalize_offers  # noqa: E402
from codeshare_service import get_codeshare_offers  # noqa: E402


def _carrier(iata, name):
    return {"iata_code": iata, "name": name}


def _segment(marketing, operating, number, origin="KIX", destination="ICN",
             departing="2026-12-02T10:00:00", arriving="2026-12-02T12:00:00"):
    return {
        "marketing_carrier": marketing,
        "operating_carrier": operating,
        "marketing_carrier_flight_number": number,
        "operating_carrier_flight_number": number,
        "origin": {"iata_code": origin},
        "destination": {"iata_code": destination},
        "departing_at": departing,
        "arriving_at": arriving,
    }


HR = _carrier("HR", "Hahn Air")
SEVEN_C = _carrier("7C", "Jeju Air")
JL = _carrier("JL", "Japan Airlines")
CI = _carrier("CI", "China Airlines")
BR = _carrier("BR", "EVA Air")

RAW_FIXTURE = {"data": {"offers": [
    # a) ticketed by HR, sold and operated by 7C
    {"id": "off_a", "total_amount": "100.00", "total_currency": "USD", "owner": HR,
     "slices": [{"segments": [_segment(SEVEN_C, SEVEN_C, "901")]}]},
    # b) ticketed and sold by JL, operated by CI
    {"id": "off_b", "total_amount": "120.00", "total_currency": "USD", "owner": JL,
     "slices": [{"segments": [_segment(JL, CI, "5001")]}]},
    # c) ticketed, sold and operated by BR
    {"id": "off_c", "total_amount": "140.00", "total_currency": "USD", "owner": BR,
     "slices": [{"segments": [_segment(BR, BR, "101")]}]},
    # d) connection: leg 1 is a codeshare (JL sells, CI operates), leg 2 is BR's own flight
    {"id": "off_d", "total_amount": "160.00", "total_currency": "USD", "owner": BR,
     "slices": [{"segments": [
         _segment(JL, CI, "5002", destination="TPE",
                  departing="2026-12-02T08:00:00", arriving="2026-12-02T10:00:00"),
         _segment(BR, BR, "102", origin="TPE", destination="ICN",
                  departing="2026-12-02T12:00:00", arriving="2026-12-02T15:00:00"),
     ]}]},
]}}

# 'is Codeshare' captured by running the normalizer at HEAD (before 'is Marketing Codeshare'
# existed). get_codeshare_offers keeps only the offers whose flag is true and whose
# 'Owner Airline IATA' is not HR.
HEAD_IS_CODESHARE = {"off_a": True, "off_b": True, "off_c": False, "off_d": False}
HEAD_CODESHARE_IDS = ["off_a", "off_b"]


class NormalizerCodeshareFlagTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {o["Offer ID"]: o for o in normalize_offers(RAW_FIXTURE)}

    def test_is_codeshare_unchanged_from_head(self):
        self.assertEqual(
            {k: v["is Codeshare"] for k, v in self.by_id.items()},
            HEAD_IS_CODESHARE,
        )

    def test_is_marketing_codeshare(self):
        self.assertEqual(
            {k: v["is Marketing Codeshare"] for k, v in self.by_id.items()},
            {"off_a": False, "off_b": True, "off_c": False, "off_d": False},
        )

    def test_connection_uses_last_segment(self):
        # First leg would give True (JL/CI); the last leg (BR/BR) decides.
        offer = self.by_id["off_d"]
        self.assertEqual(offer["Marketing IATA"], "BR")
        self.assertEqual(offer["Operating IATA"], "BR")
        self.assertIs(offer["is Marketing Codeshare"], False)

    def test_get_codeshare_offers_unchanged_from_head(self):
        self.assertEqual(
            [o["Offer ID"] for o in get_codeshare_offers(RAW_FIXTURE)],
            HEAD_CODESHARE_IDS,
        )


# Sanitized connection: first leg departs 10:40, last leg departs 22:00.
CONNECTION_FIXTURE = {"data": {"offers": [
    {"id": "off_conn", "total_amount": "200.00", "total_currency": "USD", "owner": BR,
     "slices": [{"segments": [
         _segment(BR, BR, "201", origin="KIX", destination="TPE",
                  departing="2026-12-02T10:40:00", arriving="2026-12-02T13:00:00"),
         _segment(BR, BR, "202", origin="TPE", destination="BKK",
                  departing="2026-12-02T22:00:00", arriving="2026-12-03T00:50:00"),
     ]}]},
    {"id": "off_direct", "total_amount": "150.00", "total_currency": "USD", "owner": BR,
     "slices": [{"segments": [_segment(BR, BR, "203", origin="KIX", destination="BKK",
                                       departing="2026-12-02T10:40:00",
                                       arriving="2026-12-02T15:00:00")]}]},
]}}


class NormalizerFirstDepartureTest(unittest.TestCase):
    def setUp(self):
        self.by_id = {o["Offer ID"]: o for o in normalize_offers(CONNECTION_FIXTURE)}

    def test_connection_first_departure_is_first_leg(self):
        offer = self.by_id["off_conn"]
        self.assertEqual(offer["First Departure Time"], "2026-12-02T10:40:00")
        # Unchanged: grouping/pairing still reads the last leg.
        self.assertEqual(offer["Departure Time"], "2026-12-02T22:00:00")
        self.assertEqual(offer["Segment Count"], 2)

    def test_direct_first_departure_equals_departure(self):
        offer = self.by_id["off_direct"]
        self.assertEqual(offer["First Departure Time"], "2026-12-02T10:40:00")
        self.assertEqual(offer["Departure Time"], offer["First Departure Time"])
        self.assertEqual(offer["Segment Count"], 1)


if __name__ == "__main__":
    unittest.main()
