#!/usr/bin/env python3
"""
Sofia Pulse - Email Sender
Envia insights e CSVs para augustosvm@gmail.com
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime

# Configurações
EMAIL_TO = os.getenv('EMAIL_TO', 'augustosvm@gmail.com')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'sofia-pulse@tiespecialistas.com')
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', 'augustosvm@gmail.com')
SMTP_PASS = os.getenv('SMTP_PASS', '')

print("📧 Sofia Pulse - Email Sender")
print("=" * 60)
print(f"De: {EMAIL_FROM}")
print(f"Para: {EMAIL_TO}")
print(f"SMTP: {SMTP_HOST}:{SMTP_PORT}")
print()

# Ler insights (v3.0 ou fallback para geo)
insights_file = 'analytics/premium-insights/latest-v3.txt'
if not os.path.exists(insights_file):
    insights_file = 'analytics/premium-insights/latest-geo.txt'

if not os.path.exists(insights_file):
    print("❌ Arquivo de insights não encontrado!")
    exit(1)

with open(insights_file, 'r', encoding='utf-8') as f:
    insights_content = f.read()

version = "v3.0" if "latest-v3" in insights_file else "v2.0"

# Criar mensagem
msg = MIMEMultipart()
msg['From'] = EMAIL_FROM
msg['To'] = EMAIL_TO
msg['Subject'] = f'Sofia Pulse - Premium Insights {version} - {datetime.now().strftime("%Y-%m-%d")}'

# Corpo do email
body = f"""
Olá!

Segue em anexo os **Premium Insights** gerados pelo Sofia Pulse.

📊 **O que você vai encontrar:**

1. **Insights Completos** (latest-geo.txt) - Análise executiva pronta
2. **Dados RAW**:
   - funding_rounds_30d.csv - Rodadas de investimento (últimos 30 dias)
   - market_b3_30d.csv - Ações B3 com melhor performance

Você pode usar os insights prontos ou pegar os CSVs e mandar para outra IA
gerar análises customizadas!

---

📈 **PREVIEW DOS INSIGHTS:**

{insights_content[:800]}

...

[Ver arquivo completo anexado]

---

Gerado automaticamente por Sofia Pulse
Data: {datetime.now().strftime("%Y-%m-%d %H:%M")}
"""

msg.attach(MIMEText(body, 'plain', 'utf-8'))

# Anexar arquivos
attachments = [
    'analytics/premium-insights/latest-v3.txt',
    'analytics/premium-insights/latest-v3.md',
    'analytics/premium-insights/latest-geo.txt',
    'analytics/premium-insights/latest-geo.md',
    'analytics/premium-insights/funding_rounds_30d.csv',
    'analytics/premium-insights/market_b3_30d.csv',
]

print("📎 Anexando arquivos:")
for filepath in attachments:
    if os.path.exists(filepath):
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)
        print(f"   ✅ {filename}")
    else:
        print(f"   ⚠️  {filepath} não encontrado")

# Enviar email
print("\n📤 Enviando email...")

if not SMTP_PASS:
    print("❌ SMTP_PASS não configurado!")
    print("   Configure a senha SMTP no .env")
    exit(1)

try:
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    text = msg.as_string()
    server.sendmail(EMAIL_FROM, EMAIL_TO, text)
    server.quit()

    print("✅ Email enviado com sucesso!")
    print(f"📬 Destinatário: {EMAIL_TO}")
    print(f"📊 Anexos: {len([a for a in attachments if os.path.exists(a)])} arquivos")

except Exception as e:
    print(f"❌ Erro ao enviar email: {e}")
    exit(1)
