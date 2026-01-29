#!/usr/bin/env python3
"""
Sofia Pulse Cross Signals Builder v1

Generates outputs/cross_signals.json from PostgreSQL sources.
Safe plug-in design: does not modify existing email/site infrastructure.

Usage:
    python build-cross-signals.py [--window-days 7] [--dry-run]
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === Configuration ===

DB_CONFIG = {
    'host': os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', 'localhost')),
    'port': int(os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432'))),
    'dbname': os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'sofia_db')),
    'user': os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'sofia')),
    'password': os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', '')),
}

OUTPUT_FILE = Path(__file__).parent.parent / 'outputs' / 'cross_signals.json'
SCHEMA_VERSION = '1.0.0'

# Source thresholds for confidence scoring
MIN_SOURCES_FOR_INSIGHT = 2
MIN_SOURCES_FOR_HIGH_CONFIDENCE = 4
MIN_SOURCES_FOR_MEDIUM_CONFIDENCE = 2

# === Database Connection ===

def get_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# === Source Availability Detection ===

def detect_source_availability(conn, window_start: datetime, window_end: datetime) -> List[Dict]:
    """
    Detect which sources are available and their coverage.
    Returns sources[] array for cross_signals.json
    """
    sources = []

    with conn.cursor() as cur:
        # GA4 (analytics_events) - event_timestamp is bigint (microseconds)
        window_start_micros = int(window_start.timestamp() * 1_000_000)
        window_end_micros = int(window_end.timestamp() * 1_000_000)

        cur.execute("""
            SELECT
                COUNT(*) as records,
                MIN(event_timestamp) as min_date,
                MAX(event_timestamp) as max_date
            FROM sofia.analytics_events
            WHERE event_timestamp >= %s AND event_timestamp < %s
        """, (window_start_micros, window_end_micros))
        ga4 = cur.fetchone()

        # Convert bigint microseconds back to datetime for ISO format
        ga4_max_date = None
        ga4_min_date = None
        coverage_days = 0
        if ga4['max_date']:
            ga4_max_date = datetime.fromtimestamp(ga4['max_date'] / 1_000_000, tz=timezone.utc)
            ga4_min_date = datetime.fromtimestamp(ga4['min_date'] / 1_000_000, tz=timezone.utc)
            coverage_days = (ga4_max_date - ga4_min_date).days

        sources.append({
            'source_id': 'ga4',
            'status': 'ok' if ga4['records'] > 0 else 'offline',
            'last_updated_at': ga4_max_date.isoformat() if ga4_max_date else None,
            'coverage_days': coverage_days,
            'records_count': ga4['records'],
            'notes': '' if ga4['records'] > 0 else 'No analytics events in window'
        })

        # VSCode Marketplace
        cur.execute("""
            SELECT
                COUNT(*) as records,
                MIN(snapshot_date) as min_date,
                MAX(snapshot_date) as max_date
            FROM sofia.vscode_extensions_daily
            WHERE snapshot_date >= %s::DATE AND snapshot_date < %s::DATE
        """, (window_start, window_end))
        vscode = cur.fetchone()
        sources.append({
            'source_id': 'vscode_marketplace',
            'status': 'ok' if vscode['records'] > 100 else ('partial' if vscode['records'] > 0 else 'offline'),
            'last_updated_at': vscode['max_date'].isoformat() if vscode['max_date'] else None,
            'coverage_days': (vscode['max_date'] - vscode['min_date']).days if vscode['max_date'] else 0,
            'records_count': vscode['records'],
            'notes': 'Full extension data available' if vscode['records'] > 100 else ''
        })

        # GitHub Trending
        cur.execute("""
            SELECT
                COUNT(*) as records,
                MIN(collected_at) as min_date,
                MAX(collected_at) as max_date
            FROM sofia.github_trending
            WHERE collected_at >= %s AND collected_at < %s
        """, (window_start, window_end))
        github = cur.fetchone()
        sources.append({
            'source_id': 'github_trending',
            'status': 'ok' if github['records'] > 50 else ('partial' if github['records'] > 0 else 'offline'),
            'last_updated_at': github['max_date'].isoformat() if github['max_date'] else None,
            'coverage_days': (github['max_date'] - github['min_date']).days if github['max_date'] else 0,
            'records_count': github['records'],
            'notes': ''
        })

        # Patents (check existence, not date range since it's cumulative)
        try:
            cur.execute("SELECT COUNT(*) as records FROM sofia.patents LIMIT 1")
            patents = cur.fetchone()
            sources.append({
                'source_id': 'patents',
                'status': 'ok',
                'last_updated_at': None,
                'coverage_days': None,
                'records_count': None,  # Too large to count
                'notes': 'Patents data available (aggregated queries only)'
            })
        except psycopg2.ProgrammingError:
            sources.append({
                'source_id': 'patents',
                'status': 'missing',
                'last_updated_at': None,
                'coverage_days': 0,
                'records_count': 0,
                'notes': 'Patents table not found'
            })
            conn.rollback()

        # ArXiv Papers
        cur.execute("""
            SELECT
                COUNT(*) as records,
                MIN(published_date) as min_date,
                MAX(published_date) as max_date
            FROM sofia.arxiv_ai_papers
            WHERE published_date >= %s::DATE AND published_date < %s::DATE
        """, (window_start, window_end))
        arxiv = cur.fetchone()
        sources.append({
            'source_id': 'arxiv',
            'status': 'ok' if arxiv['records'] > 10 else ('partial' if arxiv['records'] > 0 else 'offline'),
            'last_updated_at': arxiv['max_date'].isoformat() if arxiv['max_date'] else None,
            'coverage_days': (arxiv['max_date'] - arxiv['min_date']).days if arxiv['max_date'] else 0,
            'records_count': arxiv['records'],
            'notes': ''
        })

        # HackerNews (news_items)
        cur.execute("""
            SELECT
                COUNT(*) as records,
                MIN(published_at) as min_date,
                MAX(published_at) as max_date
            FROM sofia.news_items
            WHERE source = 'hackernews'
              AND published_at >= %s AND published_at < %s
        """, (window_start, window_end))
        hn = cur.fetchone()
        sources.append({
            'source_id': 'hackernews',
            'status': 'ok' if hn['records'] > 20 else ('partial' if hn['records'] > 0 else 'offline'),
            'last_updated_at': hn['max_date'].isoformat() if hn['max_date'] else None,
            'coverage_days': (hn['max_date'] - hn['min_date']).days if hn['max_date'] else 0,
            'records_count': hn['records'],
            'notes': ''
        })

        # Chat Sessions (optional)
        try:
            cur.execute("""
                SELECT COUNT(*) as records
                FROM sofia.ga4_chat_sessions
                WHERE session_start >= %s AND session_start < %s
            """, (window_start, window_end))
            chat = cur.fetchone()
            sources.append({
                'source_id': 'chat_sessions',
                'status': 'ok' if chat['records'] > 0 else 'offline',
                'last_updated_at': None,
                'coverage_days': None,
                'records_count': chat['records'],
                'notes': ''
            })
        except psycopg2.ProgrammingError:
            sources.append({
                'source_id': 'chat_sessions',
                'status': 'missing',
                'last_updated_at': None,
                'coverage_days': 0,
                'records_count': 0,
                'notes': 'Table ga4_chat_sessions not found'
            })
            conn.rollback()

        # Funding Rounds
        cur.execute("""
            SELECT
                COUNT(*) as records,
                MIN(announced_date) as min_date,
                MAX(announced_date) as max_date
            FROM sofia.funding_rounds
            WHERE announced_date >= %s::DATE AND announced_date < %s::DATE
        """, (window_start, window_end))
        funding = cur.fetchone()
        sources.append({
            'source_id': 'funding_rounds',
            'status': 'ok' if funding['records'] > 5 else ('partial' if funding['records'] > 0 else 'offline'),
            'last_updated_at': funding['max_date'].isoformat() if funding['max_date'] else None,
            'coverage_days': (funding['max_date'] - funding['min_date']).days if funding['max_date'] else 0,
            'records_count': funding['records'],
            'notes': ''
        })

    return sources

# === Candidate Event Detection ===

def detect_candidate_events(conn, window_start: datetime, window_end: datetime) -> List[Dict]:
    """
    Detect candidate events from high-impact news, security incidents, releases.
    Returns list of event candidates with entities extracted.
    """
    events = []

    with conn.cursor() as cur:
        # High-impact news items (HackerNews + others)
        cur.execute("""
            SELECT
                id,
                source,
                external_id,
                title,
                url,
                published_at,
                score,
                comment_count,
                rank,
                extracted_entities,
                extracted_topics
            FROM sofia.news_items_high_impact
            ORDER BY impact_score DESC
            LIMIT 50
        """)

        for row in cur.fetchall():
            events.append({
                'event_type': 'news',
                'headline': row['title'],
                'summary': row['title'],  # TODO: Generate better summary
                'happened_at': row['published_at'].isoformat(),
                'entities': row['extracted_entities'] or {},
                'source_refs': [
                    {
                        'ref_type': 'url',
                        'ref_id': row['url'] or f"{row['source']}:{row['external_id']}",
                        'title': row['title']
                    }
                ],
                'topics': row['extracted_topics'] or [],
                'source': row['source'],
                'external_id': row['external_id']
            })

    return events

# === Reaction Detection ===

def detect_reactions_for_event(conn, event: Dict, window_start: datetime, window_end: datetime) -> List[Dict]:
    """
    For a given event, detect correlated reactions from multiple sources.
    Returns list of reactions (each with source_id, signal_type, metric_name, value, etc)
    """
    reactions = []
    topics = event.get('topics', [])
    entities = event.get('entities', {})

    if not topics:
        return reactions  # No topics to match

    with conn.cursor() as cur:
        # VSCode Marketplace reaction (installs spike for related extensions)
        if topics:
            cur.execute("""
                SELECT
                    extension_id,
                    display_name,
                    installs_current,
                    installs_7d_ago,
                    installs_delta_7d,
                    installs_delta_pct_7d,
                    tags
                FROM sofia.vscode_extensions_7d_deltas
                WHERE tags && %s::TEXT[]  -- Overlap with event topics
                  AND installs_delta_7d > 1000  -- Significant increase
                ORDER BY installs_delta_7d DESC
                LIMIT 3
            """, (topics,))

            for row in cur.fetchall():
                reactions.append({
                    'source_id': 'vscode_marketplace',
                    'signal_type': 'adoption',
                    'metric_name': f"{row['extension_id']}_installs",
                    'value': row['installs_current'],
                    'delta': row['installs_delta_7d'],
                    'delta_pct': float(row['installs_delta_pct_7d']) if row['installs_delta_pct_7d'] else None,
                    'window_days': 7,
                    'direction': 'up',
                    'evidence': [
                        {
                            'ref_type': 'internal_id',
                            'ref_id': row['extension_id']
                        }
                    ],
                    'confidence': 0.85
                })

        # GitHub activity reaction (stars, commits for related repos)
        if topics:
            cur.execute("""
                SELECT
                    full_name,
                    stars,
                    language,
                    description,
                    collected_at
                FROM sofia.github_trending
                WHERE collected_at >= %s AND collected_at < %s
                  AND (
                    full_name ILIKE ANY(%s::TEXT[])
                    OR description ILIKE ANY(%s::TEXT[])
                    OR language ILIKE ANY(%s::TEXT[])
                  )
                ORDER BY stars DESC
                LIMIT 3
            """, (
                window_start,
                window_end,
                ['%' + topic + '%' for topic in topics[:5]],
                ['%' + topic + '%' for topic in topics[:5]],
                topics[:5]  # Language exact match
            ))

            for row in cur.fetchall():
                reactions.append({
                    'source_id': 'github_trending',
                    'signal_type': 'activity',
                    'metric_name': f"{row['full_name']}_stars",
                    'value': row['stars'],
                    'window_days': 7,
                    'direction': 'up',
                    'evidence': [
                        {
                            'ref_type': 'github_repo',
                            'ref_id': row['full_name']
                        }
                    ],
                    'confidence': 0.80
                })

        # ArXiv papers reaction (papers mentioning same topics)
        if topics:
            cur.execute("""
                SELECT COUNT(*) as paper_count
                FROM sofia.arxiv_ai_papers
                WHERE published_date >= %s::DATE AND published_date < %s::DATE
                  AND (
                    title ILIKE ANY(%s::TEXT[])
                    OR abstract ILIKE ANY(%s::TEXT[])
                  )
            """, (
                window_start,
                window_end,
                ['%' + topic + '%' for topic in topics[:5]],  # Limit to top 5 topics
                ['%' + topic + '%' for topic in topics[:5]]
            ))
            paper_row = cur.fetchone()
            if paper_row and paper_row['paper_count'] > 2:
                reactions.append({
                    'source_id': 'arxiv',
                    'signal_type': 'research',
                    'metric_name': 'papers_mentioning_topics',
                    'value': paper_row['paper_count'],
                    'window_days': 7,
                    'direction': 'up',
                    'confidence': 0.70
                })

        # Funding rounds reaction (funding for related companies/sectors)
        if topics or entities:
            # Build search terms from entities (companies) and topics
            search_terms = []
            if isinstance(entities, dict):
                search_terms.extend(entities.get('companies', []))
                search_terms.extend(entities.get('technologies', []))
            search_terms.extend(topics[:5])

            if search_terms:
                cur.execute("""
                    SELECT
                        o.name as organization_name,
                        fr.amount_usd,
                        fr.round_type,
                        fr.announced_date,
                        fr.investor_names
                    FROM sofia.funding_rounds fr
                    LEFT JOIN sofia.organizations o ON fr.organization_id = o.id
                    WHERE fr.announced_date >= %s::DATE AND fr.announced_date < %s::DATE
                      AND (
                        o.name ILIKE ANY(%s::TEXT[])
                        OR fr.description ILIKE ANY(%s::TEXT[])
                      )
                    ORDER BY fr.amount_usd DESC NULLS LAST
                    LIMIT 3
                """, (
                    window_start,
                    window_end,
                    ['%' + term + '%' for term in search_terms if term],
                    ['%' + term + '%' for term in search_terms if term]
                ))

                for row in cur.fetchall():
                    reactions.append({
                        'source_id': 'funding_rounds',
                        'signal_type': 'market',
                        'metric_name': f"{row['organization_name']}_funding",
                        'value': row['amount_usd'] or 0,
                        'window_days': 7,
                        'direction': 'up',
                        'evidence': [
                            {
                                'ref_type': 'internal_id',
                                'ref_id': f"funding_{row['announced_date']}"
                            }
                        ],
                        'confidence': 0.75
                    })

    return reactions

# === Classification Helpers ===

def classify_domain(topics: List[str], entities: Dict) -> str:
    """
    Classify domain based on topics and entities.
    Returns one of: TECH, JOBS, SECURITY, SPACE, AI, DEVTOOLS, PATENTS, HEALTH, FINANCE, RESEARCH, POLICY, SOCIAL
    """
    topics_lower = [t.lower() for t in topics]

    # Security keywords
    if any(kw in topics_lower for kw in ['security', 'vulnerability', 'cve', 'breach', 'exploit', 'malware', 'ransomware', 'cybersecurity']):
        return 'SECURITY'

    # AI keywords
    if any(kw in topics_lower for kw in ['ai', 'ml', 'machine-learning', 'deep-learning', 'llm', 'gpt', 'neural', 'transformer']):
        return 'AI'

    # DevTools keywords
    if any(kw in topics_lower for kw in ['vscode', 'ide', 'debugger', 'compiler', 'framework', 'library', 'sdk', 'api']):
        return 'DEVTOOLS'

    # Space keywords
    if any(kw in topics_lower for kw in ['space', 'satellite', 'rocket', 'spacex', 'nasa', 'orbit', 'launch']):
        return 'SPACE'

    # Jobs keywords
    if any(kw in topics_lower for kw in ['hiring', 'jobs', 'career', 'salary', 'recruitment', 'layoff', 'remote-work']):
        return 'JOBS'

    # Health keywords
    if any(kw in topics_lower for kw in ['health', 'medical', 'pharma', 'biotech', 'disease', 'vaccine', 'clinical']):
        return 'HEALTH'

    # Finance keywords
    if any(kw in topics_lower for kw in ['finance', 'banking', 'fintech', 'crypto', 'blockchain', 'trading', 'investment']):
        return 'FINANCE'

    # Research keywords
    if any(kw in topics_lower for kw in ['research', 'paper', 'study', 'arxiv', 'science', 'academic', 'university']):
        return 'RESEARCH'

    # Policy keywords
    if any(kw in topics_lower for kw in ['policy', 'regulation', 'law', 'government', 'legislation', 'compliance', 'gdpr']):
        return 'POLICY'

    # Patents keywords
    if any(kw in topics_lower for kw in ['patent', 'intellectual-property', 'trademark', 'copyright']):
        return 'PATENTS'

    # Default to TECH
    return 'TECH'

def extract_regions(entities: Dict) -> List[str]:
    """
    Extract ISO country codes from entities.
    Returns list of 2-letter country codes or ['GLOBAL'] if no specific countries found.
    """
    if not isinstance(entities, dict):
        return ['GLOBAL']

    countries = entities.get('countries', [])
    if not countries:
        return ['GLOBAL']

    # Map country names to ISO codes (simplified)
    country_map = {
        'united states': 'US', 'usa': 'US', 'us': 'US',
        'brazil': 'BR', 'brasil': 'BR',
        'united kingdom': 'GB', 'uk': 'GB',
        'germany': 'DE', 'deutschland': 'DE',
        'france': 'FR',
        'china': 'CN',
        'india': 'IN',
        'japan': 'JP',
        'canada': 'CA',
        'australia': 'AU',
        'russia': 'RU',
        'south korea': 'KR',
        'mexico': 'MX',
        'spain': 'ES',
        'italy': 'IT',
        'netherlands': 'NL',
        'sweden': 'SE',
        'switzerland': 'CH',
        'singapore': 'SG',
        'israel': 'IL',
    }

    regions = []
    for country in countries[:10]:  # Max 10 countries
        country_lower = country.lower().strip()
        if country_lower in country_map:
            regions.append(country_map[country_lower])
        elif len(country) == 2 and country.isupper():
            regions.append(country)  # Already ISO code

    return regions if regions else ['GLOBAL']

def convert_entities_to_schema(entities: Dict) -> List[Dict]:
    """
    Convert extracted_entities JSONB to schema format.
    Input: {companies: [...], technologies: [...], people: [...], countries: [...]}
    Output: [{type: 'company', name: '...'}, ...]
    """
    if not isinstance(entities, dict):
        return []

    schema_entities = []

    # Companies
    for company in entities.get('companies', [])[:10]:
        schema_entities.append({
            'type': 'company',
            'name': company
        })

    # Technologies
    for tech in entities.get('technologies', [])[:10]:
        schema_entities.append({
            'type': 'technology',
            'name': tech
        })

    # People
    for person in entities.get('people', [])[:5]:
        schema_entities.append({
            'type': 'person',
            'name': person
        })

    # Countries
    for country in entities.get('countries', [])[:5]:
        schema_entities.append({
            'type': 'country',
            'name': country
        })

    # Frameworks (if exists)
    for framework in entities.get('frameworks', [])[:5]:
        schema_entities.append({
            'type': 'framework',
            'name': framework
        })

    return schema_entities[:20]  # Max 20 per schema

# === Confidence Scoring ===

def calculate_confidence(reactions: List[Dict], data_quality_flags: Dict) -> str:
    """
    Calculate confidence level (LOW/MEDIUM/HIGH) based on:
    - Number of independent reactions
    - Hard signals vs soft signals
    - Data quality flags
    """
    reaction_count = len(reactions)

    # Count hard signals (VSCode, GitHub, Patents, Funding)
    hard_signals = sum(1 for r in reactions if r['source_id'] in [
        'vscode_marketplace', 'github_trending', 'patents', 'funding_rounds'
    ])

    # Baseline confidence
    if reaction_count < 2:
        return 'LOW'  # Should not happen for insights (enforced by schema)

    if reaction_count >= 4 and hard_signals >= 2:
        confidence = 'HIGH'
    elif reaction_count >= 2 and hard_signals >= 1:
        confidence = 'MEDIUM'
    else:
        confidence = 'LOW'

    # Downgrade based on data quality
    if not data_quality_flags.get('ga4_available') and confidence == 'HIGH':
        confidence = 'MEDIUM'  # Downgrade if GA4 missing

    if not data_quality_flags.get('github_available') and confidence == 'HIGH':
        confidence = 'MEDIUM'

    return confidence

# === Null Rates Calculation ===

def calculate_null_rates(conn, window_start: datetime, window_end: datetime, data_quality_flags: Dict) -> Dict:
    """
    Calculate null rates for data quality assessment.
    Returns dict with deep_read_null_rate, engagement_null_rate, chat_activation_null_rate.
    """
    null_rates = {}

    with conn.cursor() as cur:
        # Deep read null rate (from content_meta)
        if data_quality_flags.get('content_meta_available'):
            try:
                cur.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN reading_time_sec IS NULL THEN 1 ELSE 0 END) as null_count
                    FROM sofia.content_meta
                """)
                result = cur.fetchone()
                if result and result['total'] > 0:
                    null_rates['deep_read_null_rate'] = round(result['null_count'] / result['total'], 4)
                else:
                    null_rates['deep_read_null_rate'] = 1.0
            except psycopg2.ProgrammingError:
                null_rates['deep_read_null_rate'] = 1.0
                conn.rollback()
        else:
            null_rates['deep_read_null_rate'] = 1.0

        # Engagement null rate (from analytics_events)
        if data_quality_flags.get('ga4_available'):
            try:
                cur.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN engagement_time_msec IS NULL THEN 1 ELSE 0 END) as null_count
                    FROM sofia.analytics_events
                    WHERE event_timestamp >= %s AND event_timestamp < %s
                """, (window_start, window_end))
                result = cur.fetchone()
                if result and result['total'] > 0:
                    null_rates['engagement_null_rate'] = round(result['null_count'] / result['total'], 4)
                else:
                    null_rates['engagement_null_rate'] = 1.0
            except psycopg2.ProgrammingError:
                null_rates['engagement_null_rate'] = 1.0
                conn.rollback()
        else:
            null_rates['engagement_null_rate'] = 1.0

        # Chat activation null rate (from ga4_chat_sessions)
        if data_quality_flags.get('chat_table_available'):
            try:
                cur.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN chat_activated IS NULL THEN 1 ELSE 0 END) as null_count
                    FROM sofia.ga4_chat_sessions
                    WHERE session_start >= %s AND session_start < %s
                """, (window_start, window_end))
                result = cur.fetchone()
                if result and result['total'] > 0:
                    null_rates['chat_activation_null_rate'] = round(result['null_count'] / result['total'], 4)
                else:
                    null_rates['chat_activation_null_rate'] = 1.0
            except psycopg2.ProgrammingError:
                null_rates['chat_activation_null_rate'] = 1.0
                conn.rollback()
        else:
            null_rates['chat_activation_null_rate'] = 1.0

    return null_rates

