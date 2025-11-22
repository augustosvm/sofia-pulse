#!/usr/bin/env python3
"""
Sofia Pulse - Test WhatsApp API Connectivity
Debug script to check sofia-mastra-rag endpoint
"""

import requests
import json
import os

# Configuration
WHATSAPP_RECIPIENT = os.getenv('WHATSAPP_NUMBER', '5527988024062')  # Seu número pessoal
SOFIA_API_ENDPOINT = os.getenv('SOFIA_API_ENDPOINT', 'http://localhost:8001/api/v2/chat')

print("════════════════════════════════════════════════════════════════")
print("🧪 SOFIA PULSE - WHATSAPP API TEST")
print("════════════════════════════════════════════════════════════════")
print("")
print("Configuration:")
print(f"  Endpoint: {SOFIA_API_ENDPOINT}")
print(f"  Recipient: +{WHATSAPP_RECIPIENT}")
print("")

# Test 1: Check if API is accessible
print("════════════════════════════════════════════════════════════════")
print("TEST 1: API Accessibility")
print("════════════════════════════════════════════════════════════════")

try:
    response = requests.get(SOFIA_API_ENDPOINT.replace('/api/v2/chat', '/health'), timeout=5)
    print(f"✅ API is accessible (HTTP {response.status_code})")
except requests.exceptions.ConnectionError:
    print(f"❌ Cannot connect to {SOFIA_API_ENDPOINT}")
    print("   Is sofia-mastra-rag running?")
    print("   Try: curl http://localhost:8001/health")
    exit(1)
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

print("")

# Test 2: Try sending message with current payload format
print("════════════════════════════════════════════════════════════════")
print("TEST 2: Send Test Message (Current Format)")
print("════════════════════════════════════════════════════════════════")

payload_v1 = {
    'query': '🧪 TESTE - Sofia Pulse WhatsApp Integration\n\nSe você recebeu esta mensagem, a integração está funcionando!',
    'user_id': 'sofia-pulse',
    'channel': 'whatsapp',
    'phone': WHATSAPP_RECIPIENT
}

print("Payload:")
print(json.dumps(payload_v1, indent=2))
print("")

try:
    response = requests.post(
        SOFIA_API_ENDPOINT,
        json=payload_v1,
        timeout=15
    )

    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print("")
    print("Response Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text[:500])

    if response.status_code == 200:
        print("")
        print("✅ Message sent successfully!")
        print(f"   Check WhatsApp: +{WHATSAPP_RECIPIENT}")
    else:
        print("")
        print(f"⚠️  HTTP {response.status_code} - Message may not have been sent")

except Exception as e:
    print(f"❌ Error: {e}")

print("")

# Test 3: Try alternative payload formats
print("════════════════════════════════════════════════════════════════")
print("TEST 3: Alternative Payload Formats")
print("════════════════════════════════════════════════════════════════")

# Format 2: Direct WhatsApp format
payload_v2 = {
    'to': WHATSAPP_RECIPIENT,
    'message': '🧪 TESTE - Format 2\n\nTeste de formato alternativo',
    'channel': 'whatsapp'
}

print("\nFormat 2 (Direct WhatsApp):")
print(json.dumps(payload_v2, indent=2))

try:
    response = requests.post(
        SOFIA_API_ENDPOINT,
        json=payload_v2,
        timeout=15
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Format 2 works!")
    else:
        print(f"❌ Format 2 failed: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

# Format 3: Simplified
payload_v3 = {
    'message': '🧪 TESTE - Format 3\n\nTeste simplificado',
    'phone': WHATSAPP_RECIPIENT
}

print("\nFormat 3 (Simplified):")
print(json.dumps(payload_v3, indent=2))

try:
    response = requests.post(
        SOFIA_API_ENDPOINT,
        json=payload_v3,
        timeout=15
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Format 3 works!")
    else:
        print(f"❌ Format 3 failed: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("")
print("════════════════════════════════════════════════════════════════")
print("📋 SUMMARY")
print("════════════════════════════════════════════════════════════════")
print("")
print("Next steps:")
print("1. Check which format returned HTTP 200")
print("2. Check your WhatsApp (+55 27 98802-4062)")
print("3. Check sofia-mastra-rag logs for errors")
print("")
print("If no format works:")
print("  • Check sofia-mastra-rag is running: curl http://localhost:8001/health")
print("  • Check WhatsApp Business API is configured")
print("  • Check recipient number is registered: +55 27 98802-4062")
print("  • Check sender number in sofia-mastra-rag: +55 11 5199-0773")
print("")
