#!/usr/bin/env python3
"""
Coletor focado em áreas com baixa cobertura
Foca em: Gestão, Arquitetura, QA, Data Science, DevOps, DBA, IoT
"""
import requests
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Keywords expandidas focadas em áreas com baixa cobertura
KEYWORDS = [
    # Gestão
    "CTO", "VP Engineering", "Engineering Manager", "Tech Lead", "Technical Lead",
    "Director of Engineering", "Head of Engineering", "Product Manager",
    
    # Arquitetura
    "Software Architect", "Solutions Architect", "Cloud Architect", "Enterprise Architect",
    "Data Architect", "Security Architect", "API Architect",
    
    # QA/Testes
    "QA Engineer", "Quality Assurance", "Test Engineer", "SDET", "Test Automation",
    "QA Lead", "QA Manager", "Performance Tester", "Security Tester",
    
    # Data Science
    "Data Scientist", "Data Engineer", "Data Analyst", "ML Engineer",
    "Big Data Engineer", "BI Developer", "ETL Developer",
    
    # DevOps/SRE
    "DevOps Engineer", "SRE", "Site Reliability Engineer", "Platform Engineer",
    "Kubernetes Engineer", "Infrastructure Engineer", "CI/CD Engineer",
    
    # DBA
    "Database Administrator", "DBA", "PostgreSQL DBA", "MySQL DBA", "Oracle DBA",
    
    # IoT/Embedded
    "IoT Engineer", "Embedded Systems Engineer", "Firmware Engineer",
    
    # Outras especializadas
    "Blockchain Developer", "Smart Contract Developer", "Game Developer",
    "Computer Vision Engineer", "NLP Engineer", "LLM Engineer"
]

def collect_from_remotive():
    """Coleta da API Remotive (focada em remote jobs)"""
    jobs = []
    for keyword in KEYWORDS[:10]:  # Limitar para não sobrecarregar
        try:
            url = f"https://remotive.com/api/remote-jobs?search={keyword.replace(' ', '+')}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for job in data.get('jobs', [])[:20]:
                    jobs.append({
                        'job_id': f"remotive-{job.get('id')}",
                        'title': job.get('title'),
                        'company': job.get('company_name'),
                        'location': job.get('candidate_required_location', 'Remote'),
                        'description': job.get('description', '')[:1000],
                        'url': job.get('url'),
                        'platform': 'remotive',
                        'remote_type': 'remote',
                        'posted_date': job.get('publication_date'),
                        'search_keyword': keyword
                    })
                print(f"✅ Remotive: {len(jobs)} vagas para '{keyword}'")
        except Exception as e:
            print(f"⚠️  Remotive erro para '{keyword}': {str(e)[:50]}")
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
                    platform, remote_type, posted_date, search_keyword, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    collected_at = NOW()
            """, (
                job['job_id'], job['title'], job['company'], job['location'],
                job['description'], job['url'], job['platform'], job['remote_type'],
                job['posted_date'], job['search_keyword']
            ))
            saved += 1
        except Exception as e:
            print(f"⚠️  Erro ao salvar: {str(e)[:50]}")
    
    conn.commit()
    conn.close()
    return saved

if __name__ == "__main__":
    print("=" * 70)
    print("🎯 COLETOR FOCADO - Gestão, Arquitetura, QA, Data, DevOps")
    print("=" * 70)
    
    all_jobs = []
    
    # Coletar de Remotive
    print("\n📥 Coletando de Remotive...")
    all_jobs.extend(collect_from_remotive())
    
    # Salvar no banco
    print(f"\n💾 Salvando {len(all_jobs)} vagas...")
    saved = save_to_db(all_jobs)
    
    print(f"\n✅ Total salvo: {saved} vagas")
    print("=" * 70)
