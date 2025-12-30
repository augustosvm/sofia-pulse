#!/usr/bin/env python3
"""
Coletor: Careerjet API
URL: https://www.careerjet.com/partners/api/
Features: Global job search engine, requires API key
"""
import os
import sys
from pathlib import Path

import psycopg2
import requests
from dotenv import load_dotenv

# Import geo helpers
sys.path.insert(0, str(Path(__file__).parent / "shared"))
from geo_helpers import normalize_location

load_dotenv()

# API Configuration
CAREERJET_API_KEY = os.getenv("CAREERJET_API_KEY", "")
CAREERJET_API_URL = "http://public.api.careerjet.net/search"

# Search queries
QUERIES = [
    "software engineer",
    "data scientist",
    "devops engineer",
    "frontend developer",
    "backend developer",
    "full stack",
    "machine learning",
    "ai engineer",
    "cloud engineer",
]


def collect_careerjet():
    """Coleta vagas da Careerjet API"""
    if not CAREERJET_API_KEY:
        print("⚠️  CAREERJET_API_KEY não configurada no .env")
        return []

    jobs = []

    for query in QUERIES:
        try:
            params = {
                "affid": CAREERJET_API_KEY,
                "keywords": query,
                "location": "worldwide",
                "pagesize": 99,  # Max per request
                "page": 1,
                "sort": "date",
                "user_ip": "11.22.33.44",  # Required by API
                "user_agent": "Mozilla/5.0",
            }

            response = requests.get(CAREERJET_API_URL, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()

                if data.get("type") == "JOBS":
                    job_list = data.get("jobs", [])

                    for job in job_list:
                        jobs.append(
                            {
                                "job_id": f"careerjet-{hash(job.get('url'))}",
                                "title": job.get("title"),
                                "company": job.get("company"),
                                "location": job.get("locations"),
                                "description": job.get("description", "")[:1000],
                                "url": job.get("url"),
                                "platform": "careerjet",
                                "posted_date": job.get("date"),
                                "salary_min": job.get("salary_min"),
                                "salary_max": job.get("salary_max"),
                                "search_keyword": query,
                            }
                        )

                    print(f"✅ Careerjet: {len(job_list)} vagas para '{query}'")
                else:
                    print(f"⚠️  Careerjet: {data.get('type')} para '{query}'")
            else:
                print(f"⚠️  Careerjet: {response.status_code} para '{query}'")

        except Exception as e:
            print(f"❌ Careerjet erro para '{query}': {str(e)[:50]}")

    return jobs


def save_to_db(jobs):
    """Salva vagas no banco"""
    if not jobs:
        return 0

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
    )
    cur = conn.cursor()

    saved = 0
    for job in jobs:
        try:
            # Parse location
            location_str = job.get("location", "")
            parts = location_str.split(",") if location_str else []
            city = parts[0].strip() if len(parts) > 0 else None
            country = parts[-1].strip() if len(parts) > 0 else None

            # Normalize geographic data
            geo = normalize_location(conn, {"country": country, "city": city})

            cur.execute(
                """
                INSERT INTO sofia.jobs (
                    job_id, title, company, location, city, country, country_id, city_id,
                    description, url, platform, posted_date, salary_min, salary_max,
                    search_keyword, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    collected_at = NOW()
            """,
                (
                    job["job_id"],
                    job["title"],
                    job["company"],
                    job["location"],
                    city,
                    country,
                    geo["country_id"],
                    geo["city_id"],
                    job["description"],
                    job["url"],
                    job["platform"],
                    job["posted_date"],
                    job["salary_min"],
                    job["salary_max"],
                    job["search_keyword"],
                ),
            )
            saved += 1
        except Exception as e:
            print(f"⚠️  Erro ao salvar: {str(e)[:50]}")

    conn.commit()
    conn.close()
    return saved


if __name__ == "__main__":
    print("=" * 70)
    print("🌐 CAREERJET API COLLECTOR")
    print("=" * 70)

    jobs = collect_careerjet()
    print(f"\n💾 Salvando {len(jobs)} vagas...")
    saved = save_to_db(jobs)

    print(f"\n✅ Total salvo: {saved} vagas")
    print("=" * 70)
