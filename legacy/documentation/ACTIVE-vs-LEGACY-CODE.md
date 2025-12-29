# 📊 ANÁLISE: CÓDIGO ATIVO vs LEGACY - SOFIA PULSE

**Data**: 2025-12-29 11:43 BRT  
**Objetivo**: Identificar código em produção vs scripts descartáveis

---

## 🎯 RESUMO EXECUTIVO

### Código Total vs Código Ativo

| Categoria | Arquivos | Linhas | % do Total |
|:---|---:|---:|---:|
| **🟢 CÓDIGO ATIVO (Produção)** | **~70** | **~16,500** | **12.6%** |
| **🔴 CÓDIGO LEGACY (One-time)** | **74** | **~4,500** | **3.4%** |
| **📝 DOCUMENTAÇÃO** | **121** | **32,082** | **24.6%** |
| **🗄️ SQL/Migrations** | **101** | **11,865** | **9.1%** |
| **🔧 Outros (configs, utils)** | **407** | **65,620** | **50.3%** |
| **TOTAL** | **773** | **130,567** | **100%** |

**Insight Crítico**: Apenas **12.6%** do código está em produção ativa!

---

## 🟢 CÓDIGO ATIVO (Produção)

### 1. Collectors Python (55 arquivos, 14,755 linhas)

**Localização**: `scripts/collect-*.py`

**Principais**:
- `collect-mdic-comexstat.py` - 330 linhas (Comércio exterior Brasil)
- `collect-fiesp-data.py` - 417 linhas (Indicadores industriais)
- `collect-infojobs-web-scraper.py` - 208 linhas (Vagas de emprego)
- + 52 outros collectors (APIs, scraping, dados públicos)

**Configurados em**: `scripts/configs/legacy-python-config.ts` (44 collectors)

**Status**: ✅ Rodando em produção via cron (hourly)

---

### 2. Core TypeScript (2 arquivos, 548 linhas)

**Arquivos**:
- `scripts/collect.ts` - 216 linhas (CLI unificado)
- `scripts/generate-crontab.ts` - 332 linhas (Gerador de cron)

**Função**: Orquestração de todos os collectors

**Status**: ✅ Essencial para automação

---

### 3. Helpers & Utilities (3 arquivos, 1,162 linhas)

**Arquivos**:
- `scripts/shared/geo_helpers.py` - 548 linhas (Normalização geográfica)
- `scripts/shared/org_helpers.py` - 191 linhas (Normalização de empresas)
- `scripts/utils/sofia_whatsapp_integration.py` - 423 linhas (Notificações)

**Função**: Funções compartilhadas por todos os collectors

**Status**: ✅ Crítico para qualidade de dados

---

### 4. Automação (1 arquivo, 127 linhas)

**Arquivo**:
- `run-collectors-with-notifications.sh` - 127 linhas

**Função**: Script de execução com notificações WhatsApp

**Status**: ✅ Usado pelo systemd timer

---

### 📊 Total Código Ativo: **~16,500 linhas** (61 arquivos)

---

## 🔴 CÓDIGO LEGACY (One-time Scripts)

### Scripts de Importação/Migração (74 arquivos, ~4,500 linhas)

**Categorias**:

#### 1. Análises Regionais (10 arquivos, ~1,200 linhas)
```
analise-regional-simples.py             250 linhas
ANALISE-REGIONAL-FINAL.py               184 linhas
analise-regional-COMPLETA.py            183 linhas
analise-regional-CORRETA-FINAL.py       143 linhas
analise-global-tags.py                  112 linhas
analise-por-REGIOES.py                  111 linhas
analise-regional-por-tags-IA.py         101 linhas
analise-regional-OTIMIZADA.py            92 linhas
```
**Uso**: Scripts usados 1x para gerar `regional-research-data.json`

---

