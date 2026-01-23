#!/usr/bin/env python3
"""
Sofia Pulse - GA4 Intelligence Report

Analyzes Google Analytics 4 data to detect:
1. Trending topics (most accessed pages)
2. Interest in skills (tech pages analysis)
3. Acquisition channels (source/medium engagement)
4. Chat conversations (Sofia AI interactions)
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

# Tech skills keywords mapping
TECH_SKILLS = {
    'AI/ML': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 'neural', 'llm', 'gpt', 'gemini'],
    'Cloud': ['cloud', 'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'devops'],
    'Data': ['data', 'analytics', 'bigquery', 'sql', 'database', 'bi', 'power bi', 'tableau'],
    'Programming': ['python', 'java', 'javascript', 'typescript', 'node', 'react', 'angular', 'vue'],
    'Architecture': ['arquitetura', 'architecture', 'microservices', 'api', 'rest', 'graphql'],
    'Testing': ['test', 'tdd', 'bdd', 'ddd', 'qa', 'quality'],
    'Agile': ['agile', 'scrum', 'kanban', 'sprint'],
    'Security': ['security', 'seguranca', 'ciberseguranca', 'cybersecurity', 'oauth'],
    'Mobile': ['mobile', 'android', 'ios', 'flutter', 'react native'],
    'DevOps': ['devops', 'ci/cd', 'jenkins', 'gitlab', 'github actions'],
}

def get_trending_topics(conn, days=7, limit=20):
    """Get most accessed pages in last N days"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        page_path,
        page_title,
        COUNT(*) as views,
        COUNT(DISTINCT user_pseudo_id) as unique_users,
        COUNT(DISTINCT ga_session_id) as sessions,
        AVG(engagement_time_ms) / 1000 as avg_engagement_seconds
    FROM sofia.analytics_events
    WHERE event_name = 'page_view'
        AND event_date >= CURRENT_DATE - INTERVAL '%s days'
        AND page_path NOT IN ('/', '/blog/', '/cursos/')
        AND page_path IS NOT NULL
    GROUP BY page_path, page_title
    ORDER BY views DESC
    LIMIT %s
    """

    cursor.execute(query, (days, limit))
    return cursor.fetchall()

def extract_skills_from_page(page_path, page_title):
    """Extract tech skills mentioned in page"""
    text = f"{page_path} {page_title}".lower()
    skills_found = []

    for skill_category, keywords in TECH_SKILLS.items():
        for keyword in keywords:
            if keyword in text:
                skills_found.append(skill_category)
                break  # Only add category once

    return list(set(skills_found))

def get_skill_interest(conn, days=30):
    """Analyze interest in tech skills based on page views"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        page_path,
        page_title,
        COUNT(*) as views,
        COUNT(DISTINCT user_pseudo_id) as unique_users
    FROM sofia.analytics_events
    WHERE event_name = 'page_view'
        AND event_date >= CURRENT_DATE - INTERVAL '%s days'
        AND page_path IS NOT NULL
    GROUP BY page_path, page_title
    """

    cursor.execute(query, (days,))
    pages = cursor.fetchall()

    # Aggregate by skill
    skill_interest = defaultdict(lambda: {'views': 0, 'users': set(), 'pages': []})

    for page in pages:
        skills = extract_skills_from_page(page['page_path'], page['page_title'] or '')

        for skill in skills:
            skill_interest[skill]['views'] += page['views']
            skill_interest[skill]['users'].add(page['unique_users'])
            skill_interest[skill]['pages'].append({
                'path': page['page_path'],
                'title': page['page_title'],
                'views': page['views']
            })

    # Convert to list and sort
    result = []
    for skill, data in skill_interest.items():
        result.append({
            'skill': skill,
            'total_views': data['views'],
            'unique_users': sum(data['users']),
            'pages_count': len(data['pages']),
            'top_page': max(data['pages'], key=lambda x: x['views']) if data['pages'] else None
        })

    return sorted(result, key=lambda x: x['total_views'], reverse=True)

def get_acquisition_channels(conn, days=30, limit=15):
    """Analyze acquisition channels by engagement"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        source,
        medium,
        COUNT(*) as events,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNT(DISTINCT ga_session_id) as sessions,
        SUM(engagement_time_ms) / 1000 / 60 as total_engagement_minutes,
        AVG(engagement_time_ms) / 1000 as avg_engagement_seconds,
        COUNT(*) FILTER (WHERE event_name = 'page_view') as page_views,
        COUNT(*) FILTER (WHERE event_name = 'form_submit') as conversions,
        COUNT(*) FILTER (WHERE event_name = 'sofia_response') as chat_interactions
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '%s days'
        AND source IS NOT NULL
    GROUP BY source, medium
    ORDER BY users DESC
    LIMIT %s
    """

    cursor.execute(query, (days, limit))
    return cursor.fetchall()

def get_chat_conversations(conn, days=30):
    """Count Sofia AI chat conversations"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Chat events
    query_events = """
    SELECT
        COUNT(*) as total_chat_events,
        COUNT(DISTINCT user_pseudo_id) as unique_users_chat,
        COUNT(DISTINCT ga_session_id) as sessions_with_chat
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '%s days'
        AND (event_name LIKE '%%sofia%%' OR event_name LIKE '%%chat%%' OR event_name = 'widget_open')
    """

    cursor.execute(query_events, (days,))
    chat_stats = cursor.fetchone()

    # Daily breakdown
    query_daily = """
    SELECT
        event_date,
        COUNT(DISTINCT user_pseudo_id) as users_with_chat,
        COUNT(*) as chat_events
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '%s days'
        AND (event_name LIKE '%%sofia%%' OR event_name LIKE '%%chat%%' OR event_name = 'widget_open')
    GROUP BY event_date
    ORDER BY event_date DESC
    """

    cursor.execute(query_daily, (days,))
    daily_stats = cursor.fetchall()

    return chat_stats, daily_stats

