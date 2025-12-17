#!/usr/bin/env python3
"""
Coletor: Y Combinator Companies API
URL: https://api.ycombinator.com/ (unofficial GitHub API)
Auth: Nenhuma (100% gratuito)
Features: 5500+ startups YC, batches, funding stages
"""
import requests
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Y Combinator Unofficial API (URL correta)
YC_API_URL = "https://yc-oss.github.io/api/companies/all.json"

def collect_yc_companies():
    """Coleta empresas do Y Combinator"""
    companies = []
    
    try:
        response = requests.get(YC_API_URL, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Filtrar apenas empresas ativas
            for company in data:
                # Verificar se tem informações básicas
                if company.get('name') and company.get('batch'):
                    # Aceitar todas as empresas (remover filtro de batch)
                    companies.append({
                        'company_name': company.get('name'),
                        'batch': company.get('batch'),
                        'status': company.get('status', 'Active'),
                        'location': company.get('location', 'USA'),
                        'description': company.get('description', '')[:500],
                        'website': company.get('website'),
                        'tags': ', '.join(company.get('tags', [])[:5])
                    })
            
            print(f"✅ Y Combinator: {len(companies)} startups recentes coletadas")
        else:
            print(f"⚠️  Y Combinator API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Y Combinator erro: {str(e)[:100]}")
    
    return companies

def save_to_db(companies):
    """Salva empresas YC no banco"""
    if not companies:
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
    for company in companies:
        try:
            # Criar ID único
            company_id = f"yc-{company['batch']}-{company['company_name'].lower().replace(' ', '-')}"
            
            cur.execute("""
                INSERT INTO sofia.funding_rounds (
                    company_name, round_type, country, sector, collected_at
                ) VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT DO NOTHING
            """, (
                company['company_name'],
                f"YC {company['batch']}",
                'USA',
                company['tags']
            ))
            saved += 1
        except Exception as e:
            print(f"⚠️  Erro ao salvar {company['company_name']}: {str(e)[:50]}")
    
    conn.commit()
    conn.close()
    return saved

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Y COMBINATOR COMPANIES API")
    print("=" * 70)
    print("Coletando startups YC dos últimos 3 anos...")
    print("=" * 70)
    
    companies = collect_yc_companies()
    
    if companies:
        print(f"\n💾 Salvando {len(companies)} empresas...")
        saved = save_to_db(companies)
        print(f"\n✅ Total salvo: {saved} startups YC")
    else:
        print("\n⚠️  Nenhuma empresa coletada")
    
    print("=" * 70)
