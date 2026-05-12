import os
from pathlib import Path
from dotenv import load_dotenv
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor

env_path = Path(__file__).parent.parent.parent / '.env.local'
load_dotenv(dotenv_path=env_path)
DATABASE_URL = os.getenv("DATABASE_URL")

@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield conn, cursor
    except:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_cached_search(route, departure_date):
    with get_db() as (conn, cursor):
        cursor.execute(""" 
                       SELECT * FROM search_cache
                        WHERE route = %s AND departure_date = %s
                        AND cached_at >= NOW() - INTERVAL '24 hours'
                        """,(route, departure_date))
        result = cursor.fetchone()
    return result

def save_search_cache(route, departure_date, passengers, result_json):
    with get_db() as (conn, cursor):
        cursor.execute("INSERT INTO search_cache (route, departure_date, passengers, result_json) VALUES (%s, %s, %s, %s)", (route, departure_date, passengers, result_json))
        conn.commit()

def save_price_history(route, departure_date, price_jpy, operating_airline, marketing_airline):
    with get_db() as (conn, cursor):
        cursor.execute("INSERT INTO price_history (route, departure_date, price_jpy, operating_airline, marketing_airline) VALUES (%s, %s, %s, %s, %s)", (route, departure_date, price_jpy, operating_airline, marketing_airline))
        conn.commit()