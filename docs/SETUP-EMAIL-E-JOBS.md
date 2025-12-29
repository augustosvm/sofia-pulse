# 📧 Sofia Pulse - Setup de Email e Jobs

**Criado**: 2025-11-18
**Para**: Envio automático de insights por email + Coleta de vagas tech

---

## 🎯 O Que Foi Adicionado

### 1. **Email Automático de Insights**
   - Envia insights geo-localizados por email
   - Anexa arquivos CSV/JSON de dados RAW
   - Você pode pegar os CSVs e mandar pra outra IA se quiser

### 2. **Collector de Jobs**
   - Indeed (Brasil, USA, Europa)
   - LinkedIn Jobs API
   - AngelList/Wellfound (startups)
   - Dados por país e setor

### 3. **Universidades Brasileiras**
   - Mapeamento de 17 universidades top
   - Expertises por universidade (Agro-tech, AI, Fintech, etc)
   - Casos de uso: Recrutamento, Job Seeking, Investidores

---

## 📧 SETUP DE EMAIL

### Passo 1: Configurar .env

Adicione no arquivo `.env`:

```bash
# Email Configuration
EMAIL_TO=seu-email@example.com
EMAIL_FROM=sofia-pulse@seu-dominio.com

# SMTP (Gmail exemplo)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASS=sua-senha-app-aqui
```

### Passo 2: Criar App Password (Gmail)

Se usar Gmail, você **NÃO PODE** usar sua senha normal. Precisa de "App Password":

1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione "Mail" e "Other (Custom name)"
3. Digite: "Sofia Pulse"
4. Clique "Generate"
5. Copie a senha de 16 caracteres (ex: `abcd efgh ijkl mnop`)
6. Cole no `.env` como `SMTP_PASS=abcdefghijklmnop` (sem espaços)

### Passo 3: Testar Email

```bash
# Executar script de email
bash send-insights-email.sh
```

**O que ele faz**:
1. ✅ Gera insights geo-localizados
2. ✅ Exporta dados RAW (CSV/JSON):
   - `funding_rounds_30d.csv`
   - `startups_recent.csv`
   - `papers_30d.csv`
   - `market_b3_30d.csv`
   - `market_nasdaq_30d.csv`
   - `ipo_calendar.csv`
   - `jobs_30d.csv`
   - `summary_by_country.json`
3. ✅ Envia email com insights + anexos
4. ✅ Você recebe email com tudo

---

## 💼 SETUP DE JOBS COLLECTOR

### Passo 1: Criar Tabela no Banco

```bash
psql -U sofia -d sofia_db -f db/migrations/008_create_jobs_table.sql
```

### Passo 2: Configurar LinkedIn API (OPCIONAL)

Se quiser coletar vagas do LinkedIn, precisa de API key:

1. Acesse: https://www.linkedin.com/developers/
2. Crie um app
3. Pegue o Access Token
4. Adicione no `.env`:

```bash
LINKEDIN_API_KEY=seu-token-aqui
```

**Nota**: LinkedIn API é PAGA e difícil de conseguir. Recomendo usar só Indeed e AngelList.

### Passo 3: Adicionar no package.json

Adicione os scripts no `package.json`:

```json
{
  "scripts": {
    "collect:jobs": "tsx collectors/jobs-collector.ts",
    "collect:jobs:brazil": "tsx collectors/jobs-collector.ts --country=Brasil",
    "collect:jobs:usa": "tsx collectors/jobs-collector.ts --country=USA"
  }
}
```

### Passo 4: Testar Collector

```bash
# Coletar vagas (Brasil + USA)
npm run collect:jobs

# Ou só Brasil
npm run collect:jobs:brazil
```

**Output esperado**:
```
🔍 Coletando vagas de emprego...

📊 Indeed Brasil...
  ✅ Indeed Brasil (software engineer): 45 vagas
  ✅ Indeed Brasil (desenvolvedor): 38 vagas
  ✅ Indeed Brasil (data scientist): 12 vagas

📊 Indeed USA...
  ✅ Indeed USA (software engineer): 67 vagas

📊 Total coletado: 162 vagas

📍 Por País:
  Brasil: 95 vagas
  USA: 67 vagas

💼 Por Setor:
  Software Engineering: 58 vagas
  Backend: 32 vagas
  Frontend: 28 vagas
  AI/ML: 15 vagas
```

---

## 🎓 UNIVERSIDADES BRASILEIRAS

### Arquivo de Dados

**Localização**: `data/brazilian-universities.json`