#### 2. Restauração de Dados (6 arquivos, ~500 linhas)
```
restore-trends-from-json.py              97 linhas
restore-trends-final.py                  84 linhas
restore-orgs-from-json.py                79 linhas
restore-trends-robust.py                 76 linhas
```
**Uso**: Importação de dados históricos (executado 1x)

---

#### 3. Migrações de Schema (8 arquivos, ~800 linhas)
```
auto-migrate-collectors.py              138 linhas
migrate-orgs-batch-v2.py                112 linhas
migrate-collectors-to-geo-helpers.py    105 linhas
migrate-orgs-batch.py                    87 linhas
migrate-orgs-v3.py                       74 linhas
```
**Uso**: Migração de collectors antigos para nova arquitetura

---

#### 4. Correções Pontuais (15 arquivos, ~1,200 linhas)
```
fix-all-errors.py                       128 linhas
fix-structure-and-data.py               121 linhas
fix-failed-tables.py                     99 linhas
debug-and-fix.py                         90 linhas
fix-tables-final.py                      83 linhas
fix-trends-schema-final.py               56 linhas
```
**Uso**: Correções executadas durante desenvolvimento

---

#### 5. Validações/Checks (20 arquivos, ~800 linhas)
```
check-universities-papers.py            150 linhas
check-authors-persons.py                 94 linhas
check-institutions.py                    71 linhas
check-table-structure.py                 64 linhas
check-person-roles.py                    54 linhas
check-catho-stats.py                     30 linhas
check-persons-structure.py               29 linhas
check-tables.py                          14 linhas
check_yc.py                              19 linhas
check_funding.py                         11 linhas
check_funding_schema.py                   8 linhas
```
**Uso**: Validações pontuais durante desenvolvimento

---

#### 6. Utilitários de Busca (5 arquivos, ~200 linhas)
```
find-duplicate-tables.py                167 linhas
find-trends-data.py                      87 linhas
find-columnist-tables.py                 46 linhas
find-paper-tables.py                     28 linhas
find-collectors-needing-migration.py     19 linhas
find_github_jsons.py                     16 linhas
```
**Uso**: Ferramentas de descoberta/auditoria (1x)

---

#### 7. Auto-geração (2 arquivos, ~150 linhas)
```
auto-add-normalization.py               116 linhas
add-metadata-column.py                   31 linhas
add_city_column.py                       14 linhas
```
**Uso**: Geração automática de código (1x)

---

### 📊 Total Legacy: **~4,500 linhas** (74 arquivos)

**Recomendação**: 🗑️ Mover para `archive/` ou deletar

---

## 📝 OUTROS ARQUIVOS

### Documentação (121 arquivos, 32,082 linhas)

**Principais**:
- `CLAUDE.md` - Contexto do projeto
- `DEPLOY_GUIDE.md` - Guia de deploy
- `WHATSAPP_GUIDE.md` - Integração WhatsApp
- `RAW-ANALYSIS-REPORTS.md` - Análise de qualidade
- `COMPLETE-CODE-QUALITY-REPORTS.md` - Relatórios
- + 116 outros arquivos de documentação

**Status**: ✅ Essencial para manutenção

---

### SQL/Migrations (101 arquivos, 11,865 linhas)

**Localização**: `migrations/`

**Conteúdo**:
- Schema evolution (CREATE TABLE, ALTER TABLE)
- Stored procedures/functions
- Data migrations
- Índices e constraints

**Status**: ✅ Histórico de evolução do banco

---

### Configs TypeScript (141 arquivos, 25,724 linhas)

**Localização**: `scripts/configs/`

**Conteúdo**:
- `tech-trends-config.ts` - Configurações de collectors
- `research-papers-config.ts` - Papers acadêmicos
- `jobs-config.ts` - Vagas de emprego
- `legacy-python-config.ts` - Collectors Python
- + 137 outros configs

**Status**: ✅ Configuração dos 70 collectors

---

## 🎯 RECOMENDAÇÕES

### 1. Limpeza Imediata (Prioridade Alta)

