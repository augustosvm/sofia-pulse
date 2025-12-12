#!/usr/bin/env python3
"""
Sofia Pulse - WhatsApp Alerts via sofia-mastra-rag
Sends alerts to user's WhatsApp via Sofia API
"""

import os
import requests
from datetime import datetime

# Configuration
WHATSAPP_NUMBER = os.getenv('WHATSAPP_NUMBER', 'YOUR_WHATSAPP_NUMBER')
SOFIA_WPP_ENDPOINT = os.getenv('SOFIA_WPP_ENDPOINT', 'http://localhost:3001/send')
ALERT_ENABLED = os.getenv('ALERT_WHATSAPP_ENABLED', 'true').lower() == 'true'

def send_whatsapp_alert(message, level='WARNING'):
    """
    Send alert via WhatsApp using sofia-mastra-rag

    Args:
        message: Alert message
        level: Alert level (INFO, WARNING, CRITICAL)

    Returns:
        bool: True if successful, False otherwise
    """
    if not ALERT_ENABLED:
        print("⚠️  WhatsApp alerts disabled")
        return False

    # Format message with emoji based on level
    emoji = {
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'CRITICAL': '🚨'
    }.get(level, '📢')

    formatted_message = f"""{emoji} *SOFIA PULSE ALERT*

*Level*: {level}
*Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}

---
_Sofia Pulse Intelligence System_
"""

    try:
        # Call sofia-wpp directly
        payload = {
            'to': WHATSAPP_NUMBER,
            'message': formatted_message
        }

        response = requests.post(
            SOFIA_WPP_ENDPOINT,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            print(f"✅ WhatsApp alert sent to +{WHATSAPP_NUMBER}")
            return True
        else:
            print(f"❌ WhatsApp alert failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to sofia-wpp at {SOFIA_WPP_ENDPOINT}")
        print(f"   Is sofia-wpp running?")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Sofia API timeout")
        return False
    except Exception as e:
        print(f"❌ Failed to send WhatsApp alert: {e}")
        return False

def alert_collector_failed(collector_name, error):
    """Send alert when collector fails"""
    message = f"""*Collector Failed*

Collector: `{collector_name}`
Error: {error}

Check logs:
`/var/log/sofia/collectors/{collector_name}.log`
"""
    return send_whatsapp_alert(message, level='CRITICAL')

def alert_data_anomaly(table_name, anomaly_type, details):
    """Send alert when data anomaly detected"""
    message = f"""*Data Anomaly Detected*

Table: `{table_name}`
Type: {anomaly_type}
Details: {details}

This may require manual investigation.
"""
    return send_whatsapp_alert(message, level='WARNING')

def alert_api_rate_limit(api_name, reset_time=None):
    """Send alert when API rate limit hit"""
    message = f"""*API Rate Limit Hit*

API: {api_name}
Reset: {reset_time or 'Unknown'}

Collector will retry automatically.
"""
    return send_whatsapp_alert(message, level='INFO')

def alert_healthcheck_failed(failed_count, total_count):
    """Send alert when healthcheck fails"""
    message = f"""*Healthcheck Failed*

Failed collectors: {failed_count}/{total_count}

Run healthcheck for details:
`bash healthcheck-collectors.sh`
"""
    return send_whatsapp_alert(message, level='CRITICAL')

def alert_sanity_check_failed(issues):
    """Send alert when sanity check fails"""
    issues_text = '\n'.join([f"• {issue}" for issue in issues[:5]])
    if len(issues) > 5:
        issues_text += f"\n• ...and {len(issues) - 5} more"

    message = f"""*Data Sanity Check Failed*

Found {len(issues)} issues:

{issues_text}

Run sanity check for details:
`python3 scripts/sanity-check.py`
"""
    return send_whatsapp_alert(message, level='WARNING')

def test_whatsapp_alert():
    """Test WhatsApp alert system"""
    message = f"""*Test Alert*

Sofia Pulse alert system is working!

Configuration:
• Phone: +{WHATSAPP_NUMBER}
• Endpoint: {SOFIA_WPP_ENDPOINT}
• Status: ✅ Active

This is a test message.
"""
    return send_whatsapp_alert(message, level='INFO')

if __name__ == '__main__':
    # Test alert
    print("Testing WhatsApp alert system...")
    success = test_whatsapp_alert()

    if success:
        print("\n✅ WhatsApp alerts working!")
    else:
        print("\n❌ WhatsApp alerts failed. Check configuration:")
        print(f"   WHATSAPP_NUMBER: {WHATSAPP_NUMBER}")
        print(f"   SOFIA_WPP_ENDPOINT: {SOFIA_WPP_ENDPOINT}")
        print(f"   ALERT_WHATSAPP_ENABLED: {ALERT_ENABLED}")
