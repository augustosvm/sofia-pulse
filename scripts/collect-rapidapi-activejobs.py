#!/usr/bin/env python3
"""
Coletor: RapidAPI - Active Jobs DB (Fantastic.jobs)
API Key: 880a9ad324msh90b6bf8ee717866p1855dfjsn6377aaee1939
Features: 8M+ jobs/month, AI-enriched, 130k+ career sites
FOCO: Brasil
"""
import requests
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '880a9ad324msh90b6bf8ee717866p1855dfjsn6377aaee1939')
API_URL = "https://active-jobs-db.p.rapidapi.com/active-ats-7d"

# Keywords focadas em Brasil
KEYWORDS = [
    "Engenheiro de Software", "Desenvolvedor", "Data Scientist", "DevOps",
    "Analista de Dados", "Cientista de Dados", "Arquiteto de Software",
    "Tech Lead", "Engineering Manager", "Product Manager",
    "QA Engineer", "Analista de Testes", "DBA", "Administrador de Banco",
    "Frontend", "Backend", "Full Stack", "Mobile", "React", "Python"
]

def collect_active_jobs_db():
    """Coleta vagas do Active Jobs DB (Fantastic.jobs)"""
    jobs = []
    
    headers = {
        'x-rapidapi-host': 'active-jobs-db.p.rapidapi.com',
        'x-rapidapi-key': RAPIDAPI_KEY
    }
    
    for keyword in KEYWORDS:
        try:
            params = {
                'limit': 100,
                'offset': 0,
                'title_filter': f'"{keyword}"',
                'location_filter': '"Brazil" OR "Brasil" OR "Remote"',
                'description_type': 'text'
            }
            
            response = requests.get(API_URL, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                job_list = data.get('jobs', data.get('data', []))
                
                for job in job_list:
                    jobs.append({
                        'job_id': f"activejobs-{job.get('id', hash(job.get('url')))}",
                        'title': job.get('title'),
                        'company': job.get('company'),
                        'location': job.get('location', 'Brazil'),
                        'description': job.get('description', '')[:1000],
                        'url': job.get('url', job.get('apply_url')),
                        'platform': 'activejobs',
                        'posted_date': job.get('posted_date'),
                        'salary_min': job.get('salary_min'),
                        'salary_max': job.get('salary_max'),
                        'remote_type': 'remote' if 'remote' in str(job.get('location', '')).lower() else None,
                        'search_keyword': keyword
                    })
                
                print(f"✅ Active Jobs DB: {len(job_list)} vagas para '{keyword}'")
            else:
                print(f"⚠️  Active Jobs DB: {response.status_code} para '{keyword}'")
                
        except Exception as e:
            print(f"❌ Active Jobs DB erro para '{keyword}': {str(e)[:50]}")
    
    return jobs

def save_to_db(jobs):
    """Salva vagas no banco"""
    if not jobs:
        return 0
    
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB')
    )
    cur = conn.cursor()
    
    saved = 0
    for job in jobs:
        try:
            cur.execute("""
                INSERT INTO sofia.jobs (
                    job_id, title, company, location, description, url,
                    platform, posted_date, salary_min, salary_max,
                    remote_type, search_keyword, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    collected_at = NOW()
            """, (
                job['job_id'], job['title'], job['company'], job['location'],
                job['description'], job['url'], job['platform'], 
                job['posted_date'], job['salary_min'], job['salary_max'],
                job['remote_type'], job['search_keyword']
            ))
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
