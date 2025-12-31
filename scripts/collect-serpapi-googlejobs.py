#!/usr/bin/env python3
"""
Coletor: SerpApi - Google Jobs
Features: Scrape Google Jobs SERP, acesso a todas vagas do Google
FOCO: Brasil
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

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
API_URL = "https://serpapi.com/search"

# Keywords focadas em Brasil
KEYWORDS = [
    "Engenheiro de Software Brasil",
    "Desenvolvedor Python Brasil",
    "Data Scientist Brasil",
    "DevOps Engineer Brasil",
    "Frontend Developer Brasil",
    "Backend Developer Brasil",
    "Full Stack Developer Brasil",
    "Mobile Developer Brasil",
    "QA Engineer Brasil",
    "Tech Lead Brasil",
    "Engineering Manager Brasil",
    "Product Manager Brasil",
    "Arquiteto de Software Brasil",
    "DBA Brasil",
    "Analista de Dados Brasil",
]


def collect_google_jobs_serpapi():
    """Coleta vagas do Google Jobs via SerpApi"""
    jobs = []

    for keyword in KEYWORDS:
        try:
            params = {
                "engine": "google_jobs",
                "q": keyword,
                "location": "Brazil",
                "hl": "pt",
                "gl": "br",
                "api_key": SERPAPI_KEY,
            }

            response = requests.get(API_URL, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                job_list = data.get("jobs_results", [])

                for job in job_list:
                    # Converter data relativa para None
                    posted_date = job.get("detected_extensions", {}).get("posted_at")
                    if posted_date and ("há" in str(posted_date) or "ago" in str(posted_date)):
                        posted_date = None  # Ignorar datas relativas

                    jobs.append(
                        {
                            "job_id": f"googlejobs-{hash(job.get('job_id', job.get('link')))}",
                            "title": job.get("title"),
                            "company": job.get("company_name"),
                            "location": job.get("location"),
                            "description": job.get("description", "")[:1000],
                            "url": job.get("share_url", job.get("link")),
                            "platform": "googlejobs",
                            "posted_date": posted_date,
                            "employment_type": job.get("detected_extensions", {}).get("schedule_type"),
                            "search_keyword": keyword,
                        }
                    )

                print(f"✅ Google Jobs: {len(job_list)} vagas para '{keyword}'")
            else:
                print(f"⚠️  Google Jobs: {response.status_code} para '{keyword}'")

        except Exception as e:
            print(f"❌ Google Jobs erro para '{keyword}': {str(e)[:50]}")

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
                    platform, posted_date, employment_type, search_keyword, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
                    city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id),
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
                    job["employment_type"],
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
    print("🔍 GOOGLE JOBS (SERPAPI) - BRASIL")
    print("=" * 70)

    jobs = collect_google_jobs_serpapi()
    print(f"\n💾 Salvando {len(jobs)} vagas...")
    saved = save_to_db(jobs)

    print(f"\n✅ Total salvo: {saved} vagas")
    print("=" * 70)
