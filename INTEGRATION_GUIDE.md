# 🔌 AI Tech Radar - Integration Guide

Este guia mostra como integrar o AI Tech Radar ao pipeline existente do Sofia Pulse **SEM QUEBRAR NADA**.

---

## 📋 OPÇÃO 1: Standalone (Recomendado para começar)

Execute o AI Tech Radar como um pipeline separado:

```bash
# Rodar uma vez manualmente
bash collect-ai-tech-radar.sh

# Ou adicionar ao cron separadamente (semanal, domingos às 8h UTC)
crontab -e
```

Adicionar linha:
```cron
0 8 * * 0 /path/to/sofia-pulse/collect-ai-tech-radar.sh >> /var/log/sofia/ai-tech-radar.log 2>&1
```

**Vantagens**:
- ✅ Não afeta pipeline existente
- ✅ Fácil de debugar
- ✅ Pode rodar em horário diferente

---

## 📋 OPÇÃO 2: Integração ao collect-all-complete.sh

### Passo 1: Adicionar ao contador

Editar `collect-all-complete.sh`:

```bash
# LINHA 34: Mudar TOTAL_COLLECTORS
- TOTAL_COLLECTORS=0
+ TOTAL_COLLECTORS=0  # Will be 60 after adding AI Tech Radar collectors

# LINHA 48: Mudar o contador no output
- echo "▶️  [$TOTAL_COLLECTORS/55] $name..."
+ echo "▶️  [$TOTAL_COLLECTORS/60] $name..."  # 55 + 5 AI collectors
```

### Passo 2: Adicionar collectors ao final do arquivo

Adicionar ANTES da seção "# Summary":

```bash
################################################################################
# AI TECHNOLOGY RADAR COLLECTORS (5 NEW)
################################################################################

echo ""
echo "================================================================================"
echo "🤖 AI TECHNOLOGY RADAR COLLECTION"
echo "================================================================================"

run_collector "AI GitHub Trends" "npx tsx scripts/collect-ai-github-trends.ts"
run_collector "AI PyPI Packages" "python3 scripts/collect-ai-pypi-packages.py"
run_collector "AI NPM Packages" "npx tsx scripts/collect-ai-npm-packages.ts"
run_collector "AI HuggingFace Models" "python3 scripts/collect-ai-huggingface-models.py"
run_collector "AI ArXiv Keywords" "python3 scripts/collect-ai-arxiv-keywords.py"
```

---

## 📋 OPÇÃO 3: Integração ao collect-limited-apis.sh

Se preferir rodar junto com APIs com rate limit:

Editar `collect-limited-apis.sh` e adicionar:

```bash
# AI Tech Radar (rate-limited APIs)
echo "🤖 AI Tech Radar Collectors..."
npx tsx scripts/collect-ai-github-trends.ts
sleep 10
python3 scripts/collect-ai-huggingface-models.py
sleep 10
python3 scripts/collect-ai-arxiv-keywords.py
```

**Nota**: PyPI e NPM podem ir em `collect-fast-apis.sh` se preferir.

---

## 📧 Integração ao Email Diário

### Adicionar relatório ao send-email-mega.py

```python
# Adicionar ao final, antes de send_email()

# ============================================================================
# AI TECH RADAR REPORT
# ============================================================================
print("\n📊 Adding AI Tech Radar report...")

ai_report_txt = 'output/ai-tech-radar-report.txt'
ai_csvs = [
    'output/ai_tech_top20.csv',
    'output/ai_tech_rising_stars.csv',
    'output/ai_tech_dark_horses.csv',
]

if os.path.exists(ai_report_txt):
    email_body += "\n\n" + "="*80 + "\n"
    email_body += "AI TECHNOLOGY RADAR REPORT\n"
    email_body += "="*80 + "\n"

    with open(ai_report_txt, 'r', encoding='utf-8') as f:
        # Include first 100 lines of the report
        lines = f.readlines()[:100]
        email_body += ''.join(lines)

        if len(f.readlines()) > 100:
            email_body += "\n\n[... Full report in attachment ...]\n"

    # Add TXT attachment
    attachments.append(ai_report_txt)

    # Add CSV attachments
    for csv_file in ai_csvs:
        if os.path.exists(csv_file):
            attachments.append(csv_file)
            print(f"  ✅ Added: {os.path.basename(csv_file)}")
else:
    print("  ⚠️  AI Tech Radar report not found (run analytics first)")
```

