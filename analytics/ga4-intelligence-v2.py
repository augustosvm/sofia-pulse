#!/usr/bin/env python3
"""
Sofia Pulse - GA4 Intelligence V2 (Store Everything, Report What Matters)

Philosophy:
- Collection: STORE EVERYTHING (all GA4 events)
- Reports: SHOW ONLY WHAT DRIVES DECISIONS

Semantic Classification (report-only, not collection):
- REAL_CONVERSATION (≥1 user message)
- DEEP_READ (scroll ≥90% OR engagement_time ≥45s)
- CONTEXT (page_view, source, device)
- NOISE (not shown)
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

# ============================================================================
# SEMANTIC CLASSIFICATION (Report-Only)
# ============================================================================

def classify_event(event_name, engagement_time_ms=None):
    """
    Classify event for reporting purposes.

    Returns: REAL_CONVERSATION, DEEP_READ, CONTEXT, NOISE
    """
    event_lower = event_name.lower() if event_name else ''

    # Chat events
    if any(x in event_lower for x in ['chat_user_message', 'sofia_response']):
        return 'REAL_CONVERSATION'

    # Deep read proxy
    if engagement_time_ms and engagement_time_ms >= 45000:  # 45s
        return 'DEEP_READ'

    # Context events
    if event_name in ['page_view', 'session_start', 'first_visit']:
        return 'CONTEXT'

    # Noise (not shown in reports)
    if any(x in event_lower for x in ['widget_open', 'scroll', 'typing']):
        return 'NOISE'

    return 'CONTEXT'

def is_qualified_conversation(messages_count, total_chars, interaction_time_s):
    """
    Determine if a conversation is qualified.

    Qualified = ≥3 messages OR ≥200 chars OR ≥120s interaction
    """
    return (
        messages_count >= 3
        or total_chars >= 200
        or interaction_time_s >= 120
    )

# ============================================================================
# DATA FETCHERS
# ============================================================================

def get_executive_summary(conn, days=7):
    """Get executive summary metrics"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Real conversations (≥1 user message)
    query_chat = f"""
    SELECT
        COUNT(DISTINCT user_pseudo_id) as users_with_conversation,
        COUNT(DISTINCT ga_session_id) as sessions_with_conversation
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
        AND (event_name LIKE '%%chat_user_message%%' OR event_name = 'sofia_response')
    """

    cursor.execute(query_chat)
    chat_stats = cursor.fetchone()

    # Deep read (engagement_time ≥ 45s)
    query_deep_read = f"""
    SELECT
        COUNT(DISTINCT user_pseudo_id) as users_with_deep_read,
        COUNT(*) as deep_read_events
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
        AND engagement_time_ms >= 45000
        AND event_name = 'page_view'
    """

    cursor.execute(query_deep_read)
    deep_read_stats = cursor.fetchone()

    # Return 7d (users who came back)
    query_return = f"""
    WITH first_visit_users AS (
        SELECT DISTINCT user_pseudo_id, MIN(event_date) as first_date
        FROM sofia.analytics_events
        WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY user_pseudo_id
    ),
    returning_users AS (
        SELECT DISTINCT f.user_pseudo_id
        FROM first_visit_users f
        JOIN sofia.analytics_events e ON f.user_pseudo_id = e.user_pseudo_id
        WHERE e.event_date > f.first_date
            AND e.event_date <= f.first_date + INTERVAL '7 days'
    )
    SELECT
        COUNT(DISTINCT f.user_pseudo_id) as total_new_users,
        COUNT(DISTINCT r.user_pseudo_id) as returning_users
    FROM first_visit_users f
    LEFT JOIN returning_users r ON f.user_pseudo_id = r.user_pseudo_id
    """

    cursor.execute(query_return)
    return_stats = cursor.fetchone()

    # Total users
    cursor.execute(f"""
        SELECT COUNT(DISTINCT user_pseudo_id) as total_users
        FROM sofia.analytics_events
        WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
    """)
    total_users = cursor.fetchone()['total_users']

    return {
        'conversations': chat_stats['users_with_conversation'] or 0,
        'deep_read_users': deep_read_stats['users_with_deep_read'] or 0,
        'deep_read_pct': (deep_read_stats['users_with_deep_read'] or 0) * 100 / total_users if total_users > 0 else 0,
        'returning_pct': (return_stats['returning_users'] or 0) * 100 / (return_stats['total_new_users'] or 1),
        'total_users': total_users
    }

