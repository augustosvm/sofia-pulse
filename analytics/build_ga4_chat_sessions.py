#!/usr/bin/env python3
"""
Build GA4 Chat Sessions (Derived Table)

Extracts real conversations from analytics_events and populates ga4_chat_sessions.

Conversation = >= 1 user message event
Qualified = >= 3 messages OR >= 200 chars OR >= 120s interaction
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'user': os.getenv('DB_USER', 'sofia'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sofia_db'),
}

def get_chat_events(conn, days=30):
    """Get chat events from analytics_events"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = f"""
    SELECT
        user_pseudo_id,
        ga_session_id,
        event_date,
        event_timestamp,
        event_name,
        page_path,
        source,
        medium,
        device_category,
        country,
        engagement_time_ms
    FROM sofia.analytics_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '{days} days'
        AND (
            event_name LIKE '%%chat%%'
            OR event_name LIKE '%%message%%'
            OR event_name LIKE '%%sofia%%'
            OR event_name = 'widget_open'
        )
    ORDER BY user_pseudo_id, ga_session_id, event_timestamp
    """

    cursor.execute(query)
    return cursor.fetchall()

def group_into_sessions(events):
    """Group events into conversation sessions"""

    sessions = {}

    for event in events:
        # Generate conversation key
        user_id = event['user_pseudo_id']
        session_id = event['ga_session_id']
        page_path = event['page_path']
        event_date = event['event_date']

        key = f"{user_id}|{session_id}|{page_path}|{event_date}"

        if key not in sessions:
            sessions[key] = {
                'conversation_key': key.replace('|', '_'),
                'user_pseudo_id': user_id,
                'ga_session_id': session_id,
                'entry_page_path': page_path,
                'source': event['source'],
                'medium': event['medium'],
                'device_category': event['device_category'],
                'country': event['country'],
                'started_at': None,
                'user_messages': [],
                'sofia_responses': [],
                'total_engagement_ms': 0
            }

        sess = sessions[key]

        # Track start time (first event)
        if sess['started_at'] is None:
            sess['started_at'] = datetime.fromtimestamp(event['event_timestamp'] / 1000000)

        # Classify event
        event_name = event['event_name'].lower()

        # User messages (real conversation)
        if 'message' in event_name or 'chat' in event_name:
            if 'user' in event_name or 'send' in event_name:
                sess['user_messages'].append(event)

        # Sofia responses
        if 'sofia' in event_name or 'response' in event_name or 'assistant' in event_name:
            sess['sofia_responses'].append(event)

        # Accumulate engagement time
        if event['engagement_time_ms']:
            sess['total_engagement_ms'] += event['engagement_time_ms']

    return list(sessions.values())

def calculate_qualified(session):
    """Determine if conversation is qualified"""
    user_messages_count = len(session['user_messages'])

    # Estimate chars (proxy: 50 chars per message)
    user_chars_total = user_messages_count * 50

    # Interaction time in seconds
    interaction_time_s = session['total_engagement_ms'] / 1000

    # Qualified = >= 3 messages OR >= 200 chars OR >= 120s
    return (
        user_messages_count >= 3
        or user_chars_total >= 200
        or interaction_time_s >= 120
    )

def upsert_sessions(conn, sessions):
    """Upsert chat sessions to database"""
    cursor = conn.cursor()

    query = """
    INSERT INTO sofia.ga4_chat_sessions (
        conversation_key,
        user_pseudo_id,
        ga_session_id,
        entry_page_path,
        source,
        medium,
        device_category,
        country,
        started_at,
        user_messages_count,
        user_chars_total,
        sofia_responses_count,
        qualified,
        updated_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
    ON CONFLICT (conversation_key) DO UPDATE SET
        user_messages_count = EXCLUDED.user_messages_count,
        user_chars_total = EXCLUDED.user_chars_total,
        sofia_responses_count = EXCLUDED.sofia_responses_count,
        qualified = EXCLUDED.qualified,
        updated_at = NOW()
    """

    inserted = 0
    for session in sessions:
        user_messages_count = len(session['user_messages'])
        sofia_responses_count = len(session['sofia_responses'])
        user_chars_total = user_messages_count * 50  # Proxy
        qualified = calculate_qualified(session)

        # Only insert if there's at least 1 user message (real conversation)
        if user_messages_count > 0:
            try:
                cursor.execute(query, (
                    session['conversation_key'],
                    session['user_pseudo_id'],
                    session['ga_session_id'],
                    session['entry_page_path'],
                    session['source'],
                    session['medium'],
                    session['device_category'],
                    session['country'],
                    session['started_at'],
                    user_messages_count,
                    user_chars_total,
                    sofia_responses_count,
                    qualified
                ))
                inserted += 1
            except Exception as e:
                print(f"  [ERROR] Failed to insert session {session['conversation_key']}: {e}")
                conn.rollback()
                continue

    conn.commit()
    cursor.close()

    return inserted

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("[OK] Connected to database")
        print("")

        # Get chat events
        print("Fetching chat events (last 30 days)...")
        events = get_chat_events(conn, days=30)
        print(f"[OK] Found {len(events)} chat-related events")
        print("")

        # Group into sessions
        print("Grouping events into sessions...")
        sessions = group_into_sessions(events)
        print(f"[OK] Identified {len(sessions)} potential sessions")
        print("")

        # Filter real conversations (>= 1 user message)
        real_conversations = [s for s in sessions if len(s['user_messages']) > 0]
        qualified_conversations = [s for s in real_conversations if calculate_qualified(s)]

        print(f"Real conversations (>= 1 message): {len(real_conversations)}")
        print(f"Qualified conversations: {len(qualified_conversations)}")
        print("")

        # Upsert sessions
        if real_conversations:
            print("Upserting chat sessions to database...")
            inserted = upsert_sessions(conn, sessions)
            print(f"[OK] Upserted {inserted} chat sessions")
        else:
            print("[INFO] No real conversations found")

        conn.close()

        print("")
        print("=" * 80)
        print("CHAT SESSIONS BUILD COMPLETE")
        print("=" * 80)
        print("")
        print(f"Total sessions processed: {len(sessions)}")
        print(f"Real conversations: {len(real_conversations)}")
        print(f"Qualified conversations: {len(qualified_conversations)}")
        print("")

    except Exception as e:
        print(f"[ERROR] Failed to build chat sessions: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
