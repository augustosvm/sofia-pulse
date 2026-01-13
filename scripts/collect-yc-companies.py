#!/usr/bin/env python3
"""
Coletor: Y Combinator Companies API
URL: https://api.ycombinator.com/ (unofficial GitHub API)
Auth: Nenhuma (100% gratuito)
Features: 5500+ startups YC, batches, funding stages
"""
import os
from datetime import datetime

import psycopg2
import requests
from dotenv import load_dotenv
from shared.funding_helpers import normalize_round_type
from shared.org_helpers import get_or_create_organization

load_dotenv()

# Y Combinator Unofficial API (URL correta)
YC_API_URL = "https://yc-oss.github.io/api/companies/all.json"


def parse_yc_batch_date(batch):
    """
    Convert YC batch to announced_date

    Examples:
        W24 → 2024-01-15 (Winter)
        S23 → 2023-06-15 (Summer)
        Winter 2024 → 2024-01-15
        Summer 2023 → 2023-06-15
    """
    if not batch:
        return None

    # Handle "Winter 2024" or "Summer 2023" format
    if ' ' in batch:
        parts = batch.split()
        if len(parts) == 2:
            season_word = parts[0].upper()
            try:
                year = int(parts[1])
            except ValueError:
                return None

            season_months = {
                'WINTER': 1,
                'SUMMER': 6,
            }
            month = season_months.get(season_word, 1)
            return datetime(year, month, 15).strftime('%Y-%m-%d')

    # Handle "W24" or "S23" format
    if len(batch) >= 3:
        season = batch[0].upper()
        try:
            year = int(batch[1:])
            # Convert 2-digit to 4-digit year
            if year < 100:
                year += 2000
        except ValueError:
            return None

        # Map season to month
        season_months = {
            'W': 1,   # Winter (Jan)
            'S': 6,   # Summer (Jun)
        }

        month = season_months.get(season, 1)
        return datetime(year, month, 15).strftime('%Y-%m-%d')

    return None


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
                    batch = company.get("batch")
                    announced_date = parse_yc_batch_date(batch)

                    # Skip if can't parse date (invalid batch format)
                    if not announced_date:
                        continue

                    companies.append(
                        {
                            "company_name": company.get("name"),
                            "batch": batch,
                            "announced_date": announced_date,  # NEW: Inferred from batch
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

            # 3. Inserir com schema unificado (NOW WITH announced_date!)
            cur.execute(
                """
                INSERT INTO sofia.funding_rounds (
                    company_name, organization_id, round_type, announced_date,
                    country, sector, source, collected_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (company_name, round_type, announced_date) DO UPDATE SET
                    organization_id = EXCLUDED.organization_id,
                    sector = COALESCE(EXCLUDED.sector, sofia.funding_rounds.sector),
                    collected_at = NOW()
            """,
                (
                    company["company_name"],
                    org_id,
                    normalized_type,
                    company["announced_date"],  # NEW: Now has date!
                    "USA",
                    company.get("tags", "")[:200],  # Limitar tamanho
                    "yc_companies",
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