def get_chat_intelligence(conn, days=30):
    """Get chat conversation intelligence"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Users who sent at least 1 message
    query_conversations = f"""
    SELECT
        COUNT(DISTINCT user_pseudo_id) as users_with_message,
        COUNT(DISTINCT ga_session_id) as conversations_started,
        COUNT(*) as total_messages
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
        AND (event_name LIKE '%%chat_user_message%%' OR event_name = 'sofia_response')
    """

    cursor.execute(query_conversations)
    chat_stats = cursor.fetchone()

    # Top pages that generated conversations
    query_pages = f"""
    SELECT
        page_path,
        page_title,
        COUNT(DISTINCT user_pseudo_id) as users_with_chat,
        COUNT(DISTINCT ga_session_id) as conversations
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
        AND (event_name LIKE '%%chat_user_message%%' OR event_name = 'sofia_response')
        AND page_path IS NOT NULL
    GROUP BY page_path, page_title
    ORDER BY users_with_chat DESC
    LIMIT 10
    """

    cursor.execute(query_pages)
    top_pages = cursor.fetchall()

    # Top sources that generated conversations
    query_sources = f"""
    SELECT
        source,
        medium,
        COUNT(DISTINCT user_pseudo_id) as users_with_chat,
        COUNT(DISTINCT ga_session_id) as conversations
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
        AND (event_name LIKE '%%chat_user_message%%' OR event_name = 'sofia_response')
        AND source IS NOT NULL
    GROUP BY source, medium
    ORDER BY users_with_chat DESC
    LIMIT 10
    """

    cursor.execute(query_sources)
    top_sources = cursor.fetchall()

    return {
        'stats': chat_stats,
        'top_pages': top_pages,
        'top_sources': top_sources
    }

def get_content_by_source(conn, days=7):
    """Get content performance by acquisition channel"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = f"""
    SELECT
        source,
        medium,
        page_path,
        page_title,
        COUNT(DISTINCT user_pseudo_id) as users,
        COUNT(*) FILTER (WHERE event_name = 'page_view') as page_views,
        COUNT(*) FILTER (WHERE engagement_time_ms >= 45000) as deep_reads,
        COUNT(*) FILTER (WHERE event_name LIKE '%%chat_user_message%%' OR event_name = 'sofia_response') as chat_events,
        AVG(engagement_time_ms) / 1000 as avg_engagement_seconds
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
        AND source IS NOT NULL
        AND page_path IS NOT NULL
    GROUP BY source, medium, page_path, page_title
    ORDER BY users DESC
    LIMIT 50
    """

    cursor.execute(query)
    return cursor.fetchall()

def get_deep_read_analysis(conn, days=7):
    """Get deep read analysis"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = f"""
    SELECT
        page_path,
        page_title,
        COUNT(DISTINCT user_pseudo_id) as total_users,
        COUNT(*) FILTER (WHERE event_name = 'page_view') as total_views,
        COUNT(*) FILTER (WHERE engagement_time_ms >= 45000) as deep_reads,
        AVG(engagement_time_ms) / 1000 as avg_engagement_seconds,
        CASE
            WHEN COUNT(*) FILTER (WHERE event_name = 'page_view') > 0
            THEN (COUNT(*) FILTER (WHERE engagement_time_ms >= 45000)::float / COUNT(*) FILTER (WHERE event_name = 'page_view')) * 100
            ELSE 0
        END as deep_read_rate
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
        AND page_path NOT IN ('/', '/blog/', '/cursos/')
        AND page_path IS NOT NULL
    GROUP BY page_path, page_title
    HAVING COUNT(*) FILTER (WHERE event_name = 'page_view') >= 2
    ORDER BY deep_reads DESC
    LIMIT 20
    """

    cursor.execute(query)
    return cursor.fetchall()

def get_retention_analysis(conn, days=30):
    """Get retention cohort analysis"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # New vs returning users
    query_cohort = f"""
    WITH user_first_visit AS (
        SELECT user_pseudo_id, MIN(event_date) as first_date
        FROM sofia.analytics_events
        WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
        GROUP BY user_pseudo_id
    ),
    user_stats AS (
        SELECT
            u.user_pseudo_id,
            u.first_date,
            COUNT(DISTINCT e.event_date) as active_days,
            COUNT(*) FILTER (WHERE e.engagement_time_ms >= 45000) as deep_reads,
            COUNT(*) FILTER (WHERE e.event_name LIKE '%%chat_user_message%%') as chat_messages
        FROM user_first_visit u
        JOIN sofia.analytics_events e ON u.user_pseudo_id = e.user_pseudo_id
        GROUP BY u.user_pseudo_id, u.first_date
    )
    SELECT
        CASE WHEN active_days = 1 THEN 'New (1 day)' ELSE 'Returning (2+ days)' END as cohort,
        COUNT(*) as users,
        AVG(deep_reads) as avg_deep_reads,
        AVG(chat_messages) as avg_chat_messages
    FROM user_stats
    GROUP BY CASE WHEN active_days = 1 THEN 'New (1 day)' ELSE 'Returning (2+ days)' END
    """

    cursor.execute(query_cohort)
    return cursor.fetchall()