# === Insight Generation ===

def generate_insights(conn, events: List[Dict], window_start: datetime, window_end: datetime, data_quality_flags: Dict) -> Tuple[List[Dict], List[Dict]]:
    """
    Generate insights (2+ reactions) and observations (0-1 reactions) from events.
    Returns (insights, observations)
    """
    insights = []
    observations = []

    for event in events:
        reactions = detect_reactions_for_event(conn, event, window_start, window_end)

        if len(reactions) >= MIN_SOURCES_FOR_INSIGHT:
            # It's an insight
            confidence = calculate_confidence(reactions, data_quality_flags)
            topics = event.get('topics', [])
            entities_raw = event.get('entities', {})

            insight = {
                'insight_id': f"INSIGHT_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{len(insights)+1:03d}",
                'title': event['headline'][:200],  # Truncate to max length
                'domain': classify_domain(topics, entities_raw),
                'regions': extract_regions(entities_raw),
                'confidence': confidence,
                'event': {
                    'event_type': event['event_type'],
                    'headline': event['headline'],
                    'summary': event['summary'],
                    'happened_at': event['happened_at'],
                    'entities': convert_entities_to_schema(entities_raw),
                    'source_refs': event['source_refs']
                },
                'reactions': reactions,
                'explanation': f"Multiple independent sources detected correlated activity around {event['headline'][:100]}",
                'implications': [
                    {
                        'category': 'technology',
                        'text': 'Emerging trend with cross-source validation'
                    }
                ],
                'recommended_actions': [],
                'tags': event.get('topics', [])[:10],
                'metrics': {},
                'trace': {
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'rule_id': 'cross_signals_builder_v1',
                    'rule_version': '1.0.0',
                    'references': []
                },
                'quality': {
                    'data_status': 'complete' if len(reactions) >= 4 else 'partial',
                    'missing_sources': [k for k, v in data_quality_flags.items() if not v],
                    'warnings': [],
                    'null_rate': 0.0
                }
            }
            insights.append(insight)

        elif len(reactions) <= 1:
            # It's an observation
            topics = event.get('topics', [])
            entities_raw = event.get('entities', {})

            observation = {
                'observation_id': f"OBS_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{len(observations)+1:03d}",
                'title': event['headline'][:200],
                'domain': classify_domain(topics, entities_raw),
                'regions': extract_regions(entities_raw),
                'event': {
                    'event_type': event['event_type'],
                    'headline': event['headline'],
                    'summary': event['summary'],
                    'happened_at': event['happened_at'],
                    'entities': convert_entities_to_schema(entities_raw),
                    'source_refs': event['source_refs']
                },
                'reactions': reactions,
                'next_check': 'monitor_7d',
                'notes': 'Insufficient independent validation - monitoring for additional signals',
                'tags': event.get('topics', [])[:10],
                'trace': {
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'rule_id': 'cross_signals_builder_v1',
                    'references': []
                }
            }
            observations.append(observation)

    return insights, observations

