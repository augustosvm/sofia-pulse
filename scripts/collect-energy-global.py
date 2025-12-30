#!/usr/bin/env python3
"""
Sofia Pulse - Global Energy Data Collector

Coleta dados de:
- Our World in Data (Energy CSV)
- Capacidade por tipo (solar, wind, hydro, nuclear, fossil)
- Consumo de energia
- Emissões por país

FREE DATA SOURCE ✅
"""

import requests
from shared.geo_helpers import normalize_location
import pandas as pd
from shared.geo_helpers import normalize_location
import psycopg2
from shared.geo_helpers import normalize_location
from psycopg2.extras import execute_batch
import os
from shared.geo_helpers import normalize_location
from datetime import datetime

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

OWID_ENERGY_CSV = 'https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv'

def download_energy_data():
    """Download Our World in Data energy dataset"""
    print("📥 Downloading Our World in Data - Energy...")

    try:
        response = requests.get(OWID_ENERGY_CSV, timeout=60)
        response.raise_for_status()

        # Save to temp file
        temp_file = '/tmp/owid-energy.csv'
        with open(temp_file, 'wb') as f:
            f.write(response.content)

        print(f"✅ Downloaded {len(response.content)} bytes")

        # Load as pandas DataFrame
        df = pd.read_csv(temp_file)
        print(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")

        return df

    except Exception as e:
        print(f"❌ Error downloading: {e}")
        return None

def filter_latest_data(df):
    """Filter to get latest year data for each country"""
    print("🔍 Filtering latest data per country...")

    # Remove rows where country is not set
    df = df[df['country'].notna()]

    # Remove aggregates (World, continents, etc)
    exclude_countries = ['World', 'Africa', 'Asia', 'Europe', 'North America',
                        'South America', 'Oceania', 'European Union', 'OECD']
    df = df[~df['country'].isin(exclude_countries)]

    # Get latest year for each country
    df = df.sort_values('year', ascending=False)
    latest = df.groupby('country').first().reset_index()

    print(f"✅ Filtered to {len(latest)} countries with latest data")

    return latest

def safe_int(value, max_value=9223372036854775807):
    """Safely convert to int, handling NaN and out-of-range values"""
    if pd.isna(value):
        return None
    try:
        int_val = int(value)
        # Check if within BIGINT range
        if abs(int_val) > max_value:
            return None
        return int_val
    except (ValueError, OverflowError):
        return None

def safe_float(value, max_value=None):
    """Safely convert to float, handling NaN and max values"""
    if pd.isna(value):
        return None
    try:
        float_val = float(value)
        # Check max value if specified
        if max_value and abs(float_val) > max_value:
            return None
        return float_val
    except (ValueError, TypeError):
        return None

def save_to_database(df, conn):
    """Save energy data to PostgreSQL"""
    print("💾 Saving to database...")

    cursor = conn.cursor()

    # Prepare data for insertion
    insert_data = []

    for _, row in df.iterrows():
        insert_data.append((
            row['country'],
            safe_int(row.get('year')),
            row.get('iso_code', None),
            safe_int(row.get('population')),
            safe_int(row.get('gdp')),

            # Electricity generation by source (TWh) - DECIMAL(10,2) max 99999999.99
            safe_float(row.get('electricity_generation'), max_value=99999999.99),
            safe_float(row.get('solar_electricity'), max_value=99999999.99),
            safe_float(row.get('wind_electricity'), max_value=99999999.99),
            safe_float(row.get('hydro_electricity'), max_value=99999999.99),
            safe_float(row.get('nuclear_electricity'), max_value=99999999.99),
            safe_float(row.get('coal_electricity'), max_value=99999999.99),
            safe_float(row.get('gas_electricity'), max_value=99999999.99),
            safe_float(row.get('oil_electricity'), max_value=99999999.99),

            # Renewable share - DECIMAL(5,2) max 999.99 (percentage)
            safe_float(row.get('renewables_electricity'), max_value=999.99),
            safe_float(row.get('low_carbon_electricity'), max_value=999.99),

            # Consumption - DECIMAL(10,2) and DECIMAL(10,4)
            safe_float(row.get('energy_per_capita'), max_value=99999999.99),
            safe_float(row.get('energy_per_gdp'), max_value=999999.9999),

            # Emissions - DECIMAL(12,2) and DECIMAL(10,2)
            safe_float(row.get('co2'), max_value=9999999999.99),
            safe_float(row.get('co2_per_capita'), max_value=99999999.99),

            # Capacity (GW) - DECIMAL(10,2) - NOT AVAILABLE in OWID dataset
            None,  # solar_capacity_gw - not in dataset
            None,  # wind_capacity_gw - not in dataset
        ))

    # Insert
    insert_query = """
        INSERT INTO sofia.energy_global (
            country, year, iso_code, population, gdp,
            electricity_generation_twh,
            solar_generation_twh, wind_generation_twh, hydro_generation_twh,
            nuclear_generation_twh, coal_generation_twh, gas_generation_twh,
            oil_generation_twh,
            renewables_share_pct, low_carbon_share_pct,
            energy_per_capita, energy_per_gdp,
            co2_mt, co2_per_capita,
            solar_capacity_gw, wind_capacity_gw
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (country, year) DO UPDATE SET
            electricity_generation_twh = EXCLUDED.electricity_generation_twh,
            solar_generation_twh = EXCLUDED.solar_generation_twh,
            wind_generation_twh = EXCLUDED.wind_generation_twh,
            updated_at = CURRENT_TIMESTAMP
    """

    try:
        execute_batch(cursor, insert_query, insert_data, page_size=100)
        conn.commit()
        print(f"✅ Inserted/updated {len(insert_data)} countries")

    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        raise

    finally:
        cursor.close()

def main():
    print("=" * 80)
    print("🌍 GLOBAL ENERGY DATA COLLECTOR")
    print("=" * 80)
    print()

    # Download data
    df = download_energy_data()
    if df is None:
        print("❌ Failed to download data")
        return

    # Filter to latest
    latest_df = filter_latest_data(df)

    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")

        # Save
        save_to_database(latest_df, conn)

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return

    print()
    print("=" * 80)
    print("✅ GLOBAL ENERGY DATA COLLECTION COMPLETE")
    print("=" * 80)
    print()

    # Print preview if columns exist
    try:
        # First, list all capacity-related columns
        print("📊 Available capacity columns in OWID dataset:")
        capacity_cols = [col for col in latest_df.columns if 'capacity' in col.lower()]
        if capacity_cols:
            print(f"   {', '.join(capacity_cols)}")
        else:
            print("   ⚠️  No capacity columns found!")

        print()
        print("📊 Available columns (first 20):")
        print(f"   {', '.join(latest_df.columns[:20])}")
        print()

        if 'solar_capacity' in latest_df.columns and 'wind_capacity' in latest_df.columns:
            print("📊 Top 10 renewable capacity (solar + wind GW):")
            latest_df['renewable_capacity'] = (
                latest_df['solar_capacity'].fillna(0) +
                latest_df['wind_capacity'].fillna(0)
            )
            top10 = latest_df.nlargest(10, 'renewable_capacity')[['country', 'solar_capacity', 'wind_capacity', 'renewable_capacity']]
            print(top10.to_string(index=False))
        else:
            print("⚠️  solar_capacity and wind_capacity columns not found in dataset")
            print("   Using generation data as fallback (TWh instead of GW)")

            # Show solar/wind generation instead
            if 'solar_electricity' in latest_df.columns and 'wind_electricity' in latest_df.columns:
                print()
                print("📊 Top 10 renewable generation (solar + wind TWh):")
                latest_df['renewable_gen'] = (
                    latest_df['solar_electricity'].fillna(0) +
                    latest_df['wind_electricity'].fillna(0)
                )
                top10 = latest_df.nlargest(10, 'renewable_gen')[['country', 'solar_electricity', 'wind_electricity', 'renewable_gen']]
                print(top10.to_string(index=False))
    except Exception as e:
        print(f"⚠️  Preview skipped: {e}")

    print()

if __name__ == '__main__':
    main()
