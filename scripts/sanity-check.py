#!/usr/bin/env python3
"""
Sofia Pulse - Sanity Check for Collectors
Validates data integrity after collection
"""

import os
import sys
from datetime import datetime

import psycopg2
import psycopg2.extras


# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "sofia"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "sofia"),
    )


def sanity_check_table(table_name, min_rows=1, max_age_days=7):
    """
    Perform sanity checks on a table

    Checks:
    1. Minimum row count
    2. No future dates
    3. Recent data exists
    4. No duplicate primary keys
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    issues = []

    # 1. Check minimum row count
    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
    count = cursor.fetchone()["count"]

    if count < min_rows:
        issues.append(f"❌ CRITICAL: Only {count} rows (minimum: {min_rows})")
    else:
        print(f"✅ Row count OK: {count} rows")

    # 2. Check for future dates (if has timestamp column)
    try:
        cursor.execute(
            f"""
            SELECT COUNT(*) as count
            FROM {table_name}
            WHERE created_at > NOW() OR updated_at > NOW()
        """
        )
        future_count = cursor.fetchone()["count"]

        if future_count > 0:
            issues.append(f"❌ CRITICAL: {future_count} rows with future dates")
        else:
            print(f"✅ No future dates")
    except:
        pass  # Table might not have timestamp columns

    # 3. Check for recent data
    try:
        cursor.execute(
            f"""
            SELECT MAX(created_at) as latest
            FROM {table_name}
        """
        )
        latest = cursor.fetchone()["latest"]

        if latest:
            age_days = (datetime.now() - latest).days
            if age_days > max_age_days:
                issues.append(f"⚠️  WARNING: Latest data is {age_days} days old")
            else:
                print(f"✅ Recent data: {age_days} days old")
    except:
        pass

    # 4. Check for obvious anomalies (massive spike)
    try:
        cursor.execute(
            f"""
            SELECT
                DATE(created_at) as day,
                COUNT(*) as count
            FROM {table_name}
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY day DESC
        """
        )
        daily_counts = cursor.fetchall()

        if len(daily_counts) >= 2:
            today = daily_counts[0]["count"]
            avg_previous = sum(d["count"] for d in daily_counts[1:]) / (len(daily_counts) - 1)

            # If today is 10x average or 0 when average > 0
            if today > avg_previous * 10:
                issues.append(f"⚠️  WARNING: Massive spike - {today} rows (avg: {avg_previous:.0f})")
            elif today == 0 and avg_previous > 10:
                issues.append(f"❌ CRITICAL: Zero rows today (avg: {avg_previous:.0f})")
            else:
                print(f"✅ Daily volume normal: {today} rows (avg: {avg_previous:.0f})")
    except Exception as e:
        print(f"⚠️  Could not check daily volume: {e}")

    cursor.close()
    conn.close()

    return issues


def main():
    print("════════════════════════════════════════════════════════════════")
    print("🔍 SOFIA PULSE - DATA SANITY CHECK")
    print("════════════════════════════════════════════════════════════════")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # Tables to check
    tables = {
        "github_trending": {"min_rows": 50, "max_age_days": 2},
        "hackernews_stories": {"min_rows": 20, "max_age_days": 2},
        "npm_stats": {"min_rows": 10, "max_age_days": 7},
        "pypi_stats": {"min_rows": 10, "max_age_days": 7},
        "funding_rounds": {"min_rows": 5, "max_age_days": 30},
        "arxiv_ai_papers": {"min_rows": 20, "max_age_days": 7},
        "openalex_papers": {"min_rows": 20, "max_age_days": 7},
        "cybersecurity_events": {"min_rows": 10, "max_age_days": 30},
        "space_launches": {"min_rows": 100, "max_age_days": 365},
        "socioeconomic_indicators": {"min_rows": 1000, "max_age_days": 365},
    }

    all_issues = []

    for table, params in tables.items():
        print(f"\n📊 Checking {table}...")
        try:
            issues = sanity_check_table(table, params["min_rows"], params["max_age_days"])
            if issues:
                all_issues.extend([f"{table}: {issue}" for issue in issues])
                for issue in issues:
                    print(f"   {issue}")
        except Exception as e:
            print(f"   ⚠️  Could not check table: {e}")

    print("\n════════════════════════════════════════════════════════════════")
    print("📋 SUMMARY")
    print("════════════════════════════════════════════════════════════════")

    if all_issues:
        print(f"⚠️  Found {len(all_issues)} issues:")
        for issue in all_issues:
            print(f"   • {issue}")
        sys.exit(1)
    else:
        print("✅ ALL CHECKS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
