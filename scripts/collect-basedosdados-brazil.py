#!/usr/bin/env python3

"""
Base dos Dados Collector - Brazilian Open Data Platform

Coleta dados de indicadores industriais e econômicos brasileiros via basedosdados.org
Usa o pacote basedosdados para acessar dados do BigQuery (1TB grátis/mês)

Datasets incluídos:
- FIRJAN IFDM (Índice de Desenvolvimento Municipal)
- FIRJAN IFGF (Índice de Gestão Fiscal)
- PIB Municipal/Estadual (IBGE)
- Indicadores Socioeconômicos

Instalação: pip install basedosdados pandas

Documentação: https://basedosdados.github.io/sdk/
"""

import os
import sys
from datetime import datetime

import psycopg2

# Check if basedosdados is installed
try:
    import basedosdados as bd
    import pandas as pd

    BD_AVAILABLE = True
except ImportError:
    BD_AVAILABLE = False
    print("⚠️  basedosdados not installed. Run: pip install basedosdados pandas")

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost")),
    "port": int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5432"))),
    "user": os.getenv("POSTGRES_USER", os.getenv("DB_USER", "sofia")),
    "password": os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "")),
    "database": os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "sofia_db")),
}

# BigQuery billing project (required for basedosdados)
# User needs to create a Google Cloud project for billing
BILLING_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("BIGQUERY_PROJECT", ""))

# Datasets to collect
# Format: (dataset_id, table_id, description, category)
DATASETS = [
    # FIRJAN Indices
    ("br_firjan_ifdm", "municipio", "FIRJAN - Índice de Desenvolvimento Municipal", "development"),
    ("br_firjan_ifgf", "municipio", "FIRJAN - Índice de Gestão Fiscal", "fiscal"),
    # IBGE Economic Data
    ("br_ibge_pib", "municipio", "IBGE - PIB Municipal", "economy"),
    ("br_ibge_pib", "uf", "IBGE - PIB Estadual", "economy"),
    # Other Economic Indicators
    ("br_ibge_ipca", "mes_brasil", "IBGE - IPCA (Inflação)", "inflation"),
    ("br_bcb_sgs", "serie_tempo", "BACEN - Séries Temporais", "macro"),
]


def check_bigquery_setup():
    """Check if BigQuery is properly configured"""
    if not BILLING_PROJECT:
        print(
            """
❌ BigQuery billing project not configured!

To use basedosdados, you need:
1. Create a Google Cloud project (free tier available)
2. Enable BigQuery API
3. Set environment variable:
   export GOOGLE_CLOUD_PROJECT="your-project-id"

More info: https://basedosdados.github.io/sdk/
"""
        )
        return False
    return True


def fetch_dataset(dataset_id: str, table_id: str, limit: int = 10000) -> pd.DataFrame:
    """Fetch dataset from Base dos Dados via BigQuery"""

    try:
        # Use SQL query to limit data and get recent records
        query = f"""
        SELECT *
        FROM `basedosdados.{dataset_id}.{table_id}`
        ORDER BY ano DESC
        LIMIT {limit}
        """

        df = bd.read_sql(query, billing_project_id=BILLING_PROJECT)
        return df

    except Exception as e:
        print(f"   ❌ Error fetching {dataset_id}.{table_id}: {e}")
        return pd.DataFrame()


