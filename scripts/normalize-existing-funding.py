#!/usr/bin/env python3
"""
Normaliza dados existentes em funding_rounds:
1. Adiciona organization_id
2. Padroniza round_type
3. Adiciona source
4. Adiciona metadata
"""

import os

import psycopg2
from dotenv import load_dotenv
from shared.funding_helpers import normalize_round_type
from shared.org_helpers import get_or_create_organization

load_dotenv()


def normalize_funding_data():
    """Normaliza todos os dados existentes em funding_rounds"""

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
    )
    cur = conn.cursor()

    print("=" * 70)
    print("🔧 NORMALIZAÇÃO DE DADOS DE FUNDING")
    print("=" * 70)

    # 1. Adicionar source baseado em round_type
    print("\n1️⃣  Adicionando 'source' baseado em round_type...")
    cur.execute(
        """
        UPDATE sofia.funding_rounds
        SET source = CASE
            WHEN round_type LIKE 'SEC%' THEN 'sec_edgar'
            WHEN round_type LIKE 'YC%' THEN 'yc_companies'
            WHEN round_type LIKE '%Crunchbase%' THEN 'crunchbase'
            ELSE 'unknown'
        END
        WHERE source IS NULL
    """
    )
    updated_source = cur.rowcount
    print(f"   ✅ {updated_source} registros atualizados com source")

    # 2. Normalizar round_type
    print("\n2️⃣  Normalizando round_type...")
    cur.execute("SELECT id, round_type FROM sofia.funding_rounds WHERE round_type IS NOT NULL")
    rows = cur.fetchall()

    normalized_count = 0
    for row in rows:
        funding_id, round_type = row
        normalized = normalize_round_type(round_type)

        if normalized != round_type:
            cur.execute("UPDATE sofia.funding_rounds SET round_type = %s WHERE id = %s", (normalized, funding_id))
            normalized_count += 1

    print(f"   ✅ {normalized_count} registros com round_type normalizado")

    # 3. Adicionar organization_id
    print("\n3️⃣  Adicionando organization_id...")
    cur.execute(
        """
        SELECT id, company_name, country, source 
        FROM sofia.funding_rounds 
        WHERE organization_id IS NULL 
        AND company_name IS NOT NULL
        LIMIT 1000
    """
    )

    rows = cur.fetchall()
    org_added = 0

    for row in rows:
        funding_id, company_name, country, source = row

        try:
            org_id = get_or_create_organization(
                cur,
                company_name,
                None,  # website
                None,  # location
                country or "USA",
                source or "funding_normalization",
            )

            if org_id:
                cur.execute("UPDATE sofia.funding_rounds SET organization_id = %s WHERE id = %s", (org_id, funding_id))
                org_added += 1

                if org_added % 100 == 0:
                    print(f"   📊 Processados: {org_added}/{len(rows)}...")
                    conn.commit()  # Commit parcial

        except Exception as e:
            print(f"   ⚠️  Erro em '{company_name}': {str(e)[:50]}")

    print(f"   ✅ {org_added} registros com organization_id adicionado")

    # 4. Estatísticas finais
    print("\n📊 ESTATÍSTICAS FINAIS:")

    cur.execute("SELECT COUNT(*) FROM sofia.funding_rounds")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM sofia.funding_rounds WHERE organization_id IS NOT NULL")
    with_org = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM sofia.funding_rounds WHERE source IS NOT NULL")
    with_source = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT round_type) FROM sofia.funding_rounds")
    unique_types = cur.fetchone()[0]

    print(f"   Total de registros: {total}")
    print(f"   Com organization_id: {with_org} ({100*with_org/total:.1f}%)")
    print(f"   Com source: {with_source} ({100*with_source/total:.1f}%)")
    print(f"   Tipos de round únicos: {unique_types}")

    # 5. Top round types
    print("\n📈 TOP 10 ROUND TYPES:")
    cur.execute(
        """
        SELECT round_type, COUNT(*) as count
        FROM sofia.funding_rounds
        GROUP BY round_type
        ORDER BY count DESC
        LIMIT 10
    """
    )

    for row in cur.fetchall():
        round_type, count = row
        print(f"   {round_type}: {count}")

    conn.commit()
    conn.close()

    print("\n" + "=" * 70)
    print("✅ NORMALIZAÇÃO CONCLUÍDA!")
    print("=" * 70)


if __name__ == "__main__":
    normalize_funding_data()
