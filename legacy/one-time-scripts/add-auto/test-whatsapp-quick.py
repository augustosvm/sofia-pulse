#!/usr/bin/env python3
"""
Quick WhatsApp Test - Works on ANY branch
Tests direct WhatsApp integration without Sofia
"""

import requests
import os
from datetime import datetime

# Configuration (hardcoded for quick test)
WHATSAPP_NUMBER = "5527988024062"
WHATSAPP_API_URL = "http://91.98.158.19:3001/send"

def send_whatsapp(message):
    """Send message directly to WhatsApp"""
    print("="*60)
    print(f"📱 Sending WhatsApp Message")
    print("="*60)
    print(f"To: {WHATSAPP_NUMBER}")
    print(f"Message length: {len(message)} chars")
    print()

    payload = {
        'to': WHATSAPP_NUMBER,
        'message': message
    }

    try:
        response = requests.post(
            WHATSAPP_API_URL,
            json=payload,
            timeout=10
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print()
            print("✅ Message sent successfully!")
            print("Check your WhatsApp! 📱")
            return True
        else:
            print()
            print(f"❌ Failed: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Test messages
print("\n🧪 WhatsApp Integration Test")
print("="*60)
print()

# Test 1: Simple message
print("TEST 1: Simple message")
send_whatsapp("🎉 Sofia Pulse - Sistema funcionando!")
print()

# Test 2: Formatted alert
print("TEST 2: Formatted alert")
alert_message = f"""🚨 ALERTA DE TESTE

API: Test API
Status: 200
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
Este é um teste do sistema Sofia Pulse.
Se você está vendo isto, o WhatsApp está 100% funcional!

---
Sofia Pulse Intelligence System
"""

send_whatsapp(alert_message)
print()

print("="*60)
print("✅ Tests complete!")
print("="*60)
print()
print("If you received 2 messages, the system is working!")
print()
