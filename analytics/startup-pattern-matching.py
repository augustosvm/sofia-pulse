#!/usr/bin/env python3
"""
STARTUP PATTERN MATCHING - Find Next Unicorns

Uses K-Means clustering to find startups with similar patterns to:
- Stripe (2015 early stage)
- Airbnb (2013 early stage)
- OpenAI (2020 early stage)
- Figma (2017 early stage)

Features analyzed:
1. Funding pattern (amount, frequency, stage)
2. Growth rate (deals over time)
3. Sector similarities
4. Geographic location
5. Time since founding

Output:
- "These 5 startups have patterns similar to Stripe in 2015"
- "High unicorn potential: Company X (95% match)"
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST') or 'localhost',
    'port': int(os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT') or '5432'),
    'user': os.getenv('POSTGRES_USER') or os.getenv('DB_USER') or 'sofia',
    'password': os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD') or '',
    'database': os.getenv('POSTGRES_DB') or os.getenv('DB_NAME') or 'sofia_db',
}

# ============================================================================
# REFERENCE UNICORN PATTERNS (Historical Data)
# ============================================================================

UNICORN_PATTERNS = {
    'stripe': {
        'early_stage': {
            'total_funding_range': (10e6, 50e6),  # $10M-$50M
            'deals_count_range': (2, 4),
            'avg_deal_size_range': (5e6, 20e6),
            'time_to_series_b_months': 24,
            'sector_keywords': ['fintech', 'payments', 'finance', 'api'],
            'location': 'United States'
        }
    },
    'airbnb': {
        'early_stage': {
            'total_funding_range': (7e6, 120e6),
            'deals_count_range': (3, 6),
            'avg_deal_size_range': (2e6, 25e6),
            'time_to_series_b_months': 30,
            'sector_keywords': ['marketplace', 'sharing economy', 'travel', 'hospitality'],
            'location': 'United States'
        }
    },
    'openai': {
        'early_stage': {
            'total_funding_range': (1e9, 10e9),  # OpenAI was unique (high initial funding)
            'deals_count_range': (2, 5),
            'avg_deal_size_range': (1e9, 5e9),
            'time_to_series_b_months': 12,
            'sector_keywords': ['ai', 'ml', 'artificial intelligence', 'research'],
            'location': 'United States'
        }
    },
    'figma': {
        'early_stage': {
            'total_funding_range': (14e6, 40e6),
            'deals_count_range': (2, 4),
            'avg_deal_size_range': (7e6, 20e6),
            'time_to_series_b_months': 36,
            'sector_keywords': ['design', 'collaboration', 'saas', 'tools'],
            'location': 'United States'
        }
    }
}

# ============================================================================
# FEATURE EXTRACTION
# ============================================================================

def extract_startup_features(conn):
    """
    Extract features for all startups in database

    Features:
    - total_funding: Total funding raised
    - deals_count: Number of funding rounds
    - avg_deal_size: Average deal size
    - latest_amount: Most recent funding round
    - sector: Normalized sector
    - country: Geographic location
    """
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get funding data by company
    cur.execute("""
        SELECT
            company_name,
            sector,
            fr.country_id,
            c.common_name as country,
            COUNT(*) as deals_count,
            SUM(amount_usd) as total_funding,
            AVG(amount_usd) as avg_deal_size,
            MAX(amount_usd) as max_deal_size,
            MIN(announced_date) as first_deal_date,
            MAX(announced_date) as latest_deal_date
        FROM sofia.funding_rounds fr
        LEFT JOIN sofia.countries c ON fr.country_id = c.id
        WHERE announced_date >= CURRENT_DATE - INTERVAL '180 days'
            AND amount_usd IS NOT NULL
            AND amount_usd > 0
        GROUP BY company_name, sector, fr.country_id, c.common_name
        HAVING COUNT(*) >= 1
    """)

    startups = cur.fetchall()

    features = []

    for startup in startups:
        # Calculate days since first funding
        first_date = startup['first_deal_date']
        latest_date = startup['latest_deal_date']

        if first_date and latest_date:
            days_active = (latest_date - first_date).days
        else:
            days_active = 0

        features.append({
            'company_name': startup['company_name'],
            'sector': startup['sector'] or 'unknown',
            'country': startup['country'] or 'unknown',
            'total_funding': float(startup['total_funding']),
            'deals_count': int(startup['deals_count']),
            'avg_deal_size': float(startup['avg_deal_size']),
            'max_deal_size': float(startup['max_deal_size']),
            'days_active': days_active
        })

    return features

# ============================================================================
# PATTERN MATCHING
# ============================================================================

def calculate_similarity_score(startup, unicorn_pattern):
    """
    Calculate similarity score (0-100) between startup and unicorn pattern

    Higher score = more similar to unicorn
    """
    pattern = unicorn_pattern['early_stage']
    score = 0
    max_score = 0

    # 1. Total funding range (30 points)
    max_score += 30
    min_funding, max_funding = pattern['total_funding_range']

    if min_funding <= startup['total_funding'] <= max_funding:
        score += 30
    elif startup['total_funding'] < min_funding:
        # Partial credit if close
        ratio = startup['total_funding'] / min_funding
        score += min(30, 30 * ratio)
    else:
        # Over-funded (less typical of early stage)
        ratio = max_funding / startup['total_funding']
        score += min(30, 30 * ratio)

    # 2. Deals count (20 points)
    max_score += 20
    min_deals, max_deals = pattern['deals_count_range']

    if min_deals <= startup['deals_count'] <= max_deals:
        score += 20
    elif abs(startup['deals_count'] - min_deals) <= 2:
        score += 10

    # 3. Average deal size (20 points)
    max_score += 20
    min_avg, max_avg = pattern['avg_deal_size_range']

    if min_avg <= startup['avg_deal_size'] <= max_avg:
        score += 20
    elif startup['avg_deal_size'] < min_avg:
        ratio = startup['avg_deal_size'] / min_avg
        score += min(20, 20 * ratio)
    else:
        ratio = max_avg / startup['avg_deal_size']
        score += min(20, 20 * ratio)

    # 4. Sector match (20 points)
    max_score += 20
    sector_lower = startup['sector'].lower()

    for keyword in pattern['sector_keywords']:
        if keyword in sector_lower:
            score += 20
            break

    # 5. Location match (10 points)
    max_score += 10
    if startup['country'] == pattern['location']:
        score += 10

    # Normalize to 0-100
    final_score = (score / max_score) * 100 if max_score > 0 else 0

    return final_score

def find_similar_startups(startups_features):
    """
    Find startups similar to unicorn patterns using pattern matching
    """
    results = {
        'stripe': [],
        'airbnb': [],
        'openai': [],
        'figma': []
    }

    for startup in startups_features:
        for unicorn_name, unicorn_pattern in UNICORN_PATTERNS.items():
            similarity = calculate_similarity_score(startup, unicorn_pattern)

            if similarity >= 50:  # At least 50% match
                results[unicorn_name].append({
                    **startup,
                    'similarity_score': similarity
                })

    # Sort by similarity score
    for unicorn_name in results:
        results[unicorn_name].sort(key=lambda x: -x['similarity_score'])

    return results

# ============================================================================
# CLUSTERING ANALYSIS
# ============================================================================

def cluster_startups(startups_features):
    """
    Use K-Means clustering to group similar startups
    """
    if len(startups_features) < 5:
        return None

    # Prepare features for clustering
    features_for_clustering = []
    companies = []

    for startup in startups_features:
        features_for_clustering.append([
            startup['total_funding'],
            startup['deals_count'],
            startup['avg_deal_size'],
            startup['days_active']
        ])
        companies.append(startup['company_name'])

    # Normalize
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features_for_clustering)

    # K-Means (3-5 clusters)
    n_clusters = min(5, max(3, len(startups_features) // 10))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features_scaled)

    # Group by cluster
    clusters = defaultdict(list)

    for i, label in enumerate(labels):
        clusters[label].append(startups_features[i])

    return clusters

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(conn):
    report = []

    report.append("=" * 80)
    report.append("STARTUP PATTERN MATCHING - Find Next Unicorns")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Extract features
    startups = extract_startup_features(conn)

    report.append(f"Total startups analyzed: {len(startups)}")
    report.append("")

    # Find similar to unicorns
    similar_to_unicorns = find_similar_startups(startups)

    # 1. Stripe-like startups
    report.append("=" * 80)
    report.append("💳 STARTUPS SIMILAR TO STRIPE (Early Stage 2015)")
    report.append("=" * 80)
    report.append("")

    if similar_to_unicorns['stripe']:
        report.append("🎯 HIGH POTENTIAL MATCHES:")
        for startup in similar_to_unicorns['stripe'][:10]:
            report.append(f"• {startup['company_name']}")
            report.append(f"  Sector: {startup['sector']}")
            report.append(f"  Funding: ${startup['total_funding']/1e6:.1f}M ({startup['deals_count']} deals)")
            report.append(f"  Similarity: {startup['similarity_score']:.0f}%")
            report.append("")
    else:
        report.append("(No Stripe-like patterns detected)")
        report.append("")

    # 2. Airbnb-like startups
    report.append("=" * 80)
    report.append("🏠 STARTUPS SIMILAR TO AIRBNB (Early Stage 2013)")
    report.append("=" * 80)
    report.append("")

    if similar_to_unicorns['airbnb']:
        report.append("🎯 HIGH POTENTIAL MATCHES:")
        for startup in similar_to_unicorns['airbnb'][:10]:
            report.append(f"• {startup['company_name']}")
            report.append(f"  Sector: {startup['sector']}")
            report.append(f"  Funding: ${startup['total_funding']/1e6:.1f}M ({startup['deals_count']} deals)")
            report.append(f"  Similarity: {startup['similarity_score']:.0f}%")
            report.append("")
    else:
        report.append("(No Airbnb-like patterns detected)")
        report.append("")

    # 3. OpenAI-like startups
    report.append("=" * 80)
    report.append("🤖 STARTUPS SIMILAR TO OPENAI (Early Stage 2020)")
    report.append("=" * 80)
    report.append("")

    if similar_to_unicorns['openai']:
        report.append("🎯 HIGH POTENTIAL MATCHES:")
        for startup in similar_to_unicorns['openai'][:10]:
            report.append(f"• {startup['company_name']}")
            report.append(f"  Sector: {startup['sector']}")
            report.append(f"  Funding: ${startup['total_funding']/1e6:.1f}M ({startup['deals_count']} deals)")
            report.append(f"  Similarity: {startup['similarity_score']:.0f}%")
            report.append("")
    else:
        report.append("(No OpenAI-like patterns detected)")
        report.append("")

    # 4. Figma-like startups
    report.append("=" * 80)
    report.append("🎨 STARTUPS SIMILAR TO FIGMA (Early Stage 2017)")
    report.append("=" * 80)
    report.append("")

    if similar_to_unicorns['figma']:
        report.append("🎯 HIGH POTENTIAL MATCHES:")
        for startup in similar_to_unicorns['figma'][:10]:
            report.append(f"• {startup['company_name']}")
            report.append(f"  Sector: {startup['sector']}")
            report.append(f"  Funding: ${startup['total_funding']/1e6:.1f}M ({startup['deals_count']} deals)")
            report.append(f"  Similarity: {startup['similarity_score']:.0f}%")
            report.append("")
    else:
        report.append("(No Figma-like patterns detected)")
        report.append("")

    # 5. Clustering Analysis
    report.append("=" * 80)
    report.append("🔬 CLUSTERING ANALYSIS (K-Means)")
    report.append("=" * 80)
    report.append("")

    clusters = cluster_startups(startups)

    if clusters:
        report.append("Startups grouped by similarity:")
        report.append("")

        for cluster_id, startups_in_cluster in clusters.items():
            # Calculate cluster characteristics
            avg_funding = np.mean([s['total_funding'] for s in startups_in_cluster])
            avg_deals = np.mean([s['deals_count'] for s in startups_in_cluster])

            # Cluster label
            if avg_funding > 1e9:
                cluster_label = "UNICORN TRAJECTORY"
            elif avg_funding > 100e6:
                cluster_label = "HIGH GROWTH"
            elif avg_funding > 10e6:
                cluster_label = "EARLY STAGE"
            else:
                cluster_label = "SEED/PRE-SEED"

            report.append(f"📊 Cluster {cluster_id + 1}: {cluster_label}")
            report.append(f"   Companies: {len(startups_in_cluster)}")
            report.append(f"   Avg funding: ${avg_funding/1e6:.1f}M")
            report.append(f"   Avg deals: {avg_deals:.1f}")
            report.append("")

            # Top startups in cluster
            for startup in sorted(startups_in_cluster, key=lambda x: -x['total_funding'])[:3]:
                report.append(f"   • {startup['company_name']}: ${startup['total_funding']/1e6:.1f}M")

            report.append("")
    else:
        report.append("(Insufficient data for clustering)")
        report.append("")

    # Summary
    report.append("=" * 80)
    report.append("🎯 INVESTMENT RECOMMENDATIONS")
    report.append("=" * 80)
    report.append("")

    # Combine all high-potential startups
    all_matches = []
    for unicorn_name, matches in similar_to_unicorns.items():
        for match in matches[:3]:  # Top 3 from each pattern
            all_matches.append({
                **match,
                'pattern': unicorn_name
            })

    # Sort by similarity score
    all_matches.sort(key=lambda x: -x['similarity_score'])

    if all_matches:
        report.append("TOP 10 STARTUPS WITH UNICORN POTENTIAL:")
        report.append("")

        for i, startup in enumerate(all_matches[:10], 1):
            report.append(f"{i}. {startup['company_name']}")
            report.append(f"   Pattern: Similar to {startup['pattern'].upper()}")
            report.append(f"   Match: {startup['similarity_score']:.0f}%")
            report.append(f"   Funding: ${startup['total_funding']/1e6:.1f}M")
            report.append(f"   Sector: {startup['sector']}")
            report.append("")

    report.append("=" * 80)
    report.append("✅ Startup Pattern Matching Complete!")
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
        with open('analytics/startup-pattern-matching.txt', 'w') as f:
            f.write(report)

        print("💾 Saved to: analytics/startup-pattern-matching.txt")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
