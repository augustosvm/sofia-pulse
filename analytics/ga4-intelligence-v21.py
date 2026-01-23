#!/usr/bin/env python3
"""
Sofia Pulse - GA4 Intelligence V2.1 (Complete Production System)

Philosophy: Store Everything, Report What Matters

Features:
- Deep Read Score based on word_count (not fixed 45s)
- Real conversations (>= 1 user message)
- Minimum sample sizes (no false rankings)
- Deterministic scoring (same input = same output)
- Recommended actions (if-then format with owner/SLA)
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import defaultdict
import csv
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

# Minimum sample sizes (no false rankings)
MIN_USERS_CHANNEL = 20
MIN_USERS_PAGE = 15
MIN_CONVERSATIONS = 5
MIN_DAYS_BASELINE = 14

# Deep read thresholds
DEEP_READ_TRUE_THRESHOLD = 0.85
DEEP_READ_PARTIAL_THRESHOLD = 0.45
DEEP_READ_PROXY_FALLBACK_SEC = 45

# ============================================================================
# DATA FETCHERS
# ============================================================================

def get_executive_summary(conn, days=7):
    """Get executive summary with intelligent deep read scoring"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Total users
    cursor.execute(f"""
        SELECT COUNT(DISTINCT user_pseudo_id) as total_users
        FROM sofia.analytics_events
        WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
    """)
    total_users = cursor.fetchone()['total_users']

    # Real conversations (from derived table)
    cursor.execute(f"""
        SELECT
            COUNT(DISTINCT user_pseudo_id) as users_with_conversation,
            COUNT(*) FILTER (WHERE qualified) as qualified_conversations
        FROM sofia.ga4_chat_sessions
        WHERE started_at >= CURRENT_DATE - INTERVAL '{days} days'
    """)
    chat_stats = cursor.fetchone()

    # Deep read using content_meta
    cursor.execute(f"""
        SELECT
            COUNT(DISTINCT e.user_pseudo_id) as users_with_deep_read,
            COUNT(*) as deep_read_events
        FROM sofia.analytics_events e
        JOIN sofia.content_meta cm ON e.page_path = cm.page_path
        WHERE e.event_date >= CURRENT_DATE - INTERVAL '{days} days'
            AND e.event_name = 'page_view'
            AND e.engagement_time_ms >= (cm.reading_time_sec * 1000 * {DEEP_READ_TRUE_THRESHOLD})
    """)
    deep_read = cursor.fetchone()

    # Fallback: use proxy for pages without content_meta
    cursor.execute(f"""
        SELECT
            COUNT(DISTINCT user_pseudo_id) as users_with_deep_read_proxy
        FROM sofia.analytics_events
        WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
            AND event_name = 'page_view'
            AND engagement_time_ms >= {DEEP_READ_PROXY_FALLBACK_SEC * 1000}
            AND page_path NOT IN (SELECT page_path FROM sofia.content_meta)
    """)
    deep_read_proxy = cursor.fetchone()

    # Return 7d (simple proxy)
    cursor.execute(f"""
        WITH first_visit AS (
            SELECT user_pseudo_id, MIN(event_date) as first_date
            FROM sofia.analytics_events
            WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY user_pseudo_id
        ),
        returners AS (
            SELECT DISTINCT f.user_pseudo_id
            FROM first_visit f
            JOIN sofia.analytics_events e ON f.user_pseudo_id = e.user_pseudo_id
            WHERE e.event_date > f.first_date
                AND e.event_date <= f.first_date + INTERVAL '7 days'
        )
        SELECT
            COUNT(DISTINCT f.user_pseudo_id) as new_users,
            COUNT(DISTINCT r.user_pseudo_id) as returning_users
        FROM first_visit f
        LEFT JOIN returners r ON f.user_pseudo_id = r.user_pseudo_id
    """)
    return_stats = cursor.fetchone()

    deep_read_total = (deep_read['users_with_deep_read'] or 0) + (deep_read_proxy['users_with_deep_read_proxy'] or 0)

    return {
        'total_users': total_users,
        'conversations': chat_stats['users_with_conversation'] or 0,
        'qualified_conversations': chat_stats['qualified_conversations'] or 0,
        'deep_read_users': deep_read_total,
        'deep_read_pct': (deep_read_total * 100 / total_users) if total_users > 0 else 0,
        'returning_pct': (return_stats['returning_users'] or 0) * 100 / (return_stats['new_users'] or 1),
        'deep_read_with_meta': deep_read['users_with_deep_read'] or 0,
        'deep_read_proxy': deep_read_proxy['users_with_deep_read_proxy'] or 0
    }

