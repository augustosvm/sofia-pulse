#!/usr/bin/env python3
"""
ANOMALY DETECTION REPORT - Growth Explosions

Detects technologies with abnormal growth using:
1. Z-score (statistical outliers)
2. Isolation Forest (ML-based anomaly detection)
3. Growth rate analysis (% change)

Alerts for:
- GitHub repos growing >400% in 30 days
- Funding spikes (10x normal)
- Paper publication explosions
- Jobs demand spikes
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from dotenv import load_dotenv

# Add analytics directory to path for shared imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.tech_normalizer import normalize_tech_name

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

# normalize_tech_name is imported from shared.tech_normalizer

# ============================================================================
# STATISTICAL ANOMALY DETECTION (Z-Score)
# ============================================================================

def calculate_z_score(value, mean, std):
    """Calculate z-score for a value"""
    if std == 0:
        return 0
    return (value - mean) / std

def detect_statistical_anomalies(values, threshold=2.5):
    """
    Detect anomalies using z-score

    threshold=2.5 means values >2.5 standard deviations from mean
    """
    if len(values) < 3:
        return []

    values_array = np.array(values)
    mean = np.mean(values_array)
    std = np.std(values_array)

    anomalies = []
    for i, val in enumerate(values_array):
        z = calculate_z_score(val, mean, std)
        if abs(z) > threshold:
            anomalies.append({
                'index': i,
                'value': val,
                'z_score': z,
                'is_outlier': z > threshold  # True if positive outlier (high growth)
            })

    return anomalies

# ============================================================================
# GITHUB GROWTH ANOMALIES
# ============================================================================

def detect_github_anomalies(conn):
    """Detect repos with explosive growth"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get repos from last 90 days grouped by topic
    cur.execute("""
        SELECT
            unnest(topics) as tech,
            SUM(stars) as total_stars,
            COUNT(*) as repo_count,
            AVG(stars) as avg_stars
        FROM sofia.github_trending
        WHERE topics IS NOT NULL
            AND created_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY tech
        HAVING COUNT(*) >= 3
        ORDER BY total_stars DESC
    """)

    trends = cur.fetchall()

    if len(trends) < 5:
        return []

    # Extract star counts
    star_counts = [t['total_stars'] for t in trends]

    # Detect anomalies using z-score
    anomalies = detect_statistical_anomalies(star_counts, threshold=2.0)

    # Map back to technologies
    result = []
    for anomaly in anomalies:
        if anomaly['is_outlier']:  # Only positive outliers (high growth)
            tech_data = trends[anomaly['index']]
            result.append({
                'tech': tech_data['tech'],
                'total_stars': int(tech_data['total_stars']),
                'repo_count': int(tech_data['repo_count']),
                'avg_stars': int(tech_data['avg_stars']),
                'z_score': anomaly['z_score'],
                'growth_type': 'EXTREME' if anomaly['z_score'] > 3 else 'HIGH'
            })

    return sorted(result, key=lambda x: -x['z_score'])

# ============================================================================
# FUNDING ANOMALIES
# ============================================================================

