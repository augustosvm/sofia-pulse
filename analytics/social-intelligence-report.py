#!/usr/bin/env python3
"""
================================================================================
SOCIAL INTELLIGENCE REPORT
================================================================================
Analyzes social factors for market intelligence:
- Religion demographics (40+ countries)
- Top NGOs by sector (200+ organizations)
- Drug consumption patterns (UNODC + state-level)
- Sports & physical activity

Use Cases:
- Market segmentation by cultural factors
- CSR partnership opportunities
- Health/wellness market analysis
- Regional cultural analysis
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
    print("🌐 SOCIAL INTELLIGENCE REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    conn = get_connection()
    cur = conn.cursor()

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("🌐 SOCIAL INTELLIGENCE REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # =========================================================================
    # 1. RELIGION DEMOGRAPHICS
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🙏 1. RELIGION DEMOGRAPHICS BY COUNTRY")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.world_religion_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # Top Christian countries
            cur.execute("""
                SELECT country_name, religion, percentage, population, year
                FROM sofia.world_religion_data
                WHERE LOWER(religion) LIKE '%christian%'
                  AND percentage IS NOT NULL
                ORDER BY percentage DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("✝️ TOP CHRISTIAN COUNTRIES:")
                report_lines.append("-" * 60)
                for country_name, religion, pct, pop, year in rows:
                    pop_str = f"{pop/1e6:.1f}M" if pop else "N/A"
                    report_lines.append(f"  • {country_name:<25} {pct:>5.1f}% ({pop_str})")
                report_lines.append("")

            # Top Muslim countries
            cur.execute("""
                SELECT country_name, religion, percentage, population, year
                FROM sofia.world_religion_data
                WHERE LOWER(religion) LIKE '%muslim%' OR LOWER(religion) LIKE '%islam%'
                  AND percentage IS NOT NULL
                ORDER BY percentage DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("☪️ TOP MUSLIM COUNTRIES:")
                report_lines.append("-" * 60)
                for country_name, religion, pct, pop, year in rows:
                    pop_str = f"{pop/1e6:.1f}M" if pop else "N/A"
                    report_lines.append(f"  • {country_name:<25} {pct:>5.1f}% ({pop_str})")
                report_lines.append("")

            # Top secular/non-religious countries
            cur.execute("""
                SELECT country_name, religion, percentage, population, year
                FROM sofia.world_religion_data
                WHERE LOWER(religion) LIKE '%non%relig%'
                   OR LOWER(religion) LIKE '%atheist%'
                   OR LOWER(religion) LIKE '%secular%'
                   OR LOWER(religion) LIKE '%unaffiliat%'
                  AND percentage IS NOT NULL
                ORDER BY percentage DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🔬 TOP SECULAR/NON-RELIGIOUS COUNTRIES:")
                report_lines.append("-" * 60)
                for country_name, religion, pct, pop, year in rows:
                    pop_str = f"{pop/1e6:.1f}M" if pop else "N/A"
                    report_lines.append(f"  • {country_name:<25} {pct:>5.1f}% ({pop_str})")
                report_lines.append("")

            # Religious diversity (multiple religions in country)
            cur.execute("""
                SELECT country_name, COUNT(DISTINCT religion) as religions
                FROM sofia.world_religion_data
                WHERE percentage > 5
                GROUP BY country_name
                ORDER BY religions DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🌈 MOST RELIGIOUSLY DIVERSE COUNTRIES:")
                report_lines.append("-" * 60)
                for country_name, religions in rows:
                    report_lines.append(f"  • {country_name:<30} {religions} major religions")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ Religion data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 2. TOP NGOs BY SECTOR
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("🏛️ 2. TOP NGOs BY SECTOR")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.world_ngos")
        count = cur.fetchone()[0]
        report_lines.append(f"Total NGOs tracked: {count:,}")
        report_lines.append("")

        if count > 0:
            # By sector
            cur.execute("""
                SELECT sector, COUNT(*) as count
                FROM sofia.world_ngos
                GROUP BY sector
                ORDER BY count DESC
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 NGOs BY SECTOR:")
                report_lines.append("-" * 60)
                for sector, count in rows:
                    report_lines.append(f"  • {sector:<30} {count:>5} organizations")
                report_lines.append("")

            # Top NGOs by budget/revenue
            cur.execute("""
                SELECT name, sector, headquarters, budget_usd, employees, year_founded
                FROM sofia.world_ngos
                WHERE budget_usd IS NOT NULL
                ORDER BY budget_usd DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("💰 LARGEST NGOs BY BUDGET:")
                report_lines.append("-" * 60)
                for name, sector, hq, budget, emp, founded in rows:
                    budget_str = f"${budget/1e9:.1f}B" if budget >= 1e9 else f"${budget/1e6:.0f}M"
                    emp_str = f"{emp:,}" if emp else "N/A"
                    report_lines.append(f"  • {name[:35]:<35}")
                    report_lines.append(f"    Sector: {sector} | HQ: {hq} | Budget: {budget_str} | Staff: {emp_str}")
                report_lines.append("")

            # Tech-related NGOs
            cur.execute("""
                SELECT name, sector, headquarters, focus_areas
                FROM sofia.world_ngos
                WHERE LOWER(sector) LIKE '%tech%' 
                   OR LOWER(focus_areas) LIKE '%tech%'
                   OR LOWER(focus_areas) LIKE '%digital%'
                   OR LOWER(focus_areas) LIKE '%innovat%'
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🖥️ TECH-FOCUSED NGOs (CSR Partnership Opportunities):")
                report_lines.append("-" * 60)
                for name, sector, hq, focus in rows:
                    report_lines.append(f"  • {name} ({hq})")
                    if focus:
                        report_lines.append(f"    Focus: {focus[:60]}")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ NGO data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 3. DRUG CONSUMPTION PATTERNS
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("💊 3. DRUG CONSUMPTION PATTERNS (UNODC)")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        cur.execute("SELECT COUNT(*) FROM sofia.world_drugs_data")
        count = cur.fetchone()[0]
        report_lines.append(f"Total records: {count:,}")
        report_lines.append("")

        if count > 0:
            # By drug type
            cur.execute("""
                SELECT drug_type, COUNT(DISTINCT country) as countries, AVG(prevalence) as avg_prevalence
                FROM sofia.world_drugs_data
                WHERE prevalence IS NOT NULL
                GROUP BY drug_type
                ORDER BY avg_prevalence DESC
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 DRUG CONSUMPTION BY TYPE:")
                report_lines.append("-" * 60)
                for drug, countries, prevalence in rows:
                    report_lines.append(f"  • {drug:<25} {countries:>3} countries | Avg: {prevalence:>5.2f}%")
                report_lines.append("")

            # Top cannabis countries
            cur.execute("""
                SELECT country, drug_type, prevalence, year
                FROM sofia.world_drugs_data
                WHERE LOWER(drug_type) LIKE '%cannabis%'
                  AND prevalence IS NOT NULL
                ORDER BY prevalence DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🌿 TOP CANNABIS CONSUMPTION COUNTRIES:")
                report_lines.append("-" * 60)
                for country, drug, prevalence, year in rows:
                    report_lines.append(f"  • {country:<25} {prevalence:>5.2f}% ({year})")
                report_lines.append("")

            # Brazil/USA state-level if available
            cur.execute("""
                SELECT country, state, drug_type, prevalence, year
                FROM sofia.world_drugs_data
                WHERE state IS NOT NULL AND state != ''
                ORDER BY prevalence DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🏛️ STATE-LEVEL DATA (USA/Brazil):")
                report_lines.append("-" * 60)
                for country, state, drug, prevalence, year in rows:
                    report_lines.append(f"  • {state} ({country}): {drug} - {prevalence:.2f}%")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ Drugs data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 4. SPORTS & PHYSICAL ACTIVITY
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("⚽ 4. SPORTS & PHYSICAL ACTIVITY")
    report_lines.append("=" * 80)
    report_lines.append("")

    try:
        # Sports federations
        cur.execute("SELECT COUNT(*) FROM sofia.sports_federations")
        count = cur.fetchone()[0]
        report_lines.append(f"Sports federations tracked: {count:,}")

        cur.execute("SELECT COUNT(*) FROM sofia.sports_regional")
        count2 = cur.fetchone()[0]
        report_lines.append(f"Regional sports data: {count2:,}")
        report_lines.append("")

        if count > 0:
            cur.execute("""
                SELECT federation, sport, ranking_type, country, rank, year
                FROM sofia.sports_federations
                ORDER BY rank ASC
                LIMIT 20
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("🏆 TOP COUNTRIES BY SPORT (FIFA, IOC, etc.):")
                report_lines.append("-" * 60)
                current_sport = None
                for fed, sport, ranking, country, rank, year in rows:
                    if sport != current_sport:
                        report_lines.append(f"\n  {sport.upper()} ({fed}):")
                        current_sport = sport
                    report_lines.append(f"    {rank:>2}. {country}")
                report_lines.append("")

        if count2 > 0:
            cur.execute("""
                SELECT sport, region, country, participation_rate, year
                FROM sofia.sports_regional
                WHERE participation_rate IS NOT NULL
                ORDER BY participation_rate DESC
                LIMIT 15
            """)
            rows = cur.fetchall()
            if rows:
                report_lines.append("📊 SPORTS PARTICIPATION BY REGION:")
                report_lines.append("-" * 60)
                for sport, region, country, rate, year in rows:
                    report_lines.append(f"  • {sport}: {country} ({region}) - {rate:.1f}%")
                report_lines.append("")

    except Exception as e:
        conn.rollback()
        report_lines.append(f"⚠️ Sports data error: {e}")
        report_lines.append("")

    # =========================================================================
    # 5. MARKET INSIGHTS
    # =========================================================================
    report_lines.append("=" * 80)
    report_lines.append("💡 MARKET INSIGHTS & RECOMMENDATIONS")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("CULTURAL MARKETING:")
    report_lines.append("  • Secular markets: Nordics, Japan, China - tech-first messaging")
    report_lines.append("  • Religious markets: LATAM, Middle East - family/community values")
    report_lines.append("  • Diverse markets: USA, UK, Brazil - inclusive messaging required")
    report_lines.append("")
    report_lines.append("CSR OPPORTUNITIES:")
    report_lines.append("  • Partner with tech-focused NGOs for talent pipeline")
    report_lines.append("  • Environment NGOs for sustainability credentials")
    report_lines.append("  • Education NGOs for emerging market presence")
    report_lines.append("")
    report_lines.append("HEALTH & WELLNESS MARKETS:")
    report_lines.append("  • Cannabis legalization trend - US, Canada, Uruguay, Germany")
    report_lines.append("  • Sports tech - high participation markets")
    report_lines.append("  • Mental health - secular, developed markets")
    report_lines.append("")

    cur.close()
    conn.close()

    # Save report
    report_text = "\n".join(report_lines)
    print(report_text)

    output_path = "analytics/social-intelligence-report.txt"
    with open(output_path, 'w') as f:
        f.write(report_text)
    print(f"\n✅ Report saved to: {output_path}")

if __name__ == "__main__":
    main()