def get_chat_intelligence(conn, days=30):
    """Get chat intelligence from derived table"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Overall stats
    cursor.execute(f"""
        SELECT
            COUNT(DISTINCT user_pseudo_id) as users_with_message,
            COUNT(*) as conversations_started,
            COUNT(*) FILTER (WHERE qualified) as qualified_conversations,
            SUM(user_messages_count) as total_messages,
            AVG(user_messages_count) as avg_messages_per_conv
        FROM sofia.ga4_chat_sessions
        WHERE started_at >= CURRENT_DATE - INTERVAL '{days} days'
    """)
    stats = cursor.fetchone()

    # Top pages
    cursor.execute(f"""
        SELECT
            entry_page_path,
            COUNT(DISTINCT user_pseudo_id) as users_with_chat,
            COUNT(*) as conversations,
            COUNT(*) FILTER (WHERE qualified) as qualified
        FROM sofia.ga4_chat_sessions
        WHERE started_at >= CURRENT_DATE - INTERVAL '{days} days'
            AND entry_page_path IS NOT NULL
        GROUP BY entry_page_path
        ORDER BY users_with_chat DESC
        LIMIT 10
    """)
    top_pages = cursor.fetchall()

    # Top sources
    cursor.execute(f"""
        SELECT
            source,
            medium,
            COUNT(DISTINCT user_pseudo_id) as users_with_chat,
            COUNT(*) as conversations
        FROM sofia.ga4_chat_sessions
        WHERE started_at >= CURRENT_DATE - INTERVAL '{days} days'
            AND source IS NOT NULL
        GROUP BY source, medium
        ORDER BY users_with_chat DESC
        LIMIT 10
    """)
    top_sources = cursor.fetchall()

    return {
        'stats': stats,
        'top_pages': top_pages,
        'top_sources': top_sources
    }

def get_deep_read_with_scores(conn, days=7):
    """Get deep read analysis with intelligent scoring"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = f"""
    SELECT
        e.page_path,
        cm.title,
        cm.word_count,
        cm.reading_time_sec,
        COUNT(DISTINCT e.user_pseudo_id) as users,
        COUNT(*) FILTER (WHERE e.event_name = 'page_view') as pageviews,
        AVG(e.engagement_time_ms / 1000.0) as avg_engagement_sec,
        AVG(
            CASE
                WHEN cm.reading_time_sec > 0
                THEN LEAST(1.0, (e.engagement_time_ms / 1000.0) / cm.reading_time_sec)
                ELSE NULL
            END
        ) as avg_deep_read_score,
        COUNT(*) FILTER (
            WHERE cm.reading_time_sec > 0
            AND (e.engagement_time_ms / 1000.0) >= (cm.reading_time_sec * {DEEP_READ_TRUE_THRESHOLD})
        ) as deep_read_true_count,
        COUNT(*) FILTER (
            WHERE cm.reading_time_sec > 0
            AND (e.engagement_time_ms / 1000.0) >= (cm.reading_time_sec * {DEEP_READ_PARTIAL_THRESHOLD})
            AND (e.engagement_time_ms / 1000.0) < (cm.reading_time_sec * {DEEP_READ_TRUE_THRESHOLD})
        ) as deep_read_partial_count,
        CASE
            WHEN cm.reading_time_sec IS NULL THEN TRUE
            ELSE FALSE
        END as is_proxy
    FROM sofia.analytics_events e
    LEFT JOIN sofia.content_meta cm ON e.page_path = cm.page_path
    WHERE e.event_date >= CURRENT_DATE - INTERVAL '{days} days'
        AND e.event_name = 'page_view'
        AND e.page_path NOT IN ('/', '/blog/', '/cursos/')
        AND e.page_path IS NOT NULL
    GROUP BY e.page_path, cm.title, cm.word_count, cm.reading_time_sec
    HAVING COUNT(DISTINCT e.user_pseudo_id) >= {MIN_USERS_PAGE}
    ORDER BY users DESC
    LIMIT 50
    """

    cursor.execute(query)
    return cursor.fetchall()

def get_channel_scores(conn, days=7):
    """Calculate channel quality scores (0-100) with minimum sample"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = f"""
    WITH channel_metrics AS (
        SELECT
            e.source,
            e.medium,
            COUNT(DISTINCT e.user_pseudo_id) as users,
            COUNT(*) FILTER (WHERE e.event_name = 'page_view') as pageviews,
            AVG(
                CASE
                    WHEN cm.reading_time_sec > 0
                    THEN LEAST(1.0, (e.engagement_time_ms / 1000.0) / cm.reading_time_sec)
                    ELSE NULL
                END
            ) as deep_read_score_avg,
            COUNT(DISTINCT cs.conversation_key) as conversations,
            COUNT(DISTINCT cs.conversation_key) FILTER (WHERE cs.qualified) as qualified_conversations
        FROM sofia.analytics_events e
        LEFT JOIN sofia.content_meta cm ON e.page_path = cm.page_path
        LEFT JOIN sofia.ga4_chat_sessions cs ON e.user_pseudo_id = cs.user_pseudo_id
        WHERE e.event_date >= CURRENT_DATE - INTERVAL '{days} days'
            AND e.source IS NOT NULL
        GROUP BY e.source, e.medium
    )
    SELECT
        source,
        medium,
        users,
        pageviews,
        deep_read_score_avg,
        conversations,
        qualified_conversations,
        CASE
            WHEN users >= {MIN_USERS_CHANNEL}
            THEN ROUND(
                100 * (
                    COALESCE(deep_read_score_avg, 0) * 0.50 +
                    LEAST(1.0, qualified_conversations::float / NULLIF(users, 0)) * 0.30 +
                    LEAST(1.0, conversations::float / NULLIF(users, 0) * 10) * 0.20
                )
            )
            ELSE NULL
        END as quality_score
    FROM channel_metrics
    WHERE users >= {MIN_USERS_CHANNEL}
    ORDER BY quality_score DESC NULLS LAST
    LIMIT 20
    """

    cursor.execute(query)
    return cursor.fetchall()

def recommend_actions(deep_read_pages, channels, exec_summary):
    """Generate deterministic recommended actions"""
    actions = []

    # Action 1: Low conversation rate
    if exec_summary['total_users'] > 0:
        conv_rate = (exec_summary['conversations'] / exec_summary['total_users']) * 100
        if conv_rate < 10:
            actions.append({
                'trigger': f"Conversation rate is {conv_rate:.1f}% (target: >10%)",
                'action': "Improve chat visibility on high-traffic pages. Add contextual prompts.",
                'owner': 'Product',
                'sla': '7 days'
            })

    # Action 2: High quality pages with low traffic
    opportunities = [p for p in deep_read_pages
                    if p['avg_deep_read_score'] and p['avg_deep_read_score'] >= 0.60
                    and p['users'] < MIN_USERS_PAGE * 2]

    if opportunities:
        top_opp = opportunities[0]
        actions.append({
            'trigger': f"Page '{top_opp['page_path'][:40]}' has {top_opp['avg_deep_read_score']:.2f} deep read score but only {top_opp['users']} users",
            'action': "Promote via LinkedIn/Newsletter. Create 3 internal links from top pages.",
            'owner': 'Marketing/SEO',
            'sla': '3 days'
        })

    # Action 3: High traffic pages with low engagement
    problems = [p for p in deep_read_pages
               if p['avg_deep_read_score'] and p['avg_deep_read_score'] < 0.25
               and p['users'] >= MIN_USERS_PAGE * 3]

    if problems:
        top_problem = problems[0]
        actions.append({
            'trigger': f"Page '{top_problem['page_path'][:40]}' has {top_problem['users']} users but only {top_problem['avg_deep_read_score']:.2f} deep read score",
            'action': "Rewrite introduction. Add TOC. Add bullet summary at top.",
            'owner': 'Editor/Content',
            'sla': '5 days'
        })

    # Action 4: Best channel needs amplification
    if channels and len(channels) > 0:
        best_channel = channels[0]
        if best_channel['quality_score'] and best_channel['quality_score'] >= 70:
            actions.append({
                'trigger': f"Channel '{best_channel['source']}/{best_channel['medium']}' has quality score {best_channel['quality_score']}/100",
                'action': "Increase posting frequency on this channel. Test 2x current volume.",
                'owner': 'Marketing',
                'sla': '7 days'
            })

    # Action 5: Deep read improvement opportunity
    if exec_summary['deep_read_pct'] < 5:
        actions.append({
            'trigger': f"Deep read rate is only {exec_summary['deep_read_pct']:.1f}%",
            'action': "Run A/B test: Add estimated reading time badges. Improve first paragraph hook.",
            'owner': 'Product/Content',
            'sla': '14 days'
        })

    return actions[:5]  # Max 5 actions

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_daily_report(exec_summary, chat_intel, deep_read, channels, actions):
    """Generate daily operational report"""

    report = []
    report.append("=" * 100)
    report.append("SOFIA PULSE - GA4 INTELLIGENCE V2.1 DAILY REPORT")
    report.append("=" * 100)
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")
    report.append("Philosophy: Store Everything, Report What Matters")
    report.append("")

    # 1. Executive Summary
    report.append("=" * 100)
    report.append("1. EXECUTIVE SUMMARY (7 Days)")
    report.append("=" * 100)
    report.append("")

    signal = f"{exec_summary['conversations']} conversations, " \
             f"{exec_summary['deep_read_pct']:.1f}% deep read, " \
             f"{exec_summary['returning_pct']:.1f}% return 7d"

    report.append(f"Signal: {signal}")
    report.append("")
    report.append(f"Total Users: {exec_summary['total_users']:,}")
    report.append(f"Real Conversations: {exec_summary['conversations']:,} ({exec_summary['conversations']*100/exec_summary['total_users']:.1f}%)")
    report.append(f"Qualified Conversations: {exec_summary['qualified_conversations']:,}")
    report.append(f"Deep Read Users: {exec_summary['deep_read_users']:,}")
    report.append(f"  - With content meta: {exec_summary['deep_read_with_meta']:,}")
    report.append(f"  - Proxy (no meta): {exec_summary['deep_read_proxy']:,}")
    report.append("")

    # 2. Chat Health
    report.append("=" * 100)
    report.append("2. CHAT HEALTH (30 Days)")
    report.append("=" * 100)
    report.append("")

    if chat_intel['stats']:
        stats = chat_intel['stats']
        report.append(f"Users with messages: {stats['users_with_message']:,}")
        report.append(f"Conversations started: {stats['conversations_started']:,}")
        report.append(f"Qualified conversations: {stats['qualified_conversations']:,}")
        report.append(f"Total messages: {stats['total_messages']:,}")
        if stats['avg_messages_per_conv']:
            report.append(f"Avg messages/conversation: {stats['avg_messages_per_conv']:.1f}")
    report.append("")

    # 3. Deep Read Analysis
    report.append("=" * 100)
    report.append("3. DEEP READ ANALYSIS (7 Days, Min {MIN_USERS_PAGE} Users)")
    report.append("=" * 100)
    report.append("")
    report.append(f"Scoring: Deep Read Score = min(1.0, engagement_sec / reading_time_sec)")
    report.append(f"  - True: score >= {DEEP_READ_TRUE_THRESHOLD}")
    report.append(f"  - Partial: score >= {DEEP_READ_PARTIAL_THRESHOLD}")
    report.append("")

    if deep_read:
        report.append(f"{'Page':<50} {'Users':>7} {'Score':>7} {'True':>6} {'Partial':>8} {'Proxy':>7}")
        report.append("-" * 100)

        for page in deep_read[:15]:
            path = page['page_path'][:49]
            users = page['users']
            score = page['avg_deep_read_score']
            true_count = page['deep_read_true_count']
            partial_count = page['deep_read_partial_count']
            is_proxy = 'Yes' if page['is_proxy'] else 'No'

            score_str = f"{score:.2f}" if score else "N/A"

            report.append(f"{path:<50} {users:>7} {score_str:>7} {true_count:>6} {partial_count:>8} {is_proxy:>7}")

    report.append("")

    # 4. Channel Scores
    report.append("=" * 100)
    report.append(f"4. ACQUISITION CHANNEL SCORES (7 Days, Min {MIN_USERS_CHANNEL} Users)")
    report.append("=" * 100)
    report.append("")
    report.append("Scoring: 50% deep_read + 30% qualified_chat + 20% chat_rate")
    report.append("")

    if channels:
        report.append(f"{'Channel':<40} {'Users':>7} {'Score':>7} {'Deep':>7} {'Convs':>7}")
        report.append("-" * 75)

        for ch in channels:
            channel = f"{ch['source']}/{ch['medium'] or '(none)'}"[:39]
            users = ch['users']
            score = ch['quality_score']
            deep = ch['deep_read_score_avg']
            convs = ch['conversations']

            score_str = f"{score}/100" if score else "N/A"
            deep_str = f"{deep:.2f}" if deep else "N/A"

            report.append(f"{channel:<40} {users:>7} {score_str:>7} {deep_str:>7} {convs:>7}")

    report.append("")

    # 5. Recommended Actions
    report.append("=" * 100)
    report.append("5. RECOMMENDED ACTIONS (If-Then Format)")
    report.append("=" * 100)
    report.append("")

    for i, action in enumerate(actions, 1):
        report.append(f"ACTION {i}:")
        report.append(f"  Trigger: {action['trigger']}")
        report.append(f"  Action:  {action['action']}")
        report.append(f"  Owner:   {action['owner']}")
        report.append(f"  SLA:     {action['sla']}")
        report.append("")

    report.append("=" * 100)
    report.append("END OF DAILY REPORT")
    report.append("=" * 100)

    return "\n".join(report)

# ============================================================================
# CSV EXPORTS
# ============================================================================

def export_deep_read_csv(deep_read, output_dir):
    """Export deep read analysis to CSV"""
    filepath = f"{output_dir}/ga4-deep-read-v21.csv"

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['page_path', 'title', 'users', 'pageviews', 'avg_deep_read_score',
                        'deep_read_true_count', 'deep_read_partial_count', 'word_count',
                        'reading_time_sec', 'is_proxy'])

        for page in deep_read:
            writer.writerow([
                page['page_path'],
                page['title'],
                page['users'],
                page['pageviews'],
                f"{page['avg_deep_read_score']:.3f}" if page['avg_deep_read_score'] else '',
                page['deep_read_true_count'],
                page['deep_read_partial_count'],
                page['word_count'] or '',
                page['reading_time_sec'] or '',
                'Yes' if page['is_proxy'] else 'No'
            ])

    return filepath

def export_channels_csv(channels, output_dir):
    """Export channel scores to CSV"""
    filepath = f"{output_dir}/ga4-channel-scores-v21.csv"

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['source', 'medium', 'users', 'pageviews', 'quality_score',
                        'deep_read_score_avg', 'conversations', 'qualified_conversations'])

        for ch in channels:
            writer.writerow([
                ch['source'],
                ch['medium'] or '(none)',
                ch['users'],
                ch['pageviews'],
                ch['quality_score'] or '',
                f"{ch['deep_read_score_avg']:.3f}" if ch['deep_read_score_avg'] else '',
                ch['conversations'],
                ch['qualified_conversations']
            ])

    return filepath

# ============================================================================
# MAIN
# ============================================================================

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("Loading GA4 Intelligence V2.1 data...")

        # Fetch data
        exec_summary = get_executive_summary(conn, days=7)
        print(f"  Executive summary: {exec_summary['total_users']} users")

        chat_intel = get_chat_intelligence(conn, days=30)
        print(f"  Chat intelligence: {chat_intel['stats']['users_with_message']} users with messages")

        deep_read = get_deep_read_with_scores(conn, days=7)
        print(f"  Deep read: {len(deep_read)} pages (min {MIN_USERS_PAGE} users)")

        channels = get_channel_scores(conn, days=7)
        print(f"  Channels: {len(channels)} channels (min {MIN_USERS_CHANNEL} users)")

        # Generate actions
        actions = recommend_actions(deep_read, channels, exec_summary)
        print(f"  Actions: {len(actions)} recommended")

        print("")
        print("Generating daily report...")

        # Generate report
        report = generate_daily_report(exec_summary, chat_intel, deep_read, channels, actions)

        # Print to console
        print(report)

        # Save TXT report
        os.makedirs("outputs", exist_ok=True)
        txt_file = "outputs/ga4-intelligence-v21-daily.txt"

        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n✅ Daily report saved to: {txt_file}")

        # Export CSVs
        csv1 = export_deep_read_csv(deep_read, "outputs")
        csv2 = export_channels_csv(channels, "outputs")

        print(f"✅ CSV exports:")
        print(f"   - {csv1}")
        print(f"   - {csv2}")

        conn.close()

    except Exception as e:
        print(f"[ERROR] Failed to generate GA4 Intelligence V2.1: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