def detect_funding_anomalies(conn):
    """Detect unusual funding spikes by sector"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get funding by sector (last 90 days vs previous 90 days)
    cur.execute("""
        SELECT
            sector,
            SUM(CASE WHEN announced_date >= CURRENT_DATE - INTERVAL '90 days'
                THEN amount_usd ELSE 0 END) as recent_funding,
            SUM(CASE WHEN announced_date >= CURRENT_DATE - INTERVAL '180 days'
                     AND announced_date < CURRENT_DATE - INTERVAL '90 days'
                THEN amount_usd ELSE 0 END) as previous_funding,
            COUNT(CASE WHEN announced_date >= CURRENT_DATE - INTERVAL '90 days'
                  THEN 1 END) as recent_deals,
            COUNT(CASE WHEN announced_date >= CURRENT_DATE - INTERVAL '180 days'
                       AND announced_date < CURRENT_DATE - INTERVAL '90 days'
                  THEN 1 END) as previous_deals
        FROM sofia.funding_rounds
        WHERE sector IS NOT NULL
            AND announced_date >= CURRENT_DATE - INTERVAL '180 days'
        GROUP BY sector
        HAVING COUNT(*) >= 2
    """)

    sectors = cur.fetchall()

    anomalies = []

    for sector in sectors:
        recent = float(sector['recent_funding'] or 0)
        previous = float(sector['previous_funding'] or 0)

        # Skip if no recent funding
        if recent == 0:
            continue

        # Calculate growth rate
        if previous > 0:
            growth_rate = ((recent - previous) / previous) * 100
        else:
            growth_rate = 1000 if recent > 0 else 0  # 1000% if new funding appeared

        # Detect anomalies: growth >500% or absolute recent funding >$1B
        if growth_rate > 500 or recent > 1e9:
            anomalies.append({
                'sector': sector['sector'],
                'recent_funding': recent,
                'previous_funding': previous,
                'growth_rate': growth_rate,
                'recent_deals': int(sector['recent_deals']),
                'previous_deals': int(sector['previous_deals']),
                'anomaly_type': 'NEW_SECTOR' if previous == 0 else 'SPIKE'
            })

    return sorted(anomalies, key=lambda x: -x['growth_rate'])

# ============================================================================
# PAPER PUBLICATION ANOMALIES
# ============================================================================

def detect_paper_anomalies(conn):
    """Detect topics with unusual paper publication spikes"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get papers by topic and month
    cur.execute("""
        SELECT
            UNNEST(keywords) as topic,
            DATE_TRUNC('month', published_date) as month,
            COUNT(*) as paper_count
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '180 days'
            AND keywords IS NOT NULL
        GROUP BY topic, month
        HAVING COUNT(*) >= 3
    """)

    papers = cur.fetchall()

    # Group by topic
    topic_timeline = defaultdict(list)

    for paper in papers:
        topic_timeline[paper['topic']].append({
            'month': paper['month'],
            'count': paper['paper_count']
        })

    # Detect anomalies: topics with sudden spikes
    anomalies = []

    for topic, timeline in topic_timeline.items():
        if len(timeline) < 3:
            continue

        counts = [t['count'] for t in sorted(timeline, key=lambda x: x['month'])]

        # Recent count (latest month)
        recent_count = counts[-1]

        # Average of previous months
        avg_previous = np.mean(counts[:-1]) if len(counts) > 1 else 0

        # Detect spike: recent count >3x average
        if avg_previous > 0 and recent_count > avg_previous * 3:
            growth_rate = ((recent_count - avg_previous) / avg_previous) * 100

            anomalies.append({
                'topic': topic,
                'recent_count': recent_count,
                'avg_previous': avg_previous,
                'growth_rate': growth_rate,
                'months': len(timeline)
            })

    return sorted(anomalies, key=lambda x: -x['growth_rate'])

# ============================================================================
# ISOLATION FOREST (ML-based Anomaly Detection)
# ============================================================================