def calculate_page_score(users, deep_reads, chat_events, total_views):
    """
    Calculate page quality score (0-100)

    Weights:
    - Deep read rate: 40%
    - Chat rate: 30%
    - Traffic volume: 20%
    - Bounce proxy penalty: 10%
    """
    if total_views == 0:
        return 0

    deep_read_rate = (deep_reads / total_views) * 100 if total_views > 0 else 0
    chat_rate = (chat_events / users) * 100 if users > 0 else 0
    traffic_score = min(users / 100 * 100, 100)  # Cap at 100 users

    # Bounce proxy: penalize if avg engagement is too low
    bounce_penalty = 0  # Would need avg_engagement to calculate

    score = (
        deep_read_rate * 0.4 +
        chat_rate * 0.3 +
        traffic_score * 0.2 +
        (100 - bounce_penalty) * 0.1
    )

    return min(score, 100)

def calculate_channel_score(deep_read_avg, chat_rate, return_7d_rate):
    """
    Calculate channel quality score (0-100)

    Weights:
    - Deep read average: 40%
    - Chat conversion: 35%
    - 7-day return: 25%
    """
    score = (
        deep_read_avg * 0.4 +
        chat_rate * 0.35 +
        return_7d_rate * 0.25
    )

    return min(score, 100)

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report_v2(exec_summary, chat_intel, content_by_source, deep_read, retention):
    """Generate V2 intelligence report"""

    report = []
    report.append("=" * 100)
    report.append("SOFIA PULSE - GA4 INTELLIGENCE V2 (Store Everything, Report What Matters)")
    report.append("=" * 100)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")
    report.append("Philosophy: Collection = Store ALL events | Reports = Show only decision-driving metrics")
    report.append("")

    # ========================================================================
    # 1. EXECUTIVE SUMMARY (Deterministic)
    # ========================================================================

    report.append("=" * 100)
    report.append("1. EXECUTIVE SUMMARY (7 Days)")
    report.append("=" * 100)
    report.append("")

    report.append(f"Signal: {exec_summary['conversations']} real conversations, "
                 f"{exec_summary['deep_read_pct']:.1f}% deep read, "
                 f"{exec_summary['returning_pct']:.1f}% return 7d")
    report.append("")
    report.append(f"Total Users: {exec_summary['total_users']:,}")
    report.append(f"Users with Conversations: {exec_summary['conversations']:,}")
    report.append(f"Users with Deep Read: {exec_summary['deep_read_users']:,}")
    report.append("")

    # ========================================================================
    # 2. CHAT INTELLIGENCE
    # ========================================================================

    report.append("=" * 100)
    report.append("2. CHAT INTELLIGENCE (30 Days)")
    report.append("=" * 100)
    report.append("")

    if chat_intel['stats']:
        stats = chat_intel['stats']
        report.append(f"Users who sent message: {stats['users_with_message']:,}")
        report.append(f"Conversations started: {stats['conversations_started']:,}")
        report.append(f"Total messages: {stats['total_messages']:,}")

        if stats['conversations_started'] > 0:
            avg_msgs = stats['total_messages'] / stats['conversations_started']
            report.append(f"Avg messages per conversation: {avg_msgs:.1f}")

    report.append("")

    if chat_intel['top_pages']:
        report.append("Top Pages Generating Conversations:")
        report.append(f"{'Page':<60} {'Users':>8} {'Convs':>8}")
        report.append("-" * 80)

        for page in chat_intel['top_pages'][:5]:
            path = page['page_path'][:59]
            users = page['users_with_chat']
            convs = page['conversations']
            report.append(f"{path:<60} {users:>8} {convs:>8}")

    report.append("")

    if chat_intel['top_sources']:
        report.append("Top Sources Generating Conversations:")
        report.append(f"{'Source':<30} {'Medium':<15} {'Users':>8} {'Convs':>8}")
        report.append("-" * 70)

        for src in chat_intel['top_sources'][:5]:
            source = src['source'][:29]
            medium = (src['medium'] or '(none)')[:14]
            users = src['users_with_chat']
            convs = src['conversations']
            report.append(f"{source:<30} {medium:<15} {users:>8} {convs:>8}")

    report.append("")

    # ========================================================================
    # 3. DEEP READ ANALYSIS
    # ========================================================================

    report.append("=" * 100)
    report.append("3. DEEP READ ANALYSIS (7 Days)")
    report.append("=" * 100)
    report.append("")
    report.append("Deep Read = engagement_time >= 45s (or scroll >= 90% if available)")
    report.append("")

    if deep_read:
        report.append(f"{'Page':<55} {'Views':>8} {'Deep':>8} {'Rate':>8}")
        report.append("-" * 85)

        for page in deep_read[:10]:
            path = page['page_path'][:54]
            views = page['total_views']
            deep = page['deep_reads']
            rate = page['deep_read_rate']
            report.append(f"{path:<55} {views:>8} {deep:>8} {rate:>7.1f}%")

        report.append("")

        # Opportunities (high deep read, low traffic)
        opportunities = [p for p in deep_read if p['deep_read_rate'] >= 50 and p['total_views'] < 10]
        if opportunities:
            report.append("Opportunities (High quality, low traffic):")
            for page in opportunities[:3]:
                report.append(f"  • {page['page_path']} - {page['deep_read_rate']:.0f}% deep read, only {page['total_views']} views")

        report.append("")

        # Problems (high traffic, low deep read)
        problems = [p for p in deep_read if p['total_views'] >= 10 and p['deep_read_rate'] < 20]
        if problems:
            report.append("Problems (High traffic, low engagement):")
            for page in problems[:3]:
                report.append(f"  • {page['page_path']} - {page['total_views']} views, only {page['deep_read_rate']:.0f}% deep read")

    report.append("")

    # ========================================================================
    # 4. RETENTION COHORTS
    # ========================================================================

    report.append("=" * 100)
    report.append("4. RETENTION ANALYSIS (30 Days)")
    report.append("=" * 100)
    report.append("")

    if retention:
        report.append(f"{'Cohort':<20} {'Users':>10} {'Avg Deep Reads':>16} {'Avg Chat Msgs':>16}")
        report.append("-" * 70)

        for cohort in retention:
            name = cohort['cohort']
            users = cohort['users']
            deep = cohort['avg_deep_reads'] or 0
            chat = cohort['avg_chat_messages'] or 0
            report.append(f"{name:<20} {users:>10} {deep:>16.1f} {chat:>16.1f}")

    report.append("")

    # ========================================================================
    # 5. CHANNEL QUALITY SCORES
    # ========================================================================

    report.append("=" * 100)
    report.append("5. ACQUISITION CHANNEL SCORES (7 Days)")
    report.append("=" * 100)
    report.append("")

    # Aggregate by source/medium
    channel_stats = defaultdict(lambda: {
        'users': 0,
        'page_views': 0,
        'deep_reads': 0,
        'chat_events': 0
    })

    for row in content_by_source:
        key = f"{row['source']} / {row['medium'] or '(none)'}"
        channel_stats[key]['users'] += row['users']
        channel_stats[key]['page_views'] += row['page_views']
        channel_stats[key]['deep_reads'] += row['deep_reads']
        channel_stats[key]['chat_events'] += row['chat_events']

    # Calculate scores
    channel_scores = []
    for channel, stats in channel_stats.items():
        if stats['page_views'] > 0:
            deep_read_rate = (stats['deep_reads'] / stats['page_views']) * 100
            chat_rate = (stats['chat_events'] / stats['users']) * 100 if stats['users'] > 0 else 0

            # Simplified score (no 7d return data yet)
            score = (deep_read_rate * 0.5 + chat_rate * 0.5)

            channel_scores.append({
                'channel': channel,
                'users': stats['users'],
                'deep_read_rate': deep_read_rate,
                'chat_rate': chat_rate,
                'score': min(score, 100)
            })

    channel_scores.sort(key=lambda x: x['score'], reverse=True)

    if channel_scores:
        report.append(f"{'Channel':<35} {'Users':>8} {'Deep%':>8} {'Chat%':>8} {'Score':>8}")
        report.append("-" * 75)

        for ch in channel_scores[:10]:
            channel = ch['channel'][:34]
            users = ch['users']
            deep = ch['deep_read_rate']
            chat = ch['chat_rate']
            score = ch['score']
            report.append(f"{channel:<35} {users:>8} {deep:>7.1f}% {chat:>7.1f}% {score:>7.0f}/100")

    report.append("")

    # ========================================================================
    # 6. RECOMMENDED ACTIONS
    # ========================================================================

    report.append("=" * 100)
    report.append("6. RECOMMENDED ACTIONS")
    report.append("=" * 100)
    report.append("")

    # Action 1: Low conversation rate
    if exec_summary['total_users'] > 0:
        conv_rate = (exec_summary['conversations'] / exec_summary['total_users']) * 100
        if conv_rate < 10:
            report.append(f"ACTION 1: Conversation rate is {conv_rate:.1f}% (target: >10%)")
            report.append(f"  → If conversation rate < 10%, then improve chat visibility on high-traffic pages")
            report.append(f"  → Owner: Product. SLA: 7 days")
            report.append("")

    # Action 2: Deep read opportunities
    opportunities = [p for p in deep_read if p['deep_read_rate'] >= 50 and p['total_views'] < 10]
    if opportunities:
        report.append(f"ACTION 2: {len(opportunities)} pages have high engagement but low traffic")
        report.append(f"  → If deep_read_rate > 50% AND views < 10, then promote via social/email")
        report.append(f"  → Owner: Marketing. SLA: 3 days")
        report.append("")

    # Action 3: Low engagement pages
    problems = [p for p in deep_read if p['total_views'] >= 10 and p['deep_read_rate'] < 20]
    if problems:
        report.append(f"ACTION 3: {len(problems)} pages have high traffic but low engagement")
        report.append(f"  → If views >= 10 AND deep_read_rate < 20%, then audit content quality")
        report.append(f"  → Owner: Content. SLA: 5 days")
        report.append("")

    report.append("=" * 100)
    report.append("END OF REPORT")
    report.append("=" * 100)

    return "\n".join(report)

