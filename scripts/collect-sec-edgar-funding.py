#!/usr/bin/env python3
"""
Coletor: SEC EDGAR API - IPOs e Funding
URL: https://data.sec.gov/
Auth: Nenhuma (100% gratuito)
Features: IPOs, funding rounds, Form D (venture capital), Form S-1
"""
import requests
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

load_dotenv()

# SEC EDGAR API
SEC_API_URL = "https://data.sec.gov/submissions"
SEC_HEADERS = {
    'User-Agent': 'Sofia Pulse augustosvm@gmail.com',  # SEC requer User-Agent
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'data.sec.gov'
}

# CIKs de empresas tech conhecidas (exemplos)
TECH_COMPANIES_CIK = [
    '0001018724',  # Amazon
    '0001652044',  # Alphabet (Google)
    '0001326801',  # Meta (Facebook)
    '0001045810',  # NVIDIA
    '0000789019',  # Microsoft
    '0001559720',  # Databricks (se público)
    '0001564590',  # Stripe (se público)
]

def collect_sec_edgar():
    """Coleta dados de funding do SEC EDGAR"""
    funding_data = []
    
    for cik in TECH_COMPANIES_CIK:
        try:
            # Buscar submissions da empresa
            url = f"{SEC_API_URL}/CIK{cik}.json"
            response = requests.get(url, headers=SEC_HEADERS, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                company_name = data.get('name', 'Unknown')
                
                # Procurar por Forms relevantes (S-1, D, 8-K)
                filings = data.get('filings', {}).get('recent', {})
                forms = filings.get('form', [])
                dates = filings.get('filingDate', [])
                
                for i, form in enumerate(forms):
                    if form in ['S-1', 'S-1/A', 'D', '8-K']:  # IPO, VC funding, events
                        filing_date = dates[i] if i < len(dates) else None
                        
                        # Verificar se é recente (últimos 365 dias)
                        if filing_date:
                            filing_dt = datetime.strptime(filing_date, '%Y-%m-%d')
                            if (datetime.now() - filing_dt).days <= 365:
                                funding_data.append({
                                    'company_name': company_name,
                                    'form_type': form,
                                    'filing_date': filing_date,
                                    'cik': cik,
                                    'source': 'sec_edgar'
                                })
                
                print(f"✅ SEC EDGAR: {company_name} - {len([f for f in forms if f in ['S-1', 'D', '8-K']])} filings")
                
            elif response.status_code == 404:
                print(f"⚠️  CIK {cik} não encontrado")
            else:
                print(f"⚠️  SEC EDGAR: {response.status_code} para CIK {cik}")
            
            # Rate limiting (SEC pede max 10 req/sec)
            time.sleep(0.2)
            
        except Exception as e:
            print(f"❌ Erro para CIK {cik}: {str(e)[:50]}")
    
    return funding_data

def save_to_db(funding_data):
    """Salva dados de funding no banco"""
    if not funding_data:
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
    for item in funding_data:
        try:
            # Criar ID único
            funding_id = f"sec-{item['cik']}-{item['form_type']}-{item['filing_date']}"
            
            cur.execute("""
                INSERT INTO sofia.funding_rounds (
                    company_name, round_type, announced_date, country, collected_at
                ) VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT DO NOTHING
            """, (
                item['company_name'],
                f"SEC {item['form_type']}",
                item['filing_date'],
                'USA'
            ))
            saved += 1
        except Exception as e:
            print(f"⚠️  Erro ao salvar: {str(e)[:50]}")
    
    conn.commit()
    conn.close()
    return saved

if __name__ == "__main__":
    print("=" * 70)
    print("🏛️  SEC EDGAR API - IPOs & FUNDING")
    print("=" * 70)
    print("Coletando dados de funding de empresas tech...")
    print("=" * 70)
    
    funding_data = collect_sec_edgar()
    
    if funding_data:
        print(f"\n💾 Salvando {len(funding_data)} registros...")
        saved = save_to_db(funding_data)
        print(f"\n✅ Total salvo: {saved} funding rounds")
    else:
        print("\n⚠️  Nenhum dado coletado")
    
    print("=" * 70)