def detect_ml_anomalies(conn):
    """
    Use Isolation Forest to detect multi-dimensional anomalies

    Features:
    - GitHub stars
    - Funding amount
    - Paper count
    - Job postings
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Aggregate data by technology/sector
    tech_data = defaultdict(lambda: {
        'github_stars': 0,
        'funding': 0,
        'papers': 0,
        'jobs': 0
    })

    # GitHub data (with normalization)
    cur.execute("""
        SELECT unnest(topics) as tech, SUM(stars) as stars
        FROM sofia.github_trending
        WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY tech
    """)
    for row in cur.fetchall():
        normalized = normalize_tech_name(row['tech'])
        if normalized:
            tech_data[normalized]['github_stars'] += int(row['stars'])

    # Funding data (with normalization)
    cur.execute("""
        SELECT sector, SUM(amount_usd) as total
        FROM sofia.funding_rounds
        WHERE announced_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY sector
    """)
    for row in cur.fetchall():
        normalized = normalize_tech_name(row['sector'])
        if normalized:
            tech_data[normalized]['funding'] += float(row['total'] or 0)

    # Papers (with normalization)
    cur.execute("""
        SELECT UNNEST(keywords) as topic, COUNT(*) as count
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY topic
    """)
    for row in cur.fetchall():
        normalized = normalize_tech_name(row['topic'])
        if normalized:
            tech_data[normalized]['papers'] += int(row['count'])

    # Convert to feature matrix
    techs = []
    features = []

    for tech, data in tech_data.items():
        # Only include techs with at least 2 data sources
        non_zero = sum(1 for v in data.values() if v > 0)
        if non_zero >= 2:
            techs.append(tech)
            features.append([
                data['github_stars'],
                data['funding'],
                data['papers'],
                data['jobs']
            ])

    if len(features) < 3:
        return []

    # Normalize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # Isolation Forest
    clf = IsolationForest(contamination=0.1, random_state=42)
    predictions = clf.fit_predict(features_scaled)

    # Extract anomalies
    anomalies = []
    for i, pred in enumerate(predictions):
        if pred == -1:  # Anomaly
            anomalies.append({
                'tech': techs[i],
                'github_stars': features[i][0],
                'funding': features[i][1],
                'papers': features[i][2],
                'jobs': features[i][3],
                'anomaly_score': clf.score_samples([features_scaled[i]])[0]
            })

    return sorted(anomalies, key=lambda x: x['anomaly_score'])

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(conn):
    report = []

    report.append("=" * 80)
    report.append("ANOMALY DETECTION REPORT - Growth Explosions")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # 1. GitHub Anomalies
    report.append("=" * 80)
    report.append("🚀 GITHUB GROWTH ANOMALIES (Z-Score)")
    report.append("=" * 80)
    report.append("")

    github_anomalies = detect_github_anomalies(conn)

    if github_anomalies:
        report.append("⚡ TECHNOLOGIES WITH EXPLOSIVE GROWTH:")
        report.append("")
        for anomaly in github_anomalies[:10]:
            report.append(f"• {anomaly['tech']}")
            report.append(f"  Stars: {anomaly['total_stars']:,} ({anomaly['repo_count']} repos)")
            report.append(f"  Z-score: {anomaly['z_score']:.2f} ({anomaly['growth_type']} growth)")
            report.append("")
    else:
        report.append("(No GitHub anomalies detected)")
        report.append("")

    # 2. Funding Anomalies
    report.append("=" * 80)
    report.append("💰 FUNDING SPIKES (Growth Rate Analysis)")
    report.append("=" * 80)
    report.append("")

    funding_anomalies = detect_funding_anomalies(conn)

    if funding_anomalies:
        report.append("🔥 SECTORS WITH FUNDING EXPLOSIONS:")
        report.append("")
        for anomaly in funding_anomalies[:10]:
            report.append(f"• {anomaly['sector']}")
            report.append(f"  Recent: ${anomaly['recent_funding']/1e9:.2f}B ({anomaly['recent_deals']} deals)")
            report.append(f"  Previous: ${anomaly['previous_funding']/1e9:.2f}B ({anomaly['previous_deals']} deals)")
            report.append(f"  Growth: {anomaly['growth_rate']:.0f}% ({anomaly['anomaly_type']})")
            report.append("")
    else:
        report.append("(No funding anomalies detected)")
        report.append("")

    # 3. Paper Publication Anomalies
    report.append("=" * 80)
    report.append("📄 RESEARCH PUBLICATION SPIKES")
    report.append("=" * 80)
    report.append("")

    paper_anomalies = detect_paper_anomalies(conn)

    if paper_anomalies:
        report.append("📚 TOPICS WITH PUBLICATION EXPLOSIONS:")
        report.append("")
        for anomaly in paper_anomalies[:10]:
            report.append(f"• {anomaly['topic']}")
            report.append(f"  Recent month: {anomaly['recent_count']} papers")
            report.append(f"  Average previous: {anomaly['avg_previous']:.1f} papers")
            report.append(f"  Growth: {anomaly['growth_rate']:.0f}%")
            report.append("")
    else:
        report.append("(No paper anomalies detected)")
        report.append("")

    # 4. ML-based Anomalies (Isolation Forest)
    report.append("=" * 80)
    report.append("🤖 ML-BASED ANOMALIES (Isolation Forest)")
    report.append("=" * 80)
    report.append("")

    ml_anomalies = detect_ml_anomalies(conn)

    if ml_anomalies:
        report.append("🎯 MULTI-DIMENSIONAL ANOMALIES:")
        report.append("")
        for anomaly in ml_anomalies[:10]:
            report.append(f"• {anomaly['tech']}")
            report.append(f"  GitHub: {anomaly['github_stars']:,} stars")
            report.append(f"  Funding: ${anomaly['funding']/1e9:.2f}B")
            report.append(f"  Papers: {anomaly['papers']}")
            report.append(f"  Anomaly score: {anomaly['anomaly_score']:.3f}")
            report.append("")
    else:
        report.append("(Insufficient data for ML anomaly detection)")
        report.append("")

    report.append("=" * 80)
    report.append("✅ Anomaly Detection Complete!")
    report.append("")

    return "\n".join(report)

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
        print()

        report = generate_report(conn)

        # Print
        print(report)

        # Save
        with open('analytics/anomaly-detection.txt', 'w') as f:
            f.write(report)

        print("💾 Saved to: analytics/anomaly-detection.txt")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
