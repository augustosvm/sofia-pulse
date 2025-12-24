#!/usr/bin/env python3
"""
Coletor: InfoJobs Brasil Web Scraper
URL: https://www.infojobs.com.br/
Método: Web Scraping (sem autenticação)
"""
import requests
from bs4 import BeautifulSoup
import psycopg2
import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Import geo helpers
sys.path.insert(0, str(Path(__file__).parent / 'shared'))
from geo_helpers import normalize_location

load_dotenv()

# Database
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'sofia_db'),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', '')
}

KEYWORDS = [
    "desenvolvedor", "programador", "python", "javascript",
    "react", "node", "java", "engenheiro de software"
]

def scrape_infojobs(keyword, max_pages=3):
    """Scrape vagas do InfoJobs.com.br"""
    jobs = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for page in range(1, max_pages + 1):
        url = f"https://www.infojobs.com.br/empregos.aspx?palabra={keyword}&page={page}"

        try:
            print(f"   📄 Página {page} de '{keyword}'...")
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"   ⚠️  Status {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Encontrar listagem de vagas
            job_items = soup.find_all('div', class_='js_vacancyLoad')

            print(f"   ✅ Encontrados {len(job_items)} anúncios")

            for item in job_items:
                try:
                    # Título e URL
                    title_elem = item.find('h2') or item.find('h3') or item.find('a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # URL - procurar link
                    link_elem = item.find('a', href=True)
                    job_url = link_elem['href'] if link_elem else ''

                    if job_url and not job_url.startswith('http'):
                        job_url = 'https://www.infojobs.com.br' + job_url

                    # Empresa - procurar múltiplos seletores
                    company_elem = item.find(string=lambda text: text and ('empresa' in text.lower() or 'company' in text.lower()))
                    if not company_elem:
                        company_elem = item.find('span', class_=lambda x: x and 'company' in str(x).lower())
                    company = company_elem.get_text(strip=True) if company_elem and hasattr(company_elem, 'get_text') else company_elem.strip() if company_elem else 'Não informado'

                    # Localização - tentar múltiplos seletores
                    location_elem = item.find('span', class_='location') or \
                                  item.find('p', class_='job-location') or \
                                  item.find('span', class_='job-location') or \
                                  item.find('div', class_='offer-location')
                    location = location_elem.get_text(strip=True) if location_elem else ''

                    # Salário - tentar múltiplos seletores
                    salary_elem = item.find('span', class_='salary') or \
                                 item.find('div', class_='offer-salary') or \
                                 item.find('span', class_='job-salary')
                    salary = salary_elem.get_text(strip=True) if salary_elem else None

                    # Descrição
                    desc_elem = item.find('div', class_='offer-description') or \
                               item.find('p', class_='job-description')
                    description = desc_elem.get_text(strip=True) if desc_elem else ''

                    # ID da vaga (extrair do URL)
                    job_id = re.search(r'/oferta-empleo/([^/]+)', job_url)
                    job_id = job_id.group(1) if job_id else job_url.split('/')[-1]

                    jobs.append({
                        'job_id': f'infojobs-{job_id}',
                        'title': title,
                        'company': company,
                        'location': location,
                        'salary': salary,
                        'description': description[:500],
                        'url': job_url,
                        'posted_date': datetime.now().date()
                    })

                except Exception as e:
                    print(f"   ⚠️  Erro ao processar item: {e}")
                    continue

        except Exception as e:
            print(f"   ❌ Erro na página {page}: {e}")
            continue

    return jobs

def insert_jobs(jobs):
    """Insere vagas no banco"""
    if not jobs:
        print("   ⚠️  Nenhuma vaga para inserir")
        return 0

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    inserted = 0

    for job in jobs:
        try:
            # Normalizar localização (já assume Brasil)
            geo = normalize_location(conn, job['location'])

            cursor.execute("""
                INSERT INTO sofia.jobs (
                    job_id, platform, title, company, location,
                    salary, description, url, posted_date, collected_at,
                    country_id, state_id, city_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s)
                ON CONFLICT (job_id, platform) DO UPDATE SET
                    title = EXCLUDED.title,
                    salary = EXCLUDED.salary,
                    location = EXCLUDED.location,
                    description = EXCLUDED.description,
                    collected_at = NOW()
            """, (
                job['job_id'],
                'infojobs-br',
                job['title'],
                job['company'],
                job['location'],
                job.get('salary'),
                job['description'],
                job['url'],
                job['posted_date'],
                geo['country_id'],
                geo['state_id'],
                geo['city_id']
            ))

            inserted += 1

        except Exception as e:
            print(f"   ⚠️  Erro ao inserir vaga: {e}")
            continue

    conn.commit()
    cursor.close()
    conn.close()

    return inserted

def main():
    print("="*70)
    print("🇧🇷 INFOJOBS BRASIL WEB SCRAPER")
    print("="*70)

    all_jobs = []

    for keyword in KEYWORDS:
        print(f"\n🔍 Buscando: '{keyword}'")
        jobs = scrape_infojobs(keyword, max_pages=2)
        all_jobs.extend(jobs)
        print(f"   ✅ Coletadas {len(jobs)} vagas")

    # Remover duplicatas
    unique_jobs = {job['job_id']: job for job in all_jobs}.values()
    print(f"\n📊 Total único: {len(unique_jobs)} vagas")

    # Inserir no banco
    print(f"\n💾 Inserindo no banco...")
    inserted = insert_jobs(list(unique_jobs))

    print(f"\n✅ Inseridas: {inserted} vagas")
    print("="*70)

if __name__ == '__main__':
    main()