# ============================================================================
# CSV EXPORTS
# ============================================================================

def export_chat_intelligence_csv(chat_intel, output_dir):
    """Export chat intelligence to CSV"""
    import csv

    filepath = f"{output_dir}/ga4-chat-intelligence.csv"

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['page_path', 'page_title', 'users_with_chat', 'conversations'])

        for page in chat_intel['top_pages']:
            writer.writerow([
                page['page_path'],
                page['page_title'],
                page['users_with_chat'],
                page['conversations']
            ])

    return filepath

def export_content_by_source_csv(content_by_source, output_dir):
    """Export content by source to CSV"""
    import csv

    filepath = f"{output_dir}/ga4-content-by-source.csv"

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['source', 'medium', 'page_path', 'page_title', 'users', 'page_views', 'deep_reads', 'chat_events', 'avg_engagement_s'])

        for row in content_by_source:
            writer.writerow([
                row['source'],
                row['medium'] or '(none)',
                row['page_path'],
                row['page_title'],
                row['users'],
                row['page_views'],
                row['deep_reads'],
                row['chat_events'],
                f"{row['avg_engagement_seconds']:.1f}" if row['avg_engagement_seconds'] else '0'
            ])

    return filepath

def export_deep_read_csv(deep_read, output_dir):
    """Export deep read analysis to CSV"""
    import csv

    filepath = f"{output_dir}/ga4-deep-read.csv"

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['page_path', 'page_title', 'total_users', 'total_views', 'deep_reads', 'deep_read_rate', 'avg_engagement_s'])

        for page in deep_read:
            writer.writerow([
                page['page_path'],
                page['page_title'],
                page['total_users'],
                page['total_views'],
                page['deep_reads'],
                f"{page['deep_read_rate']:.1f}",
                f"{page['avg_engagement_seconds']:.1f}" if page['avg_engagement_seconds'] else '0'
            ])

    return filepath

