#!/usr/bin/env python3
import psycopg2
from datetime import datetime

def check_funding():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='sofia_db',
            user='sofia',
            password='sofia123strong'
        )
        cur = conn.cursor()

        print('✅ Connected to database\n')

        # Total funding rounds
        cur.execute("SELECT COUNT(*) FROM sofia.funding_rounds")
        total = cur.fetchone()[0]
        print(f'📊 Total Funding Rounds: {total}')

        # Last 30 days
        cur.execute("""
            SELECT COUNT(*) FROM sofia.funding_rounds
            WHERE announced_date >= NOW() - INTERVAL '30 days'
        """)
        count_30 = cur.fetchone()[0]
        print(f'📅 Last 30 days: {count_30}')

        # Last 90 days
        cur.execute("""
            SELECT COUNT(*) FROM sofia.funding_rounds
            WHERE announced_date >= NOW() - INTERVAL '90 days'
        """)
        count_90 = cur.fetchone()[0]
        print(f'📅 Last 90 days: {count_90}')

        # Last 180 days
        cur.execute("""
            SELECT COUNT(*) FROM sofia.funding_rounds
            WHERE announced_date >= NOW() - INTERVAL '180 days'
        """)
        count_180 = cur.fetchone()[0]
        print(f'📅 Last 180 days: {count_180}')

        # By stage
        cur.execute("""
            SELECT funding_stage, COUNT(*) as count
            FROM sofia.funding_rounds
            GROUP BY funding_stage
            ORDER BY count DESC
        """)
        print('\n💰 By Stage:')
        for row in cur.fetchall():
            stage = row[0] or 'Unknown'
            count = row[1]
            print(f'  - {stage}: {count}')

        # Top 5 companies
        cur.execute("""
            SELECT company_name, COUNT(*) as rounds, SUM(amount_usd) as total_raised
            FROM sofia.funding_rounds
            WHERE company_name IS NOT NULL
            GROUP BY company_name
            ORDER BY total_raised DESC NULLS LAST
            LIMIT 5
        """)
        print('\n🏆 Top 5 Companies by Total Raised:')
        for i, row in enumerate(cur.fetchall(), 1):
            company = row[0]
            rounds = row[1]
            total_raised = row[2]
            amount = f'${total_raised/1000000:.1f}M' if total_raised else 'N/A'
            print(f'  {i}. {company}: {rounds} rounds, {amount}')

        cur.close()
        conn.close()

    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    check_funding()
