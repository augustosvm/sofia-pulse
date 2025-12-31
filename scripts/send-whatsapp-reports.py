#!/usr/bin/env python3
"""
Sofia Pulse - Send Reports via WhatsApp
Sends summary + key insights to WhatsApp after analytics complete
"""

import glob
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.whatsapp_alerts import send_whatsapp_alert


def read_report_summary(report_path, max_lines=30):
    """Read first N lines of report for summary"""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[:max_lines]
            return "".join(lines)
    except Exception as e:
        return f"Error reading {report_path}: {e}"


def send_mega_summary():
    """Send MEGA Analysis summary via WhatsApp"""
    mega_report = "analytics/mega-analysis-latest.txt"

    if os.path.exists(mega_report):
        summary = read_report_summary(mega_report, max_lines=50)
        message = f"""*📊 SOFIA PULSE - MEGA ANALYSIS*

{summary}

---
_Relatório completo no email_
_Total: 23 reports + CSVs_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ MEGA Analysis summary sent to WhatsApp")
        else:
            print("❌ Failed to send MEGA Analysis summary")
    else:
        print("⚠️  MEGA Analysis not found")


def send_top10_trends():
    """Send Top 10 Tech Trends via WhatsApp"""
    top10_report = "analytics/top10-latest.txt"

    if os.path.exists(top10_report):
        summary = read_report_summary(top10_report, max_lines=40)
        message = f"""*🔥 TOP 10 TECH TRENDS*

{summary}

---
_Relatório completo no email_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ Top 10 Trends sent to WhatsApp")
        else:
            print("❌ Failed to send Top 10 Trends")
    else:
        print("⚠️  Top 10 Trends not found")


def send_playbook_summary():
    """Send NLG Playbook (Gemini) via WhatsApp"""
    playbook_report = "analytics/playbook-latest.txt"

    if os.path.exists(playbook_report):
        # Gemini playbook is narrative, send first part
        summary = read_report_summary(playbook_report, max_lines=60)
        message = f"""*🤖 PLAYBOOK GEMINI AI*

{summary}

---
_Playbook completo no email_
_Narrativas prontas para publicação_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ Gemini Playbook sent to WhatsApp")
        else:
            print("❌ Failed to send Gemini Playbook")
    else:
        print("⚠️  Gemini Playbook not found (GEMINI_API_KEY configured?)")


def send_intelligence_summary():
    """Send Intelligence Reports summary via WhatsApp"""

    # Career Trends
    career_report = "analytics/career-trends-latest.txt"
    if os.path.exists(career_report):
        summary = read_report_summary(career_report, max_lines=30)
        message = f"""*🎓 CAREER TRENDS PREDICTOR*

{summary}

---
_Relatório completo no email_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ Career Trends sent to WhatsApp")
        else:
            print("❌ Failed to send Career Trends")

    # Capital Flow
    capital_report = "analytics/capital-flow-latest.txt"
    if os.path.exists(capital_report):
        summary = read_report_summary(capital_report, max_lines=30)
        message = f"""*💰 CAPITAL FLOW PREDICTOR*

{summary}

---
_Relatório completo no email_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ Capital Flow sent to WhatsApp")
        else:
            print("❌ Failed to send Capital Flow")


def send_ml_analytics_summary():
    """Send NEW Advanced ML Analytics summary via WhatsApp"""

    # Jobs Intelligence (NLP)
    jobs_report = "analytics/jobs-intelligence.txt"
    if os.path.exists(jobs_report):
        summary = read_report_summary(jobs_report, max_lines=30)
        message = f"""*💼 JOBS INTELLIGENCE (NLP)*

{summary}

---
_8,613 vagas globais analisadas_
_Skills, Remote, Seniority, Tech Stacks_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ Jobs Intelligence sent to WhatsApp")
        else:
            print("❌ Failed to send Jobs Intelligence")

    # Sentiment Analysis
    sentiment_report = "analytics/sentiment-analysis.txt"
    if os.path.exists(sentiment_report):
        summary = read_report_summary(sentiment_report, max_lines=30)
        message = f"""*📊 SENTIMENT ANALYSIS*

{summary}

---
_Papers: Hype vs Substance_
_HackerNews + Reddit sentiment_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ Sentiment Analysis sent to WhatsApp")
        else:
            print("❌ Failed to send Sentiment Analysis")

    # Anomaly Detection
    anomaly_report = "analytics/anomaly-detection.txt"
    if os.path.exists(anomaly_report):
        summary = read_report_summary(anomaly_report, max_lines=30)
        message = f"""*🚨 ANOMALY DETECTION*

{summary}

---
_Z-score + Isolation Forest ML_
_GitHub/Funding/Papers explosions_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ Anomaly Detection sent to WhatsApp")
        else:
            print("❌ Failed to send Anomaly Detection")

    # Time Series Advanced
    timeseries_report = "analytics/time-series-advanced.txt"
    if os.path.exists(timeseries_report):
        summary = read_report_summary(timeseries_report, max_lines=30)
        message = f"""*📈 TIME SERIES FORECAST (ARIMA)*

{summary}

---
_3-month predictions_
_GitHub, Funding, Papers trends_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ Time Series Forecast sent to WhatsApp")
        else:
            print("❌ Failed to send Time Series Forecast")

    # Startup Pattern Matching
    startup_report = "analytics/startup-pattern-matching.txt"
    if os.path.exists(startup_report):
        summary = read_report_summary(startup_report, max_lines=30)
        message = f"""*🦄 STARTUP PATTERN MATCHING*

