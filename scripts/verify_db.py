import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
    )
    cur = conn.cursor()

    # Check total records
    cur.execute("SELECT count(*) FROM sofia.comexstat_trade")
    total = cur.fetchone()[0]
    print(f"Total Records: {total}")

    # Check NCM 84713012 specifically
    cur.execute("SELECT count(*) FROM sofia.comexstat_trade WHERE ncm_code = '84713012'")
    count_specific = cur.fetchone()[0]
    print(f"Records for 84713012: {count_specific}")

    # Inspect some records
    cur.execute(
        """
        SELECT state_code, period, country_name, value_usd 
        FROM sofia.comexstat_trade 
        WHERE ncm_code = '84713012' 
        LIMIT 10
    """
    )
    rows = cur.fetchall()
    print("Sample 84713012 Records:")
    for row in rows:
        print(row)

    # Check distinct counts
    cur.execute(
        """
        SELECT count(distinct state_code), count(distinct period), count(distinct country_name)
        FROM sofia.comexstat_trade
        WHERE ncm_code = '84713012'
    """
    )
    distincts = cur.fetchone()
    print(f"Distinct (State, Period, Country) for 84713012: {distincts}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
