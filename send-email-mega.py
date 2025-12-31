#!/usr/bin/env python3
"""
SEND MEGA EMAIL - All 28 Reports

Sends comprehensive email with:
- 28 TXT reports (23 original + 5 new ML)
- 15+ CSV attachments
- Summary of key insights
"""

import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Email config
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')
EMAIL_TO = os.getenv('EMAIL_TO', SMTP_USER)

if not SMTP_USER or not SMTP_PASS:
    print("❌ SMTP credentials not configured!")
    print("Set SMTP_USER and SMTP_PASS in .env file")
    sys.exit(1)

# ============================================================================
# ALL 28 REPORTS (23 original + 5 new ML)
# ============================================================================

REPORTS = [
    # MEGA
    'analytics/MEGA-ANALYSIS.txt',

    # Core Analytics (5)
    'analytics/sofia-complete-report.txt',
    'analytics/top10-tech-trends.txt',
    'analytics/correlation-papers-funding.txt',
    'analytics/dark-horses-report.txt',
    'analytics/entity-resolution.txt',

    # Advanced Analytics (3)
    'analytics/special-sectors-analysis.txt',
    'analytics/early-stage-deep-dive.txt',
    'analytics/energy-global-map.txt',

    # ML Analytics (1)
    'analytics/causal-insights-ml.txt',

    # NEW: Advanced ML Analytics (5) ⭐
    'analytics/jobs-intelligence.txt',
    'analytics/sentiment-analysis.txt',
    'analytics/anomaly-detection.txt',
    'analytics/time-series-advanced.txt',
    'analytics/startup-pattern-matching.txt',

    # AI-Powered (1)
    'analytics/nlg-playbooks-gemini.txt',

    # Intelligence Analytics (6)
    'analytics/career-trends-predictor.txt',
    'analytics/capital-flow-predictor.txt',
    'analytics/expansion-location-analyzer.txt',
    'analytics/weekly-insights-generator.txt',
    'analytics/dying-sectors-detector.txt',
    'analytics/dark-horses-intelligence.txt',

    # Socioeconomic Intelligence (3)
    'analytics/best-cities-tech-talent.txt',
    'analytics/remote-work-quality-index.txt',
    'analytics/innovation-hubs.txt',

    # Women, Security & Social (3)
    'analytics/women-global-analysis.txt',
    'analytics/security-intelligence.txt',
    'analytics/social-intelligence.txt',
]

CSV_REPORTS = [
    'analytics/github_trending.csv',
    'analytics/npm_stats.csv',
    'analytics/pypi_stats.csv',
    'analytics/hackernews_stories.csv',
    'analytics/funding_90d.csv',
    'analytics/arxiv_ai_papers.csv',
    'analytics/openalex_papers.csv',
    'analytics/nih_grants.csv',
    'analytics/cybersecurity_30d.csv',
    'analytics/space_launches.csv',
    'analytics/ai_regulation.csv',
    'analytics/gdelt_events_30d.csv',
    'analytics/socioeconomic_brazil.csv',
    'analytics/socioeconomic_top_gdp.csv',
    'analytics/electricity_consumption.csv',
    'analytics/commodity_prices.csv',
    'analytics/port_traffic.csv',
]

