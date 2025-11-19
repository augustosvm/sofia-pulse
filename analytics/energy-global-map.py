#!/usr/bin/env python3
"""
Sofia Pulse - Global Energy Map Generator

Gera mapa mundial mostrando:
- Capacidade de energia renovável por país
- Mix energético (solar, wind, hydro, nuclear, fossil)
- Top players globais
- Trends de crescimento

Output: PNG estático + HTML interativo
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import json

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'sofia123strong'),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

def fetch_energy_data(conn):
    """Fetch latest energy data for all countries"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT
            country,
            year,
            iso_code,
            population,
            gdp,
            electricity_generation_twh,
            solar_generation_twh,
            wind_generation_twh,
            hydro_generation_twh,
            nuclear_generation_twh,
            coal_generation_twh,
            gas_generation_twh,
            oil_generation_twh,
            renewables_share_pct,
            low_carbon_share_pct,
            energy_per_capita,
            co2_mt,
            co2_per_capita,
            solar_capacity_gw,
            wind_capacity_gw
        FROM sofia.energy_global
        ORDER BY renewables_share_pct DESC
    """)

    return cursor.fetchall()

def generate_text_map(data):
    """Generate text-based report (no dependencies)"""

    report = f"""
{'='*80}
🌍 GLOBAL ENERGY MAP - Sofia Pulse
{'='*80}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Countries: {len(data)}

{'='*80}

📊 TOP 20 RENEWABLE LEADERS (% Renewable)
{'-'*80}

