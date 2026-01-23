#!/usr/bin/env python3
"""
GA4 Event Discovery - Automatic Event Catalog

Scans last 30 days in BigQuery to discover:
- All event_names
- Common event_params per event
- Chat candidates (message, response, open)
- Deep read candidates
- Confidence scoring based on params
"""

import os
import sys
import json
from datetime import datetime, timedelta
from google.cloud import bigquery
from collections import defaultdict, Counter
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'tiespecialistas-tts')
GA4_BQ_DATASET = os.getenv('GA4_BQ_DATASET')

def detect_ga4_dataset(client, project_id):
    """Auto-detect GA4 dataset"""
    try:
        datasets = list(client.list_datasets(project_id))
        for dataset in datasets:
            if dataset.dataset_id.startswith('analytics_'):
                return dataset.dataset_id
        return None
    except Exception as e:
        print(f"[ERROR] Failed to detect dataset: {e}")
        return None

def discover_events(client, project_id, dataset_id, days=30):
    """Discover all event names and their params"""

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    query = f"""
    SELECT
        event_name,
        COUNT(*) as event_count,
        ARRAY_AGG(DISTINCT param.key IGNORE NULLS) as param_keys
    FROM `{project_id}.{dataset_id}.events_*`,
    UNNEST(event_params) as param
    WHERE _TABLE_SUFFIX BETWEEN '{start_date.strftime('%Y%m%d')}' AND '{end_date.strftime('%Y%m%d')}'
    GROUP BY event_name
    ORDER BY event_count DESC
    """

    try:
        results = client.query(query).result()
        events = []

        for row in results:
            events.append({
                'event_name': row.event_name,
                'count': row.event_count,
                'params': row.param_keys if row.param_keys else []
            })

        return events

    except Exception as e:
        print(f"[ERROR] Failed to discover events: {e}")
        return []

def classify_event(event_name, params):
    """
    Classify event as chat/deep_read candidate with confidence.

    Returns: {
        'category': 'chat_user_message'|'chat_sofia_response'|'chat_open'|'deep_read'|'other',
        'confidence': 0.0-1.0,
        'signals': []
    }
    """
    event_lower = event_name.lower()

    # Chat signals
    chat_keywords = ['chat', 'message', 'sofia', 'assistant', 'conversation', 'response']
    deep_read_keywords = ['scroll', 'read', 'engagement', 'content']

    # Chat user message
    if any(kw in event_lower for kw in ['user_message', 'send_message', 'chat_message']):
        signals = []
        confidence = 0.6

        if 'message_length' in params:
            confidence += 0.15
            signals.append('has_message_length')
        if 'conversation_id' in params or 'session_id' in params:
            confidence += 0.15
            signals.append('has_conversation_id')
        if 'turn_index' in params or 'message_index' in params:
            confidence += 0.10
            signals.append('has_turn_index')

        return {
            'category': 'chat_user_message',
            'confidence': min(confidence, 1.0),
            'signals': signals
        }

    # Chat sofia response
    if any(kw in event_lower for kw in ['sofia_response', 'assistant_response', 'bot_reply']):
        signals = []
        confidence = 0.6

        if 'response_length' in params or 'tokens_out' in params:
            confidence += 0.15
            signals.append('has_response_length')
        if 'latency_ms' in params or 'response_time' in params:
            confidence += 0.15
            signals.append('has_latency')
        if 'conversation_id' in params:
            confidence += 0.10
            signals.append('has_conversation_id')

        return {
            'category': 'chat_sofia_response',
            'confidence': min(confidence, 1.0),
            'signals': signals
        }

    # Chat open
    if any(kw in event_lower for kw in ['widget_open', 'chat_open', 'chat_start']):
        return {
            'category': 'chat_open',
            'confidence': 0.8,
            'signals': ['keyword_match']
        }

    # Deep read candidates
    if any(kw in event_lower for kw in deep_read_keywords):
        signals = []
        confidence = 0.3

        if 'scroll_depth' in params or 'scroll_percentage' in params:
            confidence += 0.30
            signals.append('has_scroll_depth')
        if 'engagement_time_msec' in params or 'time_on_page' in params:
            confidence += 0.25
            signals.append('has_engagement_time')
        if 'content_percentage' in params or 'read_percentage' in params:
            confidence += 0.15
            signals.append('has_read_percentage')

        return {
            'category': 'deep_read',
            'confidence': min(confidence, 1.0),
            'signals': signals
        }

    # Catch-all for any chat-related event
    if any(kw in event_lower for kw in chat_keywords):
        return {
            'category': 'chat_other',
            'confidence': 0.4,
            'signals': ['keyword_partial_match']
        }

    return {
        'category': 'other',
        'confidence': 0.0,
        'signals': []
    }