---

## 📱 Integração ao WhatsApp

### Adicionar ao send-reports-whatsapp.py

```python
# Adicionar ao final, depois dos outros reports

# ============================================================================
# AI TECH RADAR SUMMARY
# ============================================================================
def send_ai_tech_radar_summary():
    """Send AI Tech Radar top 10 via WhatsApp"""

    report_file = 'output/ai-tech-radar-report.txt'

    if not os.path.exists(report_file):
        print("⚠️  AI Tech Radar report not found")
        return

    with open(report_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Extract TOP 20 section (first ~50 lines)
    summary_lines = []
    in_top20 = False

    for line in lines[:60]:
        if 'TOP 20 AI TECHNOLOGIES' in line:
            in_top20 = True

        if in_top20:
            summary_lines.append(line)

            # Stop after the table
            if len(summary_lines) > 30:
                break

    summary = ''.join(summary_lines)

    message = f"""🤖 **AI TECHNOLOGY RADAR**

{summary}

📊 Full report with 6 CSV exports available.
    """

    # Truncate to 4000 chars if needed
    if len(message) > 4000:
        message = message[:3900] + "\n\n[...truncated...]"

    send_whatsapp_message(message)
    print("✅ AI Tech Radar summary sent via WhatsApp")

# Call it
send_ai_tech_radar_summary()
```

---

## 📊 Integração ao run-mega-analytics.sh

Adicionar ANTES do email:

```bash
################################################################################
# AI TECH RADAR ANALYTICS
################################################################################

echo ""
echo "================================================================================"
echo "🤖 AI TECHNOLOGY RADAR REPORT"
echo "================================================================================"

if python3 analytics/ai-tech-radar-report.py; then
    echo "✅ AI Tech Radar report generated"
else
    echo "❌ AI Tech Radar report failed"
fi
```

---

## 🔄 Schedule Completo Sugerido

```bash
# Morning: Fast APIs (10:00 UTC)
0 10 * * 1-5 bash /path/to/collect-fast-apis.sh

# Afternoon: Limited APIs (16:00 UTC)
0 16 * * 1-5 bash /path/to/collect-limited-apis.sh

# Evening: Analytics + Email (22:00 UTC)
0 22 * * 1-5 bash /path/to/run-mega-analytics.sh && bash /path/to/send-email-mega.sh

# Sunday Morning: AI Tech Radar (8:00 UTC) - WEEKLY ONLY
0 8 * * 0 bash /path/to/collect-ai-tech-radar.sh
```

**Justificativa para semanal**:
- GitHub: Rate limit de 5000/hora (suficiente, mas não queremos desperdiçar)
- ArXiv: Rate limit estrito (3s entre requests)
- Dados mudam lentamente (1 semana é suficiente para detectar trends)

---

## ⚙️ Variáveis de Ambiente Necessárias

Adicionar ao `.env`:

```bash
# AI Tech Radar (opcional, mas recomendado)
GITHUB_TOKEN=ghp_your_token_here          # Obter em: https://github.com/settings/tokens
HF_TOKEN=hf_your_token_here               # Obter em: https://huggingface.co/settings/tokens (opcional)
```

**Sem GITHUB_TOKEN**: Rate limit de 60 req/hora (muito baixo!)
**Com GITHUB_TOKEN**: Rate limit de 5000 req/hora (suficiente)

---

## ✅ Checklist de Integração

- [ ] Rodar `test-ai-tech-radar.sh` para verificar setup
- [ ] Rodar `collect-ai-tech-radar.sh` uma vez manualmente
- [ ] Verificar outputs em `output/ai-tech-radar-report.txt`
- [ ] Adicionar ao cron (opção 1) OU ao collect-all-complete.sh (opção 2)
- [ ] Adicionar ao run-mega-analytics.sh
- [ ] Adicionar ao send-email-mega.py (opcional)
- [ ] Adicionar ao send-reports-whatsapp.py (opcional)
- [ ] Atualizar CLAUDE.md com as novidades

