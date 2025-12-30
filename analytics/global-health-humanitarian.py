#!/usr/bin/env python3
"""
================================================================================
GLOBAL HEALTH & HUMANITARIAN INTELLIGENCE
================================================================================
Data Sources:
- WHO (World Health Organization)
- UNICEF (Children's Fund)
- HDX (Humanitarian Data Exchange)

Indicators:
- Disease burden, life expectancy, healthcare access
- Child mortality, nutrition, education
- Humanitarian crises, refugee data, food security
================================================================================
"""

import os
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
    print("🏥 GLOBAL HEALTH & HUMANITARIAN INTELLIGENCE")
    print("=" * 80)

    conn = get_connection()
    cur = conn.cursor()

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("🏥 GLOBAL HEALTH & HUMANITARIAN INTELLIGENCE")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # =========================================================================
    # 1. WHO - World Health Organization
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🌍 1. WHO - WORLD HEALTH ORGANIZATION")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.who_health_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # Life expectancy by country
            cur.execute("""
                SELECT country_code as country, indicator, value, year
                FROM sofia.who_health_data
                WHERE LOWER(indicator) LIKE '%life%expect%'
                ORDER BY value DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🏆 TOP LIFE EXPECTANCY:")
                report_lines.append("-" * 60)
                for country, indicator, value, year in rows:
                    report_lines.append(f"  • {country:<25} {value:>5.1f} years ({year})")
                report_lines.append("")

            # Healthcare indicators
            cur.execute("""
                SELECT DISTINCT indicator, COUNT(*) as countries
                FROM sofia.who_health_data
                GROUP BY indicator
                ORDER BY countries DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 AVAILABLE HEALTH INDICATORS:")
                report_lines.append("-" * 60)
                for indicator, countries in rows:
                    report_lines.append(f"  • {indicator[:50]}: {countries} countries")
                report_lines.append("")

            # Mortality rates
            cur.execute("""
                SELECT country_code as country, indicator, value, year
                FROM sofia.who_health_data
                WHERE LOWER(indicator) LIKE '%mortality%' OR LOWER(indicator) LIKE '%death%'
                ORDER BY value ASC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📉 LOWEST MORTALITY RATES:")
                report_lines.append("-" * 60)
                for country, indicator, value, year in rows:
                    report_lines.append(f"  • {country}: {indicator[:30]} = {value:.2f} ({year})")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ WHO data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 2. UNICEF - Children's Data
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("👶 2. UNICEF - CHILDREN'S WELFARE")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.unicef_children_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # Child mortality
            cur.execute("""
                SELECT country_code as country, indicator, value, year
                FROM sofia.unicef_children_data
                WHERE LOWER(indicator) LIKE '%mortality%' OR LOWER(indicator) LIKE '%death%'
                ORDER BY value ASC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🏆 LOWEST CHILD MORTALITY:")
                report_lines.append("-" * 60)
                for country, indicator, value, year in rows:
                    report_lines.append(f"  • {country:<25} {value:>8.2f} ({year})")
                report_lines.append("")

            # Education indicators
            cur.execute("""
                SELECT country_code as country, indicator, value, year
                FROM sofia.unicef_children_data
                WHERE LOWER(indicator) LIKE '%school%' OR LOWER(indicator) LIKE '%education%'
                ORDER BY value DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🎓 EDUCATION INDICATORS:")
                report_lines.append("-" * 60)
                for country, indicator, value, year in rows:
                    report_lines.append(f"  • {country}: {indicator[:30]} = {value:.2f} ({year})")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ UNICEF data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 3. HDX - Humanitarian Data
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🆘 3. HDX - HUMANITARIAN DATA EXCHANGE")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.hdx_humanitarian_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # Crisis areas
            cur.execute("""
                SELECT country_code as country, indicator, value, year, source
                FROM sofia.hdx_humanitarian_data
                ORDER BY year DESC, value DESC
                LIMIT 20
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🌍 HUMANITARIAN INDICATORS:")
                report_lines.append("-" * 60)
                for country, indicator, value, year, source in rows:
                    src = source[:15] if source else "HDX"
                    report_lines.append(f"  • {country}: {indicator[:25]} = {value:,.0f} ({year}, {src})")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ HDX data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 4. ILO - Labor Data
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("👷 4. ILO - INTERNATIONAL LABOUR")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.ilo_labor_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            cur.execute("""
                SELECT country_code as country, indicator, value, year
                FROM sofia.ilo_labor_data
                ORDER BY year DESC
                LIMIT 20
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 LABOR INDICATORS:")
                report_lines.append("-" * 60)
                for country, indicator, value, year in rows:
                    report_lines.append(f"  • {country}: {indicator[:30]} = {value:.2f} ({year})")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ ILO data error: {e}")
        report_lines.append("")

    # =========================================================================
    # INSIGHTS
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("💡 HEALTH & HUMANITARIAN INSIGHTS")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("FOR EXPANSION DECISIONS:")
    report_lines.append("• High life expectancy = developed healthcare = stable workforce")
    report_lines.append("• Low child mortality = educated population pipeline")
    report_lines.append("• Humanitarian crises = avoid or consider CSR opportunities")
    report_lines.append("")
    report_lines.append("HEALTH TECH OPPORTUNITIES:")
    report_lines.append("• Countries with healthcare gaps = telehealth market")
    report_lines.append("• High disease burden = diagnostic/pharma opportunities")
    report_lines.append("• Aging populations = eldercare tech demand")
    report_lines.append("")

    cur.close()
    conn.close()

    report_text = "\n".join(report_lines)
    print(report_text)

    output_path = "analytics/global-health-humanitarian.txt"
    with open(output_path, 'w') as f:
        f.write(report_text)
    print(f"\n✅ Report saved to: {output_path}")

if __name__ == "__main__":
    main()
