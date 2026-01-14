#!/usr/bin/env python3
"""
================================================================================
SOFIA PULSE - CAUSAL INSIGHTS (Machine Learning Enhanced)
================================================================================
Intelligent cross-data analysis using ML techniques on ALL available data.

Strategy:
1. Use FULL historical data (not hardcoded time ranges)
2. Graceful fallback when tables don't exist
3. Work with whatever data is available
4. Provide insights even with limited data

Analyses:
1. Weak Signals: GitHub trends -> Future funding opportunities
2. Topic Analysis: Research trends from papers
3. Sector Patterns: Funding by sector/stage
4. Geographic Intelligence: Where is capital flowing?
5. ML Correlation: Papers vs Funding correlation
6. Sector Clustering: Group similar sectors (KMeans)
7. Time Series: Forecasting with available data
================================================================================
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from collections import defaultdict
import re
from dotenv import load_dotenv

# ML imports with graceful fallback
try:
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from scipy.stats import pearsonr
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: sklearn/scipy not installed. ML features disabled.")

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', 'localhost')),
    'port': int(os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432'))),
    'user': os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'postgres')),
    'password': os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', '')),
    'database': os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'sofia_db')),
}

def safe_query(cursor, query, params=None, fallback=None):
    """Execute query with error handling for missing tables"""
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        cursor.connection.rollback()
        return fallback if fallback is not None else []

def get_data_overview(conn):
    """Get overview of all available data"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    overview = {}

    # Funding
    result = safe_query(cur, """
        SELECT COUNT(*) as total,
               MIN(announced_date) as earliest,
               MAX(announced_date) as latest,
               SUM(COALESCE(amount_usd, 0)) as total_funding
        FROM sofia.funding_rounds
        WHERE announced_date IS NOT NULL
    """)
    overview['funding'] = result[0] if result else {'total': 0}

    # GitHub
    result = safe_query(cur, """
        SELECT COUNT(*) as total,
               MIN(collected_at) as earliest,
               MAX(collected_at) as latest,
               SUM(COALESCE(stars, 0)) as total_stars
        FROM sofia.github_trending
    """)
    overview['github'] = result[0] if result else {'total': 0}

    # Papers
    result = safe_query(cur, """
        SELECT COUNT(*) as total,
               MIN(published_date) as earliest,
               MAX(published_date) as latest
        FROM sofia.arxiv_ai_papers
    """)
    overview['papers'] = result[0] if result else {'total': 0}

    cur.close()
    return overview

