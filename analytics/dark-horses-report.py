#!/usr/bin/env python3
"""
Dark Horses Report - Monthly

Identifica tecnologias/setores com ALTO POTENCIAL mas BAIXO FUNDING

Critérios:
- Alto número de papers acadêmicos (>20 últimos 90 dias)
- Alto GitHub activity (>10k stars)
- Baixo funding (<$100M últimos 90 dias)
- Crescimento acelerado

= OPORTUNIDADES SUBVALORIZADAS
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

# Add analytics directory to path for shared imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.tech_normalizer import normalize_tech_name, normalize_tech_dict

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
    'database': os.getenv('POSTGRES_DB', 'sofia_db'),
}

def get_dark_horses(conn):
    """Identifica Dark Horses usando múltiplas fontes"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Papers por setor (últimos 90 dias)
    cursor.execute("""
        WITH flattened AS (
            SELECT
                primary_category as sector,
                is_breakthrough,
                unnest(keywords) as keyword
            FROM arxiv_ai_papers
            WHERE published_date >= CURRENT_DATE - INTERVAL '90 days'
                AND keywords IS NOT NULL
        )
        SELECT
            sector,
            COUNT(*) as paper_count,
            COUNT(*) FILTER (WHERE is_breakthrough) as breakthrough_count,
            ARRAY_AGG(DISTINCT keyword) as keywords
        FROM flattened
        GROUP BY sector
        HAVING COUNT(*) >= 5
        ORDER BY paper_count DESC;
    """)
    papers = {r['sector']: r for r in cursor.fetchall()}

    # GitHub por linguagem/topic (total)
    cursor.execute("""
        SELECT
            language as tech,
            COUNT(*) as repo_count,
            SUM(stars) as total_stars,
            AVG(stars) as avg_stars
        FROM sofia.github_trending
        WHERE language IS NOT NULL
            AND is_archived = FALSE
        GROUP BY language
        HAVING SUM(stars) >= 10000
        ORDER BY total_stars DESC;
    """)
    github = {r['tech']: r for r in cursor.fetchall()}

    # Funding por setor (últimos 90 dias)
    cursor.execute("""
        SELECT
            sector,
            COUNT(*) as deal_count,
            SUM(amount_usd) as total_funding,
            AVG(amount_usd) as avg_funding
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '90 days'
            AND amount_usd > 0
        GROUP BY sector
        ORDER BY total_funding DESC;
    """)
    funding = {r['sector']: r for r in cursor.fetchall()}

    # HackerNews mentions
    cursor.execute("""
        SELECT
            unnest(mentioned_technologies) as tech,
            COUNT(*) as mentions,
            SUM(points) as total_points
        FROM sofia.hackernews_stories
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY tech
        ORDER BY mentions DESC;
    """)
    hn_raw = {r['tech']: r for r in cursor.fetchall()}

    cursor.close()

    # Normalize tech names BEFORE lookups (fix: typescript vs TypeScript)
    github = normalize_tech_dict(github, merge_strategy='sum')
    hn = normalize_tech_dict(hn_raw, merge_strategy='sum')

    # Calcular Dark Horse Score
    dark_horses = []

    # Mapear setores
    sector_map = {
        'cs.AI': 'Artificial Intelligence',
        'cs.LG': 'Artificial Intelligence',
        'cs.CV': 'Computer Vision',
        'cs.CL': 'NLP',
        'cs.RO': 'Robotics',
        'cs.NE': 'Neural Networks',
    }

    for paper_sector, paper_data in papers.items():
        market_sector = sector_map.get(paper_sector, paper_sector)
        fund_data = funding.get(market_sector, {'total_funding': 0, 'deal_count': 0})

        paper_count = int(paper_data['paper_count'])
        total_funding = float(fund_data['total_funding']) if fund_data['total_funding'] else 0

        # Dark Horse: Muitos papers, pouco funding
        if paper_count >= 10 and total_funding < 500_000_000:  # < $500M
            dark_horse_score = paper_count / (total_funding / 1e9 + 0.01)  # Papers per $1B

            dark_horses.append({
                'sector': market_sector,
                'paper_sector': paper_sector,
                'paper_count': paper_count,
                'breakthrough_count': int(paper_data['breakthrough_count'] or 0),
                'total_funding': total_funding,
                'deal_count': int(fund_data.get('deal_count', 0)),
                'dark_horse_score': dark_horse_score,
                'keywords': paper_data.get('keywords', [])[:5] if paper_data.get('keywords') else [],
            })

    # GitHub Dark Horses (excluir linguagens mainstream)
    mainstream_langs = {
        'JavaScript', 'Python', 'Java', 'C++', 'C', 'C#', 'TypeScript',
        'PHP', 'Ruby', 'Go', 'Swift', 'Kotlin', 'Rust', 'HTML', 'CSS',
        'Shell', 'Objective-C', 'Scala', 'R', 'Perl', 'Lua', 'Dart', 'Haskell'
    }

    for tech, gh_data in github.items():
        # Normalize tech name for lookup
        tech_normalized = normalize_tech_name(tech)

        # Pular linguagens mainstream (check both original and normalized)
        if tech in mainstream_langs or tech_normalized in mainstream_langs:
            continue

        total_stars = int(gh_data.get('total_stars', 0) if isinstance(gh_data, dict) else gh_data)
        repo_count = int(gh_data.get('repo_count', 1) if isinstance(gh_data, dict) else 1)
        hn_data = hn.get(tech_normalized, {})
        hn_mentions = int(hn_data.get('mentions', 0) if isinstance(hn_data, dict) else 0)

        # Dark Horse: Linguagem emergente com tração mas baixa visibilidade
        # Critérios mais estritos: 10k-500k stars (não milhões), múltiplos repos
        if 10000 <= total_stars <= 500000 and repo_count >= 3 and hn_mentions < 5:
            dark_horse_score = total_stars / (hn_mentions + 1)

            dark_horses.append({
                'sector': f'Tech: {tech}',
                'paper_sector': tech,
                'paper_count': 0,
                'breakthrough_count': 0,
                'total_funding': 0,
                'deal_count': 0,
                'github_stars': total_stars,
                'github_repos': repo_count,
                'hn_mentions': hn_mentions,
                'dark_horse_score': dark_horse_score,
                'keywords': [tech],
            })

    return sorted(dark_horses, key=lambda x: x['dark_horse_score'], reverse=True)

