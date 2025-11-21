#!/usr/bin/env python3
"""
Sofia Pulse - Alert System
Send alerts via Telegram, WhatsApp, or Email
"""

import os
import requests
from datetime import datetime

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# WhatsApp configuration (via sofia-mastra-rag endpoint)
WHATSAPP_ENDPOINT = os.getenv('WHATSAPP_ENDPOINT', '')

# Email configuration
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

def send_whatsapp_alert(message, level='WARNING'):
    """
    Send alert via WhatsApp (using sofia-mastra-rag endpoint)

    Args:
        message: Alert message
        level: Alert level (INFO, WARNING, CRITICAL)
    """
    if not WHATSAPP_ENDPOINT:
        print("⚠️  WhatsApp not configured, skipping alert")
        return False

    emoji = {
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'CRITICAL': '🚨'
    }.get(level, '📢')

    formatted_message = f"""{emoji} *SOFIA PULSE ALERT*

*Level*: {level}
*Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}
"""

    try:
        payload = {'message': formatted_message}
        response = requests.post(WHATSAPP_ENDPOINT, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Failed to send WhatsApp alert: {e}")
        return False

def send_alert(message, level='WARNING', channels=['telegram']):
    """
    Send alert via multiple channels

    Args:
        message: Alert message
        level: Alert level (INFO, WARNING, CRITICAL)
        channels: List of channels ('telegram', 'whatsapp', 'email')

    Returns:
        True if at least one channel succeeded
    """
    success = False

    if 'telegram' in channels:
        if send_telegram_alert(message, level):
            success = True

    if 'whatsapp' in channels:
        if send_whatsapp_alert(message, level):
            success = True

    # Email alerts not implemented yet
    # Could use send-email-mega.py logic here

    return success

def alert_collector_failed(collector_name, error):
    """Alert when collector fails"""
    message = f"""
**Collector Failed**: {collector_name}
**Error**: {error}

Please check logs at /var/log/sofia/collectors/{collector_name}.log
"""
    send_alert(message, level='CRITICAL')

def alert_data_anomaly(table_name, anomaly_type, details):
    """Alert when data anomaly detected"""
    message = f"""
**Data Anomaly Detected**
**Table**: {table_name}
**Type**: {anomaly_type}
**Details**: {details}
"""
    send_alert(message, level='WARNING')

def alert_api_rate_limit(api_name, reset_time=None):
    """Alert when API rate limit hit"""
    message = f"""
**API Rate Limit Hit**
**API**: {api_name}
**Reset Time**: {reset_time or 'Unknown'}

Collector will retry automatically.
"""
    send_alert(message, level='INFO')
