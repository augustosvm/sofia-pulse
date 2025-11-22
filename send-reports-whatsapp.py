#!/usr/bin/env python3
"""Send key analysis reports via WhatsApp"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', 'utils'))

try:
    from whatsapp_notifier import WhatsAppNotifier
    whatsapp = WhatsAppNotifier()
except Exception as e:
    print(f"❌ Failed to load WhatsApp notifier: {e}")
    sys.exit(1)

# Key reports to send via WhatsApp
REPORTS = [
    {
        'path': 'analytics/mega-analysis-latest.txt',
        'name': '🌍 MEGA ANALYSIS',
        'max_chars': 4000
    },
    {
        'path': 'analytics/top10-latest.txt',
        'name': '🔥 TOP 10 TECH TRENDS',
        'max_chars': 3000
    },
    {
        'path': 'analytics/capital-flow-latest.txt',
        'name': '💰 CAPITAL FLOW PREDICTOR',
        'max_chars': 3000
    },
    {
        'path': 'analytics/career-trends-latest.txt',
        'name': '🎓 CAREER TRENDS',
        'max_chars': 3000
    },
    {
        'path': 'analytics/dying-sectors-latest.txt',
        'name': '💀 DYING SECTORS',
        'max_chars': 2500
    },
    {
        'path': 'analytics/dark-horses-intelligence-latest.txt',
        'name': '🐴 DARK HORSES',
        'max_chars': 2500
    },
]

print("════════════════════════════════════════════════════════════════")
print("📱 SENDING REPORTS VIA WHATSAPP")
print("════════════════════════════════════════════════════════════════")
print("")

sent_count = 0
failed_count = 0

for report in REPORTS:
    if not os.path.exists(report['path']):
        print(f"⚠️  {report['name']}: File not found")
        failed_count += 1
        continue

    print(f"📤 Sending: {report['name']}...")

    try:
        with open(report['path'], 'r', encoding='utf-8') as f:
            content = f.read()

        # Add header
        message = f"{report['name']}\n{'='*60}\n\n{content}"

        # Truncate if needed
        max_chars = report['max_chars']
        if len(message) > max_chars:
            # Try to cut at a line break
            truncated = message[:max_chars]
            last_newline = truncated.rfind('\n')
            if last_newline > max_chars * 0.8:  # At least 80% of content
                truncated = truncated[:last_newline]

            message = truncated + "\n\n... (relatório completo no email)"

        # Send
        if whatsapp.send(message):
            print(f"   ✅ Sent ({len(message)} chars)")
            sent_count += 1
        else:
            print(f"   ❌ Failed to send")
            failed_count += 1

        # Wait 3 seconds between messages to avoid rate limiting
        if report != REPORTS[-1]:  # Don't wait after last message
            print(f"   ⏳ Waiting 3s...")
            time.sleep(3)

    except Exception as e:
        print(f"   ❌ Error: {e}")
        failed_count += 1

print("")
print("════════════════════════════════════════════════════════════════")
print("✅ REPORTS SENT VIA WHATSAPP")
print("════════════════════════════════════════════════════════════════")
print("")
print(f"📤 Total: {len(REPORTS)}")
print(f"✅ Sent: {sent_count}")
print(f"❌ Failed: {failed_count}")
print("")

# Send summary
summary = f"""✅ Sofia Pulse Reports Sent

📱 WhatsApp: {sent_count}/{len(REPORTS)} reports
📧 Email: Full reports + CSVs

Key reports:
• MEGA Analysis
• Top 10 Tech Trends
• Capital Flow Predictor
• Career Trends
• Dying Sectors
• Dark Horses

Check WhatsApp for details!"""

whatsapp.send(summary)
print("📱 Summary sent")
print("")
