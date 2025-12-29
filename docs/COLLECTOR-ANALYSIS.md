# 🔍 ANÁLISE DE COLLECTORS - Nomes e Caminhos

**Data**: 2025-12-29 14:20 BRT  
**Objetivo**: Validar caminhos e nomes dos collectors após reorganização

---

## ✅ STATUS DOS CAMINHOS

### Verificação de Localização

**Resultado**: ✅ **TODOS OS COLLECTORS ESTÃO NO LUGAR CORRETO**

- **Collectors em `scripts/`**: 55 arquivos
- **Collectors movidos por engano**: 0
- **Caminhos no config**: ✅ Corretos (`scripts/collect-*.py`)

---

## 📊 INVENTÁRIO COMPLETO

### Collectors no Disco (55 total)

| # | Nome do Arquivo | Configurado | Status |
|---:|:---|:---:|:---|
| 1 | `collect-acled-conflicts.py` | ✅ | OK |
| 2 | `collect-ai-arxiv-keywords.py` | ❌ | Não configurado |
| 3 | `collect-ai-huggingface-models.py` | ❌ | Não configurado |
| 4 | `collect-ai-pypi-packages.py` | ❌ | Não configurado |
| 5 | `collect-bacen-sgs.py` | ✅ | OK |
| 6 | `collect-basedosdados.py` | ❌ | Não configurado |
| 7 | `collect-brazil-ministries.py` | ✅ | OK |
| 8 | `collect-brazil-security.py` | ✅ | OK |
| 9 | `collect-careerjet-api.py` | ✅ | OK |
| 10 | `collect-central-banks-women.py` | ✅ | OK |
| 11 | `collect-cepal-latam.py` | ✅ | OK |
| 12 | `collect-cni-indicators.py` | ✅ | OK |
| 13 | `collect-commodity-prices.py` | ✅ | OK |
| 14 | `collect-drugs-data.py` | ✅ | OK |
| 15 | `collect-electricity-consumption.py` | ✅ | OK |
| 16 | `collect-energy-global.py` | ✅ | OK |
| 17 | `collect-fao-agriculture.py` | ✅ | OK |
| 18 | `collect-fiesp-data.py` | ❌ | **Não configurado** (CRÍTICO) |
| 19 | `collect-focused-areas.py` | ❌ | Não configurado |
| 20 | `collect-freejobs-api.py` | ✅ | OK |
| 21 | `collect-hdx-humanitarian.py` | ✅ | OK |
| 22 | `collect-himalayas-api.py` | ❌ | Não configurado |
| 23 | `collect-ibge-api.py` | ❌ | Não configurado |
| 24 | `collect-ilostat.py` | ❌ | Não configurado |
| 25 | `collect-infojobs-brasil.py` | ❌ | **Duplicado?** |
| 26 | `collect-infojobs-web-scraper.py` | ✅ | OK (config: `infojobs-brasil`) |
| 27 | `collect-ipea-api.py` | ✅ | OK |
| 28 | `collect-mdic-comexstat.py` | ✅ | OK |
| 29 | `collect-port-traffic.py` | ✅ | OK |
| 30 | `collect-producthunt-api.py` | ❌ | Não configurado |
| 31 | `collect-rapidapi-activejobs.py` | ✅ | OK |
| 32 | `collect-rapidapi-linkedin.py` | ✅ | OK |
| 33 | `collect-religion-data.py` | ✅ | OK |
| 34 | `collect-sec-edgar-funding.py` | ❌ | Não configurado |
| 35 | `collect-semiconductor-sales.py` | ✅ | OK |
| 36 | `collect-serpapi-googlejobs.py` | ✅ | OK |
| 37 | `collect-socioeconomic-indicators.py` | ✅ | OK |
| 38 | `collect-sports-federations.py` | ✅ | OK |
| 39 | `collect-sports-regional.py` | ✅ | OK |
| 40 | `collect-theirstack-api.py` | ✅ | OK |
| 41 | `collect-unicef.py` | ✅ | OK |
| 42 | `collect-un-sdg.py` | ✅ | OK |
| 43 | `collect-who-health.py` | ✅ | OK |
| 44 | `collect-women-brazil.py` | ✅ | OK |
| 45 | `collect-women-eurostat.py` | ✅ | OK |
| 46 | `collect-women-fred.py` | ✅ | OK |
| 47 | `collect-women-ilostat.py` | ✅ | OK |
| 48 | `collect-women-world-bank.py` | ✅ | OK |
| 49 | `collect-world-bank-gender.py` | ✅ | OK |
| 50 | `collect-world-ngos.py` | ✅ | OK |
| 51 | `collect-world-security.py` | ✅ | OK |
| 52 | `collect-world-sports.py` | ✅ | OK |
| 53 | `collect-world-tourism.py` | ✅ | OK |
| 54 | `collect-wto-trade.py` | ✅ | OK |
| 55 | `collect-yc-companies.py` | ❌ | Não configurado |

---

## 🔴 PROBLEMAS IDENTIFICADOS

### 1. Collectors Não Configurados (12 arquivos)

**CRÍTICO** - Estes collectors existem mas não estão no cron:

