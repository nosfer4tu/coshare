import sys
import types
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api" / "_lib"))

# trend_service imports db at module level (psycopg2 + DATABASE_URL); the filter is pure,
# so stub db and keep these tests off the database.
sys.modules.setdefault("db", types.SimpleNamespace(get_db=None))

import trend_service  # noqa: E402
from trend_service import (  # noqa: E402
    _add_months, within_schedule_horizon, filter_within_horizon, month_averages,
)


def row(departure, recorded, price=10000):
    return {"departure_date": departure, "recorded_at": recorded, "price_jpy": price}


class AddMonthsTest(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(_add_months(date(2026, 10, 5), 10), date(2027, 8, 5))

    def test_clamps_to_month_end(self):
        self.assertEqual(_add_months(date(2026, 4, 30), 10), date(2027, 2, 28))
        self.assertEqual(_add_months(date(2026, 10, 31), 4), date(2027, 2, 28))

    def test_crosses_year(self):
        self.assertEqual(_add_months(date(2026, 12, 15), 10), date(2027, 10, 15))


class HorizonTest(unittest.TestCase):
    def test_boundary_is_inclusive(self):
        recorded = datetime(2026, 8, 20, 15, 30)
        self.assertTrue(within_schedule_horizon(date(2027, 6, 20), recorded))
        self.assertFalse(within_schedule_horizon(date(2027, 6, 21), recorded))

    def test_same_departure_date_depends_on_recorded_at(self):
        departure = date(2027, 7, 13)
        self.assertFalse(within_schedule_horizon(departure, datetime(2026, 8, 5)))
        self.assertTrue(within_schedule_horizon(departure, datetime(2026, 9, 13)))

    def test_null_recorded_at_is_excluded(self):
        self.assertFalse(within_schedule_horizon(date(2026, 11, 1), None))

    def test_filter_keeps_only_rows_inside_their_own_horizon(self):
        rows = [
            row(date(2027, 7, 13), datetime(2026, 8, 5), 1),    # recorded early: 11 months out -> drop
            row(date(2027, 7, 13), datetime(2026, 10, 1), 2),   # recorded later: 9 months out -> keep
            row(date(2026, 12, 29), datetime(2026, 8, 5), 3),   # 4 months out -> keep
            row(date(2027, 6, 5), datetime(2026, 8, 5), 4),     # exactly 10 months -> keep
            row(date(2027, 6, 6), datetime(2026, 8, 5), 5),     # one day over -> drop
        ]
        self.assertEqual([r["price_jpy"] for r in filter_within_horizon(rows)], [2, 3, 4])


class MonthAveragesTest(unittest.TestCase):
    def test_groups_by_calendar_month_across_years(self):
        rows = [
            row(date(2026, 12, 29), None, 10000),
            row(date(2027, 12, 1), None, 20000),
            row(date(2026, 8, 13), None, 9000),
        ]
        self.assertEqual(month_averages(rows), {12: 15000, 8: 9000})


class QueryWiringTest(unittest.TestCase):
    """The service applies the filter to both the chart rows and the month stats."""

    ROWS = [
        row(date(2027, 7, 13), datetime(2026, 8, 5), 300000),   # dropped
        row(date(2027, 7, 13), datetime(2026, 10, 1), 100000),  # kept
        row(date(2026, 12, 29), datetime(2026, 8, 5), 50000),   # kept
    ]

    def fake_db(self):
        cursor = mock.Mock()
        cursor.fetchall.return_value = list(self.ROWS)
        db = mock.MagicMock()
        db.__enter__.return_value = (mock.Mock(), cursor)
        return mock.Mock(return_value=db)

    def test_annual_trend(self):
        with mock.patch.object(trend_service, "get_db", self.fake_db()):
            result = trend_service.get_annual_price_trend("AAA-BBB")
        self.assertEqual([r["price_jpy"] for r in result], [100000, 50000])
        self.assertTrue(all(r["average_price"] == 75000 for r in result))

    def test_recommendation(self):
        with mock.patch.object(trend_service, "get_db", self.fake_db()):
            result = trend_service.get_price_recommendation("AAA-BBB")
        self.assertEqual(result, {
            "cheapest_month": 12, "cheapest_price": 50000,
            "most_expensive_month": 7, "most_expensive_price": 100000,
        })


if __name__ == "__main__":
    unittest.main()
