# 📧📱 Sofia Pulse - Reports Delivery System

**Sistema de entrega de relatórios via EMAIL + WhatsApp**

---

## 🎯 O que você recebe

### 📧 **Email** (augustosvm@gmail.com)
- ✅ **23 relatórios completos** (.txt)
- ✅ **15+ CSVs** com dados brutos
- ✅ **Playbook Gemini** (narrativas AI-powered)

### 📱 **WhatsApp** (+55 XX XXXXX-XXXX)
- ✅ **Resumo de conclusão** (overview completo)
- ✅ **MEGA Analysis** (primeiras 50 linhas)
- ✅ **Top 10 Tech Trends**
- ✅ **Playbook Gemini** (primeiras 60 linhas)
- ✅ **Career Trends** (primeiras 30 linhas)
- ✅ **Capital Flow** (primeiras 30 linhas)
- ✅ **Tech Talent Cities** (primeiras 30 linhas)
- ✅ **Innovation Hubs** (primeiras 30 linhas)

**Total**: ~8-10 mensagens WhatsApp com os destaques principais

---

## 🚀 Como funciona

### Automação Completa

```bash
# MASTER SCRIPT - Faz tudo de uma vez
bash run-all-with-monitoring.sh
```

**Pipeline completo:**
```
1. Pre-flight healthcheck
   ↓
2. Fast APIs (World Bank, HackerNews, NPM, PyPI)
   ↓
3. Limited APIs (GitHub, Reddit, OpenAlex)
   ↓
4. Data sanity check
   ↓
5. Analytics (23 reports)
   ↓
6. Post-run healthcheck
   ↓
7. Send reports (EMAIL + WHATSAPP) ← NOVO!
```

### Manual

```bash
# 1. Só enviar relatórios (se já rodou analytics)
bash send-all-reports.sh

# 2. Só email
bash send-email-mega.sh

# 3. Só WhatsApp summaries
python3 scripts/send-whatsapp-reports.py
```

---

## 📊 Relatórios Incluídos (23 total)

### **Email: TODOS os 23 relatórios**

**Core & Advanced (11)**:
1. `MEGA-ANALYSIS.txt` - Cross-database comprehensive
2. `top10-tech-trends.txt` - Ranking semanal
3. `correlations-papers-funding.txt` - Lag temporal
4. `dark-horses-report.txt` - Oportunidades escondidas
5. `entity-resolution.txt` - Fuzzy matching
6. `special-sectors-analysis.txt` - 14 setores críticos
7. `early-stage-deep-dive.txt` - Seed/Angel analysis
8. `energy-global-map.txt` - 307 países
9. `causal-insights-ml.txt` - ML + Clustering + NLP
10. `nlg-playbooks-gemini.txt` - **Narrativas AI** ⭐
11. `sofia-complete-report.txt` - Tech Trend Scoring

**Predictive Intelligence (6)**:
12. `career-trends-predictor.txt` - Prediz skills antes
13. `capital-flow-predictor.txt` - Prediz setores antes
14. `expansion-locations-analyzer.txt` - Melhores cidades
15. `weekly-insights-generator.txt` - Top 3 topics
16. `dying-sectors-detector.txt` - Declínio terminal
17. `dark-horses-intelligence.txt` - Stealth mode

**Socioeconomic Intelligence (6)**:
18. `best-cities-tech-talent.txt` - INSEAD methodology
19. `remote-work-quality-index.txt` - Nomad List + Numbeo
20. `innovation-hubs-ranking.txt` - WIPO GII
21. `startup-founders-best-countries.txt` - World Bank
22. `digital-nomad-index.txt` - Nomad List
23. `stem-education-leaders.txt` - OECD PISA

**CSVs (15+)**:
- `github_trending.csv`
- `npm_stats.csv`, `pypi_stats.csv`
- `funding_90d.csv`
- `arxiv_ai_papers.csv`, `openalex_papers.csv`, `nih_grants.csv`
- `cybersecurity_30d.csv`
- `space_launches.csv`
- `ai_regulation.csv`
- `gdelt_events_30d.csv`
- `socioeconomic_brazil.csv`
- `socioeconomic_top_gdp.csv`
- `electricity_consumption.csv`
- `commodity_prices.csv`
- E mais...

### **WhatsApp: Summaries dos principais**

**8-10 mensagens** com destaques:
1. Resumo de conclusão (overview)
2. MEGA Analysis (top 50 linhas)
3. Top 10 Tech Trends
4. Playbook Gemini ⭐ (narrativas AI)
5. Career Trends
6. Capital Flow
7. Tech Talent Cities
8. Innovation Hubs

---

## 🤖 Playbook Gemini (Destaque!)

**O que é:**
- Narrativas geradas por Gemini AI
- Contexto de papers científicos
- Prontas para publicação
- Insights aprofundados

**Onde encontrar:**
- 📧 Email: `nlg-playbooks-gemini.txt` (completo)
- 📱 WhatsApp: Primeiras 60 linhas (resumo)

**Requer:**
- `GEMINI_API_KEY` configurada no `.env`
- Rodado via: `bash update-gemini-key.sh`

---

## ⏰ Automação via Cron

```bash
# Adicionar ao crontab
# Roda todo dia às 22:00 UTC (19:00 BRT)
0 22 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-all-with-monitoring.sh
```

**Ou usar o script de setup:**
```bash
bash update-crontab-distributed.sh
```

---

## 🔧 Troubleshooting

### Email não chegou?

```bash
# Verificar SMTP configurado
grep -E "SMTP_|EMAIL_" .env

# Testar envio manual
bash send-email-mega.sh
```

### WhatsApp não chegou?

```bash
# Verificar sofia-mastra-rag está rodando
curl http://localhost:8001/api/v2/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"teste","user_id":"pulse"}'

# Testar envio manual
python3 scripts/send-whatsapp-reports.py
```

### Playbook Gemini vazio?

```bash
# Verificar GEMINI_API_KEY configurada
grep GEMINI_API_KEY .env

# Configurar se necessário
bash update-gemini-key.sh

# Rodar playbook manualmente
python3 analytics/nlg-playbooks-gemini.py
```

---

## 📁 Arquivos do Sistema

```
send-all-reports.sh              # Master script (email + whatsapp)
├─ send-email-mega.sh            # Envia email com 23 reports + CSVs
│  └─ send-email-mega.py         # Python script do email
└─ scripts/send-whatsapp-reports.py  # Envia summaries WhatsApp
```

---

## 📊 Exemplo de Output

### Email Subject:
```
🌍 Sofia Pulse MEGA INTELLIGENCE REPORT - 2025-11-22
```

### Email Attachments:
```
📄 23 Reports (.txt):
   MEGA-ANALYSIS.txt
   top10-tech-trends.txt
   nlg-playbooks-gemini.txt ⭐
   career-trends-predictor.txt
   best-cities-tech-talent.txt
   ... (18 mais)

📊 15+ CSVs:
   github_trending.csv
   funding_90d.csv
   socioeconomic_brazil.csv
   ... (12+ mais)
```

### WhatsApp Messages:
```
1/8: ✅ SOFIA PULSE - ANALYTICS COMPLETE
     Reports: 23 | CSVs: 15 | Time: 19:05

2/8: 📊 MEGA ANALYSIS
     [Primeiras 50 linhas do relatório]

3/8: 🔥 TOP 10 TECH TRENDS
     [Lista com top 10]

4/8: 🤖 PLAYBOOK GEMINI AI ⭐
     [Narrativas geradas por AI]

5/8: 🎓 CAREER TRENDS PREDICTOR
     [Skills emergentes]

... (4 mensagens mais)
```

---

## ✅ Checklist de Execução

- [ ] Sofia-mastra-rag rodando (localhost:8001)
- [ ] GEMINI_API_KEY configurada
- [ ] SMTP configurado (email)
- [ ] WhatsApp número configurado (27 988024062)
- [ ] Rodar: `bash run-all-with-monitoring.sh`
- [ ] Verificar email (augustosvm@gmail.com)
- [ ] Verificar WhatsApp (+55 XX XXXXX-XXXX)

---

## 🎯 Resultado Final

**Email**:
- ✅ 23 relatórios completos
- ✅ 15+ CSVs
- ✅ Playbook Gemini completo

**WhatsApp**:
- ✅ 8-10 mensagens
- ✅ Destaques principais
- ✅ Playbook Gemini (resumo)

**Tudo automático, todo dia às 19:00 BRT!** 🎉

---

**Última atualização**: 2025-11-22
**Branch**: `claude/fix-github-rate-limits-012Xm4nfg6i34xKQHSDbWfq3`
