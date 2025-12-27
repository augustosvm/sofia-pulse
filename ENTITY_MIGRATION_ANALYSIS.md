# 📊 Análise de Migração para Persons e Organizations

## ✅ JÁ NORMALIZADO

### Jobs → Organizations
- **jobs** (10,549 registros): ✅ JÁ TEM `organization_id`
- Integração completa via `get_or_create_organization()`

### Authors → Persons
- **authors** (245,965 registros): ✅ JÁ integrado via `author_id`
- Relação via `paper_authors` e `person_papers`

---

## 🏢 DEVEM MIGRAR PARA ORGANIZATIONS

### Priority 1 - Alto Volume (>1k registros)

#### 1. space_industry (6,500 registros)
```sql
company: 'Soviet Space Program', 'SpaceX', etc.
```
**Ação**: Adicionar `organization_id`, migrar via `get_or_create_organization(company)`

#### 2. funding_rounds (7,097 registros)
```sql
company_name: 'OpenAI', 'Anthropic', etc.
```
**Ação**: Adicionar `organization_id`, migrar via `get_or_create_organization(company_name)`
**Benefício**: Correlacionar funding com jobs da mesma empresa

#### 3. tech_jobs (3,675 registros)
```sql
company: 'LÖWEN ENTERTAINMENT GmbH', etc.
```
**Ação**: Adicionar `organization_id`, migrar via `get_or_create_organization(company)`

### Priority 2 - Médio Volume (100-1k registros)

#### 4. global_universities_progress (370 registros)
```sql
institution_name: 'Universidade Estadual de Campinas (UNICAMP)'
institution_id: 'https://openalex.org/I181391015'
```
**Ação**: Migrar para organizations com type='university'

#### 5. world_ngos (200 registros)
```sql
name: 'Welthungerhilfe', 'UNICEF', etc.
```
**Ação**: Migrar para organizations com type='ngo'

#### 6. hdx_humanitarian_data (196 registros)
```sql
organization: 'unhcr', 'unicef', etc.
```
**Ação**: Adicionar `organization_id`

#### 7. hkex_ipos (97 registros)
```sql
company: 'ByteDance AI Division'
company_cn: '字节跳动人工智能'
```
**Ação**: Adicionar `organization_id`

### Priority 3 - Baixo Volume (<100 registros)

#### 8. startups (80 registros)
```sql
name: 'AI/ML Startup 9'
```
**Ação**: Migrar para organizations com type='startup'

#### 9. nih_grants (52 registros)
```sql
organization: 'UNIVERSITY OF TEXAS MED BR GALVESTON'
```
**Ação**: Adicionar `organization_id`

#### 10. exits (1 registro)
```sql
startup_name: 'Future Health ESG Corp.'
```
**Ação**: Adicionar `organization_id`

#### 11. sports_federations (0 registros)
```sql
federation_name: (vazio ainda)
```
**Ação**: Quando houver dados, adicionar `organization_id`

---

## 👤 DEVEM MIGRAR PARA PERSONS

### Priority 1 - Papers/Research

#### 1. research_papers (8,028 registros)
```sql
authors: ['Meta AI', 'Thomas Anderson', 'Lisa Martinez']
```
**Ação**: Extrair array de autores, criar/linkar persons para cada um

#### 2. publications (350 registros)
```sql
authors: ['Yibo Miao', 'Yifan Zhu', ...]
```
**Ação**: Extrair array de autores, criar/linkar persons

#### 3. arxiv_ai_papers (245 registros)
```sql
authors: ['Junze Ye', 'Daniel Tawfik', ...]
```
**Ação**: Extrair array de autores, criar/linkar persons

#### 4. openalex_papers (69 registros)
```sql
authors: ['Raphael Labaca-Castro']
```
**Ação**: Extrair array de autores, criar/linkar persons

### Priority 2 - Social Media

#### 5. hackernews_stories (832 registros)
```sql
author: 'tonyhb'
```
**Ação**: Adicionar `person_id`, criar persons com source='hackernews'

#### 6. reddit_tech (300 registros)
```sql
author: 'Helpful_Geologist430'
```
**Ação**: Adicionar `person_id`, criar persons com source='reddit'

