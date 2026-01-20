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

# Keywords focadas em Brasil (Unificado)
KEYWORDS = [
    "Engenheiro de Software",
    "Desenvolvedor Python",
    "Data Scientist",
    "DevOps Engineer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Mobile Developer",
    "QA Engineer",
    "Tech Lead",
    "Engineering Manager",
    "Product Manager",
    "Arquiteto de Software",
    "DBA",
    "Business Intelligence",
    "Analista de Segurança",
    "Cybersecurity"
]


def collect_google_jobs_serpapi():
    """Coleta vagas do Google Jobs via SerpApi"""
    jobs = []

    for keyword in KEYWORDS:
        start = 0
        has_more = True
        consecutive_errors = 0
        
        # Paginação: Google Jobs results geralmente vêm em páginas de 10
        # Cap de 5 páginas (50 jobs) por keyword para manter dentro do limite de 100 searches/mês free 
        # (se tivermos plano pago, podemos aumentar)
        # SerpApi cobra 1 search por página
        pages_limit = 5 
        
        while has_more and start < (pages_limit * 10):
            try:
                params = {
                    "engine": "google_jobs",
                    "q": keyword,
                    "location": "Brazil",
                    "hl": "pt",
                    "gl": "br",
                    "start": start, # Paginação
                    "api_key": SERPAPI_KEY,
                }

                response = requests.get(API_URL, params=params, timeout=15)

                if response.status_code == 200:
                    data = response.json()
                    job_list = data.get("jobs_results", [])
                    
                    if not job_list or len(job_list) == 0:
                        has_more = False
                        break

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
                                "source": "googlejobs",
                                "posted_date": posted_date,
                                "employment_type": job.get("detected_extensions", {}).get("schedule_type"),
                                "search_keyword": keyword,
                            }
                        )

                    print(f"✅ Google Jobs: {len(job_list)} vagas para '{keyword}' (Página {start//10})")
                    start += 10 # Next page
                    
                    # Check if there is a next page token or links (SerpApi usually returns all if available or next link)
                    # Simple default is increment start.
                    
                else:
                    print(f"⚠️  Google Jobs: {response.status_code} para '{keyword}'")
                    has_more = False

            except Exception as e:
                print(f"❌ Google Jobs erro para '{keyword}': {str(e)[:50]}")
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
                    platform, source, posted_date, employment_type, search_keyword, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    source = EXCLUDED.source,
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
                    job["source"],
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
