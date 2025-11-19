#!/usr/bin/env python3
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
import glob
import sys

# Carregar variáveis de ambiente
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
msg['Subject'] = f"Sofia Pulse COMPLETE Intelligence Report - {datetime.now().strftime('%Y-%m-%d')}"

body = f"""SOFIA PULSE - COMPLETE INTELLIGENCE REPORT
{'='*80}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Recipient: {EMAIL_TO}

{'='*80}

Este relatório contém TODAS as análises:

📊 DADOS COLETADOS:
- GitHub Trending (53 tecnologias)
- HackerNews (3 tecnologias)
- Reddit Tech (6 subreddits)
- NPM Stats (30+ packages)
- PyPI Stats (26+ packages Python)
- GDELT (eventos geopolíticos)
- Papers (ArXiv, OpenAlex)
- Funding Rounds
- B3, NASDAQ
- 🔒 Cybersecurity (CVEs, Breaches, Security Advisories) [NEW!]
- 🚀 Space Industry (Launches, Missions, Contracts) [NEW!]
- ⚖️  AI Regulation (Laws, Policies, Compliance) [NEW!]

📈 ANÁLISES INCLUÍDAS:
- Tech Trend Score (ranking completo)
- Top 10 Tech Trends (semanal)
- Correlações Papers ↔ Funding (lag analysis)
- Dark Horses Report (oportunidades)
- Entity Resolution (fuzzy matching)
- NLG Playbooks (Gemini AI)
- Premium Insights v2.0 (regional + temporal)
- 🔥 Special Sectors Analysis (Cybersecurity, Space, Robotics, AI Regulation, Quantum, Defense) [NEW!]

📁 ANEXOS:
- Relatórios completos (TXT)
- Dados RAW (CSVs)

Veja os anexos abaixo.

{'='*80}
"""

msg.attach(MIMEText(body, 'plain', 'utf-8'))

# Anexar relatórios
reports = [
    ('analytics/sofia-report.txt', 'sofia-complete-report.txt'),
    ('analytics/top10-latest.txt', 'top10-tech-trends.txt'),
    ('analytics/correlation-latest.txt', 'correlations-papers-funding.txt'),
    ('analytics/dark-horses-latest.txt', 'dark-horses-report.txt'),
    ('analytics/entity-resolution-latest.txt', 'entity-resolution.txt'),
    ('analytics/playbook-latest.txt', 'nlg-playbooks-gemini.txt'),
    ('analytics/special-sectors-latest.txt', 'special-sectors-analysis.txt'),
]

attached = 0
for file_path, file_name in reports:
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='txt')
            attachment.add_header('Content-Disposition', 'attachment', filename=file_name)
            msg.attach(attachment)
            attached += 1

# Anexar CSVs
for csv_file in glob.glob('data/exports/*.csv'):
    try:
        with open(csv_file, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='csv')
            filename = os.path.basename(csv_file)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
            attached += 1
    except:
        pass

try:
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.send_message(msg)
    server.quit()
    print(f"✅ Email enviado para {EMAIL_TO}")
    print(f"   {attached} anexos incluídos")
except Exception as e:
    print(f"❌ Erro ao enviar email: {e}")
    sys.exit(1)
