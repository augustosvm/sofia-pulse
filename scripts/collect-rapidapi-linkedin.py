#!/usr/bin/env python3
"""
Coletor: RapidAPI - LinkedIn Job Search API
Features: LinkedIn jobs, updated hourly
FOCO: Brasil
"""
import requests
import psycopg2
import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Import geo helpers
sys.path.insert(0, str(Path(__file__).parent / 'shared'))
from geo_helpers import normalize_location


load_dotenv()

RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
API_URL = "https://linkedin-job-search-api.p.rapidapi.com/active-jb-1h"

def collect_linkedin_rapidapi():
    """Coleta vagas do LinkedIn via RapidAPI"""
    jobs = []
    
    headers = {
        'x-rapidapi-host': 'linkedin-job-search-api.p.rapidapi.com',
        'x-rapidapi-key': RAPIDAPI_KEY
    }
    
    try:
        params = {
            'offset': 0,
            'description_type': 'text',
            'location': 'Brazil'
        }
        
        response = requests.get(API_URL, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            job_list = data.get('jobs', data.get('data', []))
            
            for job in job_list[:500]:  # Limitar a 500
                jobs.append({
                    'job_id': f"linkedin-rapid-{job.get('id', hash(job.get('url')))}",
                    'title': job.get('title'),
                    'company': job.get('company'),
                    'location': job.get('location', 'Brazil'),
                    'description': job.get('description', '')[:1000],
                    'url': job.get('url', job.get('link')),
                    'platform': 'linkedin',
                    'posted_date': job.get('posted_date'),
                    'salary_min': job.get('salary_min'),
                    'salary_max': job.get('salary_max'),
                    'remote_type': job.get('remote_type')
                })
            
            print(f"✅ LinkedIn RapidAPI: {len(jobs)} vagas")
        else:
            print(f"⚠️  LinkedIn RapidAPI: {response.status_code}")
            
    except Exception as e:
        print(f"❌ LinkedIn RapidAPI erro: {str(e)[:50]}")
    
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
                        # Parse location
            location_str = job.get('location', '')
            parts = location_str.split(',') if location_str else []
            city = parts[0].strip() if len(parts) > 0 else None
            country = parts[-1].strip() if len(parts) > 0 else 'Brazil'
            
            # Normalize geographic data
            geo = normalize_location(conn, {
                'country': country,
                'city': city
            })
            cur.execute("""
                INSERT INTO sofia.jobs (
                    job_id, title, company, location, city, country, country_id, city_id, description, url,
                    platform, posted_date, salary_min, salary_max,
                    remote_type, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    collected_at = NOW()
            """, (
                job['job_id'], job['title'], job['company'], job['location'],
                city, country, geo['country_id'], geo['city_id'],
                job['description'], job['url'], job['platform'], 
                job['posted_date'], job['salary_min'], job['salary_max'],
                job['remote_type']
            ))
            saved += 1
        except Exception as e:
            print(f"⚠️  Erro ao salvar: {str(e)[:50]}")
    
    conn.commit()
    conn.close()
    return saved

if __name__ == "__main__":
    print("=" * 70)
    print("💼 LINKEDIN JOBS (RAPIDAPI) - BRASIL")
    print("=" * 70)
    
    jobs = collect_linkedin_rapidapi()
    print(f"\n💾 Salvando {len(jobs)} vagas...")
    saved = save_to_db(jobs)
    
    print(f"\n✅ Total salvo: {saved} vagas")
    print("=" * 70)
