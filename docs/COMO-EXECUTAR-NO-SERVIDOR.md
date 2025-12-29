# 🚀 Sofia Pulse - Como Executar no Servidor

**Última Atualização**: 2025-11-18
**Branch**: `claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE`

---

## 📦 O QUE FOI ADICIONADO HOJE

### ✅ Premium Insights v2.0 (GEO-LOCALIZADOS)
- Análise por continente/país
- Universidades e suas expertises
- Especialização regional (Brasil=Agro-tech, USA=AI, etc)
- IPO Calendar (NASDAQ, B3, SEC)
- Narrativas prontas para copiar (Gemini AI)
- Fix: Bug de duplicatas nas Top 5 ações

### ✅ Email Automático
- Envia insights + dados RAW por email
- Anexos CSV/JSON para análise externa
- Configuração via SMTP (Gmail, etc)
- Você pode pegar os dados e mandar pra outra IA

### ✅ Jobs Collector
- Coleta vagas do Indeed (Brasil, USA)
- LinkedIn API (opcional)
- AngelList/Wellfound (startups)
- Classificação por país e setor

### ✅ Universidades Brasileiras
- 17 universidades mapeadas
- Expertises de cada uma
- Casos de uso: Recrutamento, Investimento

---

## 🎯 EXECUTAR NO SERVIDOR (PASSO A PASSO)

### 1️⃣ PUXAR ATUALIZAÇÕES

```bash
cd /home/ubuntu/sofia-pulse  # ou seu diretório
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
```

### 2️⃣ TESTAR PREMIUM INSIGHTS V2.0

```bash
# Teste completo (valida tudo)
bash test-premium-insights-v2.sh
```

**Isso vai**:
- ✅ Verificar arquivos
- ✅ Testar venv Python
- ✅ Validar conexão PostgreSQL
- ✅ Executar geração de insights
- ✅ Mostrar preview dos resultados

### 3️⃣ CONFIGURAR EMAIL (SE QUISER)

```bash
# Instalador interativo
bash setup-email-jobs-complete.sh
```

**Isso vai pedir**:
1. Seu email para receber insights
2. Configurar .env com SMTP

**IMPORTANTE**: Para Gmail, você precisa criar "App Password":
- https://myaccount.google.com/apppasswords
- Selecione "Mail" → "Other" → "Sofia Pulse"
- Cole a senha de 16 caracteres no .env como SMTP_PASS

### 4️⃣ CRIAR TABELA DE JOBS

```bash
psql -U sofia -d sofia_db -f db/migrations/008_create_jobs_table.sql
```

### 5️⃣ TESTAR JOBS COLLECTOR

```bash
# Adicionar scripts ao package.json primeiro
npm install  # se precisar

# Testar collector (Brasil + USA)
npm run collect:jobs || npx tsx collectors/jobs-collector.ts
```

### 6️⃣ TESTAR EMAIL

```bash
# Primeiro configure SMTP_PASS no .env
nano .env  # ou vim .env

# Adicione:
# SMTP_PASS=sua-senha-app-de-16-caracteres

# Depois teste envio
bash send-insights-email.sh
```

**Você deve receber email com**:
- latest-geo.txt (insights prontos)
- funding_rounds_30d.csv
- startups_recent.csv
- papers_30d.csv
- jobs_30d.csv
- market_b3_30d.csv
- market_nasdaq_30d.csv
- ipo_calendar.csv
- summary_by_country.json

### 7️⃣ INSTALAR CRONTAB (AUTOMATIZAR)

```bash
crontab -e
```

**Adicione**:

```bash
# Sofia Pulse - Automações Completas
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAILTO=""

# Jobs Collector - 20:00 UTC (Diário)
0 20 * * * cd /home/ubuntu/sofia-pulse && npm run collect:jobs >> /var/log/sofia-jobs.log 2>&1

# Finance B3 - 21:00 UTC (Seg-Sex)
0 21 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:brazil >> /var/log/sofia-finance-b3.log 2>&1

# Finance NASDAQ - 21:05 UTC (Seg-Sex)
5 21 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:nasdaq >> /var/log/sofia-finance-nasdaq.log 2>&1

# Funding Rounds - 21:10 UTC (Diário)
10 21 * * * cd /home/ubuntu/sofia-pulse && npm run collect:funding >> /var/log/sofia-finance-funding.log 2>&1

# Premium Insights v2 - 22:00 UTC (Seg-Sex)
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && ./generate-premium-insights-v2.sh >> /var/log/sofia-insights.log 2>&1

# Email de Insights - 23:00 UTC (Seg-Sex)
0 23 * * 1-5 cd /home/ubuntu/sofia-pulse && ./send-insights-email.sh >> /var/log/sofia-email.log 2>&1

# Limpeza de logs - Domingo 05:00 UTC
0 5 * * 0 find /var/log/sofia-*.log -mtime +30 -delete
```

---

## 📊 CRONOGRAMA AUTOMÁTICO

| Horário UTC | Horário BRT | Tarefa | Frequência |
|-------------|-------------|--------|------------|
| **20:00** | 17:00 | 💼 Jobs Collector | Diário |
| **21:00** | 18:00 | 📊 Finance B3 | Seg-Sex |
| **21:05** | 18:05 | 📊 Finance NASDAQ | Seg-Sex |
| **21:10** | 18:10 | 💰 Funding Rounds | Diário |
| **22:00** | 19:00 | 💎 Premium Insights v2 | Seg-Sex |
| **23:00** | 20:00 | 📧 Email com Insights | Seg-Sex |
| **05:00** | 02:00 | 🗑️ Limpeza Logs | Domingo |

---

## 🔍 VERIFICAR SE ESTÁ FUNCIONANDO

### Ver Insights Gerados:

```bash
cat analytics/premium-insights/latest-geo.txt
```

### Ver Logs:

```bash
# Insights
tail -f /var/log/sofia-insights.log

# Email
tail -f /var/log/sofia-email.log

# Jobs
tail -f /var/log/sofia-jobs.log

# Finance
tail -f /var/log/sofia-finance-b3.log
```

### Ver Dados no Banco:

```bash
psql -U sofia -d sofia_db

# No psql:
SELECT COUNT(*) FROM sofia.jobs;
SELECT COUNT(*) FROM sofia.ipo_calendar;
SELECT COUNT(*) FROM sofia.funding_rounds WHERE announced_date >= CURRENT_DATE - INTERVAL '30 days';

# Top 10 vagas recentes Brasil
SELECT title, company, sector, location
FROM sofia.jobs
WHERE country = 'Brasil'
ORDER BY posted_date DESC
LIMIT 10;
```

---

## 📧 EMAIL - COMO USAR OS DADOS

Você vai receber email diário (Seg-Sex às 23:00 UTC / 20:00 BRT) com:

### 1. Insights Prontos (latest-geo.txt)
- Copie e cole em suas análises
- Texto pronto para colunas
- Narrativas geradas por IA

### 2. Dados RAW (CSVs)
- Abra no Excel/Google Sheets
- Ou mande pra outra IA (ChatGPT, Claude, etc) para gerar insights customizados
- Faça suas próprias análises

### 3. Exemplos de Uso dos CSVs

**Para Investidores**:
```csv
funding_rounds_30d.csv
→ Filtrar: country=Brasil, sector=Agro-tech
→ Ver quais startups estão recebendo funding
```

**Para Recrutar**:
```csv
jobs_30d.csv
→ Filtrar: country=Brasil, sector=AI/ML
→ Ver quais empresas estão contratando
→ Cruzar com brazilian-universities.json
→ USP, UFMG, UFRGS têm expertise em AI/ML
```

**Para Job Seekers**:
```csv
jobs_30d.csv
→ Filtrar por setor da sua expertise
→ Ver empresas contratando
→ Filtrar remote=TRUE para vagas remotas
```

---

## 🇧🇷 CASOS DE USO - VENDENDO NO BRASIL

### 1. **Para Investidores Procurando Empresas**

**Dados que você fornece**:
- Startups brasileiras recebendo funding (últimos 30 dias)
- Setores em alta no Brasil
- Universidades gerando talentos nessas áreas

