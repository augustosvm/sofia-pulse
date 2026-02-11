#!/usr/bin/env python3
"""
Adzuna Jobs API Collector
50k+ vagas/dia, 20+ países, API gratuita (5000 calls/mês)
Dados de salário incluídos
"""
import os
import sys
import time
from pathlib import Path

import psycopg2
import requests
from dotenv import load_dotenv

# Import shared helpers
sys.path.insert(0, str(Path(__file__).parent / "shared"))
from geo_helpers import normalize_location

load_dotenv()

# Database config
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "sofia"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB", "sofia_db"),
}

# Adzuna credentials
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_APP_KEY")

# Países suportados pela Adzuna
COUNTRIES = [
    {"code": "us", "name": "United States"},
    {"code": "gb", "name": "United Kingdom"},
    {"code": "br", "name": "Brazil"},
    {"code": "ca", "name": "Canada"},
    {"code": "au", "name": "Australia"},
    {"code": "de", "name": "Germany"},
    {"code": "fr", "name": "France"},
    {"code": "nl", "name": "Netherlands"},
    {"code": "in", "name": "India"},
    {"code": "sg", "name": "Singapore"},
]

# Rate limiting: limite diário de chamadas (máx Adzuna free tier: 250/dia)
MAX_DAILY_CALLS = 220  # Buffer de 30 chamadas para safety
api_call_count = 0

# Tech keywords em inglês
TECH_KEYWORDS = [
    "python", "java", "javascript", "typescript", "react", "node.js",
    "aws", "cloud", "devops", "data scientist", "machine learning",
    "backend", "frontend", "full stack", "mobile", "android", "ios"
]


def check_api_limit():
    """Verifica se atingiu limite de API calls"""
    global api_call_count
    if api_call_count >= MAX_DAILY_CALLS:
        print(f"\n⚠️ RATE LIMIT: Reached {MAX_DAILY_CALLS} API calls. Stopping to preserve quota.")
        return False
    return True