**Conteúdo**:
- 17 universidades top do Brasil
- Expertises de cada universidade
- Setores → Universidades
- Casos de uso (Recrutamento, Investors, etc)

### Exemplos de Uso

#### 1. **Recrutamento** - Achar profissionais por expertise

```
Preciso de engenheiro Agro-tech:
→ USP (ESALQ), Unicamp, UNESP, UFRGS

Preciso de especialista em AI/ML:
→ USP, UFMG, UFRGS, PUC-Rio, Insper, UFABC

Preciso de profissional Fintech:
→ Insper, FGV, USP
```

#### 2. **Job Seekers** - Profissionais acham empresas

```
Formado em ITA (Aerospace):
→ Embraer, Defense Tech startups, Aerospace companies

Formado em UFMG (AI/ML):
→ Google Brasil, Sympla, Hotmart, AI startups MG

Formado em UFPE (Software Engineering):
→ Porto Digital, In Loco, Neoway
```

#### 3. **Investidores** - Ecossistemas de inovação

```
UFMG → Ecossistema MG:
- Akwan (vendida pro Google)
- Sympla
- Hotmart

ITA → Ecossistema Aerospace:
- Embraer
- Buscapé
- Peixe Urbano
```

### Query SQL para Cruzar Dados

```sql
-- Vagas em setores onde USP tem expertise
SELECT j.title, j.company, j.location, j.sector
FROM sofia.jobs j
WHERE j.country = 'Brasil'
  AND j.sector IN ('Agro-tech', 'AI/ML', 'Biotechnology', 'Computer Science')
  AND j.posted_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY j.posted_date DESC;
```

---

## 🔄 CRONTAB ATUALIZADO

Adicione no crontab para automatizar:

```bash
# Jobs Collector - 20:00 UTC (Diário)
0 20 * * * cd /home/ubuntu/sofia-pulse && npm run collect:jobs >> /var/log/sofia-jobs.log 2>&1

# Email de Insights - 23:00 UTC (Seg-Sex, após insights)
0 23 * * 1-5 cd /home/ubuntu/sofia-pulse && bash send-insights-email.sh >> /var/log/sofia-email.log 2>&1
```

**Cronograma Completo Agora**:
```
20:00 UTC - Jobs Collector (Diário)
21:00 UTC - Finance B3 (Seg-Sex)
21:05 UTC - Finance NASDAQ (Seg-Sex)
21:10 UTC - Finance Funding (Diário)
22:00 UTC - Premium Insights (Seg-Sex)
23:00 UTC - Email de Insights (Seg-Sex)
```

---

## 📊 DADOS QUE VOCÊ RECEBE NO EMAIL

### Insights (TXT/MD):
- 🌍 Mapa Global da Inovação (por continente)
- 🎯 Especialização Regional
- 🔥 Países em Destaque
- 💰 Próximos IPOs
- 📊 Performance de Mercado
- 🤖 Resumo Executivo (Gemini AI)

### Dados RAW (CSV/JSON):

#### `funding_rounds_30d.csv`:
```csv
country,sector,amount_usd,round_type,company,announced_date
Brasil,Agro-tech,50000000,Series A,AgroTech XYZ,2025-11-15
USA,AI/ML,120000000,Series B,AI Company,2025-11-12
```

#### `startups_recent.csv`:
```csv
country,sector,founded_year,employees,total_funding_usd,name
Brasil,Fintech,2024,45,15000000,Fintech ABC
```

#### `papers_30d.csv`:
```csv
title,authors,published_date,categories,url
"AI for Agriculture",John Doe (USP),2025-11-10,cs.AI,arxiv.org/...
```

#### `jobs_30d.csv`:
```csv
country,sector,title,company,location,posted_date,url
Brasil,AI/ML,Machine Learning Engineer,Nubank,São Paulo,2025-11-17,indeed.com/...
```

#### `summary_by_country.json`:
```json
{
  "funding_by_country": [
    {"country": "Brasil", "deals": 25, "total_usd": 450000000},
    {"country": "USA", "deals": 120, "total_usd": 2500000000}
  ],
  "startups_by_country": [
    {"country": "Brasil", "count": 45, "sector": "Fintech"},
    {"country": "Brasil", "count": 32, "sector": "Agro-tech"}
  ]
}
```

---

## 🎯 CASOS DE USO PARA VENDER NO BRASIL

### 1. **Para Investidores Procurando Empresas**

**Problema**: Onde investir no Brasil?

**Solução**:
```
Email diário com:
- Startups brasileiras recebendo funding por setor
- Setores em alta (Agro-tech, Fintech, Ed-tech)
- Universidades gerando talentos nessas áreas
- IPOs futuros na B3

Dados prontos:
- funding_rounds_30d.csv (filtrar country=Brasil)
- startups_recent.csv (filtrar country=Brasil)
- ipo_calendar.csv (filtrar exchange=B3)
```

### 2. **Para Empresas Procurando Investidores**

**Problema**: Quais VCs estão investindo na minha área?

**Solução**:
```
Email mostra:
- Rodadas de investimento por setor no Brasil
- VCs ativos (extrair de funding_rounds)
- Ticket médio por setor

Query SQL:
SELECT sector, AVG(amount_usd) as avg_ticket,
       COUNT(*) as deals
FROM sofia.funding_rounds
WHERE country = 'Brasil'
  AND announced_date >= NOW() - INTERVAL '90 days'
GROUP BY sector;
```

### 3. **Para Empresas Recrutando Profissionais**

**Problema**: Onde achar engenheiro de Agro-tech no Brasil?

**Solução**:
```
Cruzar dados:
1. Universidades expertise em Agro-tech:
   → USP (ESALQ), Unicamp, UNESP, UFRGS

2. Vagas abertas em Agro-tech:
   → jobs_30d.csv (filtrar sector=Agro-tech, country=Brasil)

3. Profissionais potenciais:
   → Alumni dessas universidades
   → Pessoas trabalhando nas empresas listadas em jobs
```

### 4. **Para Profissionais Procurando Emprego**

**Problema**: Quais empresas contratam na minha área?

**Solução**:
```
Email mostra:
- Vagas abertas por setor e cidade
- Empresas mais contratando
- Salto entre cidades (remoto vs presencial)

Query SQL:
SELECT company, COUNT(*) as vagas_abertas,
       SUM(CASE WHEN remote THEN 1 ELSE 0 END) as remotas
FROM sofia.jobs
WHERE country = 'Brasil'
  AND sector = 'AI/ML'
  AND posted_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY company
ORDER BY vagas_abertas DESC;
```

---

## 🐛 Troubleshooting

### Email não envia

```bash
# Verificar se SMTP está configurado
grep SMTP .env

# Testar SMTP manualmente
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('seu-email@gmail.com', 'sua-senha-app')
print('✅ SMTP OK')
server.quit()
"
```

### Jobs collector não funciona

```bash
# Verificar se tabela existe
psql -U sofia -d sofia_db -c "SELECT COUNT(*) FROM sofia.jobs;"

# Re-criar tabela se necessário
psql -U sofia -d sofia_db -f db/migrations/008_create_jobs_table.sql
```

### Indeed bloqueou scraping

Indeed pode bloquear se fizer muitos requests. Soluções:

1. **Aumentar delay entre requests** (já tem 2s no código)
2. **Usar proxy rotativo** (adicionar no axios config)
3. **Usar API paga do Indeed** (mais confiável)

---

## 📈 Próximos Passos

1. ✅ Configure email no `.env`
2. ✅ Teste envio: `bash send-insights-email.sh`
3. ✅ Crie tabela jobs: `psql -U sofia -d sofia_db -f db/migrations/008_create_jobs_table.sql`
4. ✅ Teste collector: `npm run collect:jobs`
5. ✅ Adicione ao crontab: `bash install-crontab.sh` (atualizar)
6. ✅ Receba email diário com insights + dados

---

## 🇧🇷 Foco Brasil - Resumo

Tudo configurado para focar no mercado brasileiro:

**Dados Coletados**:
- ✅ Funding rounds no Brasil
- ✅ Startups brasileiras por setor
- ✅ Papers de universidades brasileiras (USP, Unicamp, etc)
- ✅ Vagas tech no Brasil (Indeed)
- ✅ IPOs futuros B3
- ✅ Performance de ações B3

**Universidades Mapeadas**:
- ✅ 17 universidades top
- ✅ Expertises detalhadas
- ✅ Empresas fundadas por alumni
- ✅ Setores de excelência

**Casos de Uso**:
- ✅ Investidores → Achar startups
- ✅ Startups → Achar investidores
- ✅ Empresas → Recrutar profissionais
- ✅ Profissionais → Achar vagas

**Email Automático**:
- ✅ Insights prontos para copiar
- ✅ CSVs para análise customizada
- ✅ Você pode mandar pra outra IA

---

**Criado para facilitar sua vida - todos os scripts prontos!**

**v1.0** - 2025-11-18