def get_device_breakdown(conn, days=7):
    """Get traffic by device category"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        device_category,
        COUNT(*) as events,
        COUNT(DISTINCT user_pseudo_id) as users,
        AVG(engagement_time_ms) / 1000 as avg_engagement_seconds
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '%s days'
        AND device_category IS NOT NULL
    GROUP BY device_category
    ORDER BY users DESC
    """

    cursor.execute(query, (days,))
    return cursor.fetchall()

def get_top_countries(conn, days=7, limit=10):
    """Get top countries by traffic"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = """
    SELECT
        country,
        COUNT(*) as events,
        COUNT(DISTINCT user_pseudo_id) as users
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '%s days'
        AND country IS NOT NULL
    GROUP BY country
    ORDER BY users DESC
    LIMIT %s
    """

    cursor.execute(query, (days, limit))
    return cursor.fetchall()

def generate_report(trending, skills, channels, chat_stats, daily_chat, devices, countries):
    """Generate formatted report"""

    report = []
    report.append("=" * 100)
    report.append("SOFIA PULSE - GA4 INTELLIGENCE REPORT")
    report.append("=" * 100)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")

    # ========================================================================
    # 1. TRENDING TOPICS (Last 7 Days)
    # ========================================================================

    report.append("=" * 100)
    report.append("1. TRENDING TOPICS - Most Accessed Pages (Last 7 Days)")
    report.append("=" * 100)
    report.append("")

    if trending:
        report.append(f"{'Page':<60} {'Views':>8} {'Users':>8} {'Avg Time':>10}")
        report.append("-" * 100)

        for page in trending[:15]:
            path = page['page_path'][:59]
            views = page['views']
            users = page['unique_users']
            avg_time = f"{page['avg_engagement_seconds']:.0f}s" if page['avg_engagement_seconds'] else "N/A"

            report.append(f"{path:<60} {views:>8,} {users:>8,} {avg_time:>10}")
    else:
        report.append("No trending topics data available.")

    report.append("")

    # ========================================================================
    # 2. TECH SKILLS INTEREST (Last 30 Days)
    # ========================================================================

    report.append("=" * 100)
    report.append("2. TECH SKILLS INTEREST - What Users Are Learning (Last 30 Days)")
    report.append("=" * 100)
    report.append("")

    if skills:
        report.append(f"{'Skill Category':<25} {'Total Views':>12} {'Unique Users':>14} {'Pages':>8} {'Top Page'}")
        report.append("-" * 100)

        for skill in skills[:10]:
            category = skill['skill'][:24]
            views = skill['total_views']
            users = skill['unique_users']
            pages = skill['pages_count']
            top_page = skill['top_page']['path'][:40] if skill['top_page'] else "N/A"

            report.append(f"{category:<25} {views:>12,} {users:>14,} {pages:>8} {top_page}")
    else:
        report.append("No skill interest data available.")

    report.append("")

    # ========================================================================
    # 3. ACQUISITION CHANNELS (Last 30 Days)
    # ========================================================================

    report.append("=" * 100)
    report.append("3. ACQUISITION CHANNELS - Traffic Sources & Engagement (Last 30 Days)")
    report.append("=" * 100)
    report.append("")

    if channels:
        report.append(f"{'Source':<30} {'Medium':<12} {'Users':>8} {'Sessions':>9} {'Avg Time':>10} {'Chat':>6}")
        report.append("-" * 100)

        for channel in channels:
            source = channel['source'][:29]
            medium = channel['medium'][:11] if channel['medium'] else "(none)"
            users = channel['users']
            sessions = channel['sessions']
            avg_time = f"{channel['avg_engagement_seconds']:.0f}s" if channel['avg_engagement_seconds'] else "N/A"
            chat = channel['chat_interactions']

            report.append(f"{source:<30} {medium:<12} {users:>8,} {sessions:>9,} {avg_time:>10} {chat:>6}")
    else:
        report.append("No acquisition channels data available.")

    report.append("")

    # ========================================================================
    # 4. SOFIA AI CHAT CONVERSATIONS (Last 30 Days)
    # ========================================================================

    report.append("=" * 100)
    report.append("4. SOFIA AI CHAT CONVERSATIONS (Last 30 Days)")
    report.append("=" * 100)
    report.append("")

    if chat_stats:
        report.append("Overall Stats:")
        report.append(f"  Total Chat Events: {chat_stats['total_chat_events']:,}")
        report.append(f"  Unique Users with Chat: {chat_stats['unique_users_chat']:,}")
        report.append(f"  Sessions with Chat: {chat_stats['sessions_with_chat']:,}")
        report.append("")

        if daily_chat:
            report.append("Daily Breakdown (Last 7 Days):")
            report.append(f"{'Date':<12} {'Users with Chat':>16} {'Chat Events':>14}")
            report.append("-" * 50)

            for day in daily_chat[:7]:
                date = day['event_date'].strftime('%Y-%m-%d')
                users = day['users_with_chat']
                events = day['chat_events']

                report.append(f"{date:<12} {users:>16,} {events:>14,}")
    else:
        report.append("No chat conversation data available.")

    report.append("")

    # ========================================================================
    # 5. DEVICE & GEO BREAKDOWN
    # ========================================================================

    report.append("=" * 100)
    report.append("5. DEVICE & GEO BREAKDOWN (Last 7 Days)")
    report.append("=" * 100)
    report.append("")

    if devices:
        report.append("Traffic by Device:")
        report.append(f"{'Device':<15} {'Users':>10} {'Events':>10} {'Avg Engagement':>16}")
        report.append("-" * 60)

        for device in devices:
            category = device['device_category'][:14]
            users = device['users']
            events = device['events']
            avg_time = f"{device['avg_engagement_seconds']:.0f}s" if device['avg_engagement_seconds'] else "N/A"

            report.append(f"{category:<15} {users:>10,} {events:>10,} {avg_time:>16}")

    report.append("")

    if countries:
        report.append("Top Countries:")
        report.append(f"{'Country':<20} {'Users':>10} {'Events':>10}")
        report.append("-" * 45)

        for country in countries[:10]:
            name = country['country'][:19]
            users = country['users']
            events = country['events']

            report.append(f"{name:<20} {users:>10,} {events:>10,}")

    report.append("")

    # ========================================================================
    # 6. KEY INSIGHTS
    # ========================================================================

    report.append("=" * 100)
    report.append("6. KEY INSIGHTS")
    report.append("=" * 100)
    report.append("")

    # Top trending page
    if trending:
        top_page = trending[0]
        report.append(f"Most Popular Page: {top_page['page_path']}")
        report.append(f"  - {top_page['views']:,} views from {top_page['unique_users']:,} unique users")

    # Hottest skill
    if skills:
        top_skill = skills[0]
        report.append(f"\nHottest Tech Skill: {top_skill['skill']}")
        report.append(f"  - {top_skill['total_views']:,} total views across {top_skill['pages_count']} pages")

    # Best acquisition channel
    if channels:
        top_channel = channels[0]
        report.append(f"\nBest Acquisition Channel: {top_channel['source']} / {top_channel['medium']}")
        report.append(f"  - {top_channel['users']:,} users, avg engagement {top_channel['avg_engagement_seconds']:.0f}s")

    # Chat engagement
    if chat_stats and chat_stats['unique_users_chat'] > 0:
        report.append(f"\nSofia AI Engagement: {chat_stats['unique_users_chat']:,} users had chat interactions")
        if chat_stats['total_chat_events'] > 0:
            report.append(f"  - {chat_stats['total_chat_events']:,} total chat events")

    report.append("")
    report.append("=" * 100)
    report.append("END OF REPORT")
    report.append("=" * 100)

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("Loading GA4 data...")

        # Fetch data
        trending = get_trending_topics(conn, days=7, limit=20)
        print(f"  Trending topics: {len(trending)} pages")

        skills = get_skill_interest(conn, days=30)
        print(f"  Tech skills: {len(skills)} categories")

        channels = get_acquisition_channels(conn, days=30, limit=15)
        print(f"  Acquisition channels: {len(channels)} sources")

        chat_stats, daily_chat = get_chat_conversations(conn, days=30)
        print(f"  Chat conversations: {chat_stats['unique_users_chat'] if chat_stats else 0} users")

        devices = get_device_breakdown(conn, days=7)
        print(f"  Device breakdown: {len(devices)} devices")

        countries = get_top_countries(conn, days=7, limit=10)
        print(f"  Top countries: {len(countries)} countries")

        print("")
        print("Generating report...")

        report = generate_report(trending, skills, channels, chat_stats, daily_chat, devices, countries)

        # Print to console
        print(report)

        # Save to file
        os.makedirs("outputs", exist_ok=True)
        output_file = "outputs/ga4-intelligence-report.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n✅ Report saved to: {output_file}")

        conn.close()

    except Exception as e:
        print(f"[ERROR] Failed to generate GA4 intelligence report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