**Ação**: Mover scripts legacy para `archive/one-time-scripts/`

```bash
mkdir -p archive/one-time-scripts/{analises,restauracao,migracoes,fixes,checks,utils}

# Mover scripts por categoria
mv *analise*.py archive/one-time-scripts/analises/
mv restore-*.py archive/one-time-scripts/restauracao/
mv migrate-*.py archive/one-time-scripts/migracoes/
mv fix-*.py archive/one-time-scripts/fixes/
mv check-*.py archive/one-time-scripts/checks/
mv find-*.py archive/one-time-scripts/utils/
mv auto-*.py archive/one-time-scripts/utils/
mv add-*.py archive/one-time-scripts/utils/
```

**Impacto**: 
- Reduz confusão sobre o que está ativo
- Mantém histórico para referência
- Facilita navegação no projeto

---

### 2. Foco na Análise de Qualidade (Prioridade Crítica)

**Código que REALMENTE importa** (16,500 linhas):

#### Prioridade 1 - Collectors Críticos (3 arquivos, 955 linhas)
- `collect-mdic-comexstat.py` - 330 linhas ⚠️ Score 7.41/10
- `collect-fiesp-data.py` - 417 linhas ⚠️ Score 5.84/10
- `collect-infojobs-web-scraper.py` - 208 linhas ✅ Score 8.04/10

**Ação**: Refatorar funções D-rated (4 funções com complexidade >20)

---

#### Prioridade 2 - Helpers (2 arquivos, 739 linhas)
- `geo_helpers.py` - 548 linhas
- `org_helpers.py` - 191 linhas

**Ação**: Revisar normalização e adicionar testes

---

#### Prioridade 3 - Core (3 arquivos, 971 linhas)
- `collect.ts` - 216 linhas
- `generate-crontab.ts` - 332 linhas
- `sofia_whatsapp_integration.py` - 423 linhas

**Ação**: Adicionar error handling robusto

---

#### Prioridade 4 - Outros Collectors (52 arquivos, ~13,800 linhas)

**Ação**: Análise gradual (5-10 collectors por semana)

---

### 3. Documentação do Código Ativo

**Criar**: `ACTIVE_CODE_INVENTORY.md`

**Conteúdo**:
- Lista de todos os 70 collectors ativos
- Função de cada um
- Frequência de execução
- Dependências
- Owner/Maintainer

---

## 📊 MÉTRICAS REVISADAS

### Código Ativo (Produção)

| Métrica | Valor Anterior | Valor Real | Diferença |
|:---|---:|---:|---:|
| Total de Linhas | 130,567 | 16,500 | **-87.4%** |
| Arquivos Python | 261 | 55 | **-78.9%** |
| Complexidade Média | B (8.48) | B (8.48) | Igual |
| Manutenibilidade | A (51.5) | A (51.5) | Igual |

**Conclusão**: O código ativo é **muito menor** do que parecia, mas a qualidade se mantém.

---

### Estimativa de Refatoração Revisada

**Antes** (assumindo 130k linhas):
- Análise completa: ~40 horas
- Refatoração crítica: ~80 horas
- Implementação: ~160 horas

**Depois** (apenas 16.5k linhas ativas):
- Análise completa: **~8 horas** ✅
- Refatoração crítica: **~16 horas** ✅
- Implementação: **~32 horas** ✅

**Economia**: **75% menos tempo** focando apenas no código ativo!

---

## ✅ PRÓXIMOS PASSOS

1. **Hoje**: Mover scripts legacy para `archive/`
2. **Esta semana**: Refatorar 4 funções D-rated
3. **Próxima semana**: Analisar 10 collectors mais críticos
4. **Mês 1**: Refatorar todos os collectors com score <7.0
5. **Mês 2**: Adicionar testes automatizados
6. **Mês 3**: Implementar CI/CD com quality gates

---

*Relatório gerado em: 2025-12-29 11:43 BRT*
