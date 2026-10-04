import calendar
from collections import defaultdict
from db import get_db
from holiday_detector import detect_holiday

# Airlines only publish schedules ~11 months out; a row recorded when its departure
# date was beyond that horizon is thin data that skews the average. The cutoff is
# relative to when the row was recorded, not to today, so it does not drift.
HORIZON_MONTHS = 10

def _add_months(d, months):
    # Same clamping as Postgres: Jan 31 + 1 month = Feb 28/29.
    index = d.year * 12 + (d.month - 1) + months
    year, month = divmod(index, 12)
    month += 1
    return d.replace(year=year, month=month, day=min(d.day, calendar.monthrange(year, month)[1]))

def within_schedule_horizon(departure_date, recorded_at):
    # A row with no recorded_at cannot be shown to be inside the horizon, so it is excluded.
    if recorded_at is None:
        return False
    return departure_date <= _add_months(recorded_at.date(), HORIZON_MONTHS)

def filter_within_horizon(rows):
    return [r for r in rows if within_schedule_horizon(r["departure_date"], r["recorded_at"])]

def month_averages(rows):
    prices = defaultdict(list)
    for r in rows:
        prices[r["departure_date"].month].append(r["price_jpy"])
    return {month: sum(p) / len(p) for month, p in prices.items()}

def _fetch_horizon_rows(route):
    with get_db() as (conn, cursor):
        cursor.execute("""
            SELECT departure_date, price_jpy, recorded_at
            FROM price_history
            WHERE route = %s
            """, (route,))
        return filter_within_horizon(cursor.fetchall())

def get_annual_price_trend(route):
    rows = _fetch_horizon_rows(route)
    average_price = sum(r["price_jpy"] for r in rows) / len(rows) if rows else None
    trend_list = []

    for row in rows:
        trend_list.append({
            "date": row["departure_date"],
            "price_jpy": row["price_jpy"],
            "average_price": average_price,
            "holiday": detect_holiday(str(row["departure_date"]))
        })
    return trend_list

def get_price_recommendation(route):
    averages = month_averages(_fetch_horizon_rows(route))
    if not averages:
        return {
            "cheapest_month": None,
            "cheapest_price": None,
            "most_expensive_month": None,
            "most_expensive_price": None,
            "reason": "no_data"
        }
    cheapest = min(averages.items(), key=lambda item: item[1])
    most_expensive = max(averages.items(), key=lambda item: item[1])
    return {
        "cheapest_month": cheapest[0],
        "cheapest_price": cheapest[1],
        "most_expensive_month": most_expensive[0],
        "most_expensive_price": most_expensive[1]
    }
