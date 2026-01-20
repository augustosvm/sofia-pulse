#!/usr/bin/env python3
"""
Coletor: RapidAPI - Active Jobs DB (Fantastic.jobs)
Features: 8M+ jobs/month, AI-enriched, 130k+ career sites
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

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_URL = "https://active-jobs-db.p.rapidapi.com/active-ats-7d"

# Keywords focadas em Brasil (Unificado e Expandido)
KEYWORDS = [
    # Tech / Development
    "Software Engineer", "Engenheiro de Software",
    "Data Scientist", "Cientista de Dados",
    "DevOps",
    "Full Stack", "Fullstack",
    "Backend Developer", "Desenvolvedor Backend",
    "Frontend Developer", "Desenvolvedor Frontend",
    "Java Developer", "Desenvolvedor Java",
    "Python Developer", "Desenvolvedor Python",
    "JavaScript Developer", "Desenvolvedor JavaScript",
    "Machine Learning",
    "Cybersecurity", "Segurança da Informação",
    "Product Manager", "Gerente de Produto",
    "UX Designer", "UI/UX",
    "QA Engineer", "Analista de Testes"
]


def collect_active_jobs_db():
    """Coleta vagas do Active Jobs DB (Fantastic.jobs)"""
    jobs = []

    headers = {"x-rapidapi-host": "active-jobs-db.p.rapidapi.com", "x-rapidapi-key": RAPIDAPI_KEY}

    for keyword in KEYWORDS:
        offset = 0
        has_more = True
        consecutive_errors = 0
        
        # Paginação (offset loop) - Cap de 500 vagas por keyword para evitar rate limit excessivo
        while has_more and offset < 500:
            try:
                # Add explicit Brazil context to keyword if not present to ensure relevance
                # search_term = keyword if "Brazil" in keyword or "Brasil" in keyword else f"{keyword} Brazil"
                
                params = {
                    "limit": 100, # Max limit
                    "offset": offset,
                    "title_filter": f'"{keyword}"',
                    "location_filter": '"Brazil" OR "Brasil" OR "Remote"',
                    "description_type": "text",
                }

                response = requests.get(API_URL, headers=headers, params=params, timeout=15)

                if response.status_code == 200:
                    data = response.json()
                    job_list = []
                    
                    if isinstance(data, list):
                        job_list = data
                    else:
                        job_list = data.get("jobs", data.get("data", data.get("results", [])))

                    if not job_list or len(job_list) == 0:
                        has_more = False
                        break

                    for job in job_list:
                        if isinstance(job, dict):
                            jobs.append(
                                {
                                    "job_id": f"activejobs-{job.get('id', hash(str(job.get('url', keyword))))}",
                                    "title": job.get("title", job.get("job_title")),
                                    "company": job.get("company", job.get("company_name")),
                                    "location": job.get("location", "Brazil"),
                                    "description": str(job.get("description", ""))[:1000],
                                    "url": job.get("url", job.get("apply_url", job.get("link"))),
                                    "platform": "activejobs",
                                    "source": "activejobs",
                                    "posted_date": job.get("posted_date", job.get("date_posted")),
                                    "salary_min": job.get("salary_min"),
                                    "salary_max": job.get("salary_max"),
                                    "remote_type": "remote" if "remote" in str(job.get("location", "")).lower() else None,
                                    "search_keyword": keyword,
                                }
                            )

                    print(f"✅ Active Jobs DB: {len(job_list)} vagas para '{keyword}' (Offset {offset})")
                    offset += 100 # Increment offset
                    consecutive_errors = 0
                    
                elif response.status_code == 429:
                    print(f"⚠️  Rate limit! Aguardando 60s...")
                    import time
                    time.sleep(60)
                    consecutive_errors += 1
                else:
                    print(f"⚠️  Active Jobs DB: {response.status_code} para '{keyword}'")
                    consecutive_errors += 1
                
                if consecutive_errors >= 3:
                    has_more = False

            except Exception as e:
                print(f"❌ Active Jobs DB erro para '{keyword}': {str(e)[:50]}")
                has_more = False

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
                    job_id, title, company, raw_location, raw_city, country, country_id, city_id, description, url,
                    platform, source, posted_date, salary_min, salary_max,
                    remote_type, search_keyword, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    source = EXCLUDED.source,
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
                    job["source"],
                    job["posted_date"],
                    job["salary_min"],
                    job["salary_max"],
                    job["remote_type"],
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
    print("🚀 ACTIVE JOBS DB (FANTASTIC.JOBS) - BRASIL")
    print("=" * 70)

    jobs = collect_active_jobs_db()
    print(f"\n💾 Salvando {len(jobs)} vagas...")
    saved = save_to_db(jobs)

    print(f"\n✅ Total salvo: {saved} vagas")
    print("=" * 70)