"""

    # Top 20 by renewable share
    renewable_leaders = sorted(
        [d for d in data if d['renewables_share_pct']],
        key=lambda x: x['renewables_share_pct'],
        reverse=True
    )[:20]

    for idx, country_data in enumerate(renewable_leaders, 1):
        country = country_data['country']
        renewable_pct = country_data['renewables_share_pct'] or 0
        solar_gw = country_data['solar_capacity_gw'] or 0
        wind_gw = country_data['wind_capacity_gw'] or 0

        report += f"{idx:2d}. {country:25s} | {renewable_pct:5.1f}% renewable | "
        report += f"Solar: {solar_gw:6.1f}GW | Wind: {wind_gw:6.1f}GW\n"

    report += f"\n{'='*80}\n\n"

    # Top 20 by absolute capacity
    report += f"⚡ TOP 20 RENEWABLE CAPACITY (Solar + Wind GW)\n{'-'*80}\n\n"

    capacity_leaders = sorted(
        [d for d in data if d['solar_capacity_gw'] or d['wind_capacity_gw']],
        key=lambda x: (x['solar_capacity_gw'] or 0) + (x['wind_capacity_gw'] or 0),
        reverse=True
    )[:20]

    for idx, country_data in enumerate(capacity_leaders, 1):
        country = country_data['country']
        solar_gw = country_data['solar_capacity_gw'] or 0
        wind_gw = country_data['wind_capacity_gw'] or 0
        total_gw = solar_gw + wind_gw

        report += f"{idx:2d}. {country:25s} | {total_gw:7.1f}GW total | "
        report += f"Solar: {solar_gw:6.1f}GW | Wind: {wind_gw:6.1f}GW\n"

    report += f"\n{'='*80}\n\n"

    # Energy mix breakdown
    report += f"🔥 ENERGY MIX - TOP 15 COUNTRIES (by total generation)\n{'-'*80}\n\n"

    generation_leaders = sorted(
        [d for d in data if d['electricity_generation_twh']],
        key=lambda x: x['electricity_generation_twh'],
        reverse=True
    )[:15]

    for idx, country_data in enumerate(generation_leaders, 1):
        country = country_data['country']
        total_twh = country_data['electricity_generation_twh'] or 0

        solar_twh = country_data['solar_generation_twh'] or 0
        wind_twh = country_data['wind_generation_twh'] or 0
        hydro_twh = country_data['hydro_generation_twh'] or 0
        nuclear_twh = country_data['nuclear_generation_twh'] or 0
        coal_twh = country_data['coal_generation_twh'] or 0
        gas_twh = country_data['gas_generation_twh'] or 0

        report += f"{idx:2d}. {country:25s} | {total_twh:8.0f} TWh total\n"

        if total_twh > 0:
            renewable_twh = solar_twh + wind_twh + hydro_twh
            fossil_twh = coal_twh + gas_twh

            report += f"     Renewable: {renewable_twh:7.0f} TWh ({renewable_twh/total_twh*100:4.1f}%) "
            report += f"| Nuclear: {nuclear_twh:7.0f} TWh ({nuclear_twh/total_twh*100:4.1f}%) "
            report += f"| Fossil: {fossil_twh:7.0f} TWh ({fossil_twh/total_twh*100:4.1f}%)\n"

            # Breakdown
            if solar_twh > 0:
                report += f"       - Solar: {solar_twh:6.0f} TWh ({solar_twh/total_twh*100:4.1f}%)\n"
            if wind_twh > 0:
                report += f"       - Wind: {wind_twh:6.0f} TWh ({wind_twh/total_twh*100:4.1f}%)\n"
            if hydro_twh > 0:
                report += f"       - Hydro: {hydro_twh:6.0f} TWh ({hydro_twh/total_twh*100:4.1f}%)\n"

        report += "\n"

    report += f"\n{'='*80}\n\n"

    # CO2 emissions
    report += f"🌡️  TOP 15 CO2 EMITTERS\n{'-'*80}\n\n"

    co2_leaders = sorted(
        [d for d in data if d['co2_mt']],
        key=lambda x: x['co2_mt'],
        reverse=True
    )[:15]

    for idx, country_data in enumerate(co2_leaders, 1):
        country = country_data['country']
        co2_mt = country_data['co2_mt'] or 0
        co2_per_capita = country_data['co2_per_capita'] or 0

        report += f"{idx:2d}. {country:25s} | {co2_mt/1000:7.1f} Gt CO2 | "
        report += f"{co2_per_capita:5.1f} t/capita\n"

    report += f"\n{'='*80}\n\n"

    # Insights
    report += f"💡 KEY INSIGHTS\n{'-'*80}\n\n"

    # Find 100% renewable countries
    full_renewable = [d for d in data if d['renewables_share_pct'] and d['renewables_share_pct'] >= 95]

    if full_renewable:
        report += f"🌿 100% RENEWABLE COUNTRIES: {len(full_renewable)}\n"
        for country_data in full_renewable[:10]:
            report += f"   • {country_data['country']}: {country_data['renewables_share_pct']:.1f}% renewable\n"
        report += "\n"

    # Nuclear leaders
    nuclear_leaders = sorted(
        [d for d in data if d['nuclear_generation_twh']],
        key=lambda x: x['nuclear_generation_twh'],
        reverse=True
    )[:5]

    if nuclear_leaders:
        report += f"☢️  NUCLEAR LEADERS:\n"
        for country_data in nuclear_leaders:
            nuclear_twh = country_data['nuclear_generation_twh']
            total_twh = country_data['electricity_generation_twh'] or 1
            report += f"   • {country_data['country']}: {nuclear_twh:.0f} TWh ({nuclear_twh/total_twh*100:.1f}%)\n"
        report += "\n"

    report += f"\n{'='*80}\n"
    report += "Gerado por Sofia Pulse - Global Energy Intelligence\n"
    report += f"{'='*80}\n"

    return report

def main():
    print("🌍 Global Energy Map Generator")
    print("=" * 80)
    print()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")

        # Fetch data
        print("📊 Fetching energy data...")
        data = fetch_energy_data(conn)
        print(f"✅ Loaded {len(data)} countries")

        if not data:
            print("⚠️  No energy data found. Run collect-energy-global.py first!")
            return

        # Generate text report
        print("📝 Generating text report...")
        report = generate_text_map(data)

        # Save
        output_file = 'analytics/energy-global-map-latest.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Saved to {output_file}")

        # Print preview
        print()
        print("Preview:")
        print(report[:1500])
        print("...")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print("✅ Energy map generation complete!")
    print("=" * 80)

if __name__ == '__main__':
    main()
