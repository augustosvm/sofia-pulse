#!/usr/bin/env python3
"""
Special Sectors Analysis - Sofia Pulse

Analisa setores críticos usando dados existentes:
- Space Industry (corrida espacial)
- Robotics & Automation (humanoides, automação)
- Cybersecurity (ataques, vulnerabilidades)
- AI Regulation (leis, compliance)
- Quantum Computing
- Defense Tech
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

# Import config
import sys
sys.path.insert(0, os.path.dirname(__file__))
from special_sectors_config import (
    SPECIAL_SECTORS, match_special_sector,
    get_sector_priority, get_all_sectors,
    get_sector_description
)

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

def analyze_papers_by_sector(conn):
    """Analisa papers por setor especial"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Papers dos últimos 90 dias
    cursor.execute("""
        SELECT
            title,
            abstract,
            primary_category,
            keywords,
            published_date
        FROM arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '90 days'
        ORDER BY published_date DESC
    """)

    papers = cursor.fetchall()

    # Agrupar por setor especial
    sector_stats = defaultdict(lambda: {
        'count': 0,
        'recent_titles': []
    })

    for paper in papers:
        text = f"{paper['title']} {paper['abstract'] or ''} {' '.join(paper['keywords'] or [])}"
        matched_sectors = match_special_sector(text)

        for sector in matched_sectors:
            sector_stats[sector]['count'] += 1

            if len(sector_stats[sector]['recent_titles']) < 5:
                sector_stats[sector]['recent_titles'].append(paper['title'])

    return sector_stats

def analyze_funding_by_sector(conn):
    """Analisa funding por setor especial"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Funding dos últimos 90 dias
    cursor.execute("""
        SELECT
            company_name,
            sector,
            amount_usd,
            round_type,
            announced_date,
            investors
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '90 days'
            AND amount_usd > 0
        ORDER BY amount_usd DESC
    """)

    rounds = cursor.fetchall()

    # Agrupar por setor especial
    sector_stats = defaultdict(lambda: {
        'total_funding': 0,
        'deal_count': 0,
        'avg_ticket': 0,
        'top_deals': []
    })

    for round_data in rounds:
        text = f"{round_data['company_name']} {round_data['sector']}"
        matched_sectors = match_special_sector(text)

        for sector in matched_sectors:
            sector_stats[sector]['total_funding'] += round_data['amount_usd']
            sector_stats[sector]['deal_count'] += 1

            if len(sector_stats[sector]['top_deals']) < 5:
                sector_stats[sector]['top_deals'].append({
                    'company': round_data['company_name'],
                    'amount': round_data['amount_usd']
                })

    # Calcular avg ticket
    for sector in sector_stats:
        if sector_stats[sector]['deal_count'] > 0:
            sector_stats[sector]['avg_ticket'] = (
                sector_stats[sector]['total_funding'] /
                sector_stats[sector]['deal_count']
            )

    return sector_stats

def analyze_gdelt_events(conn):
    """Analisa eventos GDELT por setor"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Eventos dos últimos 30 dias
    cursor.execute("""
        SELECT
            event_date,
            actor1_name,
            actor2_name,
            goldstein_scale,
            avg_tone,
            num_mentions,
            source_url
        FROM sofia.gdelt_events
        WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY num_mentions DESC
        LIMIT 500
    """)

    events = cursor.fetchall()

    # Agrupar por setor
    sector_stats = defaultdict(lambda: {
        'event_count': 0,
        'avg_sentiment': 0,
        'total_mentions': 0,
        'top_events': []
    })

    for event in events:
        text = f"{event['actor1_name'] or ''} {event['actor2_name'] or ''}"
        matched_sectors = match_special_sector(text)

        for sector in matched_sectors:
            sector_stats[sector]['event_count'] += 1
            sector_stats[sector]['avg_sentiment'] += event['avg_tone'] or 0
            sector_stats[sector]['total_mentions'] += event['num_mentions'] or 0

            if len(sector_stats[sector]['top_events']) < 3:
                sector_stats[sector]['top_events'].append({
                    'actors': f"{event['actor1_name']} + {event['actor2_name']}",
                    'mentions': event['num_mentions'],
                    'tone': event['avg_tone']
                })

    # Calcular média de sentimento
    for sector in sector_stats:
        if sector_stats[sector]['event_count'] > 0:
            sector_stats[sector]['avg_sentiment'] /= sector_stats[sector]['event_count']

    return sector_stats

