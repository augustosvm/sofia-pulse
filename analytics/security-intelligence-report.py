#!/usr/bin/env python3
"""
================================================================================
SECURITY INTELLIGENCE REPORT
================================================================================
Analyzes security data for:
- Brazil (27 states + 30 major cities)
- World (Top 10 Americas, Europe, Asia)

Metrics:
- Homicide rates
- Crime indices
- Safety scores
- Year-over-year trends

Use Cases:
- Expansion location analysis
- Risk assessment for operations
- Employee safety planning
================================================================================
"""

import os
import sys
import psycopg2
from datetime import datetime

def get_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        dbname=os.getenv('POSTGRES_DB', 'sofia'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', '')
    )

def main():
    print("=" * 80)
    print("🔒 SECURITY INTELLIGENCE REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    conn = get_connection()
    cur = conn.cursor()

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("🔒 SECURITY INTELLIGENCE REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # =========================================================================
    # 1. BRAZIL - STATE SECURITY
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🇧🇷 1. BRAZIL - SECURITY BY STATE")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.brazil_security_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # Safest states (lowest homicide rate)
            cur.execute("""
                SELECT region_name, region_code, indicator, value, year
                FROM sofia.brazil_security_data
                WHERE LOWER(indicator) LIKE '%homic%' OR LOWER(indicator) LIKE '%murder%'
                  AND value IS NOT NULL
                ORDER BY value ASC
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🏆 SAFEST BRAZILIAN STATES (Lowest Homicide Rate):")
                report_lines.append("-" * 60)
                for i, (region, code, indicator, value, year) in enumerate(rows, 1):
                    report_lines.append(f"  {i:2}. {region:<25} ({code}) {value:>8.2f} ({year})")
                report_lines.append("")

            # Most dangerous states
            cur.execute("""
                SELECT region_name, region_code, indicator, value, year
                FROM sofia.brazil_security_data
                WHERE (LOWER(indicator) LIKE '%homic%' OR LOWER(indicator) LIKE '%murder%')
                  AND value IS NOT NULL
                ORDER BY value DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("⚠️ HIGHEST CRIME BRAZILIAN STATES:")
                report_lines.append("-" * 60)
                for i, (region, code, indicator, value, year) in enumerate(rows, 1):
                    report_lines.append(f"  {i:2}. {region:<25} ({code}) {value:>8.2f} ({year})")
                report_lines.append("")

            # All indicators available
            cur.execute("""
                SELECT DISTINCT indicator, COUNT(*) as records
                FROM sofia.brazil_security_data
                GROUP BY indicator
                ORDER BY records DESC
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 SECURITY INDICATORS AVAILABLE:")
                report_lines.append("-" * 60)
                for indicator, records in rows:
                    report_lines.append(f"  • {indicator}: {records} records")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ Brazil state data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 2. BRAZIL - CITY SECURITY
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🏙️ 2. BRAZIL - SECURITY BY CITY")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.brazil_security_cities")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # Safest cities
            cur.execute("""
                SELECT city, state, homicide_rate, year
                FROM sofia.brazil_security_cities
                WHERE homicide_rate IS NOT NULL
                ORDER BY homicide_rate ASC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🏆 SAFEST BRAZILIAN CITIES:")
                report_lines.append("-" * 60)
                for i, (city, state, homicide_rate, year) in enumerate(rows, 1):
                    report_lines.append(f"  {i:2}. {city:<20} ({state}) Homicide rate: {homicide_rate:>8.2f} ({year})")
                report_lines.append("")

            # Most dangerous cities
            cur.execute("""
                SELECT city, state, homicide_rate, year
                FROM sofia.brazil_security_cities
                WHERE homicide_rate IS NOT NULL
                ORDER BY homicide_rate DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("⚠️ HIGHEST CRIME BRAZILIAN CITIES:")
                report_lines.append("-" * 60)
                for i, (city, state, homicide_rate, year) in enumerate(rows, 1):
                    report_lines.append(f"  {i:2}. {city:<20} ({state}) Homicide rate: {homicide_rate:>8.2f} ({year})")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ Brazil cities data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 3. WORLD SECURITY - BY REGION
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🌍 3. WORLD SECURITY - TOP COUNTRIES BY REGION")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.world_security_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # By region - safest (only latest year per country, avg indicators)
            for region in ['Americas', 'Europe', 'Asia']:
                cur.execute("""
                    SELECT DISTINCT ON (w.country_name) w.country_name, w.region, AVG(w.value) as avg_value, w.year
                    FROM sofia.world_security_data w
                    INNER JOIN (
                        SELECT country_name, MAX(year) as max_year
                        FROM sofia.world_security_data
                        WHERE LOWER(region) LIKE %s AND value IS NOT NULL
                        GROUP BY country_name
                    ) latest ON w.country_name = latest.country_name AND w.year = latest.max_year
                    WHERE LOWER(w.region) LIKE %s AND w.value IS NOT NULL
                    GROUP BY w.country_name, w.region, w.year
                    ORDER BY w.country_name, avg_value ASC
                    LIMIT 10
                """, (f'%{region.lower()}%', f'%{region.lower()}%'))
                rows = cur.fetchall()
                if rows:
                    report_lines.append(f"🏆 SAFEST IN {region.upper()}:")
                    report_lines.append("-" * 60)
                    for i, (country_name, reg, value, year) in enumerate(rows, 1):
                        report_lines.append(f"  {i:2}. {country_name:<25} {float(value):>8.2f} ({year})")
                    report_lines.append("")

            # Global ranking - safest (only latest year per country, avg indicators)
            cur.execute("""
                SELECT DISTINCT ON (w.country_name) w.country_name, w.region, AVG(w.value) as avg_value
                FROM sofia.world_security_data w
                INNER JOIN (
                    SELECT country_name, MAX(year) as max_year
                    FROM sofia.world_security_data
                    WHERE value IS NOT NULL
                    GROUP BY country_name
                ) latest ON w.country_name = latest.country_name AND w.year = latest.max_year
                WHERE w.value IS NOT NULL
                GROUP BY w.country_name, w.region
                ORDER BY w.country_name, avg_value ASC
                LIMIT 20
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🌍 GLOBAL RANKING - SAFEST COUNTRIES:")
                report_lines.append("-" * 60)
                for i, (country_name, region, value) in enumerate(rows, 1):
                    report_lines.append(f"  {i:2}. {country_name:<25} ({region:<10}) {float(value):>8.2f}")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ World security data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 4. SECURITY RECOMMENDATIONS FOR EXPANSION
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("💡 SECURITY RECOMMENDATIONS FOR EXPANSION")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("AMERICAS:")
    report_lines.append("  ✅ RECOMMENDED: Canada, Chile, Uruguay, Costa Rica")
    report_lines.append("  ⚠️ CAUTION: Venezuela, Honduras, El Salvador, Brazil (varies by state)")
    report_lines.append("")
    report_lines.append("EUROPE:")
    report_lines.append("  ✅ RECOMMENDED: Iceland, Switzerland, Norway, Denmark, Portugal")
    report_lines.append("  ⚠️ CAUTION: Ukraine (conflict), some Eastern European countries")
    report_lines.append("")
    report_lines.append("ASIA:")
    report_lines.append("  ✅ RECOMMENDED: Japan, Singapore, South Korea, Taiwan")
    report_lines.append("  ⚠️ CAUTION: Philippines, Papua New Guinea, some SE Asian countries")
    report_lines.append("")
    report_lines.append("BRAZIL SPECIFIC:")
    report_lines.append("  ✅ SAFEST STATES: Santa Catarina, São Paulo, Minas Gerais")
    report_lines.append("  ✅ SAFEST CITIES: Florianópolis, Curitiba, Belo Horizonte")
    report_lines.append("  ⚠️ HIGHER RISK: Northern states (Pará, Amazonas), some Northeast states")
    report_lines.append("")

    # =========================================================================
    # METHODOLOGY
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("📚 METHODOLOGY")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("Metrics used:")
    report_lines.append("• Intentional homicide rate per 100,000")
    report_lines.append("• Crime index (composite)")
    report_lines.append("• Safety index (inverse of crime)")
    report_lines.append("• Property crime rates")
    report_lines.append("• Violent crime rates")
    report_lines.append("")
    report_lines.append("Data Sources:")
    report_lines.append("• World Bank Development Indicators")
    report_lines.append("• UNODC Global Study on Homicide")
    report_lines.append("• IBGE/IPEA Brazil Crime Statistics")
    report_lines.append("• Numbeo Safety Index")
    report_lines.append("")

    cur.close()
    conn.close()

    # Save report
    report_text = "\n".join(report_lines)
    print(report_text)

    output_path = "analytics/security-intelligence-report.txt"
    with open(output_path, 'w') as f:
        f.write(report_text)
    print(f"\n✅ Report saved to: {output_path}")

if __name__ == "__main__":
    main()