{summary}

---
_Similar to: Stripe, Airbnb, OpenAI_
_K-Means clustering_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ Startup Pattern Matching sent to WhatsApp")
        else:
            print("❌ Failed to send Startup Pattern Matching")


def send_socioeconomic_summary():
    """Send Socioeconomic Intelligence summary via WhatsApp"""

    # Best Cities for Tech Talent
    talent_report = "analytics/best-cities-tech-talent-latest.txt"
    if os.path.exists(talent_report):
        summary = read_report_summary(talent_report, max_lines=30)
        message = f"""*💼 BEST CITIES FOR TECH TALENT*

{summary}

---
_Relatório completo no email_
_Metodologia: INSEAD Global Talent Index_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ Tech Talent Cities sent to WhatsApp")
        else:
            print("❌ Failed to send Tech Talent Cities")

    # Innovation Hubs
    innovation_report = "analytics/innovation-hubs-latest.txt"
    if os.path.exists(innovation_report):
        summary = read_report_summary(innovation_report, max_lines=30)
        message = f"""*🔬 INNOVATION HUBS RANKING*

{summary}

---
_Relatório completo no email_
_Metodologia: WIPO Global Innovation Index_
"""
        if send_whatsapp_alert(message, level="INFO"):
            print("✅ Innovation Hubs sent to WhatsApp")
        else:
            print("❌ Failed to send Innovation Hubs")


def send_completion_summary():
    """Send final completion summary with all artifacts"""

    # Count reports
    reports = glob.glob("analytics/*-latest.txt")
    csvs = glob.glob("data/exports/*.csv")

    message = f"""*✅ SOFIA PULSE - ANALYTICS COMPLETE*

*Reports Generated*: {len(reports)}
*CSVs Exported*: {len(csvs)}
*Timestamp*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*📊 Relatórios (28 total)*:

*Core & Advanced (11)*:
• MEGA Analysis
• Sofia Complete Report
• Top 10 Tech Trends
• Correlações Papers ↔ Funding
• Dark Horses Report
• Entity Resolution
• Special Sectors Analysis
• Early-Stage Deep Dive
• Global Energy Map
• Causal Insights ML
• NLG Playbooks (Gemini)

*🧠 NEW: Advanced ML Analytics (5)*:
• Jobs Intelligence (NLP 8,613 vagas)
• Sentiment Analysis (Hype vs Substance)
• Anomaly Detection (Z-score + ML)
• Time Series Advanced (ARIMA)
• Startup Pattern Matching (Unicorns)

*Predictive Intelligence (6)*:
• Career Trends Predictor
• Capital Flow Predictor
• Expansion Location Analyzer
• Weekly Insights Generator
• Dying Sectors Detector
• Dark Horses Intelligence

*Socioeconomic Intelligence (6)*:
• Best Cities for Tech Talent
• Remote Work Quality Index
• Innovation Hubs Ranking
• Best Countries for Startup Founders
• Digital Nomad Index
• STEM Education Leaders

*📧 Email enviado para*: augustosvm@gmail.com

---
_Sofia Pulse Intelligence System_
_Próxima execução: 22:00 UTC / 19:00 BRT_
"""

    if send_whatsapp_alert(message, level="INFO"):
        print("✅ Completion summary sent to WhatsApp")
    else:
        print("❌ Failed to send Completion summary")


def main():
    """Send all report summaries via WhatsApp"""

    print("════════════════════════════════════════════════════════════════")
    print("📱 SOFIA PULSE - SEND REPORTS VIA WHATSAPP")
    print("════════════════════════════════════════════════════════════════")
    print("")

    # 1. Completion summary (overview)
    print("1️⃣  Sending completion summary...")
    send_completion_summary()
    print("")

    # 2. MEGA Analysis (most important)
    print("2️⃣  Sending MEGA Analysis summary...")
    send_mega_summary()
    print("")

    # 3. Top 10 Trends
    print("3️⃣  Sending Top 10 Tech Trends...")
    send_top10_trends()
    print("")

    # 4. Gemini Playbook (if available)
    print("4️⃣  Sending Gemini Playbook...")
    send_playbook_summary()
    print("")

    # 5. NEW: Advanced ML Analytics (5 reports)
    print("5️⃣  Sending Advanced ML Analytics...")
    send_ml_analytics_summary()
    print("")

    # 6. Intelligence summaries (key predictions)
    print("6️⃣  Sending Intelligence summaries...")
    send_intelligence_summary()
    print("")

    # 7. Socioeconomic summaries
    print("7️⃣  Sending Socioeconomic summaries...")
    send_socioeconomic_summary()
    print("")

    print("════════════════════════════════════════════════════════════════")
    print("✅ ALL SUMMARIES SENT TO WHATSAPP")
    print("════════════════════════════════════════════════════════════════")
    print("")
    print("You should have received ~15-18 WhatsApp messages with:")
    print("  • Completion summary (overview)")
    print("  • MEGA Analysis summary")
    print("  • Top 10 Tech Trends")
    print("  • Gemini Playbook (if available)")
    print("  • 5 Advanced ML Analytics (NEW!)")
    print("  • Career Trends + Capital Flow")
    print("  • Tech Talent Cities + Innovation Hubs")
    print("")
    print("Full reports sent via email to: augustosvm@gmail.com")
    print("")


if __name__ == "__main__":
    main()
