#!/usr/bin/env python3
"""
Coletor: InfoJobs Brasil API
URL: https://developer.infojobs.net/
Auth: OAuth2 (requer registro)
Features: Busca de vagas tech no Brasil
"""
import requests
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# InfoJobs API (Brasil)
INFOJOBS_CLIENT_ID = os.getenv('INFOJOBS_CLIENT_ID', '')
INFOJOBS_CLIENT_SECRET = os.getenv('INFOJOBS_CLIENT_SECRET', '')
INFOJOBS_API_URL = "https://api.infojobs.com.br/api/2/offer"

# Keywords tech focadas em Brasil
KEYWORDS = [
    "desenvolvedor", "programador", "software engineer",
    "data scientist", "devops", "frontend", "backend",
    "full stack", "mobile", "qa", "tech lead"
]

def get_access_token():
    """Obtém token OAuth2 do InfoJobs"""
    if not INFOJOBS_CLIENT_ID or not INFOJOBS_CLIENT_SECRET:
        print("⚠️  INFOJOBS_CLIENT_ID e INFOJOBS_CLIENT_SECRET não configurados")
        return None
    
    auth_url = "https://www.infojobs.com.br/oauth/authorize"
    token_url = "https://api.infojobs.com.br/oauth/user-authorize/authorize"
    
    # Nota: OAuth2 requer fluxo de autorização completo
    # Por enquanto, retornar None e usar scraping alternativo
    return None

def collect_infojobs():
    """Coleta vagas do InfoJobs Brasil"""
    jobs = []
    
    # Tentar endpoint público sem auth (se existir)
    for keyword in KEYWORDS:
        try:
            # Endpoint público de busca (sem auth)
            params = {
                'q': keyword,
                'province': 'brasil',
                'category': 'informatica-telecomunicaciones',
                'maxResults': 50
            }
            
            # Tentar sem autenticação primeiro
            response = requests.get(INFOJOBS_API_URL, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                job_list = data.get('offers', data.get('items', []))
                
                for job in job_list:
                    jobs.append({
                        'job_id': f"infojobs-{job.get('id')}",
                        'title': job.get('title'),
                        'company': job.get('author', {}).get('name') if isinstance(job.get('author'), dict) else job.get('company'),
                        'location': job.get('province', {}).get('value') if isinstance(job.get('province'), dict) else job.get('location', 'Brasil'),
                        'description': job.get('description', '')[:1000],
                        'url': job.get('link'),
                        'platform': 'infojobs',
                        'posted_date': job.get('updated'),
                        'salary_min': job.get('salaryMin', {}).get('value') if isinstance(job.get('salaryMin'), dict) else None,
                        'salary_max': job.get('salaryMax', {}).get('value') if isinstance(job.get('salaryMax'), dict) else None,
                        'search_keyword': keyword
                    })
                
                print(f"✅ InfoJobs: {len(job_list)} vagas para '{keyword}'")
            elif response.status_code == 401:
                print(f"⚠️  InfoJobs: Requer autenticação OAuth2")
                print(f"   Registre-se em: https://developer.infojobs.net/")
                break
            else:
                print(f"⚠️  InfoJobs: {response.status_code} para '{keyword}'")
                
        except Exception as e:
            print(f"❌ InfoJobs erro para '{keyword}': {str(e)[:50]}")
    
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
                    search_keyword, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    collected_at = NOW()
            """, (
                job['job_id'], job['title'], job['company'], job['location'],
                job['description'], job['url'], job['platform'], 
                job['posted_date'], job['salary_min'], job['salary_max'],
                job['search_keyword']
            ))
            saved += 1
        except Exception as e:
            print(f"⚠️  Erro ao salvar: {str(e)[:50]}")
    
    conn.commit()
    conn.close()
    return saved

if __name__ == "__main__":
    print("=" * 70)
    print("🇧🇷 INFOJOBS BRASIL")
    print("=" * 70)
    print("⚠️  NOTA: InfoJobs requer OAuth2")
    print("   1. Registre-se em: https://developer.infojobs.net/")
    print("   2. Crie uma aplicação")
    print("   3. Adicione INFOJOBS_CLIENT_ID e INFOJOBS_CLIENT_SECRET no .env")
    print("=" * 70)
    
    jobs = collect_infojobs()
    
    if jobs:
        print(f"\n💾 Salvando {len(jobs)} vagas...")
        saved = save_to_db(jobs)
        print(f"\n✅ Total salvo: {saved} vagas")
    else:
        print("\n⚠️  Nenhuma vaga coletada. Configure OAuth2 primeiro.")
    
    print("=" * 70)