def build_catalog(events):
    """Build event catalog with classifications"""

    catalog = {
        'generated_at': datetime.now().isoformat(),
        'total_events': len(events),
        'chat_user_message_candidates': [],
        'chat_sofia_response_candidates': [],
        'chat_open_candidates': [],
        'deep_read_candidates': [],
        'other_events': [],
        'param_hints': {}
    }

    for event in events:
        classification = classify_event(event['event_name'], event['params'])

        entry = {
            'event_name': event['event_name'],
            'count': event['count'],
            'params': event['params'],
            'confidence': classification['confidence'],
            'signals': classification['signals']
        }

        category = classification['category']

        if category == 'chat_user_message':
            catalog['chat_user_message_candidates'].append(entry)
        elif category == 'chat_sofia_response':
            catalog['chat_sofia_response_candidates'].append(entry)
        elif category == 'chat_open':
            catalog['chat_open_candidates'].append(entry)
        elif category == 'deep_read':
            catalog['deep_read_candidates'].append(entry)
        else:
            if event['count'] >= 100:  # Only keep high-volume others
                catalog['other_events'].append(entry)

        # Collect param hints
        for param in event['params']:
            if param not in catalog['param_hints']:
                catalog['param_hints'][param] = []
            catalog['param_hints'][param].append(event['event_name'])

    # Sort by confidence
    catalog['chat_user_message_candidates'].sort(key=lambda x: x['confidence'], reverse=True)
    catalog['chat_sofia_response_candidates'].sort(key=lambda x: x['confidence'], reverse=True)
    catalog['chat_open_candidates'].sort(key=lambda x: x['confidence'], reverse=True)
    catalog['deep_read_candidates'].sort(key=lambda x: x['confidence'], reverse=True)

    return catalog

def main():
    try:
        # Initialize BigQuery client
        client = bigquery.Client(project=GCP_PROJECT_ID)
        print(f"[OK] BigQuery client initialized (project: {GCP_PROJECT_ID})")

        # Detect dataset
        if GA4_BQ_DATASET:
            dataset_id = GA4_BQ_DATASET
        else:
            dataset_id = detect_ga4_dataset(client, GCP_PROJECT_ID)

        if not dataset_id:
            print("[ERROR] No GA4 dataset found")
            sys.exit(1)

        print(f"[OK] Using dataset: {dataset_id}")
        print("")

        # Discover events
        print("Discovering GA4 events (last 30 days)...")
        events = discover_events(client, GCP_PROJECT_ID, dataset_id, days=30)

        if not events:
            print("[ERROR] No events discovered")
            sys.exit(1)

        print(f"[OK] Discovered {len(events)} unique events")
        print("")

        # Build catalog
        print("Building event catalog...")
        catalog = build_catalog(events)

        # Save catalog
        os.makedirs("outputs", exist_ok=True)
        catalog_file = "outputs/ga4_event_catalog.json"

        with open(catalog_file, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

        print(f"[OK] Catalog saved to: {catalog_file}")
        print("")

        # Print summary
        print("=" * 80)
        print("EVENT CATALOG SUMMARY")
        print("=" * 80)
        print("")
        print(f"Total events discovered: {catalog['total_events']}")
        print(f"Chat user message candidates: {len(catalog['chat_user_message_candidates'])}")
        print(f"Chat sofia response candidates: {len(catalog['chat_sofia_response_candidates'])}")
        print(f"Chat open candidates: {len(catalog['chat_open_candidates'])}")
        print(f"Deep read candidates: {len(catalog['deep_read_candidates'])}")
        print(f"Other high-volume events: {len(catalog['other_events'])}")
        print("")

        # Show top candidates
        if catalog['chat_user_message_candidates']:
            print("Top Chat User Message Candidates:")
            for event in catalog['chat_user_message_candidates'][:3]:
                print(f"  - {event['event_name']} (confidence: {event['confidence']:.2f}, count: {event['count']:,})")

        print("")

        if catalog['chat_sofia_response_candidates']:
            print("Top Chat Sofia Response Candidates:")
            for event in catalog['chat_sofia_response_candidates'][:3]:
                print(f"  - {event['event_name']} (confidence: {event['confidence']:.2f}, count: {event['count']:,})")

        print("")
        print("[OK] Discovery complete")

    except Exception as e:
        print(f"[ERROR] Failed to discover GA4 events: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