**Como fazer**:
```bash
# Filtrar funding_rounds_30d.csv
country = "Brasil"
→ Mostra todas as rodadas de investimento BR

# Cruzar com startups_recent.csv
→ Detalhes das startups

# Cruzar com brazilian-universities.json
→ Quais universidades têm expertise no setor
```

### 2. **Para Empresas Procurando Investidores**

**Dados que você fornece**:
- Quais VCs estão investindo em cada setor
- Ticket médio por setor
- Setores quentes no Brasil

**Query SQL**:
```sql
SELECT sector,
       COUNT(*) as num_deals,
       AVG(amount_usd) as avg_ticket,
       SUM(amount_usd) as total_invested
FROM sofia.funding_rounds
WHERE country = 'Brasil'
  AND announced_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY sector
ORDER BY total_invested DESC;
```

### 3. **Para Empresas Recrutando Profissionais**

**Dados que você fornece**:
- Universidades com expertise na área desejada
- Alumni dessas universidades
- Onde eles estão trabalhando agora

**Exemplo**:
```
Precisa de engenheiro Agro-tech?

1. Universidades expertise: USP (ESALQ), Unicamp, UNESP
2. Ver jobs_30d.csv: Empresas de Agro-tech contratando
3. Profissionais: Alumni dessas universidades
```

### 4. **Para Profissionais Procurando Emprego**

**Dados que você fornece**:
- Vagas abertas por setor
- Empresas mais contratando
- Salário estimado (se disponível)
- Remote vs Presencial

**Query SQL**:
```sql
SELECT company,
       COUNT(*) as vagas_abertas,
       SUM(CASE WHEN remote THEN 1 ELSE 0 END) as remotas
FROM sofia.jobs
WHERE country = 'Brasil'
  AND sector = 'AI/ML'
  AND posted_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY company
ORDER BY vagas_abertas DESC;
```

---

## 🐛 TROUBLESHOOTING

### "GEMINI_API_KEY não configurada"

```bash
echo 'GEMINI_API_KEY=sua-chave-aqui' >> .env
```

Pegar chave: https://aistudio.google.com/app/apikey

### "Tabela jobs não existe"

```bash
psql -U sofia -d sofia_db -f db/migrations/008_create_jobs_table.sql
```

### "Email não envia"

1. Verificar SMTP_PASS no .env
2. Para Gmail, usar App Password (não senha normal)
3. Testar SMTP:

```bash
python3 <<EOF
import smtplib, os
from dotenv import load_dotenv
load_dotenv()
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASS'))
print('✅ SMTP OK')
server.quit()
EOF
```

### "Indeed bloqueou scraping"

Indeed pode bloquear muitos requests. Soluções:
1. Aumentar delay entre requests (já tem 2s)
2. Executar menos vezes por dia
3. Usar proxy rotativo (avançado)

---

## 📚 DOCUMENTAÇÃO COMPLETA

- **PREMIUM-INSIGHTS-V2-RELEASE.md**: Detalhes da v2.0
- **SETUP-EMAIL-E-JOBS.md**: Setup completo de email e jobs
- **CRONTAB-COMPLETO.md**: Documentação do crontab

---

## ✅ CHECKLIST RÁPIDO

```bash
# 1. Puxar atualizações
git pull

# 2. Testar v2.0
bash test-premium-insights-v2.sh

# 3. Ver insights gerados
cat analytics/premium-insights/latest-geo.txt

# 4. Configurar email (SE QUISER)
bash setup-email-jobs-complete.sh
nano .env  # adicionar SMTP_PASS

# 5. Criar tabela jobs
psql -U sofia -d sofia_db -f db/migrations/008_create_jobs_table.sql

# 6. Testar jobs collector
npx tsx collectors/jobs-collector.ts

# 7. Testar email (SE CONFIGUROU)
bash send-insights-email.sh

# 8. Instalar crontab (AUTOMATIZAR)
crontab -e  # copiar cronograma acima
```

---

## 🎉 PRONTO!

Agora você tem:
- ✅ Insights geo-localizados automáticos
- ✅ Email diário com insights + dados RAW
- ✅ Collector de vagas tech
- ✅ Mapeamento de universidades brasileiras
- ✅ Dados prontos para vender serviços

**Próximo passo**: Receba o email e veja os dados! 📧

---

**v1.0** - 2025-11-18
