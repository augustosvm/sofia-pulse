#!/usr/bin/env python3
"""
Coletor: TheirStack API (melhor agregador - LinkedIn/Indeed/Glassdoor)
API Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhdWd1c3Rvc3ZtQGdtYWlsLmNvbSIsInBlcm1pc3Npb25zIjoidXNlciIsImNyZWF0ZWRfYXQiOiIyMDI1LTEyLTEwVDE4OjU1OjA0LjYzODYwMiswMDowMCJ9.RDEuNjs-toWKa-GLiszUVbxraY8fcrDbd3SWh__4W_4
Features: 195+ countries, LinkedIn/Indeed/Glassdoor aggregator, real-time
FOCO: Brasil
"""
import requests
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

THEIRSTACK_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhdWd1c3Rvc3ZtQGdtYWlsLmNvbSIsInBlcm1pc3Npb25zIjoidXNlciIsImNyZWF0ZWRfYXQiOiIyMDI1LTEyLTEwVDE4OjU1OjA0LjYzODYwMiswMDowMCJ9.RDEuNjs-toWKa-GLiszUVbxraY8fcrDbd3SWh__4W_4'
API_URL = "https://api.theirstack.com/v1/jobs/search"

KEYWORDS = [
    "Software Engineer", "Data Scientist", "DevOps", "Frontend", "Backend",
    "Full Stack", "Mobile Developer", "QA Engineer", "Tech Lead",
    "Engineering Manager", "Product Manager", "Arquiteto Software"
]

def collect_theirstack():
    """Coleta vagas do TheirStack"""
    jobs = []
    
    headers = {
        'Authorization': f'Bearer {THEIRSTACK_KEY}',
        'Content-Type': 'application/json'
    }
    
    for keyword in KEYWORDS:
        try:
            params = {
                'query': keyword,
                'location': 'Brazil',
                'limit': 100
            }
            
            response = requests.get(API_URL, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                job_list = data.get('jobs', data.get('data', []))
                
                for job in job_list:
                    jobs.append({
                        'job_id': f"theirstack-{job.get('id', hash(job.get('url')))}",
                        'title': job.get('title'),
                        'company': job.get('company'),
                        'location': job.get('location', 'Brazil'),
                        'description': job.get('description', '')[:1000],
                        'url': job.get('url'),
                        'platform': 'theirstack',
                        'posted_date': job.get('posted_date'),
                        'salary_min': job.get('salary_min'),
                        'salary_max': job.get('salary_max'),
                        'search_keyword': keyword
                    })
                
                print(f"✅ TheirStack: {len(job_list)} vagas para '{keyword}'")
            else:
                print(f"⚠️  TheirStack: {response.status_code} para '{keyword}'")
                
        except Exception as e:
            print(f"❌ TheirStack erro para '{keyword}': {str(e)[:50]}")
    
    return jobs

def save_to_db(jobs):
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
                    search_keyword, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    collected_at = NOW()
            """, (
                job['job_id'], job['title'], job['company'], job['location'],
                job['description'], job['url'], job['platform'], 
                job['posted_date'], job['salary_min'], job['salary_max'],
                job['search_keyword']
            ))
            saved += 1
        except Exception as e:
            print(f"⚠️  Erro: {str(e)[:50]}")
    
    conn.commit()
    conn.close()
    return saved

if __name__ == "__main__":
    print("🌐 THEIRSTACK (LinkedIn/Indeed/Glassdoor) - BRASIL")
    jobs = collect_theirstack()
    saved = save_to_db(jobs)
    print(f"✅ Total salvo: {saved} vagas")
