#!/usr/bin/env python3
"""
IBGE SIDRA API Collector - Instituto Brasileiro de Geografia e Estatística
Coleta dados oficiais: PIB, inflação, emprego, produção, demografia

API SIDRA: https://apisidra.ibge.gov.br/
Documentação: https://apisidra.ibge.gov.br/home/ajuda
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List

import psycopg2
import requests

# V2: All collector logs go to stderr. Only final JSON goes to stdout.
def _log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

# Database connection — supports DATABASE_URL (set by tracked_runner) or individual vars
_DATABASE_URL = os.getenv("DATABASE_URL")
if _DATABASE_URL:
    import urllib.parse as _urlparse
    _u = _urlparse.urlparse(_DATABASE_URL)
    DB_CONFIG = {
        "host": _u.hostname or "localhost",
        "port": _u.port or 5432,
        "user": _u.username or "sofia",
        "password": _urlparse.unquote(_u.password or ""),
        "database": (_u.path or "/sofia_db").lstrip("/"),
    }
else:
    DB_CONFIG = {
        "host": os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost")),
        "port": int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5432"))),
        "user": os.getenv("POSTGRES_USER", os.getenv("DB_USER", "sofia")),
        "password": os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "")),
        "database": os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "sofia_db")),
    }

# IBGE Agregados (indicators)
# Ref: https://servicodados.ibge.gov.br/api/docs/agregados?versao=3
IBGE_INDICATORS = {
    "1737": {
        "name": "PIB - Produto Interno Bruto",
        "category": "economy",
        "frequency": "trimestral",
        "unit": "R$ milhões",
    },
    "6381": {"name": "IPCA - Inflação (mensal)", "category": "inflation", "frequency": "mensal", "unit": "%"},
    "6784": {
        "name": "PNAD Contínua - Taxa de desemprego",
        "category": "employment",
        "frequency": "trimestral",
        "unit": "%",
    },
    "6385": {"name": "PIM-PF - Produção Industrial", "category": "production", "frequency": "mensal", "unit": "índice"},
    "6786": {"name": "PNAD Contínua - Rendimento médio", "category": "income", "frequency": "trimestral", "unit": "R$"},
    "8419": {
        "name": "Pesquisa Pulso Empresa - Impacto COVID",
        "category": "business",
        "frequency": "quinzenal",
        "unit": "%",
    },
}


def fetch_ibge_sidra(table_code: str, indicator_info: Dict) -> List[Dict]:
    """Fetch data from IBGE SIDRA API

    API SIDRA: https://apisidra.ibge.gov.br/
    Format: /values/t/{tabela}/n{nivel}/{territorios}/p/{periodos}/v/{variaveis}
    """

    # SIDRA API base URL - for actual data extraction
    base_url = "https://apisidra.ibge.gov.br/values"

    # Build URL:
    # t = table code
    # n1 = Brazil level, all = all territories at that level
    # p = periods: last 12 or "all" for all, or specific like "202301"
    # v = variables: "all" or specific variable codes

    # Use "last 12" format for periods (most recent 12 periods)
    url = f"{base_url}/t/{table_code}/n1/all/p/last%2012/v/all"

    try:
        headers = {"Accept": "application/json", "User-Agent": "Sofia-Pulse-Collector/1.0"}
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        # SIDRA returns list with first row being headers
        if data and len(data) > 1:
            print(f"   ✅ Table {table_code}: {len(data)-1} records fetched")
            return data
        else:
            print(f"   ⚠️  Table {table_code}: No data returned")
            return []

    except requests.HTTPError as e:
        # Try with fewer periods
        print(f"   ⚠️  HTTP Error {e.response.status_code}, trying with fewer periods...")
        try:
            alt_url = f"{base_url}/t/{table_code}/n1/all/p/last%206/v/all"
            response = requests.get(alt_url, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 1:
                print(f"   ✅ Table {table_code}: {len(data)-1} records fetched (6 periods)")
                return data
            return []
        except Exception:
            print(f"   ❌ HTTP Error for table {table_code}: {e}")
            return []
    except Exception as e:
        print(f"   ❌ Error fetching table {table_code}: {e}")
        return []


def parse_ibge_sidra_data(table_code: str, indicator_info: Dict, raw_data: List[Dict]) -> List[Dict]:
    """Parse IBGE SIDRA API response into structured records

    SIDRA API returns data as a list where:
    - First element (index 0) contains column headers
    - Remaining elements contain data rows
    """

    records = []

    if not raw_data or len(raw_data) < 2:
        return records

    try:
        # First row is header
        headers = raw_data[0]

        # Find key columns
        list(headers.keys()) if isinstance(headers, dict) else []

        # Data rows start from index 1
        for row in raw_data[1:]:
            if not isinstance(row, dict):
                continue

            # Get value (usually in 'V' key)
            value = row.get("V", "")
            if not value or value in ["...", "-", "X", ""]:
                continue

            try:
                value_float = float(value.replace(",", "."))
            except ValueError:
                continue

            # Get period (usually in 'D2C' or similar key for trimestre/mes)
            period = row.get("D2C", row.get("D3C", row.get("D4C", "")))
            if not period:
                # Try to find any key with period-like value
                for key in row.keys():
                    if key.startswith("D") and "C" in key:
                        period = row.get(key, "")
                        if period:
                            break

            # Get territorial info
            territorial_code = row.get("D1C", "1")  # 1 = Brasil
            territorial_name = row.get("D1N", "Brasil")

            # Get variable name
            variable_name = row.get("D3N", row.get("D2N", indicator_info["name"]))

            records.append(
                {
                    "agregado_id": table_code,
                    "indicator_name": indicator_info["name"],
                    "category": indicator_info["category"],
                    "unit": indicator_info["unit"],
                    "frequency": indicator_info["frequency"],
                    "localidade_id": territorial_code,
                    "localidade_nome": territorial_name,
                    "period": period,
                    "value": value_float,
                    "variable_name": variable_name,
                }
            )

    except Exception as e:
        print(f"   ⚠️  Error parsing data: {e}")

    return records


def save_to_database(conn, records: List[Dict]) -> int:
    """Save IBGE data to PostgreSQL"""

    if not records:
        return 0

    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.ibge_indicators (
            id SERIAL PRIMARY KEY,
            agregado_id VARCHAR(20) NOT NULL,
            indicator_name TEXT NOT NULL,
            category VARCHAR(50),
            unit VARCHAR(50),
            frequency VARCHAR(20),
            localidade_id VARCHAR(20),
            localidade_nome TEXT,
            period VARCHAR(20) NOT NULL,
            value DECIMAL(18, 6),
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(agregado_id, localidade_id, period)
        )
    """
    )

    # Create index
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ibge_agregado_period
        ON sofia.ibge_indicators(agregado_id, period DESC)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ibge_category
        ON sofia.ibge_indicators(category, period DESC)
    """
    )

    inserted = 0

    for record in records:
        try:
            cursor.execute(
                """
                INSERT INTO sofia.ibge_indicators
                (agregado_id, indicator_name, category, unit, frequency,
                 localidade_id, localidade_nome, period, value)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (agregado_id, localidade_id, period)
                DO UPDATE SET value = EXCLUDED.value
            """,
                (
                    record["agregado_id"],
                    record["indicator_name"],
                    record["category"],
                    record["unit"],
                    record["frequency"],
                    record["localidade_id"],
                    record["localidade_nome"],
                    record["period"],
                    record["value"],
                ),
            )

            inserted += 1

        except Exception as e:
            print(f"   ⚠️  Error inserting record: {e}")
            continue

    conn.commit()
    cursor.close()

    return inserted


def main():
    # V2 JSON output contract
    v2_metrics = {
        "status": "ok",
        "source": "ibge-sidra-api",
        "items_read": 0,
        "items_candidate": 0,
        "items_inserted": 0,
        "items_updated": 0,
        "items_ignored_conflict": 0,
        "tables_affected": ["sofia.ibge_indicators"],
        "meta": {}
    }

    try:
        _log("=" * 80)
        _log("📊 IBGE SIDRA API - Instituto Brasileiro de Geografia e Estatística")
        _log("=" * 80)
        _log(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        _log(f"📡 Source: https://apisidra.ibge.gov.br/")
        _log("")

        # Connect to database
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            _log("✅ Database connected")
        except Exception as e:
            raise RuntimeError(f"Database connection failed: {e}")

        total_inserted = 0
        total_updated = 0
        total_read = 0

        _log("📊 Fetching IBGE indicators...")

        for table_code, indicator_info in IBGE_INDICATORS.items():
            _log(f"📈 {indicator_info['name']} (Table: {table_code})")

            raw_data = fetch_ibge_sidra(table_code, indicator_info)
            if raw_data:
                records = parse_ibge_sidra_data(table_code, indicator_info, raw_data)
                total_read += len(records)
                _log(f"   📋 Parsed: {len(records)} records")

                if records:
                    inserted = save_to_database(conn, records)
                    total_inserted += inserted
                    _log(f"   💾 Saved: {inserted} records")

        conn.close()

        v2_metrics["items_read"] = total_read
        v2_metrics["items_candidate"] = total_read
        v2_metrics["items_inserted"] = total_inserted
        v2_metrics["items_updated"] = 0
        v2_metrics["items_ignored_conflict"] = max(0, total_read - total_inserted)

        _log("")
        _log(f"✅ IBGE collection complete. Inserted: {total_inserted} / Read: {total_read}")

    except Exception as e:
        _log(f"❌ Fatal error: {e}")
        v2_metrics["status"] = "fail"
        v2_metrics["meta"]["error"] = str(e)
        # CRITICAL: print JSON before exit so runner can capture status=fail
        print(json.dumps(v2_metrics))
        sys.exit(1)

    # SINGLE STDOUT OUTPUT POINT
    print(json.dumps(v2_metrics))


if __name__ == "__main__":
    main()