def print_report(papers_stats, funding_stats, gdelt_stats):
    """Imprime relatório completo"""

    print("=" * 80)
    print("SPECIAL SECTORS ANALYSIS - Sofia Pulse")
    print("=" * 80)
    print()
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Tracking critical sectors:")
    for sector in get_all_sectors():
        priority = get_sector_priority(sector)
        emoji = "🔥" if priority == "critical" else "⚡" if priority == "high" else "📊"
        print(f"   {emoji} {sector} ({priority})")
    print()
    print("=" * 80)
    print()

    # Análise por setor
    all_sectors = set(list(papers_stats.keys()) + list(funding_stats.keys()) + list(gdelt_stats.keys()))

    for sector in sorted(all_sectors):
        priority = get_sector_priority(sector)
        emoji = "🔥" if priority == "critical" else "⚡" if priority == "high" else "📊"

        print(f"{emoji} {sector.upper()}")
        print("-" * 80)
        print(f"Description: {get_sector_description(sector)}")
        print()

        # Papers
        if sector in papers_stats:
            stats = papers_stats[sector]
            print(f"📄 RESEARCH:")
            print(f"   Papers (90d): {stats['count']}")
            if stats['recent_titles']:
                print(f"   Recent papers:")
                for title in stats['recent_titles'][:3]:
                    print(f"      • {title[:70]}...")
            print()

        # Funding
        if sector in funding_stats:
            stats = funding_stats[sector]
            print(f"💰 FUNDING:")
            print(f"   Total (90d): ${stats['total_funding']/1e9:.2f}B")
            print(f"   Deal Count: {stats['deal_count']}")
            print(f"   Avg Ticket: ${stats['avg_ticket']/1e6:.1f}M")
            if stats['top_deals']:
                print(f"   Top deals:")
                for deal in stats['top_deals'][:3]:
                    print(f"      • {deal['company']}: ${deal['amount']/1e6:.1f}M")
            print()

        # GDELT Events
        if sector in gdelt_stats:
            stats = gdelt_stats[sector]
            print(f"🌍 GEOPOLITICAL EVENTS:")
            print(f"   Events (30d): {stats['event_count']}")
            print(f"   Media Mentions: {stats['total_mentions']:,}")
            sentiment_emoji = "😊" if stats['avg_sentiment'] > 0 else "😐" if stats['avg_sentiment'] == 0 else "😟"
            print(f"   Avg Sentiment: {stats['avg_sentiment']:.2f} {sentiment_emoji}")
            if stats['top_events']:
                print(f"   Major events:")
                for evt in stats['top_events']:
                    print(f"      • {evt['actors']}: {evt['mentions']} mentions")
            print()

        print("=" * 80)
        print()

    # Summary
    print("🎯 EXECUTIVE SUMMARY")
    print("-" * 80)
    print()

    # Top por funding
    top_funding = sorted(
        [(s, funding_stats[s]['total_funding']) for s in funding_stats],
        key=lambda x: x[1],
        reverse=True
    )[:3]

    print("💰 HOTTEST SECTORS (by funding):")
    for sector, amount in top_funding:
        print(f"   {sector}: ${amount/1e9:.2f}B")
    print()

    # Top por research
    top_research = sorted(
        [(s, papers_stats[s]['count']) for s in papers_stats],
        key=lambda x: x[1],
        reverse=True
    )[:3]

    print("📄 HOTTEST SECTORS (by research):")
    for sector, count in top_research:
        print(f"   {sector}: {count} papers")
    print()

    # Critical alerts
    print("🔥 CRITICAL ALERTS:")
    if 'Cybersecurity' in gdelt_stats:
        print(f"   🔒 Cybersecurity: {gdelt_stats['Cybersecurity']['event_count']} security events (30d)")
    if 'AI Regulation' in gdelt_stats:
        print(f"   ⚖️ AI Regulation: {gdelt_stats['AI Regulation']['event_count']} regulatory events (30d)")
    print()

    print("=" * 80)
    print()
    print("✅ Analysis complete!")
    print()

def main():
    print("🔍 Analyzing special sectors...")
    print()

    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("📄 Analyzing papers...")
        try:
            papers_stats = analyze_papers_by_sector(conn)
            print(f"   ✅ {len(papers_stats)} sectors found")
        except psycopg2.errors.UndefinedTable as e:
            print(f"   ⚠️  Table not found (skipping)")
            papers_stats = {}
        print()

        print("💰 Analyzing funding...")
        try:
            funding_stats = analyze_funding_by_sector(conn)
            print(f"   ✅ {len(funding_stats)} sectors found")
        except psycopg2.errors.UndefinedTable as e:
            print(f"   ⚠️  Table not found (skipping)")
            funding_stats = {}
        print()

        print("🌍 Analyzing GDELT events...")
        try:
            gdelt_stats = analyze_gdelt_events(conn)
            print(f"   ✅ {len(gdelt_stats)} sectors found")
        except psycopg2.errors.UndefinedTable as e:
            print(f"   ⚠️  Table not found (skipping)")
            gdelt_stats = {}
        print()

        print_report(papers_stats, funding_stats, gdelt_stats)

        # Save to file
        output_file = 'analytics/special-sectors-latest.txt'
        print(f"💾 Saving to {output_file}...")

        import sys
        original_stdout = sys.stdout
        with open(output_file, 'w', encoding='utf-8') as f:
            sys.stdout = f
            print_report(papers_stats, funding_stats, gdelt_stats)
        sys.stdout = original_stdout

        print(f"✅ Saved to {output_file}")
        print()

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
