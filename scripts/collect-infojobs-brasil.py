#!/usr/bin/env python3
"""
Coletor: InfoJobs Brasil (Scraping)
URL: https://www.infojobs.com.br/
Auth: Não requer (scraping público)
Features: Busca de vagas tech no Brasil
"""
import os
import sys
import time
import re
from pathlib import Path

import psycopg2
import requests
from bs4 import BeautifulSoup
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

# Keywords tech focadas em Brasil
KEYWORDS = [
    "desenvolvedor",
    "programador",
    "python",
    "java",
    "javascript",
    "react",
    "devops",
    "data scientist",
    "frontend",
    "backend",
    "full stack",
    "mobile"
]


def parse_salary_brl(text):
    """Parse salário brasileiro"""
    if not text:
        return None, None, None

    salary_min = None
    salary_max = None
    period = None

    # Detectar período
    if re.search(r"mês|mensal|\/mês", text, re.I):
        period = "monthly"
    elif re.search(r"ano|anual|\/ano", text, re.I):
        period = "yearly"

    # Extrair números
    numbers = re.findall(r"R?\$?\s*([\d.]+)", text, re.I)
    parsed = [float(n.replace(".", "")) for n in numbers if n]

    if len(parsed) >= 2:
        salary_min = min(parsed)
        salary_max = max(parsed)
    elif len(parsed) == 1:
        salary_min = parsed[0]

    return salary_min, salary_max, period


def detect_remote_type(text):
    """Detecta tipo remoto"""
    if not text:
        return None
    text_lower = text.lower()
    if re.search(r"remoto|remote|home office", text_lower):
        return "remote"
    if re.search(r"híbrido|hybrid", text_lower):
        return "hybrid"
    return None


def get_or_create_organization(conn, company_name, location, country):
    """Get or create organization"""
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
            (company_name, location, country, 'infojobs')
        )
        conn.commit()
        return cur.fetchone()[0]
    except Exception as e:
        conn.rollback()
        return None


def scrape_infojobs(keyword):
    """Scrape vagas do InfoJobs Brasil"""
    jobs = []

    try:
        # URL de busca do InfoJobs
        url = f"https://www.infojobs.com.br/empregos.aspx"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        params = {
            "palabra": keyword
        }

        response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code != 200:
            print(f"   ⚠️  HTTP {response.status_code} for '{keyword}'")
            return jobs

        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscar elementos de vaga (ajustar seletores conforme HTML real)
        # InfoJobs usa estrutura com classes específicas
        job_items = soup.find_all(['article', 'div'], class_=re.compile(r'vaga|job|oferta', re.I))

        if not job_items:
            # Tentar outro padrão
            job_items = soup.find_all('a', href=re.compile(r'/vaga|/emprego|/oferta'))

        for i, item in enumerate(job_items[:20]):  # Limitar a 20
            try:
                # Extrair título
                title_el = item.find(['h2', 'h3', 'a'], class_=re.compile(r'titulo|title|vaga', re.I))
                if not title_el:
                    title_el = item.find('a', href=re.compile(r'/vaga|/emprego'))

                title = title_el.get_text(strip=True) if title_el else ""

                # Extrair URL
                link_el = item.find('a', href=re.compile(r'/vaga|/emprego'))
                if not link_el and title_el and title_el.name == 'a':
                    link_el = title_el

                url_path = link_el.get('href', '') if link_el else ""

                if not title or not url_path:
                    continue

                # Extrair empresa
                company_el = item.find(['span', 'div', 'p'], class_=re.compile(r'empresa|company', re.I))
                company = company_el.get_text(strip=True) if company_el else "Unknown"

                # Extrair localização
                location_el = item.find(['span', 'div', 'p'], class_=re.compile(r'local|cidade|city|location', re.I))
                location = location_el.get_text(strip=True) if location_el else "Brasil"

                # Extrair salário
                salary_el = item.find(['span', 'div', 'p'], class_=re.compile(r'salario|salary|remuneracao', re.I))
                salary = salary_el.get_text(strip=True) if salary_el else ""

                # Extrair descrição
                desc_el = item.find(['p', 'div'], class_=re.compile(r'descricao|description|resumo', re.I))
                description = desc_el.get_text(strip=True) if desc_el else ""

                # Construir URL completa
                full_url = url_path if url_path.startswith('http') else f"https://www.infojobs.com.br{url_path}"

                jobs.append({
                    "url": full_url,
                    "title": title,
                    "company": company,
                    "location": location,
                    "salary": salary,
                    "description": description[:1000],
                    "keyword": keyword
                })

            except Exception as e:
                continue

        print(f"   ✅ {len(jobs)} vagas for '{keyword}'")

    except Exception as e:
        print(f"   ❌ Error scraping '{keyword}': {str(e)[:50]}")

    return jobs