def print_report(dark_horses):
    """Imprime relatório Dark Horses"""

    print("=" * 80)
    print("🐴 DARK HORSES REPORT - MONTHLY")
    print("=" * 80)
    print()
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Oportunidades SUBVALORIZADAS: Alto potencial, baixo funding/visibilidade")
    print()
    print("=" * 80)
    print()

    # Top 20 Dark Horses
    print("🔥 TOP 20 DARK HORSES (Ranked by Score)")
    print("-" * 80)
    print(f"{'Rank':<6} {'Sector':<30} {'Papers':<10} {'Funding':<15} {'Score':<10}")
    print("-" * 80)

    for idx, dh in enumerate(dark_horses[:20], 1):
        funding_str = f"${dh.get('total_funding', 0)/1e6:.1f}M" if dh.get('total_funding', 0) > 0 else "N/A"
        github_str = f"{dh.get('github_stars', 0):,} ⭐" if dh.get('github_stars', 0) > 0 else ""

        print(
            f"{idx:<6} "
            f"{dh['sector']:<30} "
            f"{dh['paper_count']:<10} "
            f"{funding_str:<15} "
            f"{dh['dark_horse_score']:<10.1f}"
        )

        if github_str:
            print(f"       GitHub: {github_str} | HN: {dh.get('hn_mentions', 0)} mentions")

    print()
    print("=" * 80)
    print()

    # Por tipo
    print("📊 DARK HORSES BY TYPE:")
    print()

    academic_dh = [dh for dh in dark_horses if dh['paper_count'] > 0]
    github_dh = [dh for dh in dark_horses if dh.get('github_stars', 0) > 0]

    print(f"   📚 Academic Dark Horses: {len(academic_dh)}")
    print(f"      (Muitos papers, pouco funding)")
    print()

    for dh in academic_dh[:5]:
        print(
            f"      • {dh['sector']}: "
            f"{dh['paper_count']} papers, "
            f"${dh['total_funding']/1e6:.1f}M funding"
        )

    print()
    print(f"   💻 GitHub Dark Horses: {len(github_dh)}")
    print(f"      (Alto GitHub stars, baixo HN buzz)")
    print()

    for dh in github_dh[:5]:
        print(
            f"      • {dh['sector']}: "
            f"{dh.get('github_stars', 0):,} stars, "
            f"{dh.get('hn_mentions', 0)} HN mentions"
        )

    print()
    print("=" * 80)
    print()

    # Recomendações
    print("💡 INVESTMENT OPPORTUNITIES:")
    print()

    top_5 = dark_horses[:5]
    for idx, dh in enumerate(top_5, 1):
        print(f"   {idx}. {dh['sector']}")
        print(f"      Score: {dh['dark_horse_score']:.1f}")

        if dh['paper_count'] > 0:
            print(f"      Papers: {dh['paper_count']} (breakthroughs: {dh['breakthrough_count']})")
            print(f"      Funding: ${dh['total_funding']/1e6:.1f}M in {dh['deal_count']} deals")
            print(f"      Keywords: {', '.join(dh['keywords'][:5])}")

        if dh.get('github_stars', 0) > 0:
            print(f"      GitHub: {dh['github_stars']:,} stars")
            print(f"      HN visibility: {dh.get('hn_mentions', 0)} mentions (LOW = opportunity!)")

        print()

    print("=" * 80)
    print()
    print("📈 WHY DARK HORSES MATTER:")
    print()
    print("   • High academic interest = Future tech trends")
    print("   • Low funding = Less competition, better valuations")
    print("   • High GitHub, low HN = Not discovered by mainstream yet")
    print("   • Investment BEFORE hype = Maximum alpha")
    print()
    print("⏰ TYPICAL LAG: 6-12 months until mainstream recognition")
    print()
    print("✅ Report complete!")
    print()

def main():
    print("🐴 Dark Horses Report - Generating...")
    print()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
        print()

        print("🔍 Analyzing data sources...")
        dark_horses = get_dark_horses(conn)
        print(f"   ✅ {len(dark_horses)} Dark Horses identified")
        print()

        print_report(dark_horses)

        # Save to file
        output_file = 'analytics/dark-horses-latest.txt'
        import sys
        original_stdout = sys.stdout
        with open(output_file, 'w') as f:
            sys.stdout = f
            print_report(dark_horses)
        sys.stdout = original_stdout

        print(f"💾 Saved to: {output_file}")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
