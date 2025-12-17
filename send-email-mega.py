#!/usr/bin/env python3
"""
Sofia Pulse - MEGA Email Sender
Sends comprehensive email with ALL reports and CSVs
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
import glob
import sys

# WhatsApp notifications
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', 'utils'))
try:
    from whatsapp_notifier import WhatsAppNotifier
    whatsapp = WhatsAppNotifier()
except:
    whatsapp = None

# Load environment variables
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')
EMAIL_TO = os.getenv('EMAIL_TO')

if not SMTP_USER or not SMTP_PASS:
    print("❌ SMTP_USER ou SMTP_PASS não configurados")
    sys.exit(1)

msg = MIMEMultipart()
msg['From'] = SMTP_USER
msg['To'] = EMAIL_TO
msg['Subject'] = f"🌍 Sofia Pulse MEGA INTELLIGENCE REPORT - {datetime.now().strftime('%Y-%m-%d')}"

body = f"""SOFIA PULSE - MEGA INTELLIGENCE REPORT
{'='*80}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Recipient: {EMAIL_TO}

{'='*80}

🎯 ESTE É O RELATÓRIO MAIS COMPLETO DO SOFIA PULSE!

Combina dados de 30+ fontes e 150,000+ registros em análises cross-database.

{'='*80}

📊 DADOS COLETADOS (30+ Fontes):

Tech Trends & Open Source:
• GitHub Trending (53 tecnologias, 10k+ repos)
• HackerNews (top stories)
• Reddit Tech (6 subreddits)
• NPM Stats (30+ packages JavaScript)
• PyPI Stats (26+ packages Python)

Research & Academia:
• ArXiv AI Papers (machine learning, NLP, computer vision)
• OpenAlex Research (global publications)
• Asia Universities (China, Japan, Korea, Singapore)
• NIH Grants (biomedical research funding)

Funding & Finance:
• Venture Capital Funding Rounds (Seed, Series A-E)
• B3 Stocks (Brazilian market)
• NASDAQ (US tech stocks)
• HKEX IPOs (Hong Kong listings)
• IPO Calendar (upcoming listings)

Patents:
• EPO Patents (European Patent Office)
• WIPO CN Patents (Chinese patents via WIPO)

🔥 Critical Sectors (NEW!):
• 🔒 Cybersecurity (CVEs, Breaches, Security Advisories - NVD, GitHub, CISA)
• 🚀 Space Industry (Launches, Missions, Contracts - SpaceX, Blue Origin, etc)
• ⚖️  AI Regulation (EU AI Act, LGPD, US Executive Orders, China, UK, California)

Geopolitics:
• GDELT Events (global political, economic, social events)

🌍 Global Economy (NEW!):
• Socioeconomic Indicators (World Bank - 56 indicators, 200+ countries)
  - Economy: GDP, PIB per capita, Unemployment, Inflation, Gini, Debt, Reserves
  - Poverty: Extreme poverty, National poverty lines
  - Demographics: Fertility, Urbanization, Population growth
  - Health: Life expectancy, Mortality, Diseases, Resources
  - Education: Literacy, Enrollment, Completion rates
  - Environment: CO2, Renewables, Forests, Air pollution
  - Technology: Internet, Mobile, Broadband, R&D investment
  - Infrastructure: Electricity, Water, Sanitation, Roads
• Electricity Consumption (EIA + OWID - 239 countries)
• Port Traffic (World Bank - Global container TEUs)
• Commodity Prices (Oil, Gold, Copper, Wheat, Lithium, etc)
• Semiconductor Sales (WSTS/SIA - Global chip sales)
• Energy Global Data (Renewables capacity by country)

Industry Specific:
• Cardboard Production (proxy for e-commerce)
• AI Companies (major players and startups)

{'='*80}

📈 ANÁLISES INCLUÍDAS (23 Relatórios):

🆕 MEGA Analysis:
• Cross-database comprehensive analysis
• Combines ALL 30+ data sources
• Socioeconomic + Tech + Funding + Critical Sectors
• GDP per capita vs R&D investment correlations
• Fertility vs Urbanization patterns
• Country rankings across multiple dimensions

Core Analytics:
• Tech Trend Score (ranking completo de tecnologias)
• Top 10 Tech Trends (semanal)
• Correlações Papers ↔ Funding (lag temporal 6-12 meses)
• Dark Horses Report (oportunidades escondidas)
• Entity Resolution (fuzzy matching researchers → companies)

Advanced Analytics:
• Special Sectors Analysis (14 setores críticos)
  - Cybersecurity, Space, Robotics, AI Regulation, Quantum Computing
  - Defense Tech, EVs/Batteries, Autonomous Driving, Smartphones
  - Edge AI, Renewable Energy, Nuclear, Energy Storage, Databases
• Early-Stage Deep Dive (Seed/Angel <$10M)
  - Cross-reference: Funding → Papers → Universities → Tech Stack → Patents
  - Geographic hubs (emerging markets outside USA)
  - Top 20 seed deals with full context
• Global Energy Map (200+ countries)
  - Renewable capacity (Solar, Wind, Hydro, Nuclear)
  - Energy mix by country
  - Top 20 leaders in renewables

AI-Powered:
• NLG Playbooks (Gemini AI - narrativas prontas para publicação)

{'='*80}

📁 ANEXOS:

📄 Relatórios Completos (23 TXT):

  🌍 MEGA Analysis:
  • mega-analysis.txt - Análise cross-database completa

  📊 Core Analytics (5):
  • sofia-complete-report.txt
  • top10-tech-trends.txt
  • correlations-papers-funding.txt
  • dark-horses-report.txt
  • entity-resolution.txt

  🎯 Advanced Analytics (3):
  • special-sectors-analysis.txt (20 setores!)
  • early-stage-deep-dive.txt
  • energy-global-map.txt

  🤖 ML Analytics (1):
  • causal-insights-ml.txt

  🔮 AI-Powered (1):
  • nlg-playbooks-gemini.txt (se Gemini configurado)

  🧠 Intelligence Analytics (6) - PREDICTIVE:
  • career-trends-predictor.txt (prediz skills antes das empresas)
  • capital-flow-predictor.txt (prediz setores antes dos VCs)
  • expansion-locations-analyzer.txt (melhores cidades para abrir filiais)
  • weekly-insights-generator.txt (top 3 topics para colunistas TI)
  • dying-sectors-detector.txt (tecnologias em declínio terminal)
  • dark-horses-intelligence.txt (oportunidades em stealth mode)

  🌍 Socioeconomic Intelligence (6) - GLOBAL RANKINGS:
  • best-cities-tech-talent.txt (INSEAD Global Talent Index)
  • remote-work-quality-index.txt (Nomad List + Numbeo QoL)
  • innovation-hubs-ranking.txt (WIPO Global Innovation Index)
  • startup-founders-best-countries.txt (World Bank Ease of Doing Business)
  • digital-nomad-index.txt (Nomad List methodology)
  • stem-education-leaders.txt (OECD PISA inspired)

📊 Dados RAW (CSVs):
  Tech:
  • github_trending.csv
  • npm_stats.csv, pypi_stats.csv

  Finance:
  • funding_30d.csv

  Critical Sectors:
  • cybersecurity_30d.csv
  • space_launches.csv
  • ai_regulation.csv

  Geopolitics:
  • gdelt_events_30d.csv

  Global Economy:
  • socioeconomic_brazil.csv (Brasil 2015-2024)
  • socioeconomic_top_gdp.csv (Top 20 PIB per capita)
  • electricity_consumption.csv
  • commodity_prices.csv
  • + outros...

{'='*80}

📈 ESTATÍSTICAS:

Total de registros analisados: ~150,000+
Fontes de dados: 30+
Países cobertos: 200+
Período temporal: 2015-2024
Atualização: Diária (automática via crontab)

{'='*80}

🎯 COMO USAR:

1. Leia o MEGA Analysis primeiro (visão geral completa)
2. Aprofunde em setores específicos:
   - Special Sectors para Cybersecurity, Space, etc
   - Early-Stage Deep Dive para startups promissoras
   - Energy Global Map para panorama energético mundial
3. Use CSVs para análises customizadas no Excel/Python
4. Narrativas prontas em NLG Playbooks (se Gemini configurado)

{'='*80}

Veja os anexos abaixo.

