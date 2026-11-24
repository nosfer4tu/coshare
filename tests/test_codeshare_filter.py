"""filter_codeshare_offers: the keep rule for /api/codeshare/detect.

An offer is kept if it passes the original rule ('is Codeshare' and not HR-displayed), or if it
is a non-HR nonstop offer in the same pairing group (departure airport, arrival airport,
departure time, operating IATA) as one that does. Fixtures are small synthetic normalized
offers; the keys are the normalizer's own.
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api" / "_lib"))

from codeshare_service import filter_codeshare_offers  # noqa: E402


def offer(offer_id, display, operating, *, codeshare, departure="2027-02-22T12:55:00",
          origin="KIX", destination="TPE", segments=1, price=50000, **extra):
    """A normalized nonstop offer. `display` is the display carrier (Owner Airline IATA)."""
    row = {
        "Offer ID": offer_id, "Total Amount": price, "Currency": "JPY",
        "Owner Airline IATA": display, "Marketing IATA": display, "Operating IATA": operating,
        "Departure Airport": origin, "Arrival Airport": destination,
        "Departure Time": departure, "Segment Count": segments, "is Codeshare": codeshare,
    }
    row.update(extra)
    return row


def ids(offers):
    return [o["Offer ID"] for o in offers]


class OwnCodeOfferJoinsAnchoredGroupTest(unittest.TestCase):
    def test_own_code_offer_is_kept_next_to_the_codeshare_offer(self):
        # NH sells a BR-operated flight (codeshare); BR sells it under its own code, ticketed
        # by BR itself, so 'is Codeshare' is False for it.
        offers = [
            offer("br_own", "BR", "BR", codeshare=False, price=38766),
            offer("nh_cs", "NH", "BR", codeshare=True, price=203701),
        ]
        self.assertEqual(ids(filter_codeshare_offers(offers)), ["br_own", "nh_cs"])

    def test_every_offer_of_the_group_is_kept_in_input_order(self):
        offers = [
            offer("br_1", "BR", "BR", codeshare=False, price=77360),
            offer("nh_1", "NH", "BR", codeshare=True, price=203701),
            offer("br_2", "BR", "BR", codeshare=False, price=38766),
            offer("nh_2", "NH", "BR", codeshare=True, price=210676),
        ]
        self.assertEqual(ids(filter_codeshare_offers(offers)), ["br_1", "nh_1", "br_2", "nh_2"])

    def test_the_other_offer_may_come_before_the_codeshare_offer(self):
        offers = [
            offer("own", "BR", "BR", codeshare=False),
            offer("cs", "NH", "BR", codeshare=True),
        ]
        self.assertEqual(ids(filter_codeshare_offers(offers)), ["own", "cs"])

    def test_an_own_code_offer_already_flagged_stays_kept(self):
        # HR-ticketed own-code offer: 'is Codeshare' is True although marketing == operating.
        offers = [offer("ci_hr_ticketed", "CI", "CI", codeshare=True)]
        self.assertEqual(ids(filter_codeshare_offers(offers)), ["ci_hr_ticketed"])

    def test_groups_are_separated_by_departure_time_airport_and_operating_carrier(self):
        offers = [
            offer("cs", "NH", "BR", codeshare=True),
            offer("other_time", "BR", "BR", codeshare=False, departure="2027-02-22T10:55:00"),
            offer("other_arrival", "BR", "BR", codeshare=False, destination="TSA"),
            offer("other_origin", "BR", "BR", codeshare=False, origin="ITM"),
            offer("other_operator", "CI", "CI", codeshare=False),
        ]
        self.assertEqual(ids(filter_codeshare_offers(offers)), ["cs"])


class HrDisplayOfferTest(unittest.TestCase):
    def test_hr_display_offer_in_an_anchored_group_is_still_dropped(self):
        offers = [
            offer("cs", "NH", "BR", codeshare=True),
            offer("hr_plain", "HR", "BR", codeshare=False),
            offer("hr_flagged", "HR", "BR", codeshare=True),
            offer("own", "BR", "BR", codeshare=False),
        ]
        self.assertEqual(ids(filter_codeshare_offers(offers)), ["cs", "own"])

    def test_an_hr_offer_does_not_anchor_a_group(self):
        offers = [
            offer("hr_flagged", "HR", "BR", codeshare=True),
            offer("own", "BR", "BR", codeshare=False),
        ]
        self.assertEqual(filter_codeshare_offers(offers), [])


class ConnectingOfferTest(unittest.TestCase):
    def test_a_connecting_offer_is_not_pulled_in_by_a_shared_key(self):
        # Its 'Departure Time' / 'Operating IATA' describe the last leg only.
        offers = [
            offer("cs", "NH", "BR", codeshare=True),
            offer("connection", "BR", "BR", codeshare=False, segments=2),
        ]
        self.assertEqual(ids(filter_codeshare_offers(offers)), ["cs"])

    def test_a_connecting_codeshare_offer_does_not_anchor_a_group(self):
        offers = [
            offer("connection_cs", "NH", "BR", codeshare=True, segments=2),
            offer("own", "BR", "BR", codeshare=False),
        ]
        # The connecting offer still passes the original rule on its own (the frontend drops it
        # in codeshare mode); it just does not drag the nonstop own-code offer in.
        self.assertEqual(ids(filter_codeshare_offers(offers)), ["connection_cs"])


class UnanchoredGroupTest(unittest.TestCase):
    def test_a_group_without_a_codeshare_offer_stays_dropped(self):
        offers = [
            offer("br_own", "BR", "BR", codeshare=False),
            offer("br_own_tier", "BR", "BR", codeshare=False, price=77360),
        ]
        self.assertEqual(filter_codeshare_offers(offers), [])

    def test_a_group_of_hr_and_own_code_offers_only_stays_dropped(self):
        offers = [
            offer("hr", "HR", "BR", codeshare=False),
            offer("own", "BR", "BR", codeshare=False),
        ]
        self.assertEqual(filter_codeshare_offers(offers), [])


class Nrt1115PairTest(unittest.TestCase):
    """NRT-BOM 11:15: Air India sells an ANA-operated flight; ANA sells it under NH."""
    ROUTE = dict(departure="2027-02-22T11:15:00", origin="NRT", destination="BOM")

    def ai(self):
        return offer("ai8001", "AI", "NH", codeshare=True, price=213978, **self.ROUTE)

    def nh(self):
        return offer("nh829", "NH", "NH", codeshare=False, price=294112, **self.ROUTE)

    def test_the_pair_appears_when_both_offers_are_present(self):
        self.assertEqual(ids(filter_codeshare_offers([self.ai(), self.nh()])), ["ai8001", "nh829"])

    def test_without_the_codeshare_offer_nothing_is_returned(self):
        self.assertEqual(filter_codeshare_offers([self.nh()]), [])

    def test_without_the_own_code_offer_only_the_codeshare_offer_is_returned(self):
        self.assertEqual(ids(filter_codeshare_offers([self.ai()])), ["ai8001"])

    def test_another_departure_time_does_not_join_the_pair(self):
        later = offer("nh827", "NH", "NH", codeshare=False, departure="2027-02-22T19:15:00",
                      origin="NRT", destination="BOM")
        self.assertEqual(ids(filter_codeshare_offers([self.ai(), later, self.nh()])), ["ai8001", "nh829"])


class OlderRowsAndPurityTest(unittest.TestCase):
    def test_offers_without_segment_count_group_as_nonstop(self):
        cs = offer("cs", "NH", "BR", codeshare=True)
        own = offer("own", "BR", "BR", codeshare=False)
        del cs["Segment Count"], own["Segment Count"]
        self.assertEqual(ids(filter_codeshare_offers([cs, own])), ["cs", "own"])

    def test_offers_without_pairing_fields_are_never_grouped(self):
        # No departure time / operating IATA: only the original rule applies.
        offers = [
            {"Offer ID": "a", "is Codeshare": True, "Owner Airline IATA": "JL"},
            {"Offer ID": "b", "is Codeshare": False, "Owner Airline IATA": "BR"},
        ]
        self.assertEqual(ids(filter_codeshare_offers(offers)), ["a"])

    def test_input_is_not_mutated_and_the_result_holds_the_same_objects(self):
        offers = [offer("own", "BR", "BR", codeshare=False), offer("cs", "NH", "BR", codeshare=True)]
        snapshot = copy.deepcopy(offers)
        result = filter_codeshare_offers(offers)
        self.assertEqual(offers, snapshot)
        self.assertIs(result[0], offers[0])

    def test_empty_input(self):
        self.assertEqual(filter_codeshare_offers([]), [])


if __name__ == "__main__":
    unittest.main()