def save_to_database(conn, df: pd.DataFrame, dataset_id: str, table_id: str, category: str) -> int:
    """Save data to PostgreSQL"""

    if df.empty:
        return 0

    cursor = conn.cursor()

    # Create table for basedosdados data
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.basedosdados_indicators (
            id SERIAL PRIMARY KEY,
            dataset_id VARCHAR(100) NOT NULL,
            table_id VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            ano INTEGER,
            mes INTEGER,
            uf VARCHAR(2),
            id_municipio VARCHAR(7),
            indicator_name VARCHAR(200),
            indicator_value DECIMAL(18, 6),
            raw_data JSONB,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(dataset_id, table_id, ano, mes, uf, id_municipio, indicator_name)
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_basedosdados_dataset_ano
        ON sofia.basedosdados_indicators(dataset_id, ano DESC)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_basedosdados_category
        ON sofia.basedosdados_indicators(category, ano DESC)
    """
    )

    inserted = 0

    # Process DataFrame rows
    for _, row in df.iterrows():
        try:
            # Extract common fields
            ano = row.get("ano", None)
            mes = row.get("mes", None)
            uf = row.get("sigla_uf", row.get("uf", None))
            id_municipio = row.get("id_municipio", None)

            # For multi-indicator datasets, iterate through numeric columns
            for col in df.select_dtypes(include=["float64", "int64"]).columns:
                if col in ["ano", "mes", "id_municipio"]:
                    continue

                value = row.get(col)
                if pd.isna(value):
                    continue

                cursor.execute(
                    """
                    INSERT INTO sofia.basedosdados_indicators
                    (dataset_id, table_id, category, ano, mes, uf, id_municipio,
                     indicator_name, indicator_value, raw_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (dataset_id, table_id, ano, mes, uf, id_municipio, indicator_name)
                    DO UPDATE SET indicator_value = EXCLUDED.indicator_value
                """,
                    (
                        dataset_id,
                        table_id,
                        category,
                        int(ano) if ano else None,
                        int(mes) if mes else None,
                        str(uf) if uf else None,
                        str(id_municipio) if id_municipio else None,
                        col,
                        float(value),
                        "{}",  # Empty JSON for now
                    ),
                )

                inserted += 1

        except Exception:
            continue

    conn.commit()
    cursor.close()

    return inserted


def main():
    print("=" * 80)
    print("📊 BASE DOS DADOS - Brazilian Open Data Platform")
    print("=" * 80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://basedosdados.org/")
    print("")

    if not BD_AVAILABLE:
        print("❌ basedosdados package not installed")
        print("   Run: pip install basedosdados pandas")
        sys.exit(1)

    if not check_bigquery_setup():
        print("⚠️  Running in demo mode (no BigQuery configured)")
        print("")
        print("To enable data collection:")
        print("1. Create Google Cloud project")
        print("2. Enable BigQuery API")
        print("3. export GOOGLE_CLOUD_PROJECT='your-project-id'")
        print("")

        # Print available datasets
        print("📋 Available datasets:")
        for dataset_id, table_id, description, category in DATASETS:
            print(f"   • {dataset_id}.{table_id}")
            print(f"     {description} [{category}]")

        sys.exit(0)

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
        print("")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    print("📊 Fetching Base dos Dados datasets...")
    print("")

    for dataset_id, table_id, description, category in DATASETS:
        print(f"📈 {description}")
        print(f"   Dataset: {dataset_id}.{table_id}")

        # Fetch data
        df = fetch_dataset(dataset_id, table_id, limit=5000)

        if not df.empty:
            print(f"   ✅ Fetched: {len(df)} rows")

            # Save to database
            inserted = save_to_database(conn, df, dataset_id, table_id, category)
            total_records += inserted
            print(f"   💾 Saved: {inserted} records")
        else:
            print(f"   ⚠️  No data returned")

        print("")

    conn.close()

    print("=" * 80)
    print("✅ BASE DOS DADOS COLLECTION COMPLETE")
    print("=" * 80)
    print("")
    print(f"📊 Total datasets: {len(DATASETS)}")
    print(f"💾 Total records: {total_records}")
    print("")
    print("Datasets collected:")
    for dataset_id, table_id, description, category in DATASETS:
        print(f"  • {description} ({category})")
    print("")
    print("💡 Use cases:")
    print("  • IFDM: Municipal development index for all cities")
    print("  • IFGF: Fiscal health of municipalities")
    print("  • PIB: GDP by municipality and state")
    print("  • Correlate with tech funding and expansion decisions")


if __name__ == "__main__":
    main()