---

## ❌ NÃO MIGRAR (Não são Entities)

### Tabelas com "name" mas não são pessoas/organizações:

- **tech_trends** (4,314) - name = 'DigitalPlatDev/FreeDomain' (repo names)
- **npm_stats** (441) - package_name = 'react' (packages)
- **pypi_stats** (821) - package_name = 'numpy' (packages)
- **stackoverflow_trends** (100) - tag_name = '.net' (tags)
- **countries** (195) - common_name = 'United States' (já normalizado)
- **cities** (1,074) - name = 'New York' (já normalizado)
- **states** (385) - name = 'California' (já normalizado)
- **religions** (22) - name = 'afro_brazilian' (categorias)
- **currency_rates** (11) - currency_name = 'Chinese Yuan' (moedas)
- **developer_tools** (100) - tool_name = 'Python Debugger' (ferramentas)
- **socioeconomic_indicators** (94,704) - indicator_name (métricas)
- **gender_indicators** (874,391) - indicator_name (métricas)
- **who_health_data** (48,091) - indicator_name (métricas)

---

## 📋 RESUMO EXECUTIVO

### Organizations - 11 tabelas para migrar
| Tabela | Registros | Priority | Benefício |
|:---|---:|:---|:---|
| space_industry | 6,500 | 🔴 Alta | Tracking de empresas espaciais |
| funding_rounds | 7,097 | 🔴 Alta | Correlação funding+jobs |
| tech_jobs | 3,675 | 🔴 Alta | Normalização de empresas |
| global_universities_progress | 370 | 🟡 Média | Tracking universidades |
| world_ngos | 200 | 🟡 Média | Normalização NGOs |
| hdx_humanitarian_data | 196 | 🟡 Média | Linking organizações humanitárias |
| hkex_ipos | 97 | 🟢 Baixa | IPOs Hong Kong |
| startups | 80 | 🟢 Baixa | Startups genéricas |
| nih_grants | 52 | 🟢 Baixa | Grants de pesquisa |
| exits | 1 | 🟢 Baixa | Exits/acquisitions |
| sports_federations | 0 | 🟢 Baixa | Quando houver dados |

**Total**: ~18k registros para normalizar

### Persons - 6 tabelas para migrar
| Tabela | Registros | Priority | Benefício |
|:---|---:|:---|:---|
| research_papers | 8,028 | 🔴 Alta | Autores de papers |
| hackernews_stories | 832 | 🟡 Média | Autores HN |
| publications | 350 | 🟡 Média | Autores acadêmicos |
| reddit_tech | 300 | 🟡 Média | Usuários Reddit |
| arxiv_ai_papers | 245 | 🟡 Média | Autores ArXiv |
| openalex_papers | 69 | 🟢 Baixa | Autores OpenAlex |

**Total**: ~9.8k registros (mas authors são arrays, pode gerar 50k+ persons)

---

## 🚀 PRÓXIMOS PASSOS

### Fase 1: Organizations (Priority 1)
1. ✅ jobs → JÁ FEITO
2. funding_rounds → Adicionar organization_id + backfill
3. space_industry → Adicionar organization_id + backfill
4. tech_jobs → Adicionar organization_id + backfill

### Fase 2: Organizations (Priority 2-3)
5. global_universities_progress, world_ngos, hdx_humanitarian_data
6. hkex_ipos, startups, nih_grants, exits

### Fase 3: Persons (Papers)
7. research_papers → Extrair autores + criar persons
8. publications, arxiv_ai_papers, openalex_papers

### Fase 4: Persons (Social)
9. hackernews_stories, reddit_tech

---

## 📊 IMPACTO ESTIMADO

**Organizations**: 18k novos registros (deduplicados ~5k únicos)
**Persons**: 50k+ novos registros (deduplicados ~20k únicos)

**Benefícios**:
- 🔗 Correlação funding ↔ jobs ↔ tech trends
- 📈 Tracking de empresas across múltiplas fontes
- 👥 Network analysis de autores/colaboradores
- 🎯 Deduplicação automática via normalized_name
