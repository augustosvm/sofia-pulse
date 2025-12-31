#!/usr/bin/env python3
"""
SENTIMENT ANALYSIS REPORT

Analyzes sentiment across:
1. Research Papers (ArXiv) - Hype vs Substance
2. HackerNews Stories - Community sentiment
3. Reddit Tech Posts - Developer sentiment

Detects:
- Overhyped technologies (many "breakthrough" claims)
- Genuine innovation (substantive language)
- Community enthusiasm vs skepticism
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from collections import Counter, defaultdict
import re
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
# SENTIMENT LEXICONS
# ============================================================================

HYPE_WORDS = [
    'breakthrough', 'revolutionary', 'game-changing', 'unprecedented',
    'paradigm shift', 'disrupting', 'transformative', 'groundbreaking',
    'cutting-edge', 'state-of-the-art', 'novel', 'innovative',
    'first-ever', 'never before', 'game changer'
]

SUBSTANCE_WORDS = [
    'empirical', 'evaluation', 'benchmark', 'dataset', 'reproducible',
    'ablation', 'baseline', 'validation', 'experiment', 'methodology',
    'quantitative', 'qualitative', 'statistical', 'rigorous'
]

POSITIVE_WORDS = [
    'excellent', 'amazing', 'great', 'awesome', 'fantastic',
    'impressive', 'outstanding', 'brilliant', 'perfect', 'love',
    'best', 'wonderful', 'superb', 'incredible'
]

NEGATIVE_WORDS = [
    'terrible', 'awful', 'bad', 'poor', 'disappointing',
    'horrible', 'useless', 'broken', 'buggy', 'slow',
    'worst', 'hate', 'annoying', 'frustrating', 'complicated'
]

SKEPTICAL_WORDS = [
    'overhyped', 'overrated', 'buzzword', 'not worth', 'waste of time',
    'nothing new', 'just hype', 'too complex', 'not practical',
    'theoretical only', 'not ready', 'premature'
]

# ============================================================================
# SENTIMENT ANALYSIS FUNCTIONS
# ============================================================================

def calculate_sentiment_score(text):
    """
    Calculate sentiment score (-1 to +1)

    Returns:
    - score: -1 (very negative) to +1 (very positive)
    - classification: 'positive', 'negative', 'neutral'
    """
    if not text:
        return 0, 'neutral'

    text_lower = text.lower()

    # Count positive/negative words
    positive_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
    skeptical_count = sum(1 for phrase in SKEPTICAL_WORDS if phrase in text_lower)

    # Skepticism counts as negative
    negative_count += skeptical_count

    # Calculate score
    total = positive_count + negative_count
    if total == 0:
        return 0, 'neutral'

    score = (positive_count - negative_count) / total

    if score > 0.3:
        classification = 'positive'
    elif score < -0.3:
        classification = 'negative'
    else:
        classification = 'neutral'

    return score, classification

def calculate_hype_ratio(text):
    """
    Calculate hype vs substance ratio for research papers

    Returns:
    - hype_score: 0-1 (0 = all substance, 1 = all hype)
    - classification: 'hype', 'substance', 'balanced'
    """
    if not text:
        return 0.5, 'balanced'

    text_lower = text.lower()

    hype_count = sum(1 for word in HYPE_WORDS if word in text_lower)
    substance_count = sum(1 for word in SUBSTANCE_WORDS if word in text_lower)

    total = hype_count + substance_count
    if total == 0:
        return 0.5, 'balanced'

    hype_ratio = hype_count / total

    if hype_ratio > 0.7:
        classification = 'hype'
    elif hype_ratio < 0.3:
        classification = 'substance'
    else:
        classification = 'balanced'

    return hype_ratio, classification

# ============================================================================
# PAPER SENTIMENT ANALYSIS
# ============================================================================

def analyze_paper_sentiment(conn):
    """Analyze ArXiv papers - Hype vs Substance"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # ArXiv AI papers
    cur.execute("""
        SELECT title, abstract, keywords
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '90 days'
        LIMIT 200
    """)

    papers = cur.fetchall()

    hype_papers = []
    substance_papers = []
    balanced_papers = []

    for paper in papers:
        text = f"{paper['title']} {paper['abstract']}"
        hype_ratio, classification = calculate_hype_ratio(text)

        paper_data = {
            'title': paper['title'],
            'hype_ratio': hype_ratio,
            'keywords': paper.get('keywords', [])[:3] if paper.get('keywords') else []
        }

        if classification == 'hype':
            hype_papers.append(paper_data)
        elif classification == 'substance':
            substance_papers.append(paper_data)
        else:
            balanced_papers.append(paper_data)

    return {
        'total': len(papers),
        'hype': len(hype_papers),
        'substance': len(substance_papers),
        'balanced': len(balanced_papers),
        'hype_examples': hype_papers[:5],
        'substance_examples': substance_papers[:5]
    }