def collect_infojobs_jobs():
    """Coleta vagas do InfoJobs Brasil"""
    print("=" * 60)
    print("🚀 InfoJobs Brasil Scraper")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    total_collected = 0

    try:
        for keyword in KEYWORDS:
            print(f"\n📋 {keyword}")
            jobs = scrape_infojobs(keyword)

            for job in jobs:
                try:
                    # Extract job_id from URL
                    job_id_match = re.search(r'/(\d+)', job["url"])
                    job_id = f"infojobs-{job_id_match.group(1)}" if job_id_match else f"infojobs-{hash(job['url']) % 1000000}"

                    # Parse city and state
                    if '-' in job["location"]:
                        parts = job["location"].split('-')
                        city = parts[0].strip() if len(parts) > 0 else None
                        state = parts[1].strip() if len(parts) > 1 else None
                    elif ',' in job["location"]:
                        parts = job["location"].split(',')
                        city = parts[0].strip() if len(parts) > 0 else None
                        state = parts[1].strip() if len(parts) > 1 else None
                    else:
                        city = job["location"] if job["location"] != "Brasil" else None
                        state = None

                    # Normalize geographic data
                    geo = normalize_location(conn, {
                        "country": "Brazil",
                        "state": state,
                        "city": city
                    })

                    # Get or create organization
                    organization_id = get_or_create_organization(
                        conn, job["company"], job["location"], "Brazil"
                    )

                    # Parse salary
                    salary_min, salary_max, salary_period = parse_salary_brl(job["salary"])
                    remote_type = detect_remote_type(job["title"] + " " + job["description"])

                    # Insert job
                    cur.execute(
                        """
                        INSERT INTO sofia.jobs (
                            job_id, title, company, raw_location, raw_city, raw_state, country, country_id, state_id, city_id,
                            url, platform, source, organization_id,
                            description, salary_min, salary_max, salary_currency, salary_period,
                            remote_type, search_keyword, posted_date, collected_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, NOW())
                        ON CONFLICT (job_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            raw_location = EXCLUDED.raw_location,
                            source = EXCLUDED.source,
                            description = EXCLUDED.description,
                            salary_min = EXCLUDED.salary_min,
                            salary_max = EXCLUDED.salary_max,
                            remote_type = EXCLUDED.remote_type,
                            organization_id = COALESCE(EXCLUDED.organization_id, sofia.jobs.organization_id),
                            country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
                            state_id = COALESCE(EXCLUDED.state_id, sofia.jobs.state_id),
                            city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id),
                            collected_at = NOW()
                        """,
                        (
                            job_id, job["title"], job["company"], job["location"], city, state,
                            "Brazil", geo.get("country_id"), geo.get("state_id"), geo.get("city_id"),
                            job["url"], "infojobs", "infojobs", organization_id,
                            job["description"], salary_min, salary_max, "BRL", salary_period,
                            remote_type, keyword
                        )
                    )
                    conn.commit()
                    total_collected += 1

                except Exception as err:
                    conn.rollback()
                    # Ignore duplicates
                    if "23505" not in str(err):
                        print(f"   ❌ Error inserting job: {str(err)[:50]}")

            # Rate limiting
            time.sleep(2)

        # Statistics
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT company) as companies
            FROM sofia.jobs
            WHERE platform = 'infojobs'
        """)
        stats = cur.fetchone()

        print("\n" + "=" * 60)
        print(f"✅ Collected: {total_collected} tech jobs from InfoJobs")
        print("\n📊 InfoJobs Statistics:")
        print(f"   Total jobs: {stats[0]}")
        print(f"   Companies: {stats[1]}")
        print("=" * 60)

    except Exception as error:
        print(f"❌ Fatal error: {str(error)}")

    finally:
        conn.close()

    return total_collected


if __name__ == "__main__":
    try:
        total = collect_infojobs_jobs()
        sys.exit(0 if total > 0 else 1)
    except Exception as err:
        print(f"Fatal error: {err}")
        sys.exit(1)