# === Main Builder ===

def build_cross_signals(window_days: int = 7, dry_run: bool = False) -> Dict:
    """
    Main builder function.
    Returns complete cross_signals.json structure.
    """
    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(days=window_days)

    print(f"Building cross-signals for window: {window_start.date()} to {window_end.date()}")

    with get_connection() as conn:
        # 1. Detect source availability
        print("Detecting source availability...")
        sources = detect_source_availability(conn, window_start, window_end)

        # Build data quality flags
        data_quality_flags = {
            'ga4_available': any(s['source_id'] == 'ga4' and s['status'] == 'ok' for s in sources),
            'vscode_available': any(s['source_id'] == 'vscode_marketplace' and s['status'] == 'ok' for s in sources),
            'github_available': any(s['source_id'] == 'github_trending' and s['status'] == 'ok' for s in sources),
            'patents_available': any(s['source_id'] == 'patents' and s['status'] == 'ok' for s in sources),
            'papers_available': any(s['source_id'] == 'arxiv' and s['status'] == 'ok' for s in sources),
            'chat_table_available': any(s['source_id'] == 'chat_sessions' and s['status'] == 'ok' for s in sources),
            'funding_available': any(s['source_id'] == 'funding_rounds' and s['status'] == 'ok' for s in sources),
        }

        # 2. Detect candidate events
        print("Detecting candidate events...")
        events = detect_candidate_events(conn, window_start, window_end)
        print(f"Found {len(events)} candidate events")

        # 3. Generate insights and observations
        print("Generating insights and observations...")
        insights, observations = generate_insights(conn, events, window_start, window_end, data_quality_flags)
        print(f"Generated {len(insights)} insights, {len(observations)} observations")

        # 4. Build coverage summary
        domains_covered = list(set(i['domain'] for i in insights))
        regions_covered = list(set(r for i in insights for r in i['regions']))
        confidence_dist = {
            'LOW': sum(1 for i in insights if i['confidence'] == 'LOW'),
            'MEDIUM': sum(1 for i in insights if i['confidence'] == 'MEDIUM'),
            'HIGH': sum(1 for i in insights if i['confidence'] == 'HIGH'),
        }
        sources_used = len(set(
            r['source_id']
            for i in insights
            for r in i['reactions']
        ))

        # 5. Build data quality warnings
        warnings = []
        for source in sources:
            if source['status'] == 'offline':
                warnings.append({
                    'severity': 'error',
                    'source': source['source_id'],
                    'message': f"{source['source_id']} is offline: {source['notes']}",
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            elif source['status'] == 'partial':
                warnings.append({
                    'severity': 'warning',
                    'source': source['source_id'],
                    'message': f"{source['source_id']} has partial data: {source['notes']}",
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })

        # 6. Calculate null rates
        print("Calculating data quality null rates...")
        null_rates = calculate_null_rates(conn, window_start, window_end, data_quality_flags)

        # 7. Assemble final JSON
        cross_signals = {
            'schema_version': SCHEMA_VERSION,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'window': {
                'start_date': window_start.date().isoformat(),
                'end_date': window_end.date().isoformat(),
                'timezone': 'UTC'
            },
            'sources': sources,
            'insights': insights[:20],  # Max 20 per schema
            'observations': observations[:50],  # Max 50 per schema
            'coverage': {
                'total_insights': len(insights),
                'total_observations': len(observations),
                'domains_covered': domains_covered,
                'regions_covered': regions_covered,
                'confidence_distribution': confidence_dist,
                'sources_used': sources_used
            },
            'data_quality': {
                'flags': data_quality_flags,
                'null_rates': null_rates,
                'warnings': warnings,
                'coverage_summary': {
                    'min_coverage_days': min((s['coverage_days'] for s in sources if s['coverage_days']), default=0),
                    'max_coverage_days': max((s['coverage_days'] for s in sources if s['coverage_days']), default=0),
                    'sources_with_full_coverage': sum(1 for s in sources if s['status'] == 'ok'),
                    'sources_with_partial_coverage': sum(1 for s in sources if s['status'] == 'partial')
                }
            },
            'render_hints': {
                'max_items_email': 5,
                'max_items_web': 10,
                'ordering': 'confidence_desc',
                'show_observations': False,
                'highlight_domains': [d for d in ['SECURITY', 'AI'] if d in domains_covered]
            }
        }

        return cross_signals

# === CLI ===

def main():
    parser = argparse.ArgumentParser(description='Sofia Pulse Cross Signals Builder')
    parser.add_argument('--window-days', type=int, default=7, help='Analysis window in days (default: 7)')
    parser.add_argument('--dry-run', action='store_true', help='Print JSON to stdout instead of writing file')
    args = parser.parse_args()

    try:
        cross_signals = build_cross_signals(window_days=args.window_days, dry_run=args.dry_run)

        if args.dry_run:
            print(json.dumps(cross_signals, indent=2))
        else:
            OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(cross_signals, f, indent=2, ensure_ascii=False)
            print(f"✅ Cross signals written to {OUTPUT_FILE}")
            print(f"   Insights: {cross_signals['coverage']['total_insights']}")
            print(f"   Observations: {cross_signals['coverage']['total_observations']}")
            print(f"   Sources used: {cross_signals['coverage']['sources_used']}")

    except Exception as e:
        print(f"❌ Error building cross-signals: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
