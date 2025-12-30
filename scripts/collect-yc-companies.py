#!/usr/bin/env python3
"""
Coletor: Y Combinator Companies API
URL: https://api.ycombinator.com/ (unofficial GitHub API)
Auth: Nenhuma (100% gratuito)
Features: 5500+ startups YC, batches, funding stages
"""
import json
import os

import psycopg2
import requests
from dotenv import load_dotenv
from shared.funding_helpers import extract_funding_metadata, normalize_round_type
from shared.org_helpers import get_or_create_organization

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
                if company.get("name") and company.get("batch"):
                    # Aceitar todas as empresas (remover filtro de batch)
                    companies.append(
                        {
                            "company_name": company.get("name"),
                            "batch": company.get("batch"),
                            "status": company.get("status", "Active"),
                            "location": company.get("location", "USA"),
                            "description": company.get("description", "")[:500],
                            "website": company.get("website"),
                            "tags": ", ".join(company.get("tags", [])[:5]),
                        }
                    )

            print(f"✅ Y Combinator: {len(companies)} startups recentes coletadas")
        else:
            print(f"⚠️  Y Combinator API: {response.status_code}")

    except Exception as e:
        print(f"❌ Y Combinator erro: {str(e)[:100]}")

    return companies


def save_to_db(companies):
    """Salva empresas YC no banco com schema unificado"""
    if not companies:
        return 0

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
    )
    cur = conn.cursor()

    saved = 0
    for company in companies:
        try:
            # 1. Criar/obter organization_id
            org_id = get_or_create_organization(
                cur,
                company["company_name"],
                company.get("website"),
                company.get("location"),
                "USA",  # YC é majoritariamente USA
                "yc_companies",
            )

            # 2. Normalizar round_type (YC é sempre Accelerator)
            normalized_type = normalize_round_type(f"YC {company['batch']}")

            # 3. Extrair metadata
            metadata = extract_funding_metadata("yc_companies", company)

            # 4. Inserir com schema unificado
            cur.execute(
                """
                INSERT INTO sofia.funding_rounds (
                    company_name, organization_id, round_type, 
                    country, sector, source, metadata, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (company_name, announced_date, source) DO NOTHING
            """,
                (
                    company["company_name"],
                    org_id,
                    normalized_type,
                    "USA",
                    company.get("tags", "")[:200],  # Limitar tamanho
                    "yc_companies",
                    json.dumps(metadata),
                ),
            )
            saved += 1
        except Exception as e:
            print(f"⚠️  Erro ao salvar {company['company_name']}: {str(e)[:100]}")

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
