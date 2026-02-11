#!/usr/bin/env python3
"""
Coletor: InfoJobs Brasil (Scraping Robusto)
URL: https://www.infojobs.com.br/
Auth: Não requer (scraping público)
Features: Busca de vagas tech no Brasil com detecção de bloqueio
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
    "desenvolvedor python",
    "programador java",
    "javascript",
    "react",
    "devops"
]


def detect_blocking(soup, response):
    """Detecta se foi bloqueado ou captcha"""
    text = response.text.lower()

    # Detecção de captcha/bloqueio
    if any(word in text for word in ['captcha', 'recaptcha', 'cloudflare', 'access denied', 'blocked']):
        return "BOT_DETECTED"

    # Verificar se tem conteúdo mínimo
    if len(response.content) < 5000:
        return "EMPTY_RESPONSE"

    return None


def scrape_infojobs(keyword):
    """Scrape vagas do InfoJobs Brasil com múltiplas estratégias"""
    jobs = []

    try:
        url = "https://www.infojobs.com.br/empregos.aspx"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.infojobs.com.br/"
        }

        params = {"palabra": keyword}

        response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code != 200:
            print(f"   ⚠️  HTTP {response.status_code} for '{keyword}'")
            return jobs

        soup = BeautifulSoup(response.content, 'html.parser')

        # Detectar bloqueio
        block_reason = detect_blocking(soup, response)
        if block_reason:
            print(f"   ❌ {block_reason} for '{keyword}'")
            # Salvar HTML para debug (apenas primeira vez)
            if not os.path.exists('/tmp/infojobs_blocked.html'):
                with open('/tmp/infojobs_blocked.html', 'w') as f:
                    f.write(response.text[:50000])  # Primeiros 50k
                print(f"   💾 Saved HTML snapshot to /tmp/infojobs_blocked.html")
            return jobs

        # Estratégia 1: Lista de ofertas oficial (ul.js-offers-list > li)
        job_list = soup.find('ul', class_='js-offers-list')
        if job_list:
            items = job_list.find_all('li', recursive=False)
            print(f"   📋 Estratégia 1: Encontrado {len(items)} items em ul.js-offers-list")

            for item in items[:20]:
                try:
                    # Título e link
                    title_link = item.find('a', class_='js-o-link')
                    if not title_link:
                        title_link = item.find('a', href=re.compile(r'/oferta-emprego/'))

                    if not title_link:
                        continue

                    title = title_link.get_text(strip=True)
                    url_path = title_link.get('href', '')

                    # Empresa
                    company_el = item.find(class_=re.compile(r'company|empresa'))
                    company = company_el.get_text(strip=True) if company_el else "Unknown"

                    # Localização
                    location_el = item.find(class_=re.compile(r'location|local|cidade'))
                    location = location_el.get_text(strip=True) if location_el else "Brasil"

                    # URL completa
                    full_url = url_path if url_path.startswith('http') else f"https://www.infojobs.com.br{url_path}"

                    jobs.append({
                        "url": full_url,
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary": "",
                        "description": "",
                        "keyword": keyword
                    })
                except Exception as e:
                    continue

        # Estratégia 2: Qualquer link com /oferta-emprego/
        if not jobs:
            print(f"   📋 Estratégia 2: Buscando links com /oferta-emprego/")
            links = soup.find_all('a', href=re.compile(r'/oferta-emprego/'))
            print(f"      Encontrados {len(links)} links")

            for link in links[:20]:
                try:
                    title = link.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue

                    url_path = link.get('href', '')
                    full_url = url_path if url_path.startswith('http') else f"https://www.infojobs.com.br{url_path}"

                    # Tentar encontrar container pai com mais info
                    parent = link.parent
                    company = "Unknown"
                    location = "Brasil"

                    for _ in range(3):
                        if not parent:
                            break

                        company_el = parent.find(class_=re.compile(r'company|empresa'))
                        if company_el and company == "Unknown":
                            company = company_el.get_text(strip=True)

                        location_el = parent.find(class_=re.compile(r'location|local'))
                        if location_el and location == "Brasil":
                            location = location_el.get_text(strip=True)

                        parent = parent.parent

                    jobs.append({
                        "url": full_url,
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary": "",
                        "description": "",
                        "keyword": keyword
                    })
                except Exception as e:
                    continue

        print(f"   ✅ {len(jobs)} vagas for '{keyword}'")

        # Salvar HTML de sucesso para análise (apenas primeira vez com sucesso)
        if jobs and not os.path.exists('/tmp/infojobs_success.html'):
            with open('/tmp/infojobs_success.html', 'w') as f:
                f.write(response.text[:50000])
            print(f"   💾 Saved successful HTML to /tmp/infojobs_success.html")

    except Exception as e:
        print(f"   ❌ Error scraping '{keyword}': {str(e)[:80]}")

    return jobs


def get_or_create_organization(conn, company_name, location, country):
    """Get or create organization"""
    if not company_name or company_name == "Unknown":
        return None

    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT id FROM sofia.organizations WHERE name = %s LIMIT 1",
            (company_name,)
        )
        result = cur.fetchone()

        if result:
            return result[0]

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
    except Exception:
        conn.rollback()
        return None


def collect_infojobs_jobs():
    """Coleta vagas do InfoJobs Brasil"""
    print("=" * 60)
    print("🚀 InfoJobs Brasil Scraper (Robusto)")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    total_collected = 0
    total_scraped = 0

    try:
        for keyword in KEYWORDS:
            print(f"\n📋 {keyword}")
            jobs = scrape_infojobs(keyword)
            total_scraped += len(jobs)

            for job in jobs:
                try:
                    # Extract job_id from URL
                    job_id_match = re.search(r'/oferta-emprego/(\d+)', job["url"])
                    if job_id_match:
                        job_id = f"infojobs-{job_id_match.group(1)}"
                    else:
                        job_id = f"infojobs-{hash(job['url']) % 1000000}"

                    # Parse location
                    city = None
                    state = None
                    if '-' in job["location"]:
                        parts = job["location"].split('-')
                        city = parts[0].strip()
                        state = parts[1].strip() if len(parts) > 1 else None
                    elif job["location"] != "Brasil":
                        city = job["location"]

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

                    # Insert job
                    cur.execute(
                        """
                        INSERT INTO sofia.jobs (
                            job_id, title, company, raw_location, raw_city, raw_state,
                            country, country_id, state_id, city_id,
                            url, platform, source, organization_id,
                            search_keyword, posted_date, collected_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, NOW())
                        ON CONFLICT (job_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            collected_at = NOW()
                        """,
                        (
                            job_id, job["title"], job["company"], job["location"], city, state,
                            "Brazil", geo.get("country_id"), geo.get("state_id"), geo.get("city_id"),
                            job["url"], "infojobs", "infojobs", organization_id,
                            keyword
                        )
                    )
                    conn.commit()
                    total_collected += 1

                except Exception as err:
                    conn.rollback()
                    if "23505" not in str(err):
                        print(f"   ⚠️  Error inserting: {str(err)[:60]}")

            time.sleep(2)

        # Statistics
        cur.execute("""
            SELECT COUNT(*) as total, COUNT(DISTINCT company) as companies
            FROM sofia.jobs
            WHERE platform = 'infojobs'
        """)
        stats = cur.fetchone()

        print("\n" + "=" * 60)
        print(f"✅ Scraped: {total_scraped} vagas")
        print(f"✅ Saved: {total_collected} new/updated jobs")
        print(f"\n📊 InfoJobs Total:")
        print(f"   Jobs: {stats[0]}")
        print(f"   Companies: {stats[1]}")
        print("=" * 60)

        # Critério de sucesso: deve inserir >0
        if total_scraped == 0:
            print("\n❌ ERROR: EMPTY_SOURCE - No jobs found")
            sys.exit(1)

        if total_collected == 0 and total_scraped > 0:
            print("\n⚠️  WARNING: Jobs scraped but none inserted (all duplicates?)")

    except Exception as error:
        print(f"\n❌ Fatal error: {str(error)}")
        sys.exit(1)

    finally:
        conn.close()

    return total_collected


if __name__ == "__main__":
    try:
        total = collect_infojobs_jobs()
        sys.exit(0)
    except Exception as err:
        print(f"Fatal error: {err}")
        sys.exit(1)
