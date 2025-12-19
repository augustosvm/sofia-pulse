#!/usr/bin/env python3
"""
Coletor: Himalayas.app Remote Jobs API
URL: https://himalayas.app/api
Features: Remote jobs, updated daily, 20 jobs/request
"""
import requests
import psycopg2
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Import geo helpers
sys.path.insert(0, str(Path(__file__).parent / 'shared'))
from geo_helpers import normalize_location

load_dotenv()

API_URL = "https://himalayas.app/jobs/api"

def collect_himalayas():
    """Coleta vagas da Himalayas API"""
    jobs = []
    
    try:
        # API pública sem auth
        response = requests.get(API_URL, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            job_list = data.get('jobs', data if isinstance(data, list) else [])
            
            for job in job_list[:100]:  # Limitar a 100
                jobs.append({
                    'job_id': f"himalayas-{job.get('id')}",
                    'title': job.get('title'),
                    'company': job.get('company', {}).get('name') if isinstance(job.get('company'), dict) else job.get('company'),
                    'location': job.get('location', 'Remote'),
                    'description': job.get('description', '')[:1000],
                    'url': job.get('url', job.get('link')),
                    'platform': 'himalayas',
                    'remote_type': 'remote',
                    'posted_date': job.get('published_at', job.get('created_at')),
                    'salary_min': job.get('salary_min'),
                    'salary_max': job.get('salary_max')
                })
            
            print(f"✅ Himalayas: {len(jobs)} remote jobs")
        else:
            print(f"⚠️  Himalayas: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Himalayas erro: {str(e)[:50]}")
    
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
            # Parse location (mostly remote)
            location_str = job.get('location', 'Remote')
            is_remote = 'remote' in location_str.lower() or location_str == 'Remote'
            country = None if is_remote else location_str
            
            # Normalize geographic data
            geo = normalize_location(conn, {
                'country': country
            })
            
            cur.execute("""
                INSERT INTO sofia.jobs (
                    job_id, title, company, location, country, country_id,
                    description, url, platform, remote_type, salary_min, salary_max, 
                    posted_date, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    collected_at = NOW()
            """, (
                job['job_id'], job['title'], job['company'], job['location'],
                country, geo['country_id'],
                job['description'], job['url'], job['platform'], 
                job['remote_type'], job['salary_min'], job['salary_max'],
                job['posted_date']
            ))
            saved += 1
        except Exception as e:
            print(f"⚠️  Erro ao salvar: {str(e)[:50]}")
    
    conn.commit()
    conn.close()
    return saved

if __name__ == "__main__":
    print("=" * 70)
    print("🏔️ HIMALAYAS REMOTE JOBS COLLECTOR")
    print("=" * 70)
    
    jobs = collect_himalayas()
    print(f"\n💾 Salvando {len(jobs)} vagas...")
    saved = save_to_db(jobs)
    
    print(f"\n✅ Total salvo: {saved} vagas")
    print("=" * 70)