def create_email_body():
    """Create email body with summary"""
    body = f"""
Sofia Pulse - Daily Intelligence Report
========================================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This email contains 28 comprehensive reports covering:

🎯 CORE ANALYTICS (6)
- MEGA Analysis (cross-database)
- Tech Trend Scoring
- Top 10 Tech Trends
- Papers ↔ Funding Correlations
- Dark Horses Detection
- Entity Resolution

🚀 ADVANCED ANALYTICS (3)
- Special Sectors (14 critical sectors)
- Early-Stage Deep Dive
- Global Energy Map

🤖 ML ANALYTICS (1)
- Causal Insights ML (Sklearn, Clustering, NLP, Forecast)

🧠 NEW: ADVANCED ML ANALYTICS (5) ⭐
1. Jobs Intelligence - NLP analysis of 8,613 global jobs
   • Skills demand by country
   • Remote vs On-site trends
   • Seniority demand
   • Tech stack patterns

2. Sentiment Analysis - Hype vs Substance
   • Research papers sentiment
   • HackerNews community sentiment
   • Most hyped vs substantive topics

3. Anomaly Detection - Growth Explosions
   • GitHub repos growing >400%
   • Funding spikes (10x normal)
   • Paper publication surges
   • Z-score & Isolation Forest ML

4. Time Series Advanced - ARIMA Forecasting
   • 3-month predictions for GitHub, Funding, Papers
   • Trend analysis (GROWING/DECLINING)
   • Technologies to watch

5. Startup Pattern Matching - Find Next Unicorns
   • Similar to Stripe, Airbnb, OpenAI, Figma
   • K-Means clustering
   • Investment recommendations

🔮 AI-POWERED (1)
- NLG Playbooks (Gemini AI narratives)

💡 INTELLIGENCE ANALYTICS (6)
- Career Trends Predictor
- Capital Flow Predictor
- Expansion Location Analyzer
- Weekly Insights Generator
- Dying Sectors Detector
- Dark Horses Intelligence

🌍 SOCIOECONOMIC INTELLIGENCE (3)
- Best Cities for Tech Talent (INSEAD methodology)
- Remote Work Quality Index (Nomad List + Numbeo)
- Innovation Hubs Ranking (WIPO GII)

🚺 WOMEN, SECURITY & SOCIAL (3)
- Women Global Analysis
- Security Intelligence
- Social Intelligence

📊 DATA SOURCES:
- 40+ international sources
- 8,613 global jobs
- 62 countries, 577 cities
- 1.5M+ database records

All reports attached as TXT files.
All data exported as CSV files.

---
Generated by Sofia Pulse Intelligence System
🤖 Powered by Claude Sonnet 4.5
"""
    return body

def attach_file(msg, filepath):
    """Attach a file to email"""
    if not os.path.exists(filepath):
        return False

    filename = os.path.basename(filepath)

    try:
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)
        return True

    except Exception as e:
        print(f"⚠️  Could not attach {filename}: {e}")
        return False

def send_email():
    """Send email with all reports"""
    print("📧 Preparing MEGA email...")
    print()

    # Create message
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = EMAIL_TO
    msg['Subject'] = f"Sofia Pulse - Daily Intelligence Report ({datetime.now().strftime('%Y-%m-%d')})"

    # Body
    body = create_email_body()
    msg.attach(MIMEText(body, 'plain'))

    # Attach TXT reports
    print("📄 Attaching TXT reports...")
    attached_txt = 0
    for report in REPORTS:
        if attach_file(msg, report):
            attached_txt += 1
            print(f"  ✅ {os.path.basename(report)}")
        else:
            print(f"  ⚠️  {os.path.basename(report)} (not found)")

    print()
    print(f"📊 Attached {attached_txt}/{len(REPORTS)} TXT reports")
    print()

    # Attach CSVs
    print("📊 Attaching CSV files...")
    attached_csv = 0
    for csv in CSV_REPORTS:
        if attach_file(msg, csv):
            attached_csv += 1
            print(f"  ✅ {os.path.basename(csv)}")

    print()
    print(f"📊 Attached {attached_csv}/{len(CSV_REPORTS)} CSV files")
    print()

    # Send
    print("📨 Sending email...")
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)

        text = msg.as_string()
        server.sendmail(SMTP_USER, EMAIL_TO, text)
        server.quit()

        print()
        print("✅ Email sent successfully!")
        print(f"   To: {EMAIL_TO}")
        print(f"   TXT reports: {attached_txt}")
        print(f"   CSV files: {attached_csv}")
        print()

        return True

    except Exception as e:
        print()
        print(f"❌ Email failed: {e}")
        print()
        return False

if __name__ == '__main__':
    success = send_email()

    # Send WhatsApp notification
    if success:
        try:
            import sys
            sys.path.insert(0, 'scripts/utils')

            from whatsapp_notifier import WhatsAppNotifier
            whatsapp = WhatsAppNotifier()

            message = f"""✅ Email Sent!

📧 Daily Intelligence Report
📄 28 TXT reports
📊 {len(CSV_REPORTS)} CSV files

Check your inbox!"""

            whatsapp.send(message)
            print("📱 WhatsApp notification sent")

        except Exception as e:
            print(f"⚠️  WhatsApp notification failed: {e}")

    sys.exit(0 if success else 1)
