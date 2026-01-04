#!/usr/bin/env python3
"""
Export CSV files for email attachments
Exports 17 CSV files from database for daily email reports
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import csv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('POSTGRES_USER', 'sofia'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'database': os.getenv('POSTGRES_DB', 'sofia_db'),
}

OUTPUT_DIR = 'analytics'

def export_to_csv(cursor, filename, limit=1000):
    """Export cursor results to CSV file"""
    rows = cursor.fetchall()
    if not rows:
        print(f"   ⚠️  No data for {filename}")
        return 0

    filepath = os.path.join(OUTPUT_DIR, filename)

    # Get column names
    columns = [desc[0] for desc in cursor.description]

    # Write CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows[:limit]:  # Limit rows for email size
            writer.writerow(dict(row))

    print(f"   ✅ {filename}: {len(rows[:limit])} rows")
    return len(rows[:limit])

def main():
    print("=" * 80)
    print("📊 EXPORTING CSVs FOR EMAIL")
    print("=" * 80)
    print()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        total_files = 0
        total_rows = 0
        failed = []

        # 1. GitHub Trending
        try:
            print("📊 GitHub Trending...")
            cur.execute("""
                SELECT full_name as repo_name, stars, language, description,
                       homepage as url, collected_at
                FROM sofia.github_trending
                ORDER BY stars DESC
                LIMIT 500
            """)
            total_rows += export_to_csv(cur, 'github_trending.csv')
            total_files += 1
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed.append(('github_trending.csv', str(e)))

        # 2. NPM Stats
        print("📊 NPM Stats...")
        cur.execute("""
            SELECT package_name, downloads_week as weekly_downloads, version, description, collected_at
            FROM sofia.npm_stats
            ORDER BY downloads_week DESC NULLS LAST
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'npm_stats.csv')
        total_files += 1

        # 3. PyPI Stats
        print("📊 PyPI Stats...")
        cur.execute("""
            SELECT package_name, downloads_month as monthly_downloads, version, description, collected_at
            FROM sofia.pypi_stats
            ORDER BY downloads_month DESC NULLS LAST
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'pypi_stats.csv')
        total_files += 1

        # 4. HackerNews Stories
        print("📊 HackerNews Stories...")
        cur.execute("""
            SELECT title, url, points, num_comments as comments, author, created_at
            FROM sofia.hackernews_stories
            ORDER BY points DESC NULLS LAST
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'hackernews_stories.csv')
        total_files += 1

        # 5. Funding Rounds (90 days)
        print("📊 Funding Rounds (90 days)...")
        cur.execute("""
            SELECT
                company_name,
                amount_usd,
                round_type,
                COALESCE(co.common_name, country) as country,
                announced_date,
                investors
            FROM sofia.funding_rounds
            LEFT JOIN sofia.countries co ON funding_rounds.country_id = co.id
            WHERE announced_date >= CURRENT_DATE - INTERVAL '90 days'
            ORDER BY amount_usd DESC NULLS LAST
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'funding_90d.csv')
        total_files += 1

        # 6. ArXiv AI Papers
        print("📊 ArXiv AI Papers...")
        cur.execute("""
            SELECT title, authors, published_date, categories, abstract, pdf_url
            FROM sofia.arxiv_ai_papers
            ORDER BY published_date DESC
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'arxiv_ai_papers.csv')
        total_files += 1

        # 7. OpenAlex Papers
        print("📊 OpenAlex Papers...")
        cur.execute("""
            SELECT title, publication_date, primary_concept, cited_by_count,
                   is_open_access, journal, publisher
            FROM sofia.openalex_papers
            ORDER BY cited_by_count DESC NULLS LAST
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'openalex_papers.csv')
        total_files += 1

        # 8. NIH Grants
        print("📊 NIH Grants...")
        cur.execute("""
            SELECT title as project_title, organization, award_amount_usd as total_cost, fiscal_year,
                   principal_investigator as pi_name, abstract as project_terms
            FROM sofia.nih_grants
            ORDER BY award_amount_usd DESC NULLS LAST
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'nih_grants.csv')
        total_files += 1

        # 9. Cybersecurity (30 days)
        print("📊 Cybersecurity Events (30 days)...")
        cur.execute("""
            SELECT event_id as cve_id, description, severity, cvss_score, published_date
            FROM sofia.cybersecurity_events
            WHERE published_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY published_date DESC
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'cybersecurity_30d.csv')
        total_files += 1

        # 10. Space Launches
        print("📊 Space Launches...")
        cur.execute("""
            SELECT mission_name, launch_date, rocket_type as rocket, launch_site,
                   status as success, description as details
            FROM sofia.space_industry
            ORDER BY launch_date DESC
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'space_launches.csv')
        total_files += 1

        # 11. AI Regulation
        print("📊 AI Regulation...")
        cur.execute("""
            SELECT title, jurisdiction as country, regulation_type, status,
                   effective_date, description
            FROM sofia.ai_regulation
            ORDER BY effective_date DESC NULLS LAST
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'ai_regulation.csv')
        total_files += 1

        # 12. GDELT Events (30 days)
        print("📊 GDELT Events (30 days)...")
        cur.execute("""
            SELECT event_date, actor1_name, actor2_name, event_code,
                   quad_class, goldstein_scale, num_mentions, source_url
            FROM sofia.gdelt_events
            WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY goldstein_scale DESC NULLS LAST
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'gdelt_events_30d.csv')
        total_files += 1

        # 13. Socioeconomic Brazil
        print("📊 Socioeconomic Brazil...")
        cur.execute("""
            SELECT indicator_name, value, year, data_source as source
            FROM sofia.socioeconomic_indicators
            WHERE country_code = 'BRA'
            ORDER BY year DESC, indicator_name
            LIMIT 1000
        """)
        total_rows += export_to_csv(cur, 'socioeconomic_brazil.csv')
        total_files += 1

        # 14. Socioeconomic Top GDP
        print("📊 Socioeconomic Top GDP Countries...")
        cur.execute("""
            SELECT
                si.country_code,
                co.common_name as country,
                si.indicator_name,
                si.value,
                si.year
            FROM sofia.socioeconomic_indicators si
            LEFT JOIN sofia.countries co ON si.country_code = co.iso_alpha3
            WHERE si.indicator_name = 'GDP (current US$)'
                AND si.year >= 2020
            ORDER BY si.value DESC NULLS LAST
            LIMIT 1000
        """)
        total_rows += export_to_csv(cur, 'socioeconomic_top_gdp.csv')
        total_files += 1

        # 15. Electricity Consumption
        print("📊 Electricity Consumption...")
        cur.execute("""
            SELECT country, consumption_twh as consumption_kwh, year, data_source as source
            FROM sofia.electricity_consumption
            ORDER BY consumption_twh DESC NULLS LAST
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'electricity_consumption.csv')
        total_files += 1

        # 16. Commodity Prices
        print("📊 Commodity Prices...")
        cur.execute("""
            SELECT commodity as commodity_name, price, unit, price_date as date, data_source as source
            FROM sofia.commodity_prices
            ORDER BY price_date DESC
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'commodity_prices.csv')
        total_files += 1

        # 17. Port Traffic
        print("📊 Port Traffic...")
        cur.execute("""
            SELECT country, teu as container_teu, year
            FROM sofia.port_traffic
            ORDER BY teu DESC NULLS LAST
            LIMIT 500
        """)
        total_rows += export_to_csv(cur, 'port_traffic.csv')
        total_files += 1

        cur.close()
        conn.close()

        print()
        print("=" * 80)
        print("✅ CSV EXPORT COMPLETE")
        print("=" * 80)
        print(f"   Files: {total_files}/17")
        print(f"   Total rows: {total_rows:,}")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
