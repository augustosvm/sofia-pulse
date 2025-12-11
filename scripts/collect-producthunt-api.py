#!/usr/bin/env python3
"""
Coletor: ProductHunt API
URL: https://api.producthunt.com/v2/api/graphql
Auth: OAuth2 (requer Developer Token)
Features: Produtos lançados + funding de startups tech
"""
import requests
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# ProductHunt API
PRODUCTHUNT_TOKEN = os.getenv('PRODUCTHUNT_TOKEN', '')
API_URL = "https://api.producthunt.com/v2/api/graphql"

def collect_producthunt():
    """Coleta produtos e funding do ProductHunt"""
    if not PRODUCTHUNT_TOKEN:
        print("WARNING: PRODUCTHUNT_TOKEN não configurado no .env")
        print("   Obtenha em: https://www.producthunt.com/v2/oauth/applications")
        return []
    
    all_jobs = []
    
    # Coletar múltiplas páginas (GraphQL permite max 50 por request)
    # Vamos fazer 4 requests para pegar ~200 produtos
    for page in range(4):
        # GraphQL query para produtos recentes
        query = """
        query {
          posts(first: 50, order: VOTES) {
            edges {
              node {
                id
                name
                tagline
                description
                url
                votesCount
                commentsCount
                createdAt
                topics {
                  edges {
                    node {
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        headers = {
            'Authorization': f'Bearer {PRODUCTHUNT_TOKEN}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(
                API_URL,
                json={'query': query},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and 'posts' in data['data']:
                    posts = data['data']['posts']['edges']
                    
                    for edge in posts:
                        post = edge['node']
                        
                        # Extrair topics
                        topics = [t['node']['name'] for t in post.get('topics', {}).get('edges', [])]
                        
                        # Filtrar apenas tech/startup topics
                        tech_keywords = ['startup', 'saas', 'ai', 'ml', 'developer', 'api', 'platform', 'tech']
                        is_tech = any(keyword in ' '.join(topics).lower() for keyword in tech_keywords)
                        
                        if is_tech:
                            all_jobs.append({
                                'job_id': f"producthunt-{post['id']}",
                                'title': f"Startup: {post['name']}",
                                'company': post['name'],
                                'location': 'Remote/Global',
                                'description': f"{post['tagline']}. {post.get('description', '')[:500]}",
                                'url': post['url'],
                                'platform': 'producthunt',
                                'posted_date': post['createdAt'][:10] if post.get('createdAt') else None,
                                'skills_required': ', '.join(topics[:5]),
                                'votes': post.get('votesCount', 0),
                                'search_keyword': 'startup launch'
                            })
                    
                    print(f"OK: ProductHunt página {page+1}: {len(posts)} produtos ({len([j for j in all_jobs if j['job_id'].startswith('producthunt-')])} tech)")
                else:
                    print(f"WARNING: ProductHunt página {page+1}: Resposta sem dados esperados")
                    if 'errors' in data:
                        print(f"DEBUG: Errors: {data['errors']}")
                    break  # Para se der erro
                    
            elif response.status_code == 401:
                print(f"ERROR: ProductHunt: Token inválido ou expirado")
                print(f"   Obtenha novo token em: https://www.producthunt.com/v2/oauth/applications")
                break
            else:
                print(f"WARNING: ProductHunt página {page+1}: {response.status_code}")
                break
                
        except Exception as e:
            print(f"ERROR: ProductHunt página {page+1} erro: {str(e)[:100]}")
            break
    
    print(f"\nOK: Total de produtos tech coletados: {len(all_jobs)}")
    return all_jobs

def save_to_db(jobs):
    """Salva produtos no banco (tabela jobs)"""
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
                    platform, posted_date, skills_required, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (job_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    collected_at = NOW()
            """, (
                job['job_id'], job['title'], job['company'], job['location'],
                job['description'], job['url'], job['platform'], 
                job['posted_date'], job['skills_required']
            ))
            saved += 1
        except Exception as e:
            print(f"WARNING: Erro ao salvar: {str(e)[:50]}")
    
    conn.commit()
    conn.close()
    return saved

if __name__ == "__main__":
    print("=" * 70)
    print("PRODUCTHUNT API - STARTUPS TECH")
    print("=" * 70)
    
    jobs = collect_producthunt()
    
    if jobs:
        print(f"\nProdutos coletados ({len(jobs)}):")
        print("=" * 70)
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Topics: {job['skills_required']}")
            print(f"   Votes: {job.get('votes', 0)}")
            print(f"   URL: {job['url']}")
        print("\n" + "=" * 70)
        
        print(f"\nSalvando {len(jobs)} produtos...")
        try:
            saved = save_to_db(jobs)
            print(f"\nOK: Total salvo: {saved} produtos")
        except Exception as e:
            print(f"\nWARNING: Erro ao salvar no banco (servidor remoto): {str(e)[:100]}")
            print("INFO: Produtos coletados com sucesso, mas nao salvos localmente")
    else:
        print("\nWARNING: Nenhum produto coletado")
    
    print("=" * 70)