---

## 🐛 Troubleshooting

### Erro: GitHub rate limit exceeded

```bash
# Verificar rate limit atual
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit

# Se limit muito baixo, aguardar reset ou adicionar token
```

### Erro: Tables already exist

```bash
# Normal na segunda execução - pode ignorar
# Se quiser recriar:
psql -h localhost -U sofia -d sofia_db -c "DROP TABLE IF EXISTS sofia.ai_github_trends CASCADE;"
bash collect-ai-tech-radar.sh
```

### Collectors rodaram mas report vazio

```bash
# Verificar se os collectors inseriram dados
psql -h localhost -U sofia -d sofia_db -c "SELECT tech_key, COUNT(*) FROM sofia.ai_github_trends GROUP BY tech_key LIMIT 10;"

# Se vazio, rodar collectors novamente com verbose
npx tsx scripts/collect-ai-github-trends.ts 2>&1 | tee debug.log
```

---

## 📝 Atualizando CLAUDE.md

Adicionar ao `CLAUDE.md`:

```markdown
### ✅ **AI Technology Radar** (04 Dec 2025)

**MAJOR FEATURE**: Sistema completo de monitoramento de 100+ tecnologias de IA!

**O que foi implementado**:

1. **5 Novos Collectors** 📡
   - GitHub AI Tech Trends (100+ tecnologias)
   - PyPI AI Packages (70+ pacotes Python)
   - NPM AI Packages (30+ pacotes JavaScript)
   - HuggingFace Models (popularidade de modelos)
   - ArXiv AI Keywords (papers acadêmicos)

2. **6 Tabelas + 9 Views SQL** 📊
   - Tracking de LLMs, Agents, RAG, Inference, Multimodal, Audio, DevTools, Edge
   - Métricas: Hype Index, Momentum, Growth Rate, Developer Adoption, Research Interest
   - Views consolidadas com rankings e dark horses

3. **1 Relatório + 6 CSVs** 📄
   - ai-tech-radar-report.txt (completo)
   - Top 20 technologies
   - Rising stars (highest momentum)
   - Dark horses (high growth, low visibility)
   - By category rankings
   - Developer adoption leaders
   - Research interest leaders

**Tecnologias Monitoradas**:
- LLMs: GPT-4, Claude, Gemini, Llama, DeepSeek, Mistral, Phi, Qwen, Gemma
- Agent Frameworks: LangChain, AutoGen, CrewAI, Pydantic AI
- Inference: vLLM, TensorRT-LLM, ONNX Runtime, llama.cpp
- RAG: ChromaDB, Milvus, pgvector, LanceDB, GraphRAG
- Dev Tools: Cursor, Aider, Continue, GitHub Copilot
- + 50 outras categorias

**Arquivos**:
- `db/migrations/020_create_ai_tech_radar.sql` - Migration
- `sql/04-ai-tech-radar-views.sql` - 9 SQL views
- `scripts/collect-ai-github-trends.ts` - GitHub collector
- `scripts/collect-ai-pypi-packages.py` - PyPI collector
- `scripts/collect-ai-npm-packages.ts` - NPM collector
- `scripts/collect-ai-huggingface-models.py` - HuggingFace collector
- `scripts/collect-ai-arxiv-keywords.py` - ArXiv collector
- `analytics/ai-tech-radar-report.py` - Report generator
- `collect-ai-tech-radar.sh` - Pipeline completo
- `AI_TECH_RADAR_README.md` - Documentação completa

**Resultado**:
- ✅ 100+ tecnologias de IA monitoradas
- ✅ 5 fontes de dados diferentes
- ✅ Métricas de momentum, growth, hype index
- ✅ Detecção de dark horses e rising stars
- ✅ Rankings por categoria

**Commit**: TBD
```

---

**Última Atualização**: 2025-12-04
**Versão**: 1.0.0