Augusto VM
Sofia Pulse Intelligence System
"""

msg.attach(MIMEText(body, 'plain', 'utf-8'))

# Attach reports (16 total: 10 core/advanced/ML + 6 intelligence)
reports = [
    # MEGA Analysis
    ('analytics/mega-analysis-latest.txt', 'MEGA-ANALYSIS.txt'),

    # Core Analytics (4)
    ('analytics/top10-latest.txt', 'top10-tech-trends.txt'),
    ('analytics/correlation-latest.txt', 'correlations-papers-funding.txt'),
    ('analytics/dark-horses-latest.txt', 'dark-horses-report.txt'),
    ('analytics/entity-resolution-latest.txt', 'entity-resolution.txt'),

    # Advanced Analytics (3)
    ('analytics/special-sectors-latest.txt', 'special-sectors-analysis.txt'),
    ('analytics/early-stage-latest.txt', 'early-stage-deep-dive.txt'),
    ('analytics/energy-global-map-latest.txt', 'energy-global-map.txt'),

    # ML Analytics (1)
    ('analytics/causal-insights-latest.txt', 'causal-insights-ml.txt'),

    # AI-Powered (1)
    ('analytics/playbook-latest.txt', 'nlg-playbooks-gemini.txt'),

    # Intelligence Analytics (6) - PREDICTIVE
    ('analytics/career-trends-latest.txt', 'career-trends-predictor.txt'),
    ('analytics/capital-flow-latest.txt', 'capital-flow-predictor.txt'),
    ('analytics/expansion-locations-latest.txt', 'expansion-locations-analyzer.txt'),
    ('analytics/weekly-insights-latest.txt', 'weekly-insights-generator.txt'),
    ('analytics/dying-sectors-latest.txt', 'dying-sectors-detector.txt'),
    ('analytics/dark-horses-intelligence-latest.txt', 'dark-horses-intelligence.txt'),

    # Socioeconomic Intelligence (6) - GLOBAL RANKINGS
    ('analytics/best-cities-tech-talent-latest.txt', 'best-cities-tech-talent.txt'),
    ('analytics/remote-work-quality-latest.txt', 'remote-work-quality-index.txt'),
    ('analytics/innovation-hubs-latest.txt', 'innovation-hubs-ranking.txt'),
    ('analytics/startup-founders-latest.txt', 'startup-founders-best-countries.txt'),
    ('analytics/digital-nomad-latest.txt', 'digital-nomad-index.txt'),
    ('analytics/stem-education-latest.txt', 'stem-education-leaders.txt'),

    # NEW: Women, Security & Social Intelligence (3)
    ('analytics/women-global-analysis.txt', 'women-global-analysis.txt'),
    ('analytics/security-intelligence-report.txt', 'security-intelligence-report.txt'),
    ('analytics/social-intelligence-report.txt', 'social-intelligence-report.txt'),

    # NEW: Brazil & Global Specialized (7)
    ('analytics/brazil-economy-intelligence.txt', 'brazil-economy-intelligence.txt'),
    ('analytics/global-health-humanitarian.txt', 'global-health-humanitarian.txt'),
    ('analytics/trade-agriculture-intelligence.txt', 'trade-agriculture-intelligence.txt'),
    ('analytics/tourism-intelligence.txt', 'tourism-intelligence.txt'),
    ('analytics/latam-intelligence.txt', 'latam-intelligence.txt'),
    ('analytics/olympics-sports-intelligence.txt', 'olympics-sports-intelligence.txt'),
    ('analytics/cross-data-correlations.txt', 'cross-data-correlations.txt'),
]

attached_reports = 0
for file_path, file_name in reports:
    if os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                attachment = MIMEApplication(f.read(), _subtype='txt')
                attachment.add_header('Content-Disposition', 'attachment', filename=file_name)
                msg.attach(attachment)
                attached_reports += 1
                print(f"   ✅ Anexado: {file_name}")
        except Exception as e:
            print(f"   ⚠️  Erro ao anexar {file_name}: {e}")

# Attach CSVs
attached_csvs = 0
for csv_file in glob.glob('data/exports/*.csv'):
    try:
        with open(csv_file, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='csv')
            filename = os.path.basename(csv_file)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
            attached_csvs += 1
            print(f"   ✅ Anexado: {filename}")
    except Exception as e:
        print(f"   ⚠️  Erro ao anexar CSV: {e}")

print("")
print(f"📊 Total anexos: {attached_reports} relatórios + {attached_csvs} CSVs")
print("")

# Send email
try:
    print("📧 Conectando ao servidor SMTP...")
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)

    print("📧 Enviando email...")
    text = msg.as_string()
    server.sendmail(SMTP_USER, EMAIL_TO, text)
    server.quit()

    print("✅ Email enviado com sucesso!")
    print(f"📧 Destinatário: {EMAIL_TO}")
    print(f"📄 Relatórios: {attached_reports}")
    print(f"📊 CSVs: {attached_csvs}")

    # Send WhatsApp notification
    if whatsapp:
        whatsapp.report_sent(attached_reports, attached_csvs, EMAIL_TO)
        print("📱 WhatsApp notification sent")

except Exception as e:
    print(f"❌ Erro ao enviar email: {e}")

    # Send WhatsApp alert on failure
    if whatsapp:
        whatsapp.analytics_error("Email Sender", str(e))

    import traceback
    traceback.print_exc()
    sys.exit(1)
