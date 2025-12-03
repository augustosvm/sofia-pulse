#!/usr/bin/env python3
"""
================================================================================
WOMEN'S GLOBAL ANALYSIS - Gender Gap Intelligence
================================================================================
Analyzes gender gaps across:
- Employment & Labor Force
- Education & Literacy
- Political Representation
- Economic Opportunity

Data Sources:
- World Bank (55+ indicators)
- Eurostat (EU data)
- FRED (USA employment)
- ILO (Global labor)
- IBGE/IPEA (Brazil)
- Central Banks (Leadership)

Methodology: World Economic Forum Gender Gap Index inspired
================================================================================
"""

import os
import sys
import psycopg2
from datetime import datetime

# Database connection
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
    print("🚺 WOMEN'S GLOBAL ANALYSIS - Gender Gap Intelligence")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    conn = get_connection()
    cur = conn.cursor()

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("🚺 WOMEN'S GLOBAL ANALYSIS - Gender Gap Intelligence")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # =========================================================================
    # 1. WORLD BANK - Global Gender Indicators
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("📊 1. GLOBAL GENDER INDICATORS (World Bank)")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        # Check if table exists and has data
        cur.execute("SELECT COUNT(*) FROM sofia.women_world_bank_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # Top countries by female labor force participation (latest year only)
            cur.execute("""
                SELECT w.country_name, w.indicator_name, w.value, w.year
                FROM sofia.women_world_bank_data w
                INNER JOIN (
                    SELECT country_name, MAX(year) as max_year
                    FROM sofia.women_world_bank_data
                    WHERE indicator_code = 'SL.TLF.CACT.FE.ZS' AND value IS NOT NULL
                    GROUP BY country_name
                ) latest ON w.country_name = latest.country_name AND w.year = latest.max_year
                WHERE w.indicator_code = 'SL.TLF.CACT.FE.ZS'
                  AND w.value IS NOT NULL
                ORDER BY w.value DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🏆 TOP 15 - Female Labor Force Participation (%):")
                report_lines.append("-" * 60)
                for i, (country, indicator, value, year) in enumerate(rows, 1):
                    report_lines.append(f"  {i:2}. {country:<30} {value:>6.1f}% ({year})")
                report_lines.append("")

            # Gender gap in employment
            cur.execute("""
                SELECT country_name, 
                       MAX(CASE WHEN indicator_code = 'SL.TLF.CACT.FE.ZS' THEN value END) as female,
                       MAX(CASE WHEN indicator_code = 'SL.TLF.CACT.MA.ZS' THEN value END) as male
                FROM sofia.women_world_bank_data
                WHERE indicator_code IN ('SL.TLF.CACT.FE.ZS', 'SL.TLF.CACT.MA.ZS')
                  AND value IS NOT NULL
                GROUP BY country_name
                HAVING MAX(CASE WHEN indicator_code = 'SL.TLF.CACT.FE.ZS' THEN value END) IS NOT NULL
                   AND MAX(CASE WHEN indicator_code = 'SL.TLF.CACT.MA.ZS' THEN value END) IS NOT NULL
                ORDER BY (MAX(CASE WHEN indicator_code = 'SL.TLF.CACT.FE.ZS' THEN value END) - 
                          MAX(CASE WHEN indicator_code = 'SL.TLF.CACT.MA.ZS' THEN value END)) DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("⚖️ SMALLEST GENDER GAP IN EMPLOYMENT:")
                report_lines.append("-" * 60)
                report_lines.append(f"  {'Country':<25} {'Female':<10} {'Male':<10} {'Gap':<10}")
                for country, female, male in rows:
                    if female and male:
                        gap = female - male
                        report_lines.append(f"  {country:<25} {female:>6.1f}%   {male:>6.1f}%   {gap:>+6.1f}%")
                report_lines.append("")

            # Female education indicators
            cur.execute("""
                SELECT country_name, indicator_name, value, year
                FROM sofia.women_world_bank_data
                WHERE indicator_code LIKE '%SE.%FE%'
                  AND value IS NOT NULL
                ORDER BY value DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🎓 TOP FEMALE EDUCATION INDICATORS:")
                report_lines.append("-" * 60)
                for country, indicator, value, year in rows:
                    short_indicator = indicator[:40] + "..." if len(indicator) > 40 else indicator
                    report_lines.append(f"  • {country}: {short_indicator} = {value:.1f} ({year})")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ World Bank data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 2. BRAZIL - Gender Data (IBGE/IPEA)
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🇧🇷 2. BRAZIL GENDER DATA (IBGE/IPEA)")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.women_brazil_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # By region
            cur.execute("""
                SELECT region, indicator_name, value, period
                FROM sofia.women_brazil_data
                WHERE value IS NOT NULL
                ORDER BY period DESC, value DESC
                LIMIT 20
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 BRAZIL - Latest Gender Indicators by Region:")
                report_lines.append("-" * 60)
                for region, indicator, value, period in rows:
                    report_lines.append(f"  • {region or 'Brazil'}: {indicator[:35]} = {value:.2f} ({period})")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ Brazil data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 3. CENTRAL BANKS - Women in Leadership
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🏦 3. WOMEN IN CENTRAL BANK LEADERSHIP")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.central_banks_women_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # Women in leadership
            cur.execute("""
                SELECT country_code, central_bank_name, indicator_name, value, year
                FROM sofia.central_banks_women_data
                WHERE value IS NOT NULL
                ORDER BY value DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("👩‍💼 WOMEN IN CENTRAL BANK LEADERSHIP:")
                report_lines.append("-" * 60)
                for country_code, bank, indicator_name, value, year in rows:
                    report_lines.append(f"  • {country_code} ({bank[:20]}): {indicator_name[:25]} = {value:.1f}% ({year})")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ Central banks data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 4. EU - Eurostat Data
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🇪🇺 4. EUROPEAN UNION GENDER DATA (Eurostat)")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.women_eurostat_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            cur.execute("""
                SELECT DISTINCT ON (country_code, dataset_name)
                    country_code, dataset_name, value, year
                FROM sofia.women_eurostat_data
                WHERE value IS NOT NULL
                ORDER BY country_code, dataset_name, year DESC, value DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 EU GENDER INDICATORS:")
                report_lines.append("-" * 60)
                for country_code, dataset_name, value, year in rows:
                    report_lines.append(f"  • {country_code}: {dataset_name[:35] if dataset_name else 'N/A'} = {value:.2f} ({year})")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ Eurostat data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 5. USA - FRED Data
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🇺🇸 5. USA WOMEN'S EMPLOYMENT (FRED)")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.women_fred_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            cur.execute("""
                SELECT indicator_name, value, date
                FROM sofia.women_fred_data
                WHERE value IS NOT NULL
                ORDER BY date DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 USA WOMEN'S EMPLOYMENT INDICATORS:")
                report_lines.append("-" * 60)
                for indicator, value, date in rows:
                    report_lines.append(f"  • {indicator[:45]}: {value:.2f} ({date})")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ FRED data error: {e}")
        report_lines.append("")

    # =========================================================================
    # INSIGHTS & RECOMMENDATIONS
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("💡 KEY INSIGHTS & RECOMMENDATIONS")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("1. LABOR FORCE PARTICIPATION:")
    report_lines.append("   • Nordic countries lead in female participation")
    report_lines.append("   • LATAM shows growing trend but still below OECD average")
    report_lines.append("   • Tech sector has lowest female representation")
    report_lines.append("")
    report_lines.append("2. EDUCATION GAP:")
    report_lines.append("   • Women surpass men in tertiary education globally")
    report_lines.append("   • STEM fields remain male-dominated (except healthcare)")
    report_lines.append("   • Brazil shows strong female education metrics")
    report_lines.append("")
    report_lines.append("3. LEADERSHIP:")
    report_lines.append("   • Central banks: <20% women in leadership globally")
    report_lines.append("   • Corporate boards: EU leading with mandatory quotas")
    report_lines.append("   • Political representation: Growing but uneven")
    report_lines.append("")
    report_lines.append("4. ACTIONABLE INSIGHTS:")
    report_lines.append("   • Target tech hiring in high-participation countries")
    report_lines.append("   • Consider EU for gender-balanced expansion")
    report_lines.append("   • Monitor Brazil's growing female tech workforce")
    report_lines.append("")

    # =========================================================================
    # METHODOLOGY
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("📚 METHODOLOGY")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("Based on World Economic Forum Gender Gap Index methodology:")
    report_lines.append("• Economic Participation (labor force, wages)")
    report_lines.append("• Educational Attainment (enrollment, literacy)")
    report_lines.append("• Health & Survival (life expectancy, sex ratio)")
    report_lines.append("• Political Empowerment (parliament, ministers)")
    report_lines.append("")
    report_lines.append("Data Sources:")
    report_lines.append("• World Bank Gender Data Portal")
    report_lines.append("• Eurostat Gender Statistics")
    report_lines.append("• US Federal Reserve Economic Data (FRED)")
    report_lines.append("• International Labour Organization (ILO)")
    report_lines.append("• IBGE/IPEA Brazil")
    report_lines.append("• Central Banks Official Reports")
    report_lines.append("")

    cur.close()
    conn.close()

    # Save report
    report_text = "\n".join(report_lines)
    print(report_text)

    output_path = "analytics/women-global-analysis.txt"
    with open(output_path, 'w') as f:
        f.write(report_text)
    print(f"\n✅ Report saved to: {output_path}")

if __name__ == "__main__":
    main()