def get_or_create_organization(conn, company_name, location, country):
    """Get or create organization (simplified version)"""
    if not company_name or company_name == "Unknown":
        return None

    cur = conn.cursor()

    # Try to find existing
    cur.execute(
        "SELECT id FROM sofia.organizations WHERE name = %s LIMIT 1",
        (company_name,)
    )
    result = cur.fetchone()

    if result:
        return result[0]

    # Create new
    try:
        cur.execute(
            """
            INSERT INTO sofia.organizations (name, location, country, source)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (company_name, location, country, 'adzuna')
        )
        conn.commit()
        return cur.fetchone()[0]
    except Exception as e:
        conn.rollback()
        print(f"   [WARN] Error creating org: {str(e)[:50]}")
        return None


def collect_adzuna_jobs():
    """Coleta vagas do Adzuna API"""
    global api_call_count

    print("=" * 60)
    print("💼 Adzuna Jobs API Collector")
    print("=" * 60)

    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        print("❌ ADZUNA_APP_ID and ADZUNA_API_KEY are required!")
        print("\n📝 Get your free API key at: https://developer.adzuna.com/")
        return 0

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    total_collected = 0

    try:
        # Coletar de múltiplos países
        for country in COUNTRIES:
            print(f"\n🌍 Collecting from {country['name']}...")

            # Coletar para cada keyword
            for keyword in TECH_KEYWORDS:
                print(f"\n🔍 Searching for \"{keyword}\"...")

                page = 1
                has_more = True
                consecutive_errors = 0

                while has_more and page <= 50:  # Safety cap
                    # Check API limit before each call
                    if not check_api_limit():
                        print(f"\n📊 Total API calls made: {api_call_count}")
                        print(f"   Jobs collected so far: {total_collected}")
                        conn.close()
                        return total_collected

                    try:
                        url = f"https://api.adzuna.com/v1/api/jobs/{country['code']}/search/{page}"
                        api_call_count += 1  # Increment before call

                        response = requests.get(
                            url,
                            params={
                                "app_id": ADZUNA_APP_ID,
                                "app_key": ADZUNA_API_KEY,
                                "what": keyword,
                                "results_per_page": 50,  # Max allowed by Adzuna
                            },
                            timeout=15
                        )

                        # Check for quota exceeded errors
                        if response.status_code == 200:
                            data = response.json()

                            # Check for Adzuna specific error messages
                            if (data.get("exception") == "QuotaExceededException" or
                                "limit violation" in str(data).lower() or
                                "above 100%" in str(data).lower()):
                                print(f"\n⛔ CRITICAL ADZUNA ERROR: Quota Exceeded detected in response body.")
                                conn.close()
                                return total_collected

                            jobs = data.get("results", [])

                            if not jobs:
                                has_more = False
                                break

                            print(f"   Page {page}: {len(jobs)} jobs")

                            for job in jobs:
                                try:
                                    # Extract location details
                                    location = job.get("location", {}).get("display_name", "")
                                    area = job.get("location", {}).get("area", [])
                                    area_length = len(area)

                                    city = None
                                    state = None

                                    if area_length == 1:
                                        # Only country
                                        city = None
                                        state = None
                                    elif area_length == 2:
                                        # Country + City
                                        city = area[1]
                                        state = None
                                    elif area_length >= 3:
                                        # Multiple levels
                                        city = area[-1]  # Last element
                                        state = area[1]  # Second element

                                    country_name = country["name"]

                                    # Normalize geographic data
                                    geo = normalize_location(conn, {
                                        "country": country_name,
                                        "state": state,
                                        "city": city
                                    })

                                    # Get or create organization
                                    company_name = job.get("company", {}).get("display_name", "Unknown")
                                    organization_id = get_or_create_organization(
                                        conn, company_name, location, country_name
                                    )

                                    # Insert job
                                    cur.execute(
                                        """
                                        INSERT INTO sofia.jobs (
                                            job_id, platform, source, title, company,
                                            raw_location, raw_city, raw_state, country, country_id, state_id, city_id,
                                            remote_type, url, search_keyword, organization_id, collected_at
                                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                                        ON CONFLICT (job_id) DO UPDATE SET
                                            collected_at = NOW(),
                                            source = EXCLUDED.source,
                                            organization_id = COALESCE(EXCLUDED.organization_id, sofia.jobs.organization_id),
                                            country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
                                            state_id = COALESCE(EXCLUDED.state_id, sofia.jobs.state_id),
                                            city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id)
                                        """,
                                        (
                                            f"adzuna-{job.get('id')}",  # job_id
                                            'adzuna',  # platform
                                            'adzuna',  # source
                                            job.get('title', 'Unknown'),  # title
                                            company_name,  # company
                                            location,  # raw_location
                                            city,  # raw_city
                                            state,  # raw_state
                                            country_name,  # country
                                            geo.get('country_id'),  # country_id
                                            geo.get('state_id'),  # state_id
                                            geo.get('city_id'),  # city_id
                                            'remote',  # remote_type (placeholder)
                                            job.get('redirect_url', ''),  # url
                                            keyword,  # search_keyword
                                            organization_id  # organization_id
                                        )
                                    )
                                    conn.commit()
                                    total_collected += 1

                                except Exception as err:
                                    conn.rollback()
                                    # Ignore duplicates
                                    if "23505" not in str(err):
                                        print(f"   ❌ Error inserting job: {str(err)[:50]}")

                            # Rate limiting: aguardar 1.5s entre requests
                            time.sleep(1.5)
                            page += 1
                            consecutive_errors = 0

                        elif response.status_code in [429, 401, 402, 403]:
                            # KILL SWITCH: Exit immediately
                            print(f"\n⛔ CRITICAL API ERROR: {response.status_code} - Quota Exceeded or Auth Failed.")
                            print("   Exiting collector to save resources.")
                            conn.close()
                            return total_collected

                        elif response.status_code == 400:
                            # End of results
                            has_more = False

                        else:
                            print(f"   ❌ API Error: {response.status_code}")
                            time.sleep(5)  # Backoff
                            consecutive_errors += 1

                    except Exception as error:
                        consecutive_errors += 1
                        print(f"   ❌ Error for \"{keyword}\" p{page}: {str(error)[:50]}")
                        time.sleep(5)  # Backoff

                    if consecutive_errors >= 3:
                        print(f"   ❌ Too many errors for \"{keyword}\", skipping...")
                        has_more = False

        # Statistics
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT company) as companies,
                COUNT(DISTINCT country) as countries
            FROM sofia.jobs
            WHERE platform = 'adzuna'
        """)
        stats = cur.fetchone()

        print("\n" + "=" * 60)
        print(f"✅ Collected: {total_collected} tech jobs from Adzuna")
        print("\n📊 Adzuna Statistics:")
        print(f"   Total jobs: {stats[0]}")
        print(f"   Companies: {stats[1]}")
        print(f"   Countries: {stats[2]}")
        print(f"\n📈 API Usage: {api_call_count}/{MAX_DAILY_CALLS} calls ({round(api_call_count / MAX_DAILY_CALLS * 100)}%)")
        if api_call_count >= MAX_DAILY_CALLS:
            print("   ⚠️ Daily limit reached - remaining countries/keywords skipped")
        print("=" * 60)

    except Exception as error:
        print(f"❌ Fatal error: {str(error)}")

    finally:
        conn.close()

    return total_collected


if __name__ == "__main__":
    try:
        total = collect_adzuna_jobs()
        sys.exit(0 if total > 0 else 1)
    except Exception as err:
        print(f"Fatal error: {err}")
        sys.exit(1)