| Arquivo | Provável Categoria | Ação Recomendada |
|:---|:---|:---|
| `collect-fiesp-data.py` | 🔴 **Economic** | **ADICIONAR URGENTE** (dados Brasil) |
| `collect-ai-arxiv-keywords.py` | Tech | Adicionar ou remover |
| `collect-ai-huggingface-models.py` | Tech | Adicionar ou remover |
| `collect-ai-pypi-packages.py` | Tech | Adicionar ou remover |
| `collect-basedosdados.py` | Economic | Adicionar ou remover |
| `collect-focused-areas.py` | Other | Adicionar ou remover |
| `collect-himalayas-api.py` | Economic (Jobs) | Adicionar ou remover |
| `collect-ibge-api.py` | Economic | Adicionar ou remover |
| `collect-ilostat.py` | Social | Adicionar ou remover |
| `collect-producthunt-api.py` | Tech | Adicionar ou remover |
| `collect-sec-edgar-funding.py` | Economic | Adicionar ou remover |
| `collect-yc-companies.py` | Economic | Adicionar ou remover |

### 2. Duplicação Potencial

**`collect-infojobs-brasil.py` vs `collect-infojobs-web-scraper.py`**

- Config aponta para: `collect-infojobs-web-scraper.py`
- Existe também: `collect-infojobs-brasil.py`
- **Ação**: Verificar se são duplicados ou diferentes

### 3. Nomes Confusos ou Genéricos

| Arquivo | Problema | Sugestão |
|:---|:---|:---|
| `collect-focused-areas.py` | Muito genérico | Renomear para algo específico |
| `collect-basedosdados.py` | Nome em português | `collect-basedosdados-brazil.py` |
| `collect-ilostat.py` | Falta contexto | `collect-ilostat-labor.py` |

---

## ✅ NOMES BEM ESTRUTURADOS

### Exemplos de Bons Nomes

✅ **Claros e Descritivos**:
- `collect-mdic-comexstat.py` - Fonte + Tipo de dado
- `collect-women-world-bank.py` - Tema + Fonte
- `collect-sports-federations.py` - Tema + Tipo
- `collect-brazil-security.py` - Região + Tema
- `collect-central-banks-women.py` - Fonte + Tema específico

✅ **Padrão Consistente**:
- `collect-{fonte}-{tema}.py`
- `collect-{tema}-{região}.py`
- `collect-{api}-{tipo}.py`

---

## 📋 AÇÕES RECOMENDADAS

### Prioridade 1 - URGENTE

1. **Adicionar `collect-fiesp-data.py` ao config**
   ```typescript
   'fiesp-data': {
     name: 'fiesp-data',
     description: 'FIESP Industry Indicators',
     script: 'scripts/collect-fiesp-data.py',
     schedule: '0 9 * * *',
     category: 'economic'
   },
   ```

2. **Resolver duplicação InfoJobs**
   - Verificar diferença entre os 2 arquivos
   - Manter apenas 1 ou renomear claramente

### Prioridade 2 - ALTA

3. **Adicionar collectors importantes ao config**:
   - `collect-ibge-api.py` (dados Brasil)
   - `collect-sec-edgar-funding.py` (funding data)
   - `collect-yc-companies.py` (startups)

4. **Renomear arquivos confusos**:
   ```bash
   mv collect-basedosdados.py collect-basedosdados-brazil.py
   mv collect-ilostat.py collect-ilostat-labor.py
   mv collect-focused-areas.py collect-[nome-especifico].py
   ```

### Prioridade 3 - MÉDIA

5. **Decidir sobre collectors AI**:
   - Manter: Adicionar ao config
   - Remover: Mover para `legacy/`

6. **Atualizar documentação**:
   - Criar `COLLECTORS.md` com lista completa
   - Documentar cada collector (fonte, dados, frequência)

---

## 🔧 CORREÇÃO DO CONFIG

### Adicionar ao `legacy-python-config.ts`

```typescript
// FIESP (CRÍTICO - faltando)
'fiesp-data': {
  name: 'fiesp-data',
  description: 'FIESP Industry Indicators (Sensor + INA)',
  script: 'scripts/collect-fiesp-data.py',
  schedule: '0 9 * * *',  // Mesmo horário do MDIC
  category: 'economic'
},

// IBGE
'ibge-api': {
  name: 'ibge-api',
  description: 'IBGE Brazil Statistics',
  script: 'scripts/collect-ibge-api.py',
  schedule: '0 5 * * *',
  category: 'economic'
},

// SEC Edgar
'sec-edgar-funding': {
  name: 'sec-edgar-funding',
  description: 'SEC Edgar Funding Data',
  script: 'scripts/collect-sec-edgar-funding.py',
  schedule: '0 0 2 * *',
  category: 'economic'
},

// Y Combinator
'yc-companies': {
  name: 'yc-companies',
  description: 'Y Combinator Companies',
  script: 'scripts/collect-yc-companies.py',
  schedule: '0 0 1 * *',
  category: 'economic'
},
```

---

## 📊 RESUMO

| Métrica | Valor |
|:---|---:|
| **Total de Collectors** | 55 |
| **Configurados** | 43 (78%) |
| **Não Configurados** | 12 (22%) |
| **Críticos Faltando** | 1 (FIESP) |
| **Duplicações** | 1 (InfoJobs) |
| **Nomes Confusos** | 3 |

### Status dos Caminhos

✅ **100% Corretos** - Todos os collectors estão em `scripts/` e os caminhos no config apontam corretamente para `scripts/collect-*.py`.

**Nenhum ajuste de caminho necessário!**

---

*Análise realizada em: 2025-12-29 14:20 BRT*
