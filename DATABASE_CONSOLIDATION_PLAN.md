# Database Consolidation Plan - Sofia Pulse

**Objetivo**: Reduzir duplicações, consolidar tabelas similares, e melhorar organização

**Data**: 2025-12-22

---

## 🗑️ TABELAS DUPLICADAS (Para Dropar)

### 1. hacker_news_stories
- **Status**: VAZIA (0 rows)
- **Ativa**: hackernews_stories (751 rows, updated hoje)
- **Ação**: DROP TABLE sofia.hacker_news_stories
- **Impacto**: Zero - nunca foi usada

---

## 🔄 CONSOLIDAÇÕES PROPOSTAS

### 1. Women/Gender Data (5 tabelas → 1 tabela)

**Tabelas Atuais**:
- `women_eurostat_data` (1174 MB!) ⚠️ ENORME
- `women_world_bank_data` (32 MB)
- `women_ilo_data` (2232 kB)
- `central_banks_women_data` (1288 kB)
- `gender_indicators` (1248 kB)

**Proposta**: Consolidar em `gender_indicators`
- Adicionar coluna `source` (eurostat, world_bank, ilo, central_banks)
- Adicionar coluna `region` (global, europe, americas, etc.)
- Migrar dados gradualmente
- **Benefício**: Redução de ~1.2 GB, queries unificadas

**Prioridade**: ALTA (women_eurostat_data está usando 1.2GB!)

---

### 2. Research Papers (3 tabelas → 1 tabela)

**Tabelas Atuais**:
- `arxiv_ai_papers` (10 MB)
- `openalex_papers` (3.5 MB)
- `bdtd_theses` (não listada, mas existe)

**Proposta**: Consolidar em `research_papers`
- Adicionar coluna `source` (arxiv, openalex, bdtd)
- Schema unificado
- **Benefício**: Queries unificadas, fácil adicionar novos sources

**Prioridade**: MÉDIA

---

### 3. Jobs Data (3 tabelas → 1 tabela)

**Tabelas Atuais**:
- `jobs` (17 MB) - já unificada via collector
- `tech_jobs` (10 MB) - duplicação?
- `linkedin_jobs` (existe?)
- `trademe_jobs` (existe?)

**Status**: Verificar se tech_jobs é duplicata de jobs
**Ação**: Se duplicata, migrar para `jobs` e dropar

**Prioridade**: BAIXA (precisa investigação)

---

### 4. Embeddings (8 tabelas - Manter ou Dropar?)

**Tabelas**:
- github_embeddings (19 MB)
- hackernews_embeddings (5.5 MB)
- pypi_embeddings (4.8 MB)
- npm_embeddings (3.4 MB)
- paper_embeddings (1.2 MB)
- author_embeddings (1.2 MB)
- reddit_embeddings (1.2 MB)
- university_embeddings (1.2 MB)

**Questão**: Embeddings são usados atualmente?
- Se não: **DROPAR todos** (economiza ~40 MB)
- Se sim: Manter

**Prioridade**: BAIXA (precisa verificar se analytics usam)

---

## ✅ AÇÕES IMEDIATAS

### Fase 1 - Quick Wins (22 Dez 2025) ✅ COMPLETADO

**Script Executado**: `scripts/consolidate-database.ts`

1. ✅ **DROP hacker_news_stories** - COMPLETADO
   - Tabela vazia (0 registros) removida com sucesso
   - Versão ativa `hackernews_stories` (751 registros) está funcionando

2. ✅ **Investigar women_eurostat_data** - COMPLETADO
   - **Tamanho**: 1.2 GB
   - **Registros**: 807,866
   - **Período**: 1960-2024 (64 anos!)
   - **Cobertura**: 37 países, 17 datasets (Employment, Education, Health, etc.)
   - **Conclusão**: **MANTER** - Dados históricos legítimos e únicos
   - **Não é duplicação**: É uma fonte de dados valiosa com séries temporais longas

3. ✅ **Verificar embeddings** - COMPLETADO
   - **Total**: 1,272 registros (~37 MB)
   - **Em uso**:
     - `github_embeddings`: 955 (19 MB) ✅
     - `hackernews_embeddings`: 271 (5.5 MB) ✅
   - **Sem timestamps** (possível uso):
     - `pypi_embeddings`: 27 (4.8 MB)
     - `npm_embeddings`: 19 (3.4 MB)
   - **Vazias ou com erro** (podem dropar):
     - `reddit_embeddings`: 0 (1.2 MB) ⚠️
     - `paper_embeddings`: schema error
     - `author_embeddings`: schema error
     - `university_embeddings`: schema error
   - **Recomendação**: Dropar as 4 tabelas com erro/vazias (~10 MB economizados)

### Fase 2 - Consolidações (Próxima sessão)
1. Consolidar gender data (5 → 1 tabela)
2. Consolidar research papers (3 → 1 tabela)
3. Verificar e consolidar jobs tables

---

## 📊 IMPACTO ESTIMADO

**Espaço Economizado**:
- hacker_news_stories: 0 MB (vazia)
- Gender consolidation: ~1.2 GB
- Embeddings (se dropar): ~40 MB
- **Total**: ~1.24 GB economizados

**Benefícios**:
- Queries mais simples e rápidas
- Menor uso de disco
- Easier maintenance
- Unified data model

---

## 🚀 NOVOS COLETORES SUGERIDOS

Após consolidação, adicionar:

1. **Patent Data Collector** (já existe tabela `patents`)
   - USPTO API
   - Google Patents
   - WIPO

2. **Climate Data Collector**
   - Carbon emissions
   - Temperature trends
   - Climate tech funding

3. **Crypto/Web3 Collector**
   - DeFi protocols
   - DAO treasuries
   - NFT marketplaces

4. **App Store Rankings Collector**
   - Google Play top apps
   - Apple App Store rankings
   - Mobile tech trends
