#!/usr/bin/env python3
"""
HDX (Humanitarian Data Exchange) Collector
Coleta dados humanitários: refugiados, crises, deslocados, emergências

API: https://data.humdata.org/
Organizations: OCHA, UNHCR, MSF, WFP
"""

import os
import sys
from datetime import datetime
from typing import Dict, List

import psycopg2
import requests

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost")),
    "port": int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5432"))),
    "user": os.getenv("POSTGRES_USER", os.getenv("DB_USER", "sofia")),
    "password": os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "")),
    "database": os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "sofia_db")),
}

# HDX Organizations to search
HDX_ORGANIZATIONS = [
    "unhcr",  # UN Refugee Agency
    "ocha",  # Office for Coordination of Humanitarian Affairs
    "wfp",  # World Food Programme
    "msf",  # Médecins Sans Frontières
    "unicef",  # UNICEF
    "icrc",  # International Committee of Red Cross
    "iom",  # International Organization for Migration
]

# Key dataset tags to search
HDX_TAGS = [
    "refugees",
    "internally-displaced-persons",
    "humanitarian-needs-overview",
    "food-security",
    "conflict",
    "migration",
    "health",
]


def fetch_hdx_datasets(organization: str = None, tag: str = None, limit: int = 50) -> List[Dict]:
    """Fetch datasets from HDX CKAN API"""

    base_url = "https://data.humdata.org/api/3/action"

    # Search for datasets
    if organization:
        url = f"{base_url}/package_search"
        params = {"fq": f"organization:{organization}", "rows": limit, "sort": "metadata_modified desc"}
    elif tag:
        url = f"{base_url}/package_search"
        params = {"fq": f"tags:{tag}", "rows": limit, "sort": "metadata_modified desc"}
    else:
        url = f"{base_url}/package_search"
        params = {"rows": limit, "sort": "metadata_modified desc"}

    try:
        headers = {"Accept": "application/json", "User-Agent": "Sofia-Pulse-Collector/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        if data.get("success") and data.get("result", {}).get("results"):
            return data["result"]["results"]
        return []

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def save_to_database(conn, datasets: List[Dict], source: str) -> int:
    """Save HDX dataset metadata to PostgreSQL"""

    if not datasets:
        return 0

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sofia.hdx_humanitarian_data (
            country_id INTEGER REFERENCES sofia.countries(id),
            id SERIAL PRIMARY KEY,
            dataset_id VARCHAR(100) NOT NULL,
            dataset_name TEXT,
            title TEXT,
            organization VARCHAR(100),
            source VARCHAR(100),
            tags TEXT[],
            country_codes TEXT[],
            date_created TIMESTAMP,
            date_modified TIMESTAMP,
            num_resources INTEGER,
            total_downloads INTEGER,
            methodology TEXT,
            notes TEXT,
            url TEXT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(dataset_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_hdx_organization
        ON sofia.hdx_humanitarian_data(organization)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_hdx_date
        ON sofia.hdx_humanitarian_data(date_modified DESC)
    """
    )

    inserted = 0

    for dataset in datasets:
        try:
            # Extract tags
            tags = [t.get("name", "") for t in dataset.get("tags", [])]

            # Extract country codes
            countries = []
            for group in dataset.get("groups", []):
                if group.get("name"):
                    countries.append(group.get("name").upper()[:3])

            cursor.execute(
                """
                INSERT INTO sofia.hdx_humanitarian_data (dataset_id, dataset_name, title, organization, source, tags, country_codes,
                 date_created, date_modified, num_resources, total_downloads, methodology, notes, url, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (dataset_id)
                DO UPDATE SET
                    date_modified = EXCLUDED.date_modified,
                    num_resources = EXCLUDED.num_resources,
                    total_downloads = EXCLUDED.total_downloads
            """,
                (
                    dataset.get("id", "", country_id=EXCLUDED.country_id),
                    dataset.get("name", ""),
                    dataset.get("title", ""),
                    dataset.get("organization", {}).get("name", source),
                    source,
                    tags,
                    countries,
                    dataset.get("metadata_created"),
                    dataset.get("metadata_modified"),
                    len(dataset.get("resources", [])),
                    dataset.get("total_res_downloads", 0),
                    dataset.get("methodology", ""),
                    dataset.get("notes", "")[:500] if dataset.get("notes") else "",
                    f"https://data.humdata.org/dataset/{dataset.get('name', '')}",
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
    print("📊 HDX - Humanitarian Data Exchange")
    print("=" * 80)
    print("")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Source: https://data.humdata.org/")
    print("")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connected")
        print("")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    total_records = 0

    print("📊 Fetching humanitarian datasets...")
    print("")

    # Fetch by organization
    print("🏢 By Organization:")
    for org in HDX_ORGANIZATIONS:
        print(f"   📈 {org.upper()}...")

        datasets = fetch_hdx_datasets(organization=org, limit=30)

        if datasets:
            print(f"      ✅ Found: {len(datasets)} datasets")
            inserted = save_to_database(conn, datasets, org.upper())
            total_records += inserted
            print(f"      💾 Saved: {inserted} datasets")
        else:
            print(f"      ⚠️  No datasets")

    print("")
    print("🏷️  By Tag:")
    for tag in HDX_TAGS:
        print(f"   📈 {tag}...")

        datasets = fetch_hdx_datasets(tag=tag, limit=20)

        if datasets:
            print(f"      ✅ Found: {len(datasets)} datasets")
            inserted = save_to_database(conn, datasets, f"tag:{tag}")
            total_records += inserted
            print(f"      💾 Saved: {inserted} datasets")
        else:
            print(f"      ⚠️  No datasets")

    conn.close()

    print("")
    print("=" * 80)
    print("✅ HDX HUMANITARIAN COLLECTION COMPLETE")
    print("=" * 80)
    print(f"💾 Total dataset records: {total_records}")
    print("")
    print("💡 Organizations covered:")
    print("  • UNHCR (Refugees)")
    print("  • OCHA (Humanitarian coordination)")
    print("  • WFP (Food assistance)")
    print("  • MSF (Medical humanitarian)")
    print("  • ICRC (Red Cross)")


if __name__ == "__main__":
    main()
