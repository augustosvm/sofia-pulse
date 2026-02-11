#!/usr/bin/env python3
"""
Coletor: Catho Brasil (Scraping Simplificado)
URL: https://www.catho.com.br/
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
    "node",
    "devops",
    "data scientist",
    "frontend",
    "backend",
    "full stack",
    "mobile",
    "qa",
    "tech lead"
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
    elif re.search(r"hora|\/h", text, re.I):
        period = "hourly"

    # Extrair números (ex: "R$ 5.000 - R$ 8.000")
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
    if re.search(r"remoto|remote|home office|trabalho remoto", text_lower):
        return "remote"
    if re.search(r"híbrido|hybrid", text_lower):
        return "hybrid"
    return None


def detect_seniority(title):
    """Detecta nível de senioridade"""
    if not title:
        return "mid"
    title_lower = title.lower()
    if re.search(r"sênior|senior|sr\.|pleno sênior", title_lower):
        return "senior"
    if re.search(r"júnior|junior|jr\.|trainee|estágio", title_lower):
        return "entry"
    if re.search(r"pleno|mid|intermediário", title_lower):
        return "mid"
    if re.search(r"staff|principal|arquiteto", title_lower):
        return "principal"
    return "mid"


def extract_skills(text):
    """Extrai skills técnicas do texto"""
    if not text:
        return []

    text_lower = text.lower()
    common_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js", "Angular", "Vue",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "SQL", "PostgreSQL", "MongoDB", "MySQL",
        "Git", "CI/CD", "Scrum", "Agile", "REST API", "GraphQL", "Redis", "Kafka",
        "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn",
        "Spring", "Django", "Flask", "FastAPI", "Express",
        "HTML", "CSS", "Sass", "Tailwind", "Bootstrap",
    ]

    skills = []
    for skill in common_skills:
        if skill.lower() in text_lower:
            skills.append(skill)

    return list(set(skills))


def detect_sector(title):
    """Detecta setor tech"""
    if not title:
        return "Other Tech"
    title_lower = title.lower()

    if re.search(r"\b(ai|machine learning|ml|data scien|deep learning)", title_lower):
        return "AI & ML"
    if re.search(r"\b(security|segurança|infosec|cyber)", title_lower):
        return "Security"
    if re.search(r"\b(devops|cloud|sre|infrastructure)", title_lower):
        return "DevOps & Cloud"
    if re.search(r"\b(gerente|manager|líder|coordenador|cto|cio|director)", title_lower):
        return "Leadership"
    if re.search(r"\b(backend|back-end)", title_lower):
        return "Backend"
    if re.search(r"\b(frontend|front-end)", title_lower):
        return "Frontend"
    if re.search(r"\b(mobile|ios|android|react native|flutter)", title_lower):
        return "Mobile"
    if re.search(r"\b(data engineer|dados|etl|pipeline)", title_lower):
        return "Data Engineering"
    if re.search(r"\b(qa|quality|test|tester)", title_lower):
        return "QA & Testing"
    if re.search(r"\b(product|product manager|pm)", title_lower):
        return "Product"

    return "Other Tech"


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
            (company_name, location, country, 'catho')
        )
        conn.commit()
        return cur.fetchone()[0]
    except Exception as e:
        conn.rollback()
        print(f"   [WARN] Error creating org: {str(e)[:50]}")
        return None


def scrape_catho(keyword):
    """Scrape vagas do Catho para uma keyword"""
    jobs = []

    try:
        # URL de busca do Catho
        url = f"https://www.catho.com.br/vagas/{keyword.lower().replace(' ', '-')}/"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"   ⚠️  HTTP {response.status_code} for '{keyword}'")
            return jobs

        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscar links de vagas (padrão: /vagas/.../34...)
        job_links = soup.find_all('a', href=re.compile(r'/vagas/.*?/34'))

        for i, link in enumerate(job_links[:20]):  # Limitar a 20 por keyword
            href = link.get('href', '')
            title = link.get_text(strip=True)

            if not href or not title or 'anunciar' in href:
                continue

            # Tentar encontrar informações adicionais no parent container
            parent = link.parent
            company = "Unknown"
            location = "Brasil"
            salary = ""
            description = ""

            # Walk up to find company/location/salary
            for _ in range(5):
                if not parent:
                    break

                text = parent.get_text()

                # Look for location patterns (cidade - UF)
                valid_states = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
                loc_match = re.search(r'([A-ZÀ-Ú][a-zà-ú\s]{2,})\s*-\s*([A-Z]{2})\b', text)
                if loc_match:
                    state_code = loc_match.group(2)
                    if state_code in valid_states:
                        location = loc_match.group(0)

                # Look for company name
                company_el = parent.find(class_=re.compile(r'company|job-company'))
                if company_el and company == "Unknown":
                    company = company_el.get_text(strip=True)

                # Look for salary
                salary_el = parent.find(class_=re.compile(r'salary|job-salary'))
                if salary_el and not salary:
                    salary = salary_el.get_text(strip=True)

                # Look for description
                desc_el = parent.find(class_=re.compile(r'description|job-description'))
                if desc_el and not description:
                    description = desc_el.get_text(strip=True)

                parent = parent.parent

            # Construir URL completa
            full_url = href if href.startswith('http') else f"https://www.catho.com.br{href}"

            jobs.append({
                "url": full_url,
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "description": description,
                "keyword": keyword
            })

        print(f"   ✅ {len(jobs)} vagas for '{keyword}'")

    except Exception as e:
        print(f"   ❌ Error scraping '{keyword}': {str(e)[:50]}")

    return jobs


def collect_catho_jobs():
    """Coleta vagas do Catho"""
    print("=" * 60)
    print("🚀 Catho Scraper (Python Simplificado)")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    total_collected = 0

    try:
        for keyword in KEYWORDS:
            print(f"\n📋 {keyword}")
            jobs = scrape_catho(keyword)

            for job in jobs:
                try:
                    # Extract job_id from URL
                    job_id_match = re.search(r'/(\d+)/', job["url"])
                    job_id = f"catho-{job_id_match.group(1)}" if job_id_match else f"catho-{int(time.time())}"

                    # Parse city and state
                    if '-' in job["location"]:
                        parts = job["location"].split('-')
                        city = parts[0].strip() if len(parts) > 0 else None
                        state = parts[1].strip() if len(parts) > 1 else None
                    else:
                        city = None
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

                    # Parse using helpers
                    salary_min, salary_max, salary_period = parse_salary_brl(job["salary"])
                    remote_type = detect_remote_type(job["title"] + " " + job["description"])
                    seniority = detect_seniority(job["title"])
                    skills = extract_skills(job["title"] + " " + job["description"])
                    sector = detect_sector(job["title"])

                    # Insert job
                    cur.execute(
                        """
                        INSERT INTO sofia.jobs (
                            job_id, title, company, raw_location, raw_city, raw_state, country, country_id, state_id, city_id,
                            url, platform, source, organization_id,
                            description, salary_min, salary_max, salary_currency, salary_period,
                            remote_type, seniority_level, employment_type, skills_required, sector,
                            search_keyword, posted_date, collected_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, NOW())
                        ON CONFLICT (job_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            raw_location = EXCLUDED.raw_location,
                            source = EXCLUDED.source,
                            description = EXCLUDED.description,
                            salary_min = EXCLUDED.salary_min,
                            salary_max = EXCLUDED.salary_max,
                            salary_period = EXCLUDED.salary_period,
                            remote_type = EXCLUDED.remote_type,
                            seniority_level = EXCLUDED.seniority_level,
                            skills_required = EXCLUDED.skills_required,
                            sector = EXCLUDED.sector,
                            organization_id = COALESCE(EXCLUDED.organization_id, sofia.jobs.organization_id),
                            country_id = COALESCE(EXCLUDED.country_id, sofia.jobs.country_id),
                            state_id = COALESCE(EXCLUDED.state_id, sofia.jobs.state_id),
                            city_id = COALESCE(EXCLUDED.city_id, sofia.jobs.city_id),
                            posted_date = EXCLUDED.posted_date,
                            collected_at = NOW()
                        """,
                        (
                            job_id, job["title"], job["company"], job["location"], city, state,
                            "Brazil", geo.get("country_id"), geo.get("state_id"), geo.get("city_id"),
                            job["url"], "catho", "catho", organization_id,
                            job["description"], salary_min, salary_max, "BRL", salary_period,
                            remote_type, seniority, "full-time", skills, sector,
                            keyword
                        )
                    )
                    conn.commit()
                    total_collected += 1

                except Exception as err:
                    conn.rollback()
                    # Ignore duplicates
                    if "23505" not in str(err):
                        print(f"   ❌ Error inserting job: {str(err)[:50]}")

            # Rate limiting: aguardar entre keywords
            time.sleep(3)

        # Statistics
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT company) as companies
            FROM sofia.jobs
            WHERE platform = 'catho'
        """)
        stats = cur.fetchone()

        print("\n" + "=" * 60)
        print(f"✅ Collected: {total_collected} tech jobs from Catho")
        print("\n📊 Catho Statistics:")
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
        total = collect_catho_jobs()
        sys.exit(0 if total > 0 else 1)
    except Exception as err:
        print(f"Fatal error: {err}")
        sys.exit(1)
