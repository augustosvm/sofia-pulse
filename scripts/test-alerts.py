#!/usr/bin/env python3
"""
Sofia Pulse - Test Alert System
Tests all alert types to verify configuration
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.whatsapp_alerts import (
    test_whatsapp_alert,
    alert_collector_failed,
    alert_data_anomaly,
    alert_api_rate_limit,
    WHATSAPP_NUMBER,
    SOFIA_API_ENDPOINT,
    ALERT_ENABLED
)

def main():
    print("════════════════════════════════════════════════════════════════")
    print("🧪 SOFIA PULSE - ALERT SYSTEM TEST")
    print("════════════════════════════════════════════════════════════════")
    print("")
    print("Configuration:")
    print(f"  • WhatsApp Number: +{WHATSAPP_NUMBER}")
    print(f"  • Sofia API: {SOFIA_API_ENDPOINT}")
    print(f"  • Enabled: {ALERT_ENABLED}")
    print("")

    if not ALERT_ENABLED:
        print("❌ Alerts are disabled!")
        print("   Set ALERT_WHATSAPP_ENABLED=true in .env")
        return 1

    print("════════════════════════════════════════════════════════════════")
    print("📱 TEST 1: Basic WhatsApp Alert")
    print("════════════════════════════════════════════════════════════════")
    print("")

    success = test_whatsapp_alert()

    if not success:
        print("")
        print("❌ Basic alert failed!")
        print("   Check if sofia-mastra-rag is running:")
        print(f"   curl {SOFIA_API_ENDPOINT}")
        return 1

    print("")
    input("✅ Did you receive the test message on WhatsApp? Press ENTER to continue...")
    print("")

    print("════════════════════════════════════════════════════════════════")
    print("📱 TEST 2: Collector Failure Alert")
    print("════════════════════════════════════════════════════════════════")
    print("")

    alert_collector_failed('test-collector', 'HTTP 403 - Rate limited')

    print("")
    input("Press ENTER to continue...")
    print("")

    print("════════════════════════════════════════════════════════════════")
    print("📱 TEST 3: Data Anomaly Alert")
    print("════════════════════════════════════════════════════════════════")
    print("")

    alert_data_anomaly('test_table', 'ZERO_ROWS', 'Expected 100+ rows, got 0')

    print("")
    input("Press ENTER to continue...")
    print("")

    print("════════════════════════════════════════════════════════════════")
    print("📱 TEST 4: API Rate Limit Alert")
    print("════════════════════════════════════════════════════════════════")
    print("")

    alert_api_rate_limit('GitHub API', '2025-11-22 12:00:00')

    print("")
    print("════════════════════════════════════════════════════════════════")
    print("✅ ALL TESTS COMPLETE")
    print("════════════════════════════════════════════════════════════════")
    print("")
    print("You should have received 4 WhatsApp messages:")
    print("  1. Test alert")
    print("  2. Collector failure")
    print("  3. Data anomaly")
    print("  4. API rate limit")
    print("")
    print("If you received all messages, the alert system is working! 🎉")
    print("")

    return 0

if __name__ == '__main__':
    sys.exit(main())
