from db import get_db
from holiday_detector import detect_holiday

def get_annual_price_trend(route):
    with get_db() as (conn, cursor):
        # Airlines only publish schedules ~11 months out; beyond that Duffel
        # returns few carriers, so those months skew the average. Exclude them.
        cursor.execute("""
            SELECT departure_date,
            price_jpy,
            AVG(price_jpy) OVER () as average_price
            FROM price_history
            WHERE route = %s
            AND departure_date <= CURRENT_DATE + INTERVAL '10 months'
            """, (route,))
        result = cursor.fetchall()
    trend_list = []
    
    for row in result:
        trend_list.append({
            "date": row["departure_date"],
            "price_jpy": row["price_jpy"],
            "average_price": row["average_price"],
            "holiday": detect_holiday(str(row["departure_date"]))
        })
    return trend_list

def get_price_recommendation(route):
    with get_db() as (conn, cursor):
        cursor.execute("""
                    SELECT
                        EXTRACT(MONTH FROM departure_date) AS month,
                        AVG(price_jpy) AS avg_price
                    FROM price_history
                    WHERE route = %s
                    AND departure_date <= CURRENT_DATE + INTERVAL '10 months'
                    GROUP BY EXTRACT(MONTH FROM departure_date)
                    ORDER BY avg_price ASC
                    LIMIT 1
                    """, (route,))
        cheapest = cursor.fetchone()
        cursor.execute("""
                    SELECT
                        EXTRACT(MONTH FROM departure_date) AS month,
                        AVG(price_jpy) AS avg_price
                    FROM price_history
                    WHERE route = %s
                    AND departure_date <= CURRENT_DATE + INTERVAL '10 months'
                    GROUP BY EXTRACT(MONTH FROM departure_date)
                    ORDER BY avg_price DESC
                    LIMIT 1
                    """, (route,))
        most_expensive = cursor.fetchone()
        return {
            "cheapest_month": cheapest["month"],
            "cheapest_price": cheapest["avg_price"],
            "most_expensive_month": most_expensive["month"],
            "most_expensive_price": most_expensive["avg_price"]
        }