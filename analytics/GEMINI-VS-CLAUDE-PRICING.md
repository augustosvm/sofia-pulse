# 💰 Comparação de Preços: Gemini vs Claude vs GPT-4

**Conclusão**: **Google Gemini é 10-15x mais barato que Claude!**

---

## 📊 Preços por 1M tokens (Novembro 2025)

| Modelo | Input (1M tokens) | Output (1M tokens) | Tier Grátis |
|--------|-------------------|-------------------|-------------|
| **Gemini 1.5 Flash** | $0.075 | $0.30 | ✅ 15 RPM grátis |
| **Gemini 1.5 Pro** | $1.25 | $5.00 | ✅ 2 RPM grátis |
| **Claude Sonnet 3.5** | $3.00 | $15.00 | ❌ Não |
| **Claude Opus 3** | $15.00 | $75.00 | ❌ Não |
| **GPT-4 Turbo** | $10.00 | $30.00 | ❌ Não |
| **GPT-4o** | $2.50 | $10.00 | ❌ Não |

---

## 💡 Exemplo Prático: Sofia Pulse Data Mining

### Cenário: Análise de 970 registros, 29 tabelas

**Dados enviados por request**:
- Summary das 29 tabelas: ~5k tokens
- Correlation matrix: ~3k tokens
- Cluster analysis: ~2k tokens
- **Total por análise completa**: ~10k tokens

**Narrativa gerada** (output): ~2k tokens

---

### Custo por Análise Completa:

| Modelo | Input | Output | Total/Análise | 100 Análises |
|--------|-------|--------|---------------|--------------|
| **Gemini Flash** | $0.0007 | $0.0006 | **$0.0013** | **$0.13** |
| **Gemini Pro** | $0.0125 | $0.0100 | **$0.0225** | **$2.25** |
| **Claude Sonnet** | $0.0300 | $0.0300 | **$0.0600** | **$6.00** |
| **Claude Opus** | $0.1500 | $0.1500 | **$0.3000** | **$30.00** |
| **GPT-4 Turbo** | $0.1000 | $0.0600 | **$0.1600** | **$16.00** |
| **GPT-4o** | $0.0250 | $0.0200 | **$0.0450** | **$4.50** |

---

## 🎯 Recomendação para Sofia Pulse

### Usar **Gemini 1.5 Flash** para:
- ✅ Análises diárias automáticas
- ✅ Geração de narrativas de insights
- ✅ Sumarização de correlações
- ✅ Detecção de anomalias

**Por que**:
- **10x mais barato** que Claude Sonnet
- **Rápido** (~2s por request)
- **Tier grátis** generoso (15 RPM = 900 req/hora!)
- **Qualidade suficiente** para narrativas de dados

---

### Usar **Gemini 1.5 Pro** para:
- Análises complexas (raciocínio multi-step)
- Decisões de investimento críticas
- Quando precisar de contexto longo (2M tokens!)

**Por que**:
- Ainda **2-6x mais barato** que Claude/GPT-4
- Qualidade comparável a Claude Sonnet
- Contexto ENORME (2M tokens vs 200k Claude)

---

## 🆓 Tier Grátis do Gemini

### Limites Generosos:

| Modelo | Requests/Min | Requests/Dia | Tokens/Min |
|--------|--------------|--------------|------------|
| **Flash** | 15 RPM | 1,500/dia | 1M TPM |
| **Pro** | 2 RPM | 50/dia | 32k TPM |

**Para Sofia Pulse**:
- Coleta diária (1x): Gemini Flash GRÁTIS
- Análises ad-hoc (<50/dia): Gemini Pro GRÁTIS

---

## 💸 Cenário Real: 1 Mês de Uso

### Uso estimado:
- **Análise automática diária**: 1 request/dia = 30 req/mês
- **Análises exploratórias**: ~10 req/semana = 40 req/mês
- **Total**: ~70 requests/mês

