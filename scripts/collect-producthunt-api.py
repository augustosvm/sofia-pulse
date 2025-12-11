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
        print("⚠️  PRODUCTHUNT_TOKEN não configurado no .env")
        print("   Obtenha em: https://www.producthunt.com/v2/oauth/applications")
        return []
    
    jobs = []
    
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
            makers {
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
                        jobs.append({
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
                
                print(f"✅ ProductHunt: {len(jobs)} produtos tech coletados")
            else:
                print(f"⚠️  ProductHunt: Resposta sem dados esperados")
                
        elif response.status_code == 401:
            print(f"❌ ProductHunt: Token inválido ou expirado")
            print(f"   Obtenha novo token em: https://www.producthunt.com/v2/oauth/applications")
        else:
            print(f"⚠️  ProductHunt: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ProductHunt erro: {str(e)[:100]}")
    
    return jobs

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
            print(f"⚠️  Erro ao salvar: {str(e)[:50]}")
    
    conn.commit()
    conn.close()
    return saved

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 PRODUCTHUNT API - STARTUPS TECH")
    print("=" * 70)
    
    jobs = collect_producthunt()
    
    if jobs:
        print(f"\n💾 Salvando {len(jobs)} produtos...")
        saved = save_to_db(jobs)
        print(f"\n✅ Total salvo: {saved} produtos")
    else:
        print("\n⚠️  Nenhum produto coletado")
    
    print("=" * 70)
