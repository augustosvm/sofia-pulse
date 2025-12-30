#!/usr/bin/env python3

"""
ACLED (Armed Conflict Location & Event Data Project) Collector
Coleta dados de conflitos violentos, protestos e eventos políticos globais

API: https://acleddata.com/api/acled/read
Docs: https://acleddata.com/reactivation/api-authentication
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import psycopg2
import requests

# Import geo helpers
sys.path.insert(0, str(Path(__file__).parent / "shared"))
from geo_helpers_acled import normalize_location_acled


# Load .env manually (no python-dotenv dependency)
def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip()


load_env()

# Configuration
ACLED_TOKEN_URL = "https://acleddata.com/oauth/token"
ACLED_API_URL = "https://acleddata.com/api/acled/read"
ACLED_EMAIL = os.getenv("ACLED_EMAIL")
ACLED_PASSWORD = os.getenv("ACLED_PASSWORD")


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "sofia"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        database=os.getenv("POSTGRES_DB", "sofia_db"),
    )


def get_access_token():
    """Get OAuth2 access token from ACLED"""
    if not ACLED_EMAIL or not ACLED_PASSWORD:
        print("⚠️  ACLED credentials not configured in .env")
        print("   Add: ACLED_EMAIL and ACLED_PASSWORD")
        return None

    try:
        response = requests.post(
            ACLED_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"username": ACLED_EMAIL, "password": ACLED_PASSWORD, "grant_type": "password", "client_id": "acled"},
            timeout=30,
        )

        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Access token obtained (expires in {token_data.get('expires_in', 0)}s)")
            return token_data["access_token"]
        else:
            print(f"❌ Failed to get access token: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"❌ Error getting access token: {e}")
        return None


def fetch_acled_events(token, days_back=30):
    """Fetch recent ACLED events"""

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    # Format dates for ACLED API (YYYY-MM-DD)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"\n🔍 Fetching ACLED events from {start_str} to {end_str}...")

    params = {
        "limit": 5000,  # Max per request
        "event_date": start_str,
        "event_date_where": ">=",
    }

    try:
        response = requests.get(
            ACLED_API_URL,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            params=params,
            timeout=60,
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                events = data.get("data", [])
                print(f"✅ Fetched {len(events)} events")
                return events
            else:
                print(f"❌ API returned error")
                print(f"   Response: {data}")
                return []
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:500]}")
            return []

    except Exception as e:
        print(f"❌ Error fetching events: {e}")
        return []


def save_to_database(events):
    """Save ACLED events to database"""

    if not events:
        print("⚠️  No events to save")
        return 0

    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed")
        return 0

    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.acled_events (
            event_id_cnty VARCHAR(50) PRIMARY KEY,
            event_date DATE NOT NULL,
            year INTEGER,
            event_type VARCHAR(100),
            sub_event_type VARCHAR(100),
            actor1 TEXT,
            actor2 TEXT,
            country VARCHAR(100),
            country_id INTEGER,
            region VARCHAR(100),
            location TEXT,
            city_id INTEGER,
            latitude DECIMAL(10, 6),
            longitude DECIMAL(10, 6),
            source TEXT,
            notes TEXT,
            fatalities INTEGER DEFAULT 0,
            timestamp BIGINT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create indexes
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_acled_date ON sofia.acled_events(event_date DESC)
    """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_acled_country ON sofia.acled_events(country)
    """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_acled_type ON sofia.acled_events(event_type)
    """
    )

    conn.commit()

    # Insert events
    inserted = 0
    updated = 0

    for event in events:
        try:
            # Normalize geographic data
            geo = normalize_location_acled(conn, event.get("country"), event.get("location"))

            cursor.execute(
                """
                INSERT INTO sofia.acled_events (
                    event_id_cnty, event_date, year, event_type, sub_event_type,
                    actor1, actor2, country, country_id, region, location, city_id,
                    latitude, longitude, source, notes, fatalities, timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id_cnty) DO UPDATE SET
                    event_date = EXCLUDED.event_date,
                    year = EXCLUDED.year,
                    event_type = EXCLUDED.event_type,
                    sub_event_type = EXCLUDED.sub_event_type,
                    actor1 = EXCLUDED.actor1,
                    actor2 = EXCLUDED.actor2,
                    country = EXCLUDED.country,
                    country_id = EXCLUDED.country_id,
                    region = EXCLUDED.region,
                    location = EXCLUDED.location,
                    city_id = EXCLUDED.city_id,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    source = EXCLUDED.source,
                    notes = EXCLUDED.notes,
                    fatalities = EXCLUDED.fatalities,
                    timestamp = EXCLUDED.timestamp
            """,
                (
                    event.get("event_id_cnty"),
                    event.get("event_date"),
                    event.get("year"),
                    event.get("event_type"),
                    event.get("sub_event_type"),
                    event.get("actor1"),
                    event.get("actor2"),
                    event.get("country"),
                    geo["country_id"],
                    event.get("region"),
                    event.get("location"),
                    geo["city_id"],
                    float(event.get("latitude", 0)) if event.get("latitude") else None,
                    float(event.get("longitude", 0)) if event.get("longitude") else None,
                    event.get("source"),
                    event.get("notes"),
                    int(event.get("fatalities", 0)) if event.get("fatalities") else 0,
                    int(event.get("timestamp", 0)) if event.get("timestamp") else None,
                ),
            )

            if cursor.rowcount > 0:
                inserted += 1
            else:
                updated += 1

        except Exception as e:
            print(f"⚠️  Error inserting event {event.get('event_id_cnty')}: {e}")
            continue

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n💾 Database:")
    print(f"   Inserted: {inserted} new events")
    print(f"   Updated: {updated} existing events")

    return inserted


def main():
    print("=" * 70)
    print("🌍 ACLED - Armed Conflict Location & Event Data")
    print("=" * 70)

    # Get access token
    token = get_access_token()
    if not token:
        print("\n❌ Cannot proceed without access token")
        print("   Register at: https://acleddata.com/user/register")
        print("   Then add credentials to .env:")
        print("   ACLED_EMAIL=your_email@example.com")
        print("   ACLED_PASSWORD=your_password")
        return

    # Fetch events
    events = fetch_acled_events(token, days_back=30)

    if not events:
        print("\n⚠️  No events collected")
        return

    # Analyze events
    print(f"\n📊 Event Analysis:")

    # By type
    types = {}
    for event in events:
        event_type = event.get("event_type", "Unknown")
        types[event_type] = types.get(event_type, 0) + 1

    print(f"\n   Event Types:")
    for event_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   • {event_type}: {count}")

    # By country
    countries = {}
    for event in events:
        country = event.get("country", "Unknown")
        countries[country] = countries.get(country, 0) + 1

    print(f"\n   Top Countries:")
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   • {country}: {count}")

    # Fatalities
    total_fatalities = sum(int(e.get("fatalities", 0)) for e in events if e.get("fatalities"))
    print(f"\n   Total Fatalities: {total_fatalities}")

    # Save to database
    saved = save_to_database(events)

    print("\n" + "=" * 70)
    print(f"✅ Collection complete!")
    print(f"   Events: {len(events)}")
    print(f"   Saved: {saved}")
    print("=" * 70)


if __name__ == "__main__":
    main()