### Custo Mensal:

| Modelo | Custo/Mês | Economia vs Claude |
|--------|-----------|-------------------|
| **Gemini Flash** | **$0.09** | **98.5% mais barato** |
| **Gemini Pro** | **$1.58** | **74% mais barato** |
| **Claude Sonnet** | **$4.20** | — |
| **GPT-4o** | **$3.15** | 25% mais barato |

**Conclusão**: Com Gemini Flash, mesmo usando 70x/mês, paga **menos de $0.10**!

---

## 🔑 Como Obter API Key do Gemini

### 1. Acesse Google AI Studio:
https://aistudio.google.com/app/apikey

### 2. Crie API Key (1 click)

### 3. Adicione ao .env:
```bash
echo 'GEMINI_API_KEY=sua_key_aqui' >> ~/.env
```

**Pronto!** Tier grátis já está ativo.

---

## 📝 Código Python - Gemini API

### Instalação:
```bash
pip install google-generativeai
```

### Uso Básico:
```python
import google.generativeai as genai
import os

# Configurar
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Modelo
model = genai.GenerativeModel('gemini-1.5-flash')

# Gerar insights
response = model.generate_content(f"""
Analise estes dados do Sofia Pulse:

{data_summary}

Identifique:
1. Correlações entre funding e performance
2. Setores quentes
3. Oportunidades de investimento
""")

print(response.text)
```

**Simples assim!**

---

## 🆚 Comparação de Qualidade

### Para Data Mining/Finance:

| Critério | Gemini Flash | Gemini Pro | Claude Sonnet |
|----------|--------------|------------|---------------|
| **Narrativas** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Correlações** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Sumarizações** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Raciocínio** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Velocidade** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Custo** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

**Veredicto**: Gemini Flash é **perfeito** para insights de dados financeiros!

---

## 🎁 Bônus: Você JÁ TEM Gemini PRO

Como você tem **assinatura Gemini PRO** (Google One AI Premium):
- ✅ Acesso a Gemini Advanced (melhor modelo)
- ✅ Pode usar via interface web ILIMITADO
- ✅ API grátis até limites generosos

**Estratégia Híbrida**:
1. **Notebooks automatizados** → Gemini API (tier grátis)
2. **Análises complexas manuais** → Gemini Advanced web (ilimitado)
3. **Custo total** → $0/mês (dentro dos limites grátis!)

---

## 📌 Resumo Executivo

| | Gemini Flash | Claude Sonnet |
|---|--------------|---------------|
| **Custo/Análise** | $0.0013 | $0.0600 |
| **Economia** | **46x mais barato** | — |
| **Tier Grátis** | ✅ 15 RPM | ❌ |
| **Velocidade** | ⚡ ~2s | ~5s |
| **Qualidade** | ⭐⭐⭐⭐ (suficiente) | ⭐⭐⭐⭐⭐ |
| **Contexto** | 1M tokens | 200k tokens |

---

## 🚀 Próximo Passo

```bash
cd ~/sofia-pulse

# 1. Obter API key (grátis):
# https://aistudio.google.com/app/apikey

# 2. Adicionar ao .env:
echo 'GEMINI_API_KEY=sua_key_aqui' >> .env

# 3. Rodar setup:
./setup-data-mining.sh

# 4. Abrir Jupyter:
source venv-analytics/bin/activate
jupyter lab

# 5. Rodar notebook:
# analytics/notebooks/data-mining-insights.ipynb
```

**Resultado**: Insights automáticos por **$0/mês** (tier grátis) ou **$0.09/mês** (70 análises)!

---

**Links Úteis**:
- API Key: https://aistudio.google.com/app/apikey
- Pricing: https://ai.google.dev/pricing
- Docs: https://ai.google.dev/gemini-api/docs
- Playground: https://aistudio.google.com/

🎉 **Use Gemini e economize 98% vs Claude!**
