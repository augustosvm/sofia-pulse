#!/usr/bin/env python3
"""
Coletor: Free Jobs API (sem autenticação)
URL: https://docs.joinrise.co/
Features: 100% reliability, 0% error rate, CORS enabled
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

API_URL = "https://api.joinrise.co/v1/jobs"


def collect_free_jobs():
    """Coleta vagas da Free Jobs API"""
    jobs = []

    # Tentar diferentes endpoints/queries
    queries = ["software engineer", "data scientist", "devops", "frontend", "backend"]

    for query in queries:
        try:
            params = {"search": query, "limit": 100}
            response = requests.get(API_URL, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                job_list = data.get("jobs", data.get("data", []))

                for job in job_list:
                    jobs.append(
                        {
                            "job_id": f"freejobs-{job.get('id', job.get('job_id'))}",
                            "title": job.get("title"),
                            "company": job.get("company", job.get("company_name")),
                            "location": job.get("location"),
                            "description": job.get("description", "")[:1000],
                            "url": job.get("url", job.get("apply_url")),
                            "platform": "freejobs",
                            "salary_min": job.get("salary_min"),
                            "salary_max": job.get("salary_max"),
                            "posted_date": job.get("posted_date", job.get("created_at")),
                            "search_keyword": query,
                        }
                    )

                print(f"✅ Free Jobs: {len(job_list)} vagas para '{query}'")
            else:
                print(f"⚠️  Free Jobs: {response.status_code} para '{query}'")

        except Exception as e:
            print(f"❌ Free Jobs erro para '{query}': {str(e)[:50]}")

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
            country = parts[-1].strip() if len(parts) > 0 else "Brazil"

            # Normalize geographic data
            geo = normalize_location(conn, {"country": country, "city": city})
            cur.execute(
                """
                INSERT INTO sofia.jobs (
                    job_id, title, company, location, city, country, country_id, city_id, description, url,
                    platform, salary_min, salary_max, posted_date, 
                    search_keyword, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
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
                    job["salary_min"],
                    job["salary_max"],
                    job["posted_date"],
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
    print("🆓 FREE JOBS API COLLECTOR")
    print("=" * 70)

    jobs = collect_free_jobs()
    print(f"\n💾 Salvando {len(jobs)} vagas...")
    saved = save_to_db(jobs)

    print(f"\n✅ Total salvo: {saved} vagas")
    print("=" * 70)