# ============================================================================
# HACKERNEWS SENTIMENT
# ============================================================================

def analyze_hackernews_sentiment(conn):
    """Analyze HackerNews stories sentiment"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT title, url, points as score, num_comments as comments
        FROM sofia.hackernews_stories
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY points DESC
        LIMIT 100
    """)

    stories = cur.fetchall()

    sentiments = defaultdict(list)

    for story in stories:
        score, classification = calculate_sentiment_score(story['title'])

        sentiments[classification].append({
            'title': story['title'],
            'score': story['score'],
            'comments': story['comments'],
            'sentiment_score': score
        })

    return {
        'total': len(stories),
        'positive': len(sentiments['positive']),
        'negative': len(sentiments['negative']),
        'neutral': len(sentiments['neutral']),
        'top_positive': sorted(sentiments['positive'], key=lambda x: -x['score'])[:5],
        'top_negative': sorted(sentiments['negative'], key=lambda x: -x['score'])[:5]
    }

# ============================================================================
# REDDIT SENTIMENT (if available)
# ============================================================================

def analyze_reddit_sentiment(conn):
    """Analyze Reddit tech posts sentiment"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("""
            SELECT title, selftext, score, num_comments
            FROM sofia.reddit_tech_posts
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY score DESC
            LIMIT 100
        """)

        posts = cur.fetchall()

        if not posts:
            return None

        sentiments = defaultdict(list)

        for post in posts:
            text = f"{post['title']} {post.get('selftext', '')}"
            score, classification = calculate_sentiment_score(text)

            sentiments[classification].append({
                'title': post['title'],
                'score': post['score'],
                'comments': post['num_comments'],
                'sentiment_score': score
            })

        return {
            'total': len(posts),
            'positive': len(sentiments['positive']),
            'negative': len(sentiments['negative']),
            'neutral': len(sentiments['neutral']),
            'top_positive': sorted(sentiments['positive'], key=lambda x: -x['score'])[:3],
            'top_negative': sorted(sentiments['negative'], key=lambda x: -x['score'])[:3]
        }

    except Exception as e:
        return None

# ============================================================================
# TECH TOPIC SENTIMENT
# ============================================================================

def analyze_topic_sentiment(conn):
    """Analyze sentiment by tech topic"""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get papers by topic
    cur.execute("""
        SELECT
            UNNEST(keywords) as topic,
            title,
            abstract
        FROM sofia.arxiv_ai_papers
        WHERE published_date >= CURRENT_DATE - INTERVAL '90 days'
            AND keywords IS NOT NULL
    """)

    papers = cur.fetchall()

    topic_sentiment = defaultdict(list)

    for paper in papers:
        topic = paper['topic']
        text = f"{paper['title']} {paper['abstract']}"
        hype_ratio, _ = calculate_hype_ratio(text)

        topic_sentiment[topic].append(hype_ratio)

    # Calculate average hype ratio per topic
    topic_scores = []
    for topic, ratios in topic_sentiment.items():
        if len(ratios) >= 3:  # At least 3 papers
            avg_hype = sum(ratios) / len(ratios)
            topic_scores.append({
                'topic': topic,
                'avg_hype': avg_hype,
                'paper_count': len(ratios)
            })

    # Sort by hype ratio
    topic_scores.sort(key=lambda x: -x['avg_hype'])

    return {
        'most_hyped': topic_scores[:10],
        'least_hyped': topic_scores[-10:]
    }

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(conn):
    report = []

    report.append("=" * 80)
    report.append("SENTIMENT ANALYSIS REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # 1. Papers - Hype vs Substance
    report.append("=" * 80)
    report.append("📄 RESEARCH PAPERS - HYPE vs SUBSTANCE")
    report.append("=" * 80)
    report.append("")

    paper_sentiment = analyze_paper_sentiment(conn)

    report.append(f"Total papers analyzed: {paper_sentiment['total']}")
    report.append(f"  • HYPE: {paper_sentiment['hype']} ({paper_sentiment['hype']/paper_sentiment['total']*100:.1f}%)")
    report.append(f"  • SUBSTANCE: {paper_sentiment['substance']} ({paper_sentiment['substance']/paper_sentiment['total']*100:.1f}%)")
    report.append(f"  • BALANCED: {paper_sentiment['balanced']} ({paper_sentiment['balanced']/paper_sentiment['total']*100:.1f}%)")
    report.append("")

    report.append("🚨 MOST HYPED PAPERS:")
    for paper in paper_sentiment['hype_examples']:
        report.append(f"  • {paper['title'][:70]}...")
        report.append(f"    Hype ratio: {paper['hype_ratio']:.2f}")
        report.append("")

    report.append("✅ MOST SUBSTANTIVE PAPERS:")
    for paper in paper_sentiment['substance_examples']:
        report.append(f"  • {paper['title'][:70]}...")
        report.append(f"    Substance ratio: {1-paper['hype_ratio']:.2f}")
        report.append("")

    # 2. HackerNews Sentiment
    report.append("=" * 80)
    report.append("🗞️ HACKERNEWS SENTIMENT")
    report.append("=" * 80)
    report.append("")

    hn_sentiment = analyze_hackernews_sentiment(conn)

    report.append(f"Total stories analyzed: {hn_sentiment['total']}")
    report.append(f"  • POSITIVE: {hn_sentiment['positive']} ({hn_sentiment['positive']/hn_sentiment['total']*100:.1f}%)")
    report.append(f"  • NEGATIVE: {hn_sentiment['negative']} ({hn_sentiment['negative']/hn_sentiment['total']*100:.1f}%)")
    report.append(f"  • NEUTRAL: {hn_sentiment['neutral']} ({hn_sentiment['neutral']/hn_sentiment['total']*100:.1f}%)")
    report.append("")

    if hn_sentiment['top_positive']:
        report.append("👍 TOP POSITIVE STORIES:")
        for story in hn_sentiment['top_positive']:
            report.append(f"  • {story['title'][:70]}...")
            report.append(f"    Score: {story['score']}, Comments: {story['comments']}")
            report.append("")

    # 3. Reddit Sentiment
    reddit_sentiment = analyze_reddit_sentiment(conn)

    if reddit_sentiment:
        report.append("=" * 80)
        report.append("💬 REDDIT TECH SENTIMENT")
        report.append("=" * 80)
        report.append("")

        report.append(f"Total posts analyzed: {reddit_sentiment['total']}")
        report.append(f"  • POSITIVE: {reddit_sentiment['positive']} ({reddit_sentiment['positive']/reddit_sentiment['total']*100:.1f}%)")
        report.append(f"  • NEGATIVE: {reddit_sentiment['negative']} ({reddit_sentiment['negative']/reddit_sentiment['total']*100:.1f}%)")
        report.append(f"  • NEUTRAL: {reddit_sentiment['neutral']} ({reddit_sentiment['neutral']/reddit_sentiment['total']*100:.1f}%)")
        report.append("")

    # 4. Topic Sentiment
    report.append("=" * 80)
    report.append("🏷️ SENTIMENT BY TECH TOPIC")
    report.append("=" * 80)
    report.append("")

    topic_sentiment = analyze_topic_sentiment(conn)

    report.append("🚨 MOST HYPED TOPICS:")
    for topic in topic_sentiment['most_hyped'][:5]:
        report.append(f"  • {topic['topic']}: {topic['avg_hype']:.2f} hype ratio ({topic['paper_count']} papers)")

    report.append("")
    report.append("✅ LEAST HYPED (Most Substantive):")
    for topic in topic_sentiment['least_hyped'][:5]:
        report.append(f"  • {topic['topic']}: {topic['avg_hype']:.2f} hype ratio ({topic['paper_count']} papers)")

    report.append("")
    report.append("=" * 80)
    report.append("✅ Sentiment Analysis Complete!")
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
        with open('analytics/sentiment-analysis.txt', 'w') as f:
            f.write(report)

        print("💾 Saved to: analytics/sentiment-analysis.txt")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
