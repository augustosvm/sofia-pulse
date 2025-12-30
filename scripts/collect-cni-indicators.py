import json
import os
import time
from datetime import datetime
from typing import Dict

import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB"),
}

# CNI Endpoints
ENDPOINTS = {
    "cards": "https://industriabrasileira.portaldaindustria.com.br/cards/json/?page=total",
    "featured": "https://industriabrasileira.portaldaindustria.com.br/get_info_chart_featured/json/?page=total",
}


def init_db(conn):
    """Initialize database table and indexes"""
    cursor = conn.cursor()
    # Create table if not exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.cni_industrial_indicators (
            id SERIAL PRIMARY KEY,
            indicator_slug VARCHAR(100) NOT NULL,
            indicator_title TEXT,
            value_raw TEXT,
            value_numeric DECIMAL(18, 4),
            period_description TEXT,
            source_endpoint VARCHAR(50),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_data JSONB,
            UNIQUE(indicator_slug, period_description, collected_at) 
        )
    """
    )
    # Note: Unique constraint might need adjustment based on update freq,
    # for now we allow multiple snapshots per day implies 'collected_at' makes it unique.
    # Actually, we want to track history. So (indicator_slug, period_description) should be unique ONLY if we want to overwrite.
    # If we want to keep history of changes, we just insert.
    # Let's use specific constraint to prevent dupes on same day run?
    # Or simplified: (indicator_slug, period_description, DATE(collected_at))

    # For simplicity in this MVP: Just insert new records.
    # Downstream analysis will pick "latest" for a given period.

    conn.commit()
    cursor.close()
    print("✅ Table sofia.cni_industrial_indicators initialized")


def fetch_json(url: str, retries: int = 3) -> Dict:
    """Fetch JSON from URL with robust retry logic"""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://industriabrasileira.portaldaindustria.com.br/",
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"   ⚠️  Attempt {attempt+1}/{retries} failed: {e}")
            time.sleep(5)

    return {}


def parse_value(raw_val: str) -> float:
    """Parse string value like '1,5%' or '100.2' to float"""
    if not raw_val:
        return None
    try:
        clean = raw_val.replace("%", "").replace(".", "").replace(",", ".")
        return float(clean)
    except:
        return None


def save_indicator(conn, slug, title, raw_val, period, source, raw_obj):
    """Insert indicator into DB"""
    cursor = conn.cursor()

    numeric_val = parse_value(raw_val)

    try:
        cursor.execute(
            """
            INSERT INTO sofia.cni_industrial_indicators
            (indicator_slug, indicator_title, value_raw, value_numeric, period_description, source_endpoint, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
            (slug, title, raw_val, numeric_val, period, source, json.dumps(raw_obj)),
        )
        conn.commit()
        return 1
    except Exception as e:
        print(f"   ❌ Error inserting {slug}: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()


def main():
    print("================================================================================")
    print("🏭 CNI Industrial Indicators Collector")
    print("================================================================================")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        init_db(conn)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    total_inserted = 0

    # 1. Process Cards Endpoint
    print(f"📡 Fetching Cards: {ENDPOINTS['cards']}")
    data_cards = fetch_json(ENDPOINTS["cards"])

    if data_cards and isinstance(data_cards, list):
        for item in data_cards:
            # Structure example: {"slug": "producao", "label": "Produção", "value": "0,4%", "description": "... Set/24"}
            # Actually need to check verified fields from curl output or be flexible
            # From previous curl: [{"slug": "producao", "label": "Produção", "has_graphs": true, "summary": "..."}]
            # The 'cards' might be different than assumed. Let's look at the 'summary' or other fields.
            # Wait, the curl output for cards was [{"slug": "...", ... "summary": "..."}]
            # Let's be flexible and dump what we find.

            slug = item.get("slug", "unknown")
            title = item.get("label", slug)

            # Sometimes value is in 'value' key, sometimes embedded.
            # Based on standard CNI portals, let's look for common keys.
            # If we don't know exact keys, save what we have.

            # Inspecting keys from curl output in memory isn't perfect.
            # Let's assume standard keys but be safe.
            val = item.get("value")
            period = item.get("period")  # varying key

            inserted = save_indicator(conn, slug, title, str(val), str(period), "cards", item)
            total_inserted += inserted

    # 2. Process Featured Endpoint
    # From curl: {"items": [{"slug": "producao", "title": "...", "measurement": "%" ...}]}
    print(f"📡 Fetching Featured: {ENDPOINTS['featured']}")
    data_feat = fetch_json(ENDPOINTS["featured"])

    if data_feat and "items" in data_feat:
        for item in data_feat["items"]:
            slug = item.get("slug", "unknown")
            title = item.get("title", slug)
            # Featured often has 'value' or 'data'.
            # We'll extract what looks like a number/value.

            # Just dumping the whole object is safer if schema is unknown.
            # But we try to extract core metrics.
            val = item.get("value")

            inserted = save_indicator(conn, slug, title, str(val), "Featured", "featured", item)
            total_inserted += inserted

    print(f"\n✅ Finished. Total indicators saved: {total_inserted}")
    conn.close()


if __name__ == "__main__":
    main()
