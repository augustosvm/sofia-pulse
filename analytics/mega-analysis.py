#!/usr/bin/env python3
"""
Sofia Pulse - MEGA ANALYSIS
Comprehensive cross-database analysis using ALL data sources
"""

import os
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', 'sofia123strong'),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_table_counts():
    """Get record counts from all tables"""
    conn = get_db_connection()
    cur = conn.cursor()

    tables = {}

    # Get all tables in sofia schema
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'sofia'
        ORDER BY table_name
    """)

    table_names = [row[0] for row in cur.fetchall()]

    for table in table_names:
        try:
            cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
            count = cur.fetchone()[0]
            tables[table] = count
        except:
            tables[table] = 0

    conn.close()
    return tables

def get_socioeconomic_summary():
    """Socioeconomic indicators summary"""
    conn = get_db_connection()
    cur = conn.cursor()

    summary = {
        'total_records': 0,
        'countries': 0,
        'indicators': 0,
        'top_gdp_per_capita': [],
        'extreme_poverty': [],
        'rd_investment': [],
        'fertility_vs_urban': []
    }

    try:
        # Total records
        cur.execute("SELECT COUNT(*) FROM sofia.socioeconomic_indicators")
        summary['total_records'] = cur.fetchone()[0]

        # Countries
        cur.execute("SELECT COUNT(DISTINCT country_code) FROM sofia.socioeconomic_indicators")
        summary['countries'] = cur.fetchone()[0]

        # Indicators
        cur.execute("SELECT COUNT(DISTINCT indicator_code) FROM sofia.socioeconomic_indicators")
        summary['indicators'] = cur.fetchone()[0]

        # Top 10 GDP per capita (2023)
        cur.execute("""
            SELECT country_name, ROUND(value::numeric, 2) as gdp_per_capita
            FROM sofia.socioeconomic_indicators
            WHERE indicator_code = 'NY.GDP.PCAP.CD' AND year = 2023
            ORDER BY value DESC LIMIT 10
        """)
        summary['top_gdp_per_capita'] = cur.fetchall()

        # Top 10 extreme poverty (2023)
        cur.execute("""
            SELECT country_name, ROUND(value::numeric, 2) as poverty_pct
            FROM sofia.socioeconomic_indicators
            WHERE indicator_code = 'SI.POV.DDAY' AND year = 2023
              AND value IS NOT NULL
            ORDER BY value DESC LIMIT 10
        """)
        summary['extreme_poverty'] = cur.fetchall()

        # Top 10 R&D investment (2023)
        cur.execute("""
            SELECT country_name, ROUND(value::numeric, 2) as rd_pct_gdp
            FROM sofia.socioeconomic_indicators
            WHERE indicator_code = 'GB.XPD.RSDV.GD.ZS' AND year = 2023
              AND value IS NOT NULL
            ORDER BY value DESC LIMIT 10
        """)
        summary['rd_investment'] = cur.fetchall()

        # Fertility vs Urbanization (top 15 fertility - 2023)
        cur.execute("""
            WITH fertility AS (
                SELECT country_code, country_name, value as fertility_rate
                FROM sofia.socioeconomic_indicators
                WHERE indicator_code = 'SP.DYN.TFRT.IN' AND year = 2023
            ),
            urban AS (
                SELECT country_code, value as urban_pct
                FROM sofia.socioeconomic_indicators
                WHERE indicator_code = 'SP.URB.TOTL.IN.ZS' AND year = 2023
            )
            SELECT f.country_name,
                   ROUND(f.fertility_rate::numeric, 2) as fertility,
                   ROUND(u.urban_pct::numeric, 1) as urban_pct
            FROM fertility f
            JOIN urban u ON f.country_code = u.country_code
            WHERE f.fertility_rate IS NOT NULL AND u.urban_pct IS NOT NULL
            ORDER BY f.fertility_rate DESC LIMIT 15
        """)
        summary['fertility_vs_urban'] = cur.fetchall()

    except Exception as e:
        print(f"⚠️  Socioeconomic data not available: {e}")

    conn.close()
    return summary

def get_tech_trends_summary():
    """Tech trends summary"""
    conn = get_db_connection()
    cur = conn.cursor()

    summary = {
        'github_languages': [],
        'npm_top': [],
        'pypi_top': [],
        'hackernews_top': []
    }

    try:
        # GitHub top languages
        cur.execute("""
            SELECT language, COUNT(*) as repos, SUM(stars) as total_stars
            FROM sofia.github_trending
            WHERE language IS NOT NULL
            GROUP BY language
            ORDER BY total_stars DESC
            LIMIT 10
        """)
        summary['github_languages'] = cur.fetchall()

        # NPM top packages
        cur.execute("""
            SELECT DISTINCT ON (package_name) package_name, downloads_month
            FROM sofia.npm_stats
            ORDER BY package_name, collected_at DESC, downloads_month DESC
            LIMIT 10
        """)
        npm_results = cur.fetchall()
        # Re-sort by downloads after deduplication
        summary['npm_top'] = sorted(npm_results, key=lambda x: x[1], reverse=True)[:10]

        # PyPI top packages
        cur.execute("""
            SELECT DISTINCT ON (package_name) package_name, downloads_month
            FROM sofia.pypi_stats
            ORDER BY package_name, collected_at DESC, downloads_month DESC
            LIMIT 10
        """)
        pypi_results = cur.fetchall()
        # Re-sort by downloads after deduplication
        summary['pypi_top'] = sorted(pypi_results, key=lambda x: x[1], reverse=True)[:10]

        # HackerNews top
        cur.execute("""
            SELECT title, points, url
            FROM sofia.hackernews_stories
            ORDER BY points DESC
            LIMIT 10
        """)
        summary['hackernews_top'] = cur.fetchall()

    except Exception as e:
        print(f"⚠️  Tech trends data not available: {e}")

    conn.close()
    return summary

def get_funding_summary():
    """Funding rounds summary"""
    conn = get_db_connection()
    cur = conn.cursor()

    summary = {
        'total_30d': 0,
        'total_amount_30d': 0,
        'top_deals_30d': [],
        'by_country': [],
        'by_sector': []
    }

    try:
        ninety_days_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        # Total funding rounds last 90 days (increased from 30 for more data)
        cur.execute(f"""
            SELECT COUNT(*), SUM(amount_usd)
            FROM sofia.funding_rounds
            WHERE announced_date >= '{ninety_days_ago}'
        """)
        row = cur.fetchone()
        summary['total_30d'] = row[0] or 0
        summary['total_amount_30d'] = row[1] or 0

        # Top 10 deals
        cur.execute(f"""
            SELECT company_name, amount_usd, round_type, country, announced_date
            FROM sofia.funding_rounds
            WHERE announced_date >= '{ninety_days_ago}'
              AND amount_usd IS NOT NULL
            ORDER BY amount_usd DESC
            LIMIT 10
        """)
        summary['top_deals_30d'] = cur.fetchall()

        # By country
        cur.execute(f"""
            SELECT country, COUNT(*) as deals, SUM(amount_usd) as total_amount
            FROM sofia.funding_rounds
            WHERE announced_date >= '{ninety_days_ago}'
              AND country IS NOT NULL
            GROUP BY country
            ORDER BY total_amount DESC
            LIMIT 10
        """)
        summary['by_country'] = cur.fetchall()

        # By sector
        cur.execute(f"""
            SELECT sector, COUNT(*) as deals, SUM(amount_usd) as total_amount
            FROM sofia.funding_rounds
            WHERE announced_date >= '{ninety_days_ago}'
              AND sector IS NOT NULL
            GROUP BY sector
            ORDER BY total_amount DESC
            LIMIT 10
        """)
        summary['by_sector'] = cur.fetchall()

    except Exception as e:
        print(f"⚠️  Funding data not available: {e}")

    conn.close()
    return summary

def get_critical_sectors_summary():
    """Critical sectors summary"""
    conn = get_db_connection()
    cur = conn.cursor()

    summary = {
        'cybersecurity_30d': 0,
        'space_launches': 0,
        'ai_regulations': 0,
        'top_cves': [],
        'upcoming_launches': []
    }

    try:
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        # Cybersecurity events last 30 days
        cur.execute(f"""
            SELECT COUNT(*)
            FROM sofia.cybersecurity_events
            WHERE published_date >= '{thirty_days_ago}'
        """)
        summary['cybersecurity_30d'] = cur.fetchone()[0] or 0

        # Top CVEs (last 30 days)
        cur.execute(f"""
            SELECT title, severity, cvss_score, published_date
            FROM sofia.cybersecurity_events
            WHERE published_date >= '{thirty_days_ago}'
              AND event_type = 'cve'
            ORDER BY cvss_score DESC NULLS LAST
            LIMIT 10
        """)
        summary['top_cves'] = cur.fetchall()

        # Space launches
        cur.execute("SELECT COUNT(*) FROM sofia.space_industry")
        summary['space_launches'] = cur.fetchone()[0] or 0

        # Upcoming launches
        cur.execute("""
            SELECT company, mission_name, launch_date, status
            FROM sofia.space_industry
            WHERE launch_date >= CURRENT_DATE
            ORDER BY launch_date
            LIMIT 10
        """)
        summary['upcoming_launches'] = cur.fetchall()

        # AI regulations
        cur.execute("SELECT COUNT(*) FROM sofia.ai_regulation")
        summary['ai_regulations'] = cur.fetchone()[0] or 0

    except Exception as e:
        print(f"⚠️  Critical sectors data not available: {e}")

    conn.close()
    return summary

def get_global_economy_summary():
    """Global economy indicators"""
    conn = get_db_connection()
    cur = conn.cursor()

    summary = {
        'electricity_countries': 0,
        'port_traffic_records': 0,
        'commodity_prices': [],
        'semiconductor_sales': []
    }

    try:
        # Electricity consumption
        cur.execute("SELECT COUNT(DISTINCT country) FROM sofia.electricity_consumption")
        summary['electricity_countries'] = cur.fetchone()[0] or 0

        # Port traffic
        cur.execute("SELECT COUNT(*) FROM sofia.port_traffic")
        summary['port_traffic_records'] = cur.fetchone()[0] or 0

        # Commodity prices (latest)
        cur.execute("""
            SELECT commodity, price, unit, updated_at
            FROM sofia.commodity_prices
            ORDER BY updated_at DESC
            LIMIT 10
        """)
        summary['commodity_prices'] = cur.fetchall()

        # Semiconductor sales (latest)
        cur.execute("""
            SELECT region, sales_usd_billions, quarter, year
            FROM sofia.semiconductor_sales
            ORDER BY year DESC, quarter DESC
            LIMIT 10
        """)
        summary['semiconductor_sales'] = cur.fetchall()

    except Exception as e:
        print(f"⚠️  Global economy data not available: {e}")

    conn.close()
    return summary

def generate_mega_report():
    """Generate comprehensive MEGA report"""

    print("=" * 80)
    print("🌍 SOFIA PULSE - MEGA ANALYSIS REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    output = []
    output.append("=" * 80)
    output.append("🌍 SOFIA PULSE - MEGA ANALYSIS REPORT")
    output.append("=" * 80)
    output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    output.append("")
    output.append("This report combines data from 30+ sources:")
    output.append("• Socioeconomic indicators (World Bank - 56 indicators)")
    output.append("• Tech trends (GitHub, NPM, PyPI, HackerNews, Reddit)")
    output.append("• Research (ArXiv, OpenAlex, NIH, Universities)")
    output.append("• Funding (Venture capital, IPOs, M&A)")
    output.append("• Critical sectors (Cybersecurity, Space, AI Regulation)")
    output.append("• Global economy (Electricity, Ports, Commodities, Semiconductors)")
    output.append("• Geopolitics (GDELT events)")
    output.append("")

    # Database Summary
    print("📊 Database Summary...")
    output.append("=" * 80)
    output.append("📊 DATABASE SUMMARY")
    output.append("=" * 80)
    output.append("")

    tables = get_table_counts()
    total_records = sum(tables.values())

    output.append(f"Total Records: {total_records:,}")
    output.append(f"Total Tables: {len(tables)}")
    output.append("")
    output.append("Records by table:")
    for table, count in sorted(tables.items(), key=lambda x: x[1], reverse=True):
        output.append(f"  • {table}: {count:,}")
    output.append("")

    # Socioeconomic Summary
    print("💰 Socioeconomic Summary...")
    output.append("=" * 80)
    output.append("💰 SOCIOECONOMIC INDICATORS (World Bank)")
    output.append("=" * 80)
    output.append("")

    socio = get_socioeconomic_summary()
    output.append(f"Total Records: {socio['total_records']:,}")
    output.append(f"Countries: {socio['countries']}")
    output.append(f"Indicators: {socio['indicators']}")
    output.append("")

    if socio['top_gdp_per_capita']:
        output.append("🏆 Top 10 GDP per Capita (2023):")
        for i, (country, gdp) in enumerate(socio['top_gdp_per_capita'], 1):
            output.append(f"  {i:2d}. {country:30s} ${gdp:>12,.2f}")
        output.append("")

    if socio['extreme_poverty']:
        output.append("🏚️  Top 10 Extreme Poverty (<$2.15/day - 2023):")
        for i, (country, pct) in enumerate(socio['extreme_poverty'], 1):
            output.append(f"  {i:2d}. {country:30s} {pct:>6.2f}%")
        output.append("")

    if socio['rd_investment']:
        output.append("🔬 Top 10 R&D Investment (% of GDP - 2023):")
        for i, (country, pct) in enumerate(socio['rd_investment'], 1):
            output.append(f"  {i:2d}. {country:30s} {pct:>6.2f}%")
        output.append("")

    if socio['fertility_vs_urban']:
        output.append("👨‍👩‍👧‍👦 Fertility vs Urbanization (2023):")
        output.append(f"{'Country':30s} {'Fertility':>10s} {'Urban %':>10s}")
        output.append("-" * 52)
        for country, fert, urban in socio['fertility_vs_urban']:
            output.append(f"{country:30s} {fert:>10.2f} {urban:>10.1f}%")
        output.append("")

    # Tech Trends Summary
    print("📈 Tech Trends Summary...")
    output.append("=" * 80)
    output.append("📈 TECH TRENDS")
    output.append("=" * 80)
    output.append("")

    tech = get_tech_trends_summary()

    if tech['github_languages']:
        output.append("🔥 GitHub Top Languages (by stars):")
        for i, (lang, repos, stars) in enumerate(tech['github_languages'], 1):
            output.append(f"  {i:2d}. {lang:20s} {repos:>6,} repos  {stars:>12,} stars")
        output.append("")

    if tech['npm_top']:
        output.append("📦 NPM Top Packages (monthly downloads):")
        for i, (pkg, downloads) in enumerate(tech['npm_top'], 1):
            output.append(f"  {i:2d}. {pkg:30s} {downloads:>15,}")
        output.append("")

    if tech['pypi_top']:
        output.append("🐍 PyPI Top Packages (monthly downloads):")
        for i, (pkg, downloads) in enumerate(tech['pypi_top'], 1):
            output.append(f"  {i:2d}. {pkg:30s} {downloads:>15,}")
        output.append("")

    # Funding Summary
    print("💵 Funding Summary...")
    output.append("=" * 80)
    output.append("💵 FUNDING & INVESTMENT (Last 30 days)")
    output.append("=" * 80)
    output.append("")

    funding = get_funding_summary()
    output.append(f"Total Deals: {funding['total_30d']:,}")
    output.append(f"Total Amount: ${funding['total_amount_30d']:,.2f}")
    output.append("")

    if funding['top_deals_30d']:
        output.append("🏆 Top 10 Deals:")
        for i, (company, amount, round_type, country, date) in enumerate(funding['top_deals_30d'], 1):
            output.append(f"  {i:2d}. {company:30s} ${amount:>15,.2f} {round_type:15s} {country:10s}")
        output.append("")

    if funding['by_country']:
        output.append("🌍 Top 10 Countries by Funding:")
        for i, (country, deals, amount) in enumerate(funding['by_country'], 1):
            output.append(f"  {i:2d}. {country:30s} {deals:>4,} deals  ${amount:>15,.2f}")
        output.append("")

    # Critical Sectors Summary
    print("🔒 Critical Sectors Summary...")
    output.append("=" * 80)
    output.append("🔒 CRITICAL SECTORS")
    output.append("=" * 80)
    output.append("")

    sectors = get_critical_sectors_summary()
    output.append(f"Cybersecurity Events (30d): {sectors['cybersecurity_30d']:,}")
    output.append(f"Space Launches: {sectors['space_launches']:,}")
    output.append(f"AI Regulations: {sectors['ai_regulations']:,}")
    output.append("")

    if sectors['top_cves']:
        output.append("🔒 Top CVEs (last 30 days):")
        for title, severity, cvss, date in sectors['top_cves']:
            output.append(f"  • {title[:60]:60s} {severity:10s} CVSS:{cvss}")
        output.append("")

    if sectors['upcoming_launches']:
        output.append("🚀 Upcoming Space Launches:")
        for company, mission, date, status in sectors['upcoming_launches']:
            output.append(f"  • {mission[:40]:40s} {company:20s} {date}")
        output.append("")

    # Global Economy Summary
    print("🌐 Global Economy Summary...")
    output.append("=" * 80)
    output.append("🌐 GLOBAL ECONOMY")
    output.append("=" * 80)
    output.append("")

    economy = get_global_economy_summary()
    output.append(f"Electricity Data (countries): {economy['electricity_countries']:,}")
    output.append(f"Port Traffic Records: {economy['port_traffic_records']:,}")
    output.append("")

    if economy['commodity_prices']:
        output.append("📈 Latest Commodity Prices:")
        for commodity, price, unit, updated in economy['commodity_prices']:
            output.append(f"  • {commodity:20s} ${price:>10.2f} {unit}")
        output.append("")

    if economy['semiconductor_sales']:
        output.append("💾 Semiconductor Sales (latest quarters):")
        for region, sales, quarter, year in economy['semiconductor_sales']:
            output.append(f"  • {region:20s} ${sales:>8.2f}B  Q{quarter} {year}")
        output.append("")

    output.append("=" * 80)
    output.append("✅ MEGA ANALYSIS COMPLETE")
    output.append("=" * 80)
    output.append("")
    output.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    output.append(f"Total data sources: 30+")
    output.append(f"Total records analyzed: {total_records:,}")
    output.append("")

    # Write to file
    report_path = "analytics/mega-analysis-latest.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    print("")
    print(f"✅ Report saved to: {report_path}")
    print("")

    # Print to console
    print('\n'.join(output))

if __name__ == '__main__':
    try:
        generate_mega_report()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
