#!/usr/bin/env python3
"""
Sofia Pulse - Alert System
Send alerts via WhatsApp (primary), Telegram, or Email

PRIMARY CHANNEL: WhatsApp via sofia-mastra-rag
"""

import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import WhatsApp alerts (primary channel)
try:
    from scripts.utils.whatsapp_alerts import (
        send_whatsapp_alert,
        alert_collector_failed as wa_collector_failed,
        alert_data_anomaly as wa_data_anomaly,
        alert_api_rate_limit as wa_api_rate_limit,
    )
    WHATSAPP_AVAILABLE = True
except ImportError:
    WHATSAPP_AVAILABLE = False
    print("⚠️  WhatsApp alerts not available")

import requests
from datetime import datetime

# Telegram configuration (backup channel)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Email configuration (backup channel)
ALERT_EMAIL = os.getenv('ALERT_EMAIL', 'augustosvm@gmail.com')

def send_telegram_alert(message, level='WARNING'):
    """
    Send alert via Telegram

    Args:
        message: Alert message
        level: Alert level (INFO, WARNING, CRITICAL)
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram not configured, skipping alert")
        return False

    emoji = {
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'CRITICAL': '🚨'
    }.get(level, '📢')

    formatted_message = f"""
{emoji} **SOFIA PULSE ALERT**

**Level**: {level}
**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}
"""

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': formatted_message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Failed to send Telegram alert: {e}")
        return False


def send_alert(message, level='WARNING', channels=['whatsapp', 'telegram']):
    """
    Send alert via multiple channels

    Args:
        message: Alert message
        level: Alert level (INFO, WARNING, CRITICAL)
        channels: List of channels ('whatsapp', 'telegram', 'email')

    Returns:
        True if at least one channel succeeded

    Note: WhatsApp is the PRIMARY channel (via sofia-mastra-rag)
    """
    success = False

    # Try WhatsApp first (primary channel)
    if 'whatsapp' in channels and WHATSAPP_AVAILABLE:
        if send_whatsapp_alert(message, level):
            success = True

    # Fallback to Telegram
    if 'telegram' in channels:
        if send_telegram_alert(message, level):
            success = True

    # Email alerts not implemented yet
    # Could use send-email-mega.py logic here

    return success

def alert_collector_failed(collector_name, error):
    """
    Alert when collector fails

    PRIMARY: Sends to WhatsApp via sofia-mastra-rag
    BACKUP: Sends to Telegram if configured
    """
    # Use WhatsApp-specific alert if available
    if WHATSAPP_AVAILABLE:
        wa_collector_failed(collector_name, error)

    # Also try other channels as backup
    message = f"""
**Collector Failed**: {collector_name}
**Error**: {error}

Please check logs at /var/log/sofia/collectors/{collector_name}.log
"""
    send_alert(message, level='CRITICAL', channels=['telegram'])

def alert_data_anomaly(table_name, anomaly_type, details):
    """
    Alert when data anomaly detected

    PRIMARY: Sends to WhatsApp via sofia-mastra-rag
    BACKUP: Sends to Telegram if configured
    """
    # Use WhatsApp-specific alert if available
    if WHATSAPP_AVAILABLE:
        wa_data_anomaly(table_name, anomaly_type, details)

    # Also try other channels as backup
    message = f"""
**Data Anomaly Detected**
**Table**: {table_name}
**Type**: {anomaly_type}
**Details**: {details}
"""
    send_alert(message, level='WARNING', channels=['telegram'])

def alert_api_rate_limit(api_name, reset_time=None):
    """
    Alert when API rate limit hit

    PRIMARY: Sends to WhatsApp via sofia-mastra-rag
    BACKUP: Sends to Telegram if configured
    """
    # Use WhatsApp-specific alert if available
    if WHATSAPP_AVAILABLE:
        wa_api_rate_limit(api_name, reset_time)

    # Also try other channels as backup
    message = f"""
**API Rate Limit Hit**
**API**: {api_name}
**Reset Time**: {reset_time or 'Unknown'}

Collector will retry automatically.
"""
    send_alert(message, level='INFO', channels=['telegram'])
