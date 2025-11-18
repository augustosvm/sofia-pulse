# 🤖 CLAUDE - Resumo da Sessão (Continuar Amanhã)

**Data**: 2025-11-18
**Branch**: `claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE`
**Email Configurado**: augustosvm@gmail.com

---

## 🎯 O QUE FOI FEITO HOJE

### ✅ Premium Insights v2.0 - GEO-LOCALIZADOS

**Problema Resolvido**:
- v1.0 estava muito rasa, sem contexto geográfico
- Faltava análise por país/continente
- Duplicatas nas Top 5 ações (WEGE3 5x, NVDA 3x)

**Solução Implementada**:
1. **Análise Geográfica Completa**:
   - Mapeamento de 50+ países para continentes
   - Funding por continente
   - Papers por universidade/país
   - Startups por região

2. **Universidades e Expertises**:
   - 20+ universidades mapeadas (MIT, Stanford, USP, Unicamp, etc)
   - Expertises: MIT=AI, USP=Agro-tech, ITA=Aerospace
   - Extração automática de afiliação dos papers

3. **Especialização Regional**:
   - Brasil: Agro-tech, Fintech, Healthcare, Ed-tech
   - USA: AI, SaaS, Biotech, Space
   - China: AI, Manufacturing, Hardware, E-commerce
   - Europa: Green Tech, Privacy Tech, Mobility
   - Israel: Cybersecurity, Defense Tech, AI

4. **IPO Calendar**:
   - Collector para NASDAQ, B3, SEC/EDGAR
   - Tabela: `sofia.ipo_calendar`
   - Mostra empresas indo a público (próximos 30 dias)

5. **Narrativas IA (Gemini)**:
   - Textos corridos prontos para copiar
   - Gemini 2.5 Pro Preview (~$0.01/análise)
   - 3-4 parágrafos para colunistas

6. **Bug Fix**:
   - Duplicatas nas Top 5 ações corrigido
   - `drop_duplicates(subset='ticker')` antes de `nlargest()`

**Arquivos Criados**:
- `generate-premium-insights-v2.py` (700+ linhas)
- `generate-premium-insights-v2.sh`
- `collectors/ipo-calendar.ts`
- `db/migrations/007_create_ipo_calendar.sql`

---

### ✅ Email Automático + Dados RAW

**Feedback do Usuário**:
> "Quero que mande os insights pro meu email. Assim como os arquivos que geraram os insights. Posso pegar estes arquivos e mandar outra ia gerar insights melhores se eu achar por bem"

**Solução**:
1. **Script de Email**: `send-insights-email.sh`
   - Envia insights TXT/MD
   - Anexa CSVs de dados RAW
   - Email: **augustosvm@gmail.com** (configurado)

2. **Dados Exportados**:
   - `funding_rounds_30d.csv` - Rodadas de investimento
   - `startups_recent.csv` - Startups por país/setor
   - `papers_30d.csv` - Papers acadêmicos
   - `jobs_30d.csv` - Vagas de emprego
   - `market_b3_30d.csv` - Ações B3
   - `market_nasdaq_30d.csv` - Ações NASDAQ
   - `ipo_calendar.csv` - IPOs futuros
   - `summary_by_country.json` - Resumo agregado

3. **Configuração SMTP**:
   - Gmail via App Password
   - .env configurado automaticamente

**Arquivos Criados**:
- `send-insights-email.sh`
- `SETUP-EMAIL-E-JOBS.md`
- `setup-email-jobs-complete.sh`

---

### ✅ Jobs Collector (Indeed, LinkedIn, AngelList)

**Feedback do Usuário**:
> "Quero saber dos papers, jobs, paper pre e pos lançamentos. Tipo de empresas que estão recebendo investimento por pais. Por area. No brasil principalmente."

**Solução**:
1. **Collector de Vagas**: `collectors/jobs-collector.ts`
   - Indeed (Brasil, USA, Europa) - Web scraping
   - LinkedIn Jobs API (opcional, precisa key)
   - AngelList/Wellfound (startups)

2. **Classificação**:
   - Por país: Brasil, USA, UK, Germany, etc
   - Por setor: AI/ML, Agro-tech, Fintech, Backend, etc
   - Remote vs Presencial

3. **Tabela no Banco**: `sofia.jobs`
   - Campos: title, company, location, country, sector, remote, posted_date, url

**Arquivos Criados**:
- `collectors/jobs-collector.ts`
- `db/migrations/008_create_jobs_table.sql`

---

### ✅ Universidades Brasileiras (Foco Brasil)

**Feedback do Usuário**:
> "Quem procura empresas pra investir e quem procura investidores. Temos que ver no brasil quais as faculdades falan de quais assuntos pra sabermos que tais faculdades tm excelencia em profissionais de tal tipo."

**Solução**:
1. **Mapeamento de 17 Universidades**:
   - USP, Unicamp, UFRJ, ITA, UFMG, UFRGS, etc
   - Expertises de cada uma
   - Empresas fundadas por alumni

2. **Casos de Uso**:
   - **Recrutamento**: Precisa engenheiro Agro-tech? → USP (ESALQ), Unicamp
   - **Job Seekers**: Formado em ITA? → Embraer, Defense Tech startups
   - **Investidores**: UFMG gerou Akwan (Google), Sympla, Hotmart

3. **Setores → Universidades**:
   - Agro-tech: USP (ESALQ), Unicamp, UNESP
   - AI/ML: USP, UFMG, UFRGS, PUC-Rio, UFABC
   - Fintech: Insper, FGV, USP
   - Aerospace: ITA
   - Defense Tech: ITA, IME

**Arquivo Criado**:
- `data/brazilian-universities.json`

---

### ✅ Script Automático COMPLETO

**Feedback do Usuário**:
> "Seu script tem que fazer tudo. Não me mandar fazer as coisas. Vc gasta mais tempo gerando documentacao do qwue se fizesse o script"

**Solução**: `auto-setup.sh`

**O que ele faz automaticamente**:
1. ✅ Git pull (com stash se necessário)
2. ✅ Configura email: augustosvm@gmail.com
3. ✅ Ativa virtual environment
4. ✅ Cria tabelas no banco (ipo_calendar, jobs)
5. ✅ Torna scripts executáveis
6. ✅ Gera insights v2.0
7. ✅ Mostra preview dos insights
8. ✅ Envia email (se SMTP_PASS configurado)

**Arquivo Criado**:
- `auto-setup.sh` ← **SCRIPT PRINCIPAL**

---

## 🚀 COMO CONTINUAR AMANHÃ

### 1. NO SERVIDOR (PRIMEIRA VEZ)

```bash
cd /home/ubuntu/sofia-pulse

# Executar setup automático completo
bash auto-setup.sh
```

**Isso vai fazer tudo automaticamente!**

Se o `auto-setup.sh` não existir ainda (porque não deu pull):

```bash
# Fazer stash e pull manualmente
git stash
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE

# Agora executar setup
bash auto-setup.sh
```

### 2. CONFIGURAR SMTP_PASS (Gmail App Password)

Se o email não enviar, é porque falta SMTP_PASS:

```bash
# 1. Criar App Password no Gmail
# https://myaccount.google.com/apppasswords
# Selecione: Mail → Other → "Sofia Pulse"
# Copie a senha de 16 caracteres (ex: abcd efgh ijkl mnop)

# 2. Adicionar no .env (remover espaços da senha)
echo 'SMTP_PASS=abcdefghijklmnop' >> .env

# 3. Enviar email manualmente
./send-insights-email.sh
```

### 3. VER INSIGHTS GERADOS

```bash
# Ver insights completos
cat analytics/premium-insights/latest-geo.txt

# Ver só o resumo executivo (Gemini AI)
grep -A 20 "RESUMO EXECUTIVO" analytics/premium-insights/latest-geo.txt
```

### 4. TESTAR JOBS COLLECTOR

```bash
# Coletar vagas (Brasil + USA)
npx tsx collectors/jobs-collector.ts

# Ver vagas coletadas no banco
psql -U sofia -d sofia_db -c "
SELECT country, sector, COUNT(*) as vagas
FROM sofia.jobs
GROUP BY country, sector
ORDER BY vagas DESC
LIMIT 20;
"
```

### 5. AUTOMATIZAR COM CRONTAB

```bash
crontab -e
```

Adicione:

```bash
# Sofia Pulse - Automações
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Jobs Collector - 20:00 UTC / 17:00 BRT (Diário)
0 20 * * * cd /home/ubuntu/sofia-pulse && npx tsx collectors/jobs-collector.ts >> /var/log/sofia-jobs.log 2>&1

# Finance B3 - 21:00 UTC / 18:00 BRT (Seg-Sex)
0 21 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:brazil >> /var/log/sofia-finance-b3.log 2>&1

# Finance NASDAQ - 21:05 UTC / 18:05 BRT (Seg-Sex)
5 21 * * 1-5 cd /home/ubuntu/sofia-pulse && npm run collect:nasdaq >> /var/log/sofia-finance-nasdaq.log 2>&1

# Funding - 21:10 UTC / 18:10 BRT (Diário)
10 21 * * * cd /home/ubuntu/sofia-pulse && npm run collect:funding >> /var/log/sofia-finance-funding.log 2>&1

# Premium Insights v2 - 22:00 UTC / 19:00 BRT (Seg-Sex)
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && ./generate-premium-insights-v2.sh >> /var/log/sofia-insights.log 2>&1

# Email com Insights - 23:00 UTC / 20:00 BRT (Seg-Sex)
0 23 * * 1-5 cd /home/ubuntu/sofia-pulse && ./send-insights-email.sh >> /var/log/sofia-email.log 2>&1
```

---

## 📊 DADOS QUE VÃO PRO EMAIL (augustosvm@gmail.com)

### Insights (TXT/MD):
- 🌍 Mapa Global da Inovação (por continente)
- 🎯 Especialização Regional (Brasil=Agro, USA=AI, etc)
- 🔥 Países em Destaque
- 💰 Próximos IPOs (NASDAQ, B3)
- 📊 Top 5 B3/NASDAQ (sem duplicatas!)
- 🤖 Resumo Executivo (narrativa Gemini AI)

### Dados RAW (CSVs):
```
funding_rounds_30d.csv    → Investimentos por país/setor
startups_recent.csv       → Startups por país/setor
papers_30d.csv            → Papers de universidades
jobs_30d.csv              → Vagas tech por país/setor
market_b3_30d.csv         → Ações B3 (30 dias)
market_nasdaq_30d.csv     → Ações NASDAQ (30 dias)
ipo_calendar.csv          → IPOs futuros
summary_by_country.json   → Resumo agregado
```

**Você pode**:
- Usar insights prontos (latest-geo.txt)
- Ou pegar CSVs e mandar pra ChatGPT/Claude gerar insights customizados

---

## 🇧🇷 CASOS DE USO PARA VENDER NO BRASIL

### 1. Para Investidores Procurando Empresas

**Query**:
```bash
# Abrir funding_rounds_30d.csv
# Filtrar: country = "Brasil"
# Ordenar por: amount_usd DESC
```

**Resultado**:
- Startups brasileiras recebendo funding
- Setores em alta (Agro-tech, Fintech, etc)
- Ticket médio por setor

### 2. Para Empresas Procurando Investidores

**Query SQL**:
```sql
SELECT sector,
       COUNT(*) as deals,
       AVG(amount_usd) as avg_ticket,
       SUM(amount_usd) as total
FROM sofia.funding_rounds
WHERE country = 'Brasil'
  AND announced_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY sector
ORDER BY total DESC;
```

### 3. Para Empresas Recrutando

**Processo**:
1. Abrir `brazilian-universities.json`
2. Procurar setor (ex: Agro-tech)
3. Universidades: USP (ESALQ), Unicamp, UNESP
4. Recrutar alumni dessas universidades

**Exemplo**:
```
Precisa engenheiro AI/ML?
→ Universidades: USP, UFMG, UFRGS, UFABC, PUC-Rio
→ Ver jobs_30d.csv: Onde esses profissionais estão trabalhando
```

### 4. Para Profissionais Procurando Emprego

**Query**:
```bash
# Abrir jobs_30d.csv
# Filtrar: country = "Brasil", sector = "AI/ML"
# Ordenar por: posted_date DESC
```

**Resultado**:
- Empresas contratando na sua área
- Vagas remotas vs presenciais
- Localização (São Paulo, Floripa, etc)

---

## 🔧 ARQUIVOS IMPORTANTES

### Scripts Principais:
- **`auto-setup.sh`** ← EXECUTAR PRIMEIRO (faz tudo)
- `generate-premium-insights-v2.sh` - Gera insights geo-localizados
- `send-insights-email.sh` - Envia email com insights + CSVs
- `test-premium-insights-v2.sh` - Testa se tudo está OK

### Collectors:
- `collectors/ipo-calendar.ts` - IPOs (NASDAQ, B3, SEC)
- `collectors/jobs-collector.ts` - Vagas (Indeed, LinkedIn)

### Migrations:
- `db/migrations/007_create_ipo_calendar.sql`
- `db/migrations/008_create_jobs_table.sql`

### Dados:
- `data/brazilian-universities.json` - 17 universidades BR

### Documentação:
- **`CLAUDE.md`** ← ESTE ARQUIVO (resumo completo)
- `COMO-EXECUTAR-NO-SERVIDOR.md` - Guia passo-a-passo
- `SETUP-EMAIL-E-JOBS.md` - Setup detalhado email/jobs
- `PREMIUM-INSIGHTS-V2-RELEASE.md` - Release notes v2.0

---

## 🐛 TROUBLESHOOTING

### "auto-setup.sh: No such file or directory"

```bash
git stash
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
bash auto-setup.sh
```

### "Email não envia"

```bash
# Verificar se SMTP_PASS está configurado
grep SMTP_PASS .env

# Se vazio, configure:
echo 'SMTP_PASS=sua-senha-app-16-caracteres' >> .env

# Testar envio
./send-insights-email.sh
```

### "psql: command not found"

```bash
sudo apt update
sudo apt install postgresql-client
```

### "venv-analytics não encontrado"

```bash
# O auto-setup.sh cria automaticamente, mas se precisar:
bash setup-data-mining.sh
```

---

## 📈 COMMITS IMPORTANTES

| Commit | Descrição |
|--------|-----------|
| `a3419be` | Guia completo de execução no servidor |
| `9cb59dd` | Email automático + Jobs Collector + Universidades BR |
| `18656cc` | Script de validação v2.0 + Release Notes |
| `44ce244` | Premium Insights v2.0 + IPO Calendar + Análise Geográfica |
| `3be3cd4` | Fix: Remove duplicate stocks bug |
| `2dd6e4e` | Crontab completo + Instalador |

---

## ✅ CHECKLIST RÁPIDO

```bash
# 1. Setup automático completo
cd /home/ubuntu/sofia-pulse
bash auto-setup.sh

# 2. Configurar SMTP_PASS (se email não enviar)
echo 'SMTP_PASS=sua-senha-app' >> .env
./send-insights-email.sh

# 3. Ver insights
cat analytics/premium-insights/latest-geo.txt

# 4. Testar jobs
npx tsx collectors/jobs-collector.ts

# 5. Automatizar
crontab -e  # copiar cron acima
```

---

## 💡 PRÓXIMAS MELHORIAS (IDEIAS)

1. **Dashboard Web**:
   - Mostrar insights em dashboard interativo
   - Gráficos por país/setor
   - Filtros dinâmicos

2. **Mais Fontes de Jobs**:
   - Glassdoor
   - Stack Overflow Jobs
   - GitHub Jobs (descontinuado mas tem arquivo)

3. **Análise de Salários**:
   - Scraping de faixas salariais
   - Comparação por país/setor

4. **Alertas Personalizados**:
   - Email quando startup de Agro-tech receber funding
   - Notificar quando universidade publicar paper em área X

5. **API REST**:
   - Expor dados via API
   - Frontend pode consumir

---

## 🎯 FOCO BRASIL (Já Implementado)

✅ Funding rounds Brasil
✅ Startups brasileiras por setor
✅ Papers de universidades BR (USP, Unicamp, UFMG, etc)
✅ Vagas tech Brasil (Indeed scraping)
✅ IPOs B3
✅ Performance ações B3
✅ 17 universidades mapeadas
✅ Expertises por universidade
✅ Casos de uso: Recrutamento, Investimento, Job Seeking

---

## 📞 PARA CONTINUAR DESENVOLVIMENTO

### Se precisar adicionar nova feature:

1. **Criar branch nova** (ou continuar na atual)
2. **Implementar feature**
3. **Testar localmente** (se possível)
4. **Criar script automático** (não documentação!)
5. **Commit e push**
6. **Atualizar CLAUDE.md**

### Se encontrar bugs:

1. **Descrever bug no commit**
2. **Implementar fix**
3. **Testar**
4. **Commit com "Fix: descrição"**

---

## 🎉 RESUMO EXECUTIVO

**O que funciona agora**:
- ✅ Premium Insights v2.0 com análise geo-localizada
- ✅ Email automático para augustosvm@gmail.com
- ✅ Export de dados RAW (CSVs) para análise externa
- ✅ Jobs collector (Indeed, LinkedIn, AngelList)
- ✅ Universidades brasileiras mapeadas
- ✅ IPO calendar (NASDAQ, B3, SEC)
- ✅ Bug de duplicatas corrigido
- ✅ Script automático que faz tudo (`auto-setup.sh`)

**O que ainda precisa configurar manualmente**:
- ⚠️ SMTP_PASS (Gmail App Password) - 2 minutos
- ⚠️ Crontab (automação) - 5 minutos

**Próximo passo**:
```bash
bash auto-setup.sh
```

---

**Última Atualização**: 2025-11-18 23:30 UTC
**Branch**: `claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE`
**Status**: ✅ Pronto para uso