def export_retention_csv(retention, output_dir):
    """Export retention analysis to CSV"""
    import csv

    filepath = f"{output_dir}/ga4-retention.csv"

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['cohort', 'users', 'avg_deep_reads', 'avg_chat_messages'])

        for cohort in retention:
            writer.writerow([
                cohort['cohort'],
                cohort['users'],
                f"{cohort['avg_deep_reads']:.1f}" if cohort['avg_deep_reads'] else '0',
                f"{cohort['avg_chat_messages']:.1f}" if cohort['avg_chat_messages'] else '0'
            ])

    return filepath

# ============================================================================
# MAIN
# ============================================================================

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("Loading GA4 Intelligence V2 data...")

        # Fetch all data
        exec_summary = get_executive_summary(conn, days=7)
        print(f"  Executive summary: {exec_summary['total_users']} users")

        chat_intel = get_chat_intelligence(conn, days=30)
        print(f"  Chat intelligence: {chat_intel['stats']['users_with_message'] if chat_intel['stats'] else 0} users with messages")

        content_by_source = get_content_by_source(conn, days=7)
        print(f"  Content by source: {len(content_by_source)} rows")

        deep_read = get_deep_read_analysis(conn, days=7)
        print(f"  Deep read analysis: {len(deep_read)} pages")

        retention = get_retention_analysis(conn, days=30)
        print(f"  Retention cohorts: {len(retention)} cohorts")

        print("")
        print("Generating V2 report...")

        # Generate report
        report = generate_report_v2(exec_summary, chat_intel, content_by_source, deep_read, retention)

        # Print to console
        print(report)

        # Save TXT report
        os.makedirs("outputs", exist_ok=True)
        txt_file = "outputs/ga4-intelligence-v2.txt"

        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n✅ TXT report saved to: {txt_file}")

        # Export CSVs
        csv1 = export_chat_intelligence_csv(chat_intel, "outputs")
        csv2 = export_content_by_source_csv(content_by_source, "outputs")
        csv3 = export_deep_read_csv(deep_read, "outputs")
        csv4 = export_retention_csv(retention, "outputs")

        print(f"✅ CSV exports:")
        print(f"   - {csv1}")
        print(f"   - {csv2}")
        print(f"   - {csv3}")
        print(f"   - {csv4}")

        conn.close()

    except Exception as e:
        print(f"[ERROR] Failed to generate GA4 Intelligence V2: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