def analyze_github_signals(conn):
    """Analyze GitHub trending for weak signals (technologies without funding yet)"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get top languages/topics from GitHub
    languages = safe_query(cur, """
        SELECT language,
               COUNT(*) as repo_count,
               SUM(COALESCE(stars, 0)) as total_stars,
               AVG(COALESCE(stars, 0)) as avg_stars
        FROM sofia.github_trending
        WHERE language IS NOT NULL
        GROUP BY language
        ORDER BY total_stars DESC
        LIMIT 15
    """)

    # Get topics from GitHub (if topics column exists)
    topics = safe_query(cur, """
        SELECT topic, COUNT(*) as count, SUM(stars) as total_stars
        FROM (
            SELECT UNNEST(topics) as topic, stars
            FROM sofia.github_trending
            WHERE topics IS NOT NULL
        ) t
        GROUP BY topic
        ORDER BY total_stars DESC
        LIMIT 20
    """)

    # Get funded sectors for comparison
    funded_sectors = safe_query(cur, """
        SELECT LOWER(sector) as sector, COUNT(*) as deals
        FROM sofia.funding_rounds
        WHERE sector IS NOT NULL
        GROUP BY LOWER(sector)
    """)
    funded_set = {r['sector'] for r in funded_sectors}

    # Find topics trending on GitHub but not heavily funded
    signals = []
    for topic in topics:
        topic_lower = topic['topic'].lower()
        # Check if this topic has funding
        is_funded = any(topic_lower in sector for sector in funded_set)
        if not is_funded and topic['total_stars'] > 1000:
            signals.append({
                'topic': topic['topic'],
                'stars': int(topic['total_stars'] or 0),
                'repos': topic['count'],
                'signal': 'STRONG' if topic['total_stars'] > 10000 else 'MODERATE'
            })

    cur.close()
    return {'languages': languages, 'topics': topics, 'signals': signals[:10]}

def analyze_research_topics(conn):
    """Analyze research paper topics and keywords"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get paper categories
    categories = safe_query(cur, """
        SELECT primary_category as category, COUNT(*) as count
        FROM sofia.arxiv_ai_papers
        WHERE primary_category IS NOT NULL
        GROUP BY primary_category
        ORDER BY count DESC
        LIMIT 15
    """)

    # Get keywords if available
    keywords = safe_query(cur, """
        SELECT keyword, COUNT(*) as count
        FROM (
            SELECT UNNEST(keywords) as keyword
            FROM sofia.arxiv_ai_papers
            WHERE keywords IS NOT NULL
        ) k
        GROUP BY keyword
        ORDER BY count DESC
        LIMIT 20
    """)

    # Extract topics from titles using regex
    papers = safe_query(cur, """
        SELECT title FROM sofia.arxiv_ai_papers
        WHERE title IS NOT NULL
        LIMIT 500
    """)

    # Common AI/ML terms to look for
    tech_patterns = {
        'LLM/GPT': r'\b(llm|gpt|language model|transformer|bert|chatgpt)\b',
        'Diffusion': r'\b(diffusion|stable diffusion|imagen|dalle)\b',
        'Vision': r'\b(vision|image|visual|cnn|yolo|object detection)\b',
        'Reinforcement': r'\b(reinforcement|rl|reward|policy)\b',
        'Agents': r'\b(agent|multi-agent|autonomous)\b',
        'Robotics': r'\b(robot|manipulation|navigation)\b',
        'Medical/Bio': r'\b(medical|clinical|drug|protein|health)\b',
    }

    topic_counts = defaultdict(int)
    for paper in papers:
        title = paper['title'].lower()
        for topic, pattern in tech_patterns.items():
            if re.search(pattern, title, re.IGNORECASE):
                topic_counts[topic] += 1

    extracted_topics = [{'topic': k, 'count': v} for k, v in sorted(topic_counts.items(), key=lambda x: -x[1])]

    cur.close()
    return {'categories': categories, 'keywords': keywords, 'extracted_topics': extracted_topics}

