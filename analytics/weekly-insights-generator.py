#!/usr/bin/env python3
"""
SOFIA PULSE - WEEKLY INSIGHTS GENERATOR
Gera insights semanais para colunistas TI Especialistas
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

def generate_weekly_insights(conn):
    """Gera top 3 insights da semana"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    insights = []

    # 1. GitHub Trending (última semana)
    cur.execute("""
        SELECT
            name,
            description,
            stars,
            language,
            UNNEST(topics) as topic
        FROM sofia.github_trending
        WHERE collected_at >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY stars DESC
        LIMIT 20
    """)
    github_hot = cur.fetchall()

    # 2. HackerNews trending
    cur.execute("""
        SELECT
            title,
            points,
            url
        FROM sofia.hackernews_stories
        WHERE collected_at >= CURRENT_DATE - INTERVAL '7 days'
        AND points >= 100
        ORDER BY points DESC
        LIMIT 15
    """)
    hn_hot = cur.fetchall()

    # 3. Recent funding
    cur.execute("""
        SELECT
            company_name,
            sector,
            round_type,
            amount_usd
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY CAST(amount_usd AS NUMERIC) DESC
        LIMIT 10
    """)
    recent_funding = cur.fetchall()

    # Gerar insights
    if github_hot:
        top_repo = github_hot[0]
        insights.append({
            'title': f"{top_repo['name']} está explodindo no GitHub",
            'angle': f"Por que {top_repo['name']} ({top_repo['language']}) viralizou esta semana?",
            'evidence': [
                f"GitHub: {top_repo['stars']:,} stars (trending #1)",
                f"Linguagem: {top_repo['language']}",
                f"Descrição: {top_repo['description'][:100]}..."
            ],
            'seo': f"{top_repo['name'].lower()} {top_repo['language'].lower() if top_repo['language'] else ''} tutorial",
            'urgency': 'CRÍTICA - escreva nas próximas 48h'
        })

    if hn_hot:
        top_story = hn_hot[0]
        insights.append({
            'title': top_story['title'],
            'angle': f"Deep dive: {top_story['title']}",
            'evidence': [
                f"HackerNews: {top_story.get('points', 0)} upvotes (#1 trending)",
                f"URL: {top_story['url']}"
            ],
            'seo': ' '.join(top_story['title'].lower().split()[:5]),
            'urgency': 'ALTA - escreva esta semana'
        })

    if recent_funding:
        top_deal = recent_funding[0]
        amount_m = float(top_deal['amount_usd']) / 1000000.0 if top_deal['amount_usd'] else 0
        insights.append({
            'title': f"{top_deal['company_name']} levantou ${amount_m:.1f}M",
            'angle': f"Por que VCs estão apostando pesado em {top_deal['sector']}?",
            'evidence': [
                f"Funding: ${amount_m:.1f}M ({top_deal['round_type']} round)",
                f"Setor: {top_deal['sector']}",
                f"Empresa: {top_deal['company_name']}"
            ],
            'seo': f"{top_deal['sector'].lower()} funding trends",
            'urgency': 'MÉDIA - escreva esta semana'
        })

    return insights[:3]  # Top 3

def generate_report(insights):
    """Gera relatório formatado"""
    report = []
    report.append("=" * 80)
    report.append("📰 WEEKLY INSIGHTS - TI Especialistas")
    report.append("=" * 80)
    report.append("")
    report.append(f"Week of: {datetime.now().strftime('%Y-%m-%d')}")
    report.append("")
    report.append("🔥 TOP 3 TOPICS TO WRITE THIS WEEK")
    report.append("")
    report.append("=" * 80)
    report.append("")

    if not insights:
        report.append("⚠️  No hot topics this week. Check data sources.")
        return "\n".join(report)

    for i, insight in enumerate(insights, 1):
        report.append(f"{i}. {insight['title'].upper()}")
        report.append("")
        report.append(f"   📝 ÂNGULO: \"{insight['angle']}\"")
        report.append("")
        report.append("   Evidências:")
        for evidence in insight['evidence']:
            report.append(f"   • {evidence}")
        report.append("")
        report.append(f"   🎯 SEO Keywords: {insight['seo']}")
        report.append(f"   💡 URGÊNCIA: {insight['urgency']}")
        report.append("")
        report.append("   " + "-" * 70)
        report.append("")

    report.append("=" * 80)
    report.append("💡 COMO USAR ESTES INSIGHTS")
    report.append("=" * 80)
    report.append("")
    report.append("1. Escolha o insight com maior URGÊNCIA")
    report.append("2. Pesquise links/evidências adicionais")
    report.append("3. Escreva artigo focando no ÂNGULO sugerido")
    report.append("4. Otimize para SEO keywords listadas")
    report.append("5. Publique ANTES da concorrência")
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)

        print("📊 Generating weekly insights...")
        insights = generate_weekly_insights(conn)

        print(f"✅ Generated {len(insights)} insights")

        report = generate_report(insights)

        output_file = 'analytics/weekly-insights-latest.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ Report saved: {output_file}")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
