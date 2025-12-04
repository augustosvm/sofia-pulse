#!/usr/bin/env python3
"""
AI Technology Radar Report Generator

Generates comprehensive analysis of AI technology trends using data from:
- GitHub (stars, repos, momentum)
- PyPI (Python package downloads)
- NPM (JavaScript package downloads)
- HuggingFace (model popularity)
- ArXiv (research papers)

Output: TXT report + CSV exports
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

# Output directory
OUTPUT_DIR = 'output'

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def fetch_data(query: str) -> List[Dict[str, Any]]:
    """Execute query and return results as list of dicts"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            return [dict(row) for row in results]
    finally:
        conn.close()

def generate_report():
    """Generate comprehensive AI Tech Radar report"""

    print("=" * 80)
    print("🚀 AI TECHNOLOGY RADAR REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("AI TECHNOLOGY RADAR REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report_lines.append("Data sources: GitHub, PyPI, NPM, HuggingFace, ArXiv")
    report_lines.append("=" * 80)
    report_lines.append("")

    # ========================================================================
    # 1. TOP 20 TECHNOLOGIES BY HYPE INDEX
    # ========================================================================
    print("\n📊 TOP 20 AI TECHNOLOGIES (by Hype Index)")
    print("-" * 80)

    query_top20 = """
        SELECT
            tech_key,
            display_name,
            category,
            hype_index,
            overall_momentum,
            developer_adoption_score,
            research_interest_score,
            github_stars,
            pypi_downloads_30d,
            npm_downloads_30d,
            hf_likes,
            arxiv_papers_monthly
        FROM sofia.ai_tech_radar_consolidated
        ORDER BY hype_index DESC
        LIMIT 20;
    """

    top20 = fetch_data(query_top20)

    report_lines.append("=" * 80)
    report_lines.append("TOP 20 AI TECHNOLOGIES (by Hype Index)")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"{'Rank':<5} {'Technology':<30} {'Category':<15} {'Hype':<8} {'Momentum':<10} {'GitHub ⭐':<12}")
    report_lines.append("-" * 80)

    for i, tech in enumerate(top20, 1):
        print(f"{i:2d}. {tech['display_name']:<28} | Hype: {tech['hype_index']:>5.1f} | Momentum: {tech['overall_momentum']:>6.1f}% | Category: {tech['category']}")

        report_lines.append(
            f"{i:<5} {tech['display_name']:<30} {tech['category']:<15} "
            f"{tech['hype_index']:<8.1f} {tech['overall_momentum']:<10.1f} {tech['github_stars']:<12,}"
        )

    report_lines.append("")

    # Export to CSV
    df_top20 = pd.DataFrame(top20)
    csv_path = os.path.join(OUTPUT_DIR, 'ai_tech_top20.csv')
    df_top20.to_csv(csv_path, index=False)
    print(f"\n✅ Exported: {csv_path}")

    # ========================================================================
    # 2. RISING STARS (Highest Momentum)
    # ========================================================================
    print("\n🚀 RISING STARS (Highest Momentum)")
    print("-" * 80)

    query_rising = """
        SELECT * FROM sofia.ai_rising_stars LIMIT 15;
    """

    rising = fetch_data(query_rising)

    report_lines.append("=" * 80)
    report_lines.append("RISING STARS - Fastest Growing AI Technologies")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"{'Rank':<5} {'Technology':<30} {'Momentum':<12} {'GitHub Δ':<12} {'PyPI Δ':<12}")
    report_lines.append("-" * 80)

    for i, tech in enumerate(rising, 1):
        print(f"{i:2d}. {tech['display_name']:<28} | Momentum: {tech['overall_momentum']:>6.1f}% | GitHub: +{tech['github_momentum_30d']:>5.1f}%")

        report_lines.append(
            f"{i:<5} {tech['display_name']:<30} {tech['overall_momentum']:<12.1f} "
            f"{tech['github_momentum_30d']:<12.1f} {tech['pypi_momentum_30d']:<12.1f}"
        )

    report_lines.append("")

    # Export to CSV
    df_rising = pd.DataFrame(rising)
    csv_path = os.path.join(OUTPUT_DIR, 'ai_tech_rising_stars.csv')
    df_rising.to_csv(csv_path, index=False)
    print(f"✅ Exported: {csv_path}")

    # ========================================================================
    # 3. DARK HORSES (High Growth, Low Visibility)
    # ========================================================================
    print("\n🐴 DARK HORSES (High Growth, Low Current Visibility)")
    print("-" * 80)

    query_dark_horses = """
        SELECT * FROM sofia.ai_dark_horses LIMIT 10;
    """

    dark_horses = fetch_data(query_dark_horses)

    report_lines.append("=" * 80)
    report_lines.append("DARK HORSES - Hidden Gems with High Momentum")
    report_lines.append("=" * 80)
    report_lines.append("")

    if dark_horses:
        report_lines.append(f"{'Rank':<5} {'Technology':<30} {'Momentum':<12} {'Hype Index':<12}")
        report_lines.append("-" * 80)

        for i, tech in enumerate(dark_horses, 1):
            print(f"{i:2d}. {tech['display_name']:<28} | Momentum: {tech['overall_momentum']:>6.1f}% | Hype: {tech['hype_index']:>5.1f}")

            report_lines.append(
                f"{i:<5} {tech['display_name']:<30} {tech['overall_momentum']:<12.1f} {tech['hype_index']:<12.1f}"
            )

        report_lines.append("")

        # Export to CSV
        df_dark = pd.DataFrame(dark_horses)
        csv_path = os.path.join(OUTPUT_DIR, 'ai_tech_dark_horses.csv')
        df_dark.to_csv(csv_path, index=False)
        print(f"✅ Exported: {csv_path}")
    else:
        print("  No dark horses found")
        report_lines.append("  No dark horses found (criteria: momentum > 20%, hype_index < 30)")
        report_lines.append("")

    # ========================================================================
    # 4. TOP TECHNOLOGIES BY CATEGORY
    # ========================================================================
    print("\n📁 TOP TECHNOLOGIES BY CATEGORY")
    print("-" * 80)

    query_by_category = """
        SELECT
            category,
            tech_key,
            display_name,
            hype_index,
            overall_momentum,
            rank_in_category
        FROM sofia.ai_top_technologies_by_category
        WHERE rank_in_category <= 5
        ORDER BY category, rank_in_category;
    """

    by_category = fetch_data(query_by_category)

    report_lines.append("=" * 80)
    report_lines.append("TOP TECHNOLOGIES BY CATEGORY (Top 5 each)")
    report_lines.append("=" * 80)
    report_lines.append("")

    current_category = None
    for tech in by_category:
        if tech['category'] != current_category:
            current_category = tech['category']
            print(f"\n{current_category.upper()}:")
            report_lines.append(f"\n{current_category.upper()}:")
            report_lines.append("-" * 60)

        print(f"  {tech['rank_in_category']}. {tech['display_name']:<28} | Hype: {tech['hype_index']:>5.1f} | Momentum: {tech['overall_momentum']:>6.1f}%")

        report_lines.append(
            f"  {tech['rank_in_category']}. {tech['display_name']:<30} Hype: {tech['hype_index']:<8.1f} Momentum: {tech['overall_momentum']:<10.1f}"
        )

    report_lines.append("")

    # Export to CSV
    df_category = pd.DataFrame(by_category)
    csv_path = os.path.join(OUTPUT_DIR, 'ai_tech_by_category.csv')
    df_category.to_csv(csv_path, index=False)
    print(f"\n✅ Exported: {csv_path}")

    # ========================================================================
    # 5. DEVELOPER ADOPTION LEADERS
    # ========================================================================
    print("\n👨‍💻 DEVELOPER ADOPTION LEADERS")
    print("-" * 80)

    query_dev_adoption = """
        SELECT
            tech_key,
            display_name,
            category,
            developer_adoption_score,
            github_stars,
            pypi_downloads_30d,
            npm_downloads_30d
        FROM sofia.ai_tech_radar_consolidated
        ORDER BY developer_adoption_score DESC
        LIMIT 15;
    """

    dev_adoption = fetch_data(query_dev_adoption)

    report_lines.append("=" * 80)
    report_lines.append("DEVELOPER ADOPTION LEADERS")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"{'Rank':<5} {'Technology':<30} {'Score':<8} {'GitHub ⭐':<15} {'PyPI DL/mo':<15}")
    report_lines.append("-" * 80)

    for i, tech in enumerate(dev_adoption, 1):
        print(f"{i:2d}. {tech['display_name']:<28} | Score: {tech['developer_adoption_score']:>5.1f} | GitHub: {tech['github_stars']:>8,} stars")

        report_lines.append(
            f"{i:<5} {tech['display_name']:<30} {tech['developer_adoption_score']:<8.1f} "
            f"{tech['github_stars']:<15,} {tech['pypi_downloads_30d']:<15,}"
        )

    report_lines.append("")

    # Export to CSV
    df_dev = pd.DataFrame(dev_adoption)
    csv_path = os.path.join(OUTPUT_DIR, 'ai_tech_developer_adoption.csv')
    df_dev.to_csv(csv_path, index=False)
    print(f"✅ Exported: {csv_path}")

    # ========================================================================
    # 6. RESEARCH INTEREST LEADERS
    # ========================================================================
    print("\n🔬 RESEARCH INTEREST LEADERS")
    print("-" * 80)

    query_research = """
        SELECT
            tech_key,
            display_name,
            category,
            research_interest_score,
            arxiv_papers_monthly,
            hf_likes,
            arxiv_momentum_3mo
        FROM sofia.ai_tech_radar_consolidated
        WHERE arxiv_papers_monthly > 0
        ORDER BY research_interest_score DESC
        LIMIT 15;
    """

    research = fetch_data(query_research)

    report_lines.append("=" * 80)
    report_lines.append("RESEARCH INTEREST LEADERS")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"{'Rank':<5} {'Technology':<30} {'Score':<8} {'Papers/mo':<12} {'HF Likes':<12}")
    report_lines.append("-" * 80)

    for i, tech in enumerate(research, 1):
        print(f"{i:2d}. {tech['display_name']:<28} | Score: {tech['research_interest_score']:>5.1f} | Papers: {tech['arxiv_papers_monthly']:>4} | HF: {tech['hf_likes']:>6,}")

        report_lines.append(
            f"{i:<5} {tech['display_name']:<30} {tech['research_interest_score']:<8.1f} "
            f"{tech['arxiv_papers_monthly']:<12} {tech['hf_likes']:<12,}"
        )

    report_lines.append("")

    # Export to CSV
    df_research = pd.DataFrame(research)
    csv_path = os.path.join(OUTPUT_DIR, 'ai_tech_research_interest.csv')
    df_research.to_csv(csv_path, index=False)
    print(f"✅ Exported: {csv_path}")

    # ========================================================================
    # 7. SUMMARY STATISTICS
    # ========================================================================
    print("\n📈 SUMMARY STATISTICS")
    print("-" * 80)

    query_stats = """
        SELECT
            COUNT(DISTINCT tech_key) as total_technologies,
            COUNT(DISTINCT category) as total_categories,
            ROUND(AVG(hype_index), 2) as avg_hype_index,
            ROUND(AVG(overall_momentum), 2) as avg_momentum,
            SUM(github_stars) as total_github_stars,
            SUM(pypi_downloads_30d) as total_pypi_downloads,
            SUM(npm_downloads_30d) as total_npm_downloads,
            SUM(arxiv_papers_monthly) as total_arxiv_papers
        FROM sofia.ai_tech_radar_consolidated;
    """

    stats = fetch_data(query_stats)[0]

    report_lines.append("=" * 80)
    report_lines.append("SUMMARY STATISTICS")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"Total Technologies Tracked: {stats['total_technologies']}")
    report_lines.append(f"Total Categories: {stats['total_categories']}")
    report_lines.append(f"Average Hype Index: {stats['avg_hype_index']}")
    report_lines.append(f"Average Momentum: {stats['avg_momentum']}%")
    report_lines.append(f"Total GitHub Stars: {stats['total_github_stars']:,}")
    report_lines.append(f"Total PyPI Downloads (30d): {stats['total_pypi_downloads']:,}")
    report_lines.append(f"Total NPM Downloads (30d): {stats['total_npm_downloads']:,}")
    report_lines.append(f"Total ArXiv Papers (monthly): {stats['total_arxiv_papers']}")
    report_lines.append("")

    print(f"Total Technologies: {stats['total_technologies']}")
    print(f"Total Categories: {stats['total_categories']}")
    print(f"Avg Hype Index: {stats['avg_hype_index']}")
    print(f"Avg Momentum: {stats['avg_momentum']}%")
    print(f"Total GitHub Stars: {stats['total_github_stars']:,}")
    print(f"Total PyPI Downloads (30d): {stats['total_pypi_downloads']:,}")

    # ========================================================================
    # 8. SAVE TEXT REPORT
    # ========================================================================
    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)

    report_path = os.path.join(OUTPUT_DIR, 'ai-tech-radar-report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"\n✅ Full report saved: {report_path}")
    print("=" * 80)

if __name__ == '__main__':
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        generate_report()
        print("\n✅ AI Tech Radar Report Generation Complete!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