def analyze_funding_patterns(conn):
    """Analyze funding patterns by sector, stage, and geography"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # By sector
    sectors = safe_query(cur, """
        SELECT sector,
               COUNT(*) as deals,
               SUM(COALESCE(amount_usd, 0)) as total_funding,
               AVG(COALESCE(amount_usd, 0)) as avg_deal
        FROM sofia.funding_rounds
        WHERE sector IS NOT NULL
        GROUP BY sector
        ORDER BY total_funding DESC
        LIMIT 15
    """)

    # By round type
    stages = safe_query(cur, """
        SELECT round_type,
               COUNT(*) as deals,
               SUM(COALESCE(amount_usd, 0)) as total_funding
        FROM sofia.funding_rounds
        WHERE round_type IS NOT NULL
        GROUP BY round_type
        ORDER BY total_funding DESC
        LIMIT 10
    """)

    # By country
    countries = safe_query(cur, """
        SELECT country,
               COUNT(*) as deals,
               SUM(COALESCE(amount_usd, 0)) as total_funding
        FROM sofia.funding_rounds
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY total_funding DESC
        LIMIT 15
    """)

    # Monthly trend
    monthly = safe_query(cur, """
        SELECT DATE_TRUNC('month', announced_date) as month,
               COUNT(*) as deals,
               SUM(COALESCE(amount_usd, 0)) as total_funding
        FROM sofia.funding_rounds
        WHERE announced_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', announced_date)
        ORDER BY month DESC
        LIMIT 12
    """)

    cur.close()
    return {'sectors': sectors, 'stages': stages, 'countries': countries, 'monthly': monthly}

def ml_correlation_analysis(conn):
    """ML correlation between papers and funding"""
    if not ML_AVAILABLE:
        return None

    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Papers by month
    papers_monthly = safe_query(cur, """
        SELECT DATE_TRUNC('month', published_date) as month,
               COUNT(*) as count
        FROM sofia.arxiv_ai_papers
        WHERE published_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', published_date)
        ORDER BY month
    """)

    # Funding by month
    funding_monthly = safe_query(cur, """
        SELECT DATE_TRUNC('month', announced_date) as month,
               SUM(COALESCE(amount_usd, 0)) as total
        FROM sofia.funding_rounds
        WHERE announced_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', announced_date)
        ORDER BY month
    """)

    if len(papers_monthly) < 3 or len(funding_monthly) < 3:
        cur.close()
        return None

    # Align data by month
    papers_dict = {r['month']: r['count'] for r in papers_monthly}
    funding_dict = {r['month']: float(r['total'] or 0) for r in funding_monthly}

    common_months = set(papers_dict.keys()) & set(funding_dict.keys())
    if len(common_months) < 3:
        cur.close()
        return None

    common_months = sorted(common_months)
    X = np.array([papers_dict[m] for m in common_months]).reshape(-1, 1)
    y = np.array([funding_dict[m] for m in common_months])

    # Correlation
    corr, p_value = pearsonr(X.flatten(), y)

    # Regression
    model = LinearRegression()
    model.fit(X, y)
    r_squared = model.score(X, y)

    # Prediction
    latest_papers = papers_monthly[-1]['count'] if papers_monthly else 0
    predicted = model.predict([[latest_papers]])[0] if latest_papers > 0 else 0

    cur.close()
    return {
        'correlation': corr,
        'p_value': p_value,
        'r_squared': r_squared,
        'data_points': len(common_months),
        'latest_papers': latest_papers,
        'predicted_funding': predicted,
        'confidence': 'HIGH' if r_squared > 0.7 else 'MEDIUM' if r_squared > 0.4 else 'LOW'
    }

def cluster_sectors(conn):
    """Cluster sectors using KMeans"""
    if not ML_AVAILABLE:
        return None

    cur = conn.cursor(cursor_factory=RealDictCursor)

    sectors = safe_query(cur, """
        SELECT sector,
               COUNT(*) as deals,
               SUM(COALESCE(amount_usd, 0)) as total_funding,
               AVG(COALESCE(amount_usd, 0)) as avg_deal
        FROM sofia.funding_rounds
        WHERE sector IS NOT NULL AND amount_usd > 0
        GROUP BY sector
        HAVING COUNT(*) >= 2
    """)

    cur.close()

    if len(sectors) < 4:
        return None

    # Prepare features
    sector_names = [s['sector'] for s in sectors]
    features = np.array([[float(s['total_funding']), float(s['deals']), float(s['avg_deal'])] for s in sectors])

    # Scale
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # Cluster
    n_clusters = min(3, len(sectors))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features_scaled)

    # Group results
    clusters = defaultdict(list)
    for i, sector in enumerate(sector_names):
        clusters[int(labels[i])].append({
            'sector': sector,
            'funding': float(sectors[i]['total_funding']),
            'deals': int(sectors[i]['deals'])
        })

    # Sort each cluster by funding
    for cluster_id in clusters:
        clusters[cluster_id].sort(key=lambda x: -x['funding'])

    return dict(clusters)

def forecast_trends(conn):
    """Forecast future trends using linear regression"""
    if not ML_AVAILABLE:
        return None

    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Funding by month
    funding_monthly = safe_query(cur, """
        SELECT DATE_TRUNC('month', announced_date) as month,
               SUM(COALESCE(amount_usd, 0)) as total
        FROM sofia.funding_rounds
        WHERE announced_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', announced_date)
        ORDER BY month
    """)

    # Papers by month
    papers_monthly = safe_query(cur, """
        SELECT DATE_TRUNC('month', published_date) as month,
               COUNT(*) as count
        FROM sofia.arxiv_ai_papers
        WHERE published_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', published_date)
        ORDER BY month
    """)

    cur.close()

    forecasts = []

    # Funding forecast
    if len(funding_monthly) >= 3:
        X = np.array(range(len(funding_monthly))).reshape(-1, 1)
        y = np.array([float(r['total'] or 0) for r in funding_monthly])

        model = LinearRegression()
        model.fit(X, y)

        future = [model.predict([[len(funding_monthly) + i]])[0] for i in range(1, 4)]
        trend = 'GROWING' if future[-1] > y[-1] else 'STABLE'

        forecasts.append({
            'metric': 'Funding',
            'current': float(y[-1]),
            'predictions': [max(0, f) for f in future],
            'trend': trend
        })

    # Papers forecast
    if len(papers_monthly) >= 3:
        X = np.array(range(len(papers_monthly))).reshape(-1, 1)
        y = np.array([r['count'] for r in papers_monthly])

        model = LinearRegression()
        model.fit(X, y)

        future = [int(max(0, model.predict([[len(papers_monthly) + i]])[0])) for i in range(1, 4)]
        trend = 'GROWING' if future[-1] > y[-1] else 'STABLE'

        forecasts.append({
            'metric': 'Papers',
            'current': int(y[-1]),
            'predictions': future,
            'trend': trend
        })

    return forecasts if forecasts else None

def generate_report(conn):
    """Generate the complete ML insights report"""
    r = []

    r.append("=" * 80)
    r.append("SOFIA PULSE - CAUSAL INSIGHTS (Machine Learning Enhanced)")
    r.append("=" * 80)
    r.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    r.append("")

    # =========================================================================
    # DATA OVERVIEW
    # =========================================================================
    overview = get_data_overview(conn)

    r.append("=" * 80)
    r.append("1. DATA OVERVIEW")
    r.append("=" * 80)
    r.append("")

    funding = overview.get('funding', {})
    github = overview.get('github', {})
    papers = overview.get('papers', {})

    r.append("Available Data:")
    r.append(f"  Funding Rounds: {funding.get('total', 0):,}")
    if funding.get('earliest'):
        r.append(f"    Date Range: {funding['earliest']} to {funding['latest']}")
    total_funding = float(funding.get('total_funding', 0) or 0)
    if total_funding > 0:
        r.append(f"    Total Capital: ${total_funding/1e9:.2f}B")

    r.append(f"  GitHub Repos: {github.get('total', 0):,}")
    if github.get('total_stars'):
        r.append(f"    Total Stars: {int(github['total_stars'] or 0):,}")

    r.append(f"  Research Papers: {papers.get('total', 0):,}")
    r.append("")

    # =========================================================================
    # GITHUB SIGNALS
    # =========================================================================
    r.append("=" * 80)
    r.append("2. GITHUB SIGNALS (Weak Signal Detection)")
    r.append("=" * 80)
    r.append("")

    github_data = analyze_github_signals(conn)

    if github_data['languages']:
        r.append("TOP LANGUAGES (by stars):")
        r.append("-" * 50)
        for lang in github_data['languages'][:8]:
            stars = int(lang['total_stars'] or 0)
            r.append(f"  {lang['language']:<15} {lang['repo_count']:>5} repos, {stars:>12,} stars")
        r.append("")

    if github_data['signals']:
        r.append("WEAK SIGNALS (trending but not heavily funded):")
        r.append("-" * 50)
        for sig in github_data['signals'][:5]:
            r.append(f"  {sig['topic']}: {sig['stars']:,} stars ({sig['signal']})")
            r.append(f"    -> Potential funding opportunity in 3-6 months")
        r.append("")
    else:
        r.append("No weak signals detected with current data.")
        r.append("")

    # =========================================================================
    # RESEARCH TOPICS
    # =========================================================================
    r.append("=" * 80)
    r.append("3. RESEARCH TOPIC ANALYSIS (NLP)")
    r.append("=" * 80)
    r.append("")

    research_data = analyze_research_topics(conn)

    if research_data['extracted_topics']:
        r.append("EMERGING RESEARCH TOPICS (extracted from titles):")
        r.append("-" * 50)
        for topic in research_data['extracted_topics']:
            r.append(f"  {topic['topic']:<20} {topic['count']:>5} papers")
        r.append("")

    if research_data['categories']:
        r.append("PAPER CATEGORIES:")
        r.append("-" * 50)
        for cat in research_data['categories'][:10]:
            r.append(f"  {cat['category']:<25} {cat['count']:>5} papers")
        r.append("")

    if not research_data['extracted_topics'] and not research_data['categories']:
        r.append("No research paper data available.")
        r.append("")

    # =========================================================================
    # FUNDING PATTERNS
    # =========================================================================
    r.append("=" * 80)
    r.append("4. FUNDING PATTERNS")
    r.append("=" * 80)
    r.append("")

    funding_data = analyze_funding_patterns(conn)

    if funding_data['sectors']:
        r.append("TOP SECTORS:")
        r.append("-" * 70)
        r.append(f"{'Sector':<30} {'Deals':>8} {'Total':>18} {'Avg':>15}")
        r.append("-" * 70)
        for sector in funding_data['sectors'][:10]:
            total = float(sector['total_funding'] or 0)
            avg = float(sector['avg_deal'] or 0)
            total_str = f"${total/1e6:.1f}M" if total > 0 else "N/A"
            avg_str = f"${avg/1e6:.1f}M" if avg > 0 else "N/A"
            r.append(f"{sector['sector'][:28]:<30} {sector['deals']:>8} {total_str:>18} {avg_str:>15}")
        r.append("")

    if funding_data['countries']:
        r.append("GEOGRAPHIC DISTRIBUTION:")
        r.append("-" * 50)
        for country in funding_data['countries'][:8]:
            total = float(country['total_funding'] or 0)
            total_str = f"${total/1e6:.1f}M" if total > 0 else "N/A"
            r.append(f"  {country['country']:<20} {country['deals']:>5} deals ({total_str})")
        r.append("")

    if funding_data['monthly']:
        r.append("MONTHLY TREND (recent):")
        r.append("-" * 50)
        for month in funding_data['monthly'][:6]:
            total = float(month['total_funding'] or 0)
            month_str = str(month['month'])[:7] if month['month'] else 'N/A'
            total_str = f"${total/1e6:.1f}M" if total > 0 else "N/A"
            r.append(f"  {month_str}: {month['deals']:>4} deals, {total_str}")
        r.append("")

    if not funding_data['sectors']:
        r.append("No funding data available.")
        r.append("")

    # =========================================================================
    # ML CORRELATION
    # =========================================================================
    r.append("=" * 80)
    r.append("5. ML CORRELATION ANALYSIS (Sklearn)")
    r.append("=" * 80)
    r.append("")

    if ML_AVAILABLE:
        ml_corr = ml_correlation_analysis(conn)
        if ml_corr:
            r.append("PAPERS -> FUNDING CORRELATION:")
            r.append("-" * 50)
            r.append(f"  Pearson Correlation: {ml_corr['correlation']:.4f}")
            r.append(f"  P-value: {ml_corr['p_value']:.4f}")
            r.append(f"  R-squared: {ml_corr['r_squared']:.4f}")
            r.append(f"  Data Points: {ml_corr['data_points']} months")
            r.append(f"  Confidence: {ml_corr['confidence']}")
            r.append("")
            r.append("PREDICTION:")
            r.append(f"  Latest Papers/Month: {ml_corr['latest_papers']}")
            pred = ml_corr['predicted_funding']
            r.append(f"  Predicted Funding: ${pred/1e9:.2f}B")
            r.append("")
        else:
            r.append("Insufficient data for correlation analysis.")
            r.append("Need at least 3 months of overlapping paper and funding data.")
            r.append("")
    else:
        r.append("ML libraries not available (sklearn/scipy).")
        r.append("")

    # =========================================================================
    # SECTOR CLUSTERING
    # =========================================================================
    r.append("=" * 80)
    r.append("6. SECTOR CLUSTERING (KMeans)")
    r.append("=" * 80)
    r.append("")

    if ML_AVAILABLE:
        clusters = cluster_sectors(conn)
        if clusters:
            for cluster_id, sectors in clusters.items():
                total = sum(s['funding'] for s in sectors)
                label = "HIGH ACTIVITY" if cluster_id == 0 else "MEDIUM" if cluster_id == 1 else "EMERGING"
                r.append(f"CLUSTER {cluster_id} - {label} (${total/1e9:.2f}B total):")
                r.append("-" * 50)
                for s in sectors[:5]:
                    r.append(f"  {s['sector'][:30]:<32} {s['deals']:>4} deals, ${s['funding']/1e6:.1f}M")
                r.append("")
        else:
            r.append("Insufficient sector data for clustering.")
            r.append("Need at least 4 sectors with 2+ deals each.")
            r.append("")
    else:
        r.append("ML libraries not available (sklearn).")
        r.append("")

    # =========================================================================
    # TIME SERIES FORECASTING
    # =========================================================================
    r.append("=" * 80)
    r.append("7. TIME SERIES FORECASTING")
    r.append("=" * 80)
    r.append("")

    if ML_AVAILABLE:
        forecasts = forecast_trends(conn)
        if forecasts:
            r.append("PREDICTIONS (next 3 months):")
            r.append("-" * 50)
            for f in forecasts:
                r.append(f"\n{f['metric']}:")
                if f['metric'] == 'Funding':
                    r.append(f"  Current: ${f['current']/1e9:.2f}B")
                    for i, pred in enumerate(f['predictions'], 1):
                        r.append(f"  Month {i}: ${pred/1e9:.2f}B")
                else:
                    r.append(f"  Current: {f['current']} papers")
                    for i, pred in enumerate(f['predictions'], 1):
                        r.append(f"  Month {i}: {pred} papers")
                r.append(f"  Trend: {f['trend']}")
            r.append("")
        else:
            r.append("Insufficient temporal data for forecasting.")
            r.append("Need at least 3 months of data.")
            r.append("")
    else:
        r.append("ML libraries not available (sklearn).")
        r.append("")

    # =========================================================================
    # STRATEGIC INSIGHTS
    # =========================================================================
    r.append("=" * 80)
    r.append("8. STRATEGIC INSIGHTS")
    r.append("=" * 80)
    r.append("")

    r.append("FOR INVESTORS:")
    r.append("-" * 50)
    if github_data['signals']:
        top_signal = github_data['signals'][0]
        r.append(f"  - Watch '{top_signal['topic']}' - trending on GitHub but not heavily funded")

    if research_data['extracted_topics']:
        top_topic = research_data['extracted_topics'][0]
        r.append(f"  - '{top_topic['topic']}' is hot in research ({top_topic['count']} papers)")

    if funding_data['sectors']:
        top_sector = funding_data['sectors'][0]
        total = float(top_sector['total_funding'] or 0)
        r.append(f"  - Top sector: {top_sector['sector']} (${total/1e6:.0f}M, {top_sector['deals']} deals)")
    r.append("")

    r.append("FOR FOUNDERS:")
    r.append("-" * 50)
    if github_data['languages']:
        top_langs = [l['language'] for l in github_data['languages'][:3]]
        r.append(f"  - Hot tech stack: {', '.join(top_langs)}")

    if funding_data['countries']:
        top_countries = [c['country'] for c in funding_data['countries'][:3]]
        r.append(f"  - Capital flowing to: {', '.join(top_countries)}")
    r.append("")

    r.append("FOR TALENT:")
    r.append("-" * 50)
    r.append("  - Learn trending languages from GitHub data")
    r.append("  - Follow funded sectors for job opportunities")
    r.append("  - Research topics indicate future skill demands")
    r.append("")

    r.append("=" * 80)
    r.append("Analysis complete!")
    r.append("=" * 80)

    return "\n".join(r)

def main():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("Connected.")
    print()

    print("Generating ML insights report...")
    report = generate_report(conn)

    print(report)

    # Save
    output_path = 'analytics/causal-insights-latest.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nSaved to: {output_path}")

    conn.close()

if __name__ == '__main__':
    main()
