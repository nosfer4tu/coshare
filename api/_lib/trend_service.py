from db import get_db
from holiday_detector import detect_holiday

def get_annual_price_trend(route):
    with get_db() as (conn, cursor):
        cursor.execute("""
            SELECT departure_date,
            price_jpy,
            AVG(price_jpy) OVER () as average_price
            FROM price_history
            WHERE route = %s
            """, (route,))
        result = cursor.fetchall()
    trend_list = []
    
    for row in result:
        trend_list.append({
            "date": row["departure_date"],
            "price_jpy": row["price_jpy"],
            "average_price": row["average_price"],
            "holiday": detect_holiday(row["departure_date"])
        })
    return trend_list
        