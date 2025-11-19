# 🚀 Quick Start - Tech Intelligence v2.5

**Data**: 2025-11-19
**Branch**: `claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE`

---

## 🎯 UM COMANDO FAZ TUDO

```bash
cd /home/ubuntu/sofia-pulse
bash setup-tech-intelligence-v2.5.sh
```

**Isso vai fazer AUTOMATICAMENTE**:
- ✅ Atualizar código (git pull)
- ✅ Instalar dependências
- ✅ Criar tabelas no banco
- ✅ Coletar dados (GitHub + HackerNews)
- ✅ Gerar insights REGIONAIS e TEMPORAIS
- ✅ Configurar email automático
- ✅ Adicionar ao cron (automação 24/7)

**Tempo**: ~3-5 minutos

---

## 📊 O QUE VOCÊ VAI RECEBER

### 1. **Tech Trend Score** (Novo!)

Ranking das 20 tecnologias mais emergentes baseado em:
- GitHub stars (desenvolvedores usando)
- HackerNews mentions (comunidade falando)

**Exemplo**:
```
🔥 TOP 20 TECNOLOGIAS
Rank   Technology       Score    GitHub⭐    HN📰
1      Python           450.2    1,234,567   89
2      TypeScript       425.8    987,654     72
3      Rust             398.1    654,321     58
...

💎 DARK HORSES (oportunidades escondidas)
1. Zig: 45,678 stars, only 3 HN mentions
2. Mojo: 23,456 stars, only 2 HN mentions

⚠️  HYPE CHECK (verificar realidade vs buzz)
1. NewFramework: 12 HN mentions, but only 234 stars
```

### 2. **Premium Insights v2.0** (Existente)

Análise REGIONAL e TEMPORAL:
- 🌍 Mapa Global da Inovação (por continente)
- 🎯 Especialização Regional (Brasil=Agro, USA=AI, China=Manufacturing)
- 📊 Oceano Vermelho vs Azul (Top 50 altas vs Top 50 quedas)
- 💰 Próximos IPOs
- 🤖 Narrativas IA (Gemini 2.5)

### 3. **Dados RAW** (CSVs para análise externa)

- `github_trending.csv` - Repositórios por linguagem
- `hackernews_tech.csv` - Tecnologias mencionadas
- `funding_30d.csv` - Investimentos (últimos 30 dias)
- `jobs_30d.csv` - Vagas tech
- `market_b3_30d.csv` - Ações B3
- `market_nasdaq_30d.csv` - Ações NASDAQ

---

## 📧 CONFIGURAR EMAIL (OPCIONAL)

Para receber insights automaticamente no email:

### 1. Gerar senha de app do Gmail

Acesse: https://myaccount.google.com/apppasswords

- Nome: "Sofia Pulse"
- Tipo: "Outro (nome personalizado)"
- Clique em "Gerar"

Você receberá uma senha de 16 caracteres (ex: `abcd efgh ijkl mnop`)

### 2. Adicionar no .env

```bash
nano .env
```

Altere a linha:
```
SMTP_PASS=your-gmail-app-password-here
```

Para:
```
SMTP_PASS=abcd-efgh-ijkl-mnop
```

(Remova os espaços: `abcdefghijklmnop`)

### 3. Testar envio

```bash
bash send-insights-email-complete.sh
```

Você deve receber um email em **augustosvm@gmail.com** com:
- Insights completos (TXT)
- Tech Trend Score
- Premium Insights v2.0
- CSVs anexados

---

## ⏰ AUTOMAÇÃO (Cron)

Após rodar `setup-tech-intelligence-v2.5.sh`, o cron será configurado automaticamente:

### Diário:
- **08:00 UTC** - GitHub Trending
- **08:30 UTC** - HackerNews
- **20:00 UTC** - ArXiv AI Papers
- **20:05 UTC** - OpenAlex Papers
- **20:10 UTC** - AI Companies
- **01:00 UTC** - Patentes (China + Europa)
- **06:00 UTC** - IPO Calendar
- **07:00 UTC** - Jobs

### Seg-Sex (dias úteis):
- **21:00 UTC (18:00 BRT)** - Finance (B3, NASDAQ, Funding)
- **22:00 UTC (19:00 BRT)** - Insights Completos (Regional + Temporal + Tech Trends)
- **23:00 UTC (20:00 BRT)** - Email com insights + CSVs
- **02:00 UTC** - HKEX IPOs

### Semanal (Segundas):
- **03:00 UTC** - NIH Grants
- **05:00 UTC** - Cardboard Production

### Mensal (Dia 1):
- **04:00 UTC** - Universidades Ásia

---

## 🔍 VERIFICAR SE ESTÁ FUNCIONANDO

### 1. Ver dados coletados

```bash
# Tech Trends
cat analytics/tech-trends/latest-scores.txt

# Insights completos
cat analytics/premium-insights/latest-complete.txt
```

### 2. Verificar cron instalado

```bash
crontab -l | grep sofia
```

Deve mostrar ~16 linhas de jobs.

### 3. Acompanhar logs em tempo real

```bash
tail -f /var/log/sofia-*.log
```

### 4. Ver quantidade de dados no banco

```bash
psql -U sofia -d sofia_db -c "
SELECT 'github_trending' as table, COUNT(*) FROM sofia.github_trending
UNION ALL
SELECT 'hackernews_stories', COUNT(*) FROM sofia.hackernews_stories
UNION ALL
SELECT 'funding_rounds', COUNT(*) FROM sofia.funding_rounds
UNION ALL
SELECT 'jobs', COUNT(*) FROM sofia.jobs;
"
```

---

## 💡 CASOS DE USO

### Para Colunistas (Tech Journalists)

**Pergunta**: "Quais tecnologias estão emergindo AGORA?"

**Resposta**: Ver `analytics/tech-trends/latest-scores.txt`
- Top 20 tecnologias por trend score
- Dark Horses (oportunidades escondidas)
- Hype Check (verificar se é real ou marketing)

### Para Investidores

**Pergunta**: "Onde está acontecendo inovação em Agro-tech no Brasil?"

**Resposta**: Ver `analytics/premium-insights/latest-complete.txt`
- Seção "Especialização Regional"
- Filtrar: Brasil → Agro-tech
- Ver universidades: USP (ESALQ), Unicamp, UNESP
- Ver funding rounds recentes

### Para Empresas Recrutando

**Pergunta**: "Quais linguagens contratar para 2025?"

**Resposta**: Ver `analytics/tech-trends/latest-scores.txt`
- Seção "TOP PROGRAMMING LANGUAGES"
- Linguagens com alto GitHub stars = desenvolvedores usando
- Linguagens com alto HN mentions = comunidade falando

### Para Profissionais (Job Seekers)

**Pergunta**: "Quais skills aprender para ter mais vagas?"

**Resposta**: Combinar:
- `analytics/tech-trends/latest-scores.txt` → Tecnologias emergentes
- `data/exports/jobs_30d.csv` → Vagas abertas por skill
- Correlação: Tech com alto trend score + muitas vagas = demanda alta

---

## 🐛 TROUBLESHOOTING

### "Script falhou no passo X"

```bash
# Ver erro completo
bash setup-tech-intelligence-v2.5.sh 2>&1 | tee setup.log
less setup.log
```

### "Collectors falharam (403, rate limit)"

Normal se rodando de ambiente local. No servidor com IP real funciona.

Alternativa: Configurar `GITHUB_TOKEN` no `.env`:
```
GITHUB_TOKEN=ghp_seu_token_aqui
```

Gerar em: https://github.com/settings/tokens

### "Email não envia"

Verificar:
```bash
grep SMTP_PASS .env
```

Se vazio ou `your-gmail-app-password-here`, configure conforme instruções acima.

### "Insights vazios ou sem dados"

Aguardar 24-48h para collectors popularem o banco.

Ou rodar manualmente:
```bash
npm run collect:github-trending
npm run collect:hackernews
npm run collect:funding
npm run collect:brazil
npm run collect:arxiv-ai

# Depois gerar insights
bash generate-insights-complete.sh
```

### "Cron não executa"

Verificar se cron está rodando:
```bash
sudo systemctl status cron
```

Verificar logs do cron:
```bash
grep CRON /var/log/syslog | tail -50
```

---

## 🎯 CHECKLIST RÁPIDO

```bash
# No servidor
cd /home/ubuntu/sofia-pulse

# ✅ 1. Executar setup automático
bash setup-tech-intelligence-v2.5.sh

# ✅ 2. Configurar email (opcional)
nano .env  # Adicionar SMTP_PASS

# ✅ 3. Testar email
bash send-insights-email-complete.sh

# ✅ 4. Ver insights gerados
cat analytics/premium-insights/latest-complete.txt

# ✅ 5. Verificar cron
crontab -l

# ✅ 6. Acompanhar próxima execução
tail -f /var/log/sofia-*.log
```

---

## 📊 ESTATÍSTICAS DO SISTEMA

Após setup completo:

| Tipo | Quantidade |
|------|------------|
| Collectors ativos | 16 |
| Insights/email | 2 |
| Backups | 5 |
| **Total de jobs** | **23** |

| Tabelas no banco | Quantidade |
|------------------|------------|
| Finance | 3 |
| Research | 2 |
| AI/Innovation | 1 |
| Patents | 2 |
| IPOs | 2 |
| Biotech | 1 |
| Academia | 1 |
| Economic | 1 |
| Jobs | 1 |
| **Tech Trends** | **2 (NOVO!)** |
| **Total** | **16** |

---

## 🔮 PRÓXIMOS PASSOS (Phased Implementation)

### Week 1 (CONCLUÍDO):
- ✅ GitHub Trending Collector
- ✅ HackerNews Collector
- ✅ Tech Trend Score (formula simples)
- ✅ Integração com insights regionais/temporais
- ✅ Email automático

### Week 2 (Próximo):
- Reddit Tech Collector (`r/programming`, `r/MachineLearning`)
- NPM Stats Collector (downloads por package)
- PyPI Stats Collector (Python packages)

### Week 3:
- GDELT Collector (eventos geopolíticos)
- Correlações: Papers ↔ Funding (lag analysis)
- Dark Horses Report (alto papers, baixo funding)

### Week 4:
- NLG Playbooks (Claude API)
- Entity Resolution (fuzzy matching)
- Confidence Scores

---

## 📞 SUPORTE

### Se encontrar problemas:

1. **Ver logs**:
   ```bash
   tail -100 /var/log/sofia-*.log
   ```

2. **Ver erro específico de um collector**:
   ```bash
   grep -i error /var/log/sofia-github.log | tail -20
   ```

3. **Executar manualmente para debug**:
   ```bash
   npm run collect:github-trending
   # Ver erro completo no terminal
   ```

4. **Ver status do banco**:
   ```bash
   sudo systemctl status postgresql
   ```

---

## 🎉 RESUMO EXECUTIVO

**O que está pronto AGORA**:
- ✅ 16 collectors rodando automaticamente
- ✅ Tech Trend Score (ranking de tecnologias emergentes)
- ✅ Premium Insights v2.0 (análise regional + temporal)
- ✅ Email automático (seg-sex às 23:00 UTC)
- ✅ Dados RAW exportados (CSVs)
- ✅ Automação completa via cron

**O que você precisa fazer**:
```bash
bash setup-tech-intelligence-v2.5.sh
```

**Resultado esperado**:
- 🤖 Insights diários no email (augustosvm@gmail.com)
- 📊 Ranking de tecnologias emergentes
- 🌍 Análise geográfica e temporal
- 💎 Dark Horses (oportunidades escondidas)
- 📁 Dados RAW para análise externa

---

**Última Atualização**: 2025-11-19
**Branch**: `claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE`
**Status**: ✅ Pronto para produção
