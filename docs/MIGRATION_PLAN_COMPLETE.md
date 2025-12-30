# 📊 PLANO COMPLETO DE MIGRAÇÃO - Normalização Geográfica e Entidades

**Data**: 2025-12-26
**Análise**: 94 collectors (55 Python + 39 TypeScript)

---

## 🎯 RESUMO EXECUTIVO

### Status Atual

| Categoria | Total | Implementado | Pendente | % Completo |
|:---|---:|---:|---:|---:|
| **Normalização Geográfica** | 73 collectors | 24 | **49** | 32.9% |
| **Migração para Organizations** | 5 collectors | 0 | **5** | 0% |
| **Migração para Persons** | 0 collectors | 0 | 0 | N/A |

### Collectors com Localização

| Linguagem | Total | Normalizados | Pendentes | % |
|:---|---:|---:|---:|---:|
| Python | 43 | 12 | 31 | 27.9% |
| TypeScript | 30 | 12 | 18 | 40.0% |
| **TOTAL** | **73** | **24** | **49** | **32.9%** |

---

## 📋 PARTE 1: NORMALIZAÇÃO GEOGRÁFICA

### ✅ Já Implementados (24 collectors)

#### Python com normalize_location() (12):
1. ✅ collect-careerjet-api.py
2. ✅ collect-central-banks-women.py
3. ✅ collect-focused-areas.py
4. ✅ collect-freejobs-api.py
5. ✅ collect-himalayas-api.py
6. ✅ collect-infojobs-brasil.py
7. ✅ collect-rapidapi-activejobs.py
8. ✅ collect-rapidapi-linkedin.py
9. ✅ collect-serpapi-googlejobs.py
10. ✅ collect-theirstack-api.py
11. ✅ collect-women-eurostat.py
12. ✅ collect-world-tourism.py

#### TypeScript com normalizeLocation() (12):
1. ✅ collect-jobs-adzuna.ts
2. ✅ collect-jobs-arbeitnow.ts
3. ✅ collect-jobs-findwork.ts
4. ✅ collect-jobs-github.ts
5. ✅ collect-jobs-himalayas.ts
6. ✅ collect-jobs-remoteok.ts
7. ✅ collect-jobs-themuse.ts
8. ✅ collect-jobs-usajobs.ts
9. ✅ collect-jobs-weworkremotely.ts
10. ✅ (3 outros jobs collectors)

---

### ❌ PRIORIDADE ALTA - Normalização Urgente (15 collectors)

**Critério**: 3+ campos geográficos OU alta importância estratégica

#### Python (8):

1. **collect-acled-conflicts.py** (5 campos)
   - Tabela: acled_aggregated
   - Campos: country, region, state, admin1, admin2
   - **Ação**: Adicionar normalize_location() para country_id

2. **collect-brazil-security.py** (5 campos)
   - Tabela: brazil_security_data
   - Campos: state, region_name, region_type, region_code, city
   - **Ação**: Normalizar state_id e city_id

3. **collect-drugs-data.py** (5 campos)
   - Tabela: world_drugs_data
   - Campos: state_name, state_code, region, country_name, country_code
   - **Ação**: Normalizar country_id e state_id

4. **collect-energy-global.py** (4 campos)
   - Tabela: energy_global_data
   - Campos: country_code, country_name, region, subregion
   - **Ação**: Normalizar country_id

5. **collect-infojobs-web-scraper.py** (4 campos)
   - Tabela: jobs
   - Campos: country_id, state_id, city_id, location
   - **Ação**: Já tem os campos, só adicionar normalize_location()

6. **collect-mdic-comexstat.py** (3 campos)
   - Tabela: comexstat_trade
   - Campos: state_code, country_name, country_code
   - **Ação**: Normalizar country_id e state_id

7. **collect-sports-regional.py** (4 campos)
   - Tabela: sports_regional
   - Campos: regional_federation, region, country_name, country_code
   - **Ação**: Normalizar country_id

8. **collect-world-security.py** (3 campos)
   - Tabela: world_security_data
   - Campos: country_code, country_name, region
   - **Ação**: Normalizar country_id

#### TypeScript (7):

9. **collect-catho-stealth.ts**
   - Campos: country, location, city
   - **Ação**: Adicionar normalizeLocation()

10. **collect-catho-working.ts**
    - Campos: location, company
    - **Ação**: Adicionar normalizeLocation() + link organization

11. **collect-google-maps-locations.ts**
    - Campos: formatted_address, country, location, address, city
    - **Ação**: Normalizar todos os níveis geográficos

12. **collect-openalex.ts**
    - Campos: country, location, organization_name
    - **Ação**: Normalizar + criar organization

13. **collect-space-industry.ts**
    - Campos: country, location
    - **Ação**: Normalizar country_id

14. **collect-cardboard-production.ts**
    - Campos: country
    - **Ação**: Normalizar country_id

15. **collect-epo-patents.ts**
    - Campos: country
    - **Ação**: Normalizar country_id

---

### ⚠️ PRIORIDADE MÉDIA - Normalização Importante (34 collectors)

**Critério**: 1-2 campos geográficos

#### Python (23):

1. collect-cepal-latam.py → country_code, country_name
2. collect-electricity-consumption.py → country_code, country_name
3. collect-energy-consumption.py → country_code
4. collect-fao-agriculture.py → country_code, country_name
5. collect-fiesp-data.py → region
6. collect-hdx-humanitarian.py → country_codes
7. collect-ilostat.py → country_code
8. collect-port-traffic.py → country_code, country_name
9. collect-producthunt-api.py → location
10. collect-religion-data.py → country_code, country_name
11. collect-sec-edgar-funding.py → country
12. collect-semiconductor-sales.py → region
13. collect-socioeconomic-indicators.py → country_code, country_name
14. collect-sports-federations.py → country_code, country_name
15. collect-unicef.py → country_code, country_name
16. collect-who-health.py → country_code
17. collect-women-brazil.py → region
18. collect-women-fred.py → country (provavelmente USA)
19. collect-women-ilostat.py → country_code, country_name
20. collect-women-world-bank.py → country_code, country_name
21. collect-world-bank-gender.py → country_code, country_name
22. collect-world-ngos.py → headquarters_country
23. collect-world-sports.py → country_code

#### TypeScript (11):

24. collect-arxiv-ai.ts → location
25. collect-gdelt.ts → country
26. collect-rest-countries.ts → country
27. collect-wipo-china-patents.ts → city
28. collect-ai-github-trends.ts
29. collect-ai-npm-packages.ts
30. collect-arxiv-ai-v2.ts
31. collect-gitguardian-incidents.ts
32. collect-github-trending.ts
33. collect-npm-stats.ts
34. collect-pypi-stats.ts

---

## 📋 PARTE 2: MIGRAÇÃO PARA ORGANIZATIONS

### Collectors com company_name/organization_name (5):

1. **collect-sec-edgar-funding.py**
   - Campo: company_name
   - **Ação**: Criar organization_id + link funding

2. **collect-sports-federations.py**
   - Campo: federation_name
   - **Ação**: Criar organization_id para federações

3. **collect-wto-trade.py**
   - Campo: partner_name
   - **Ação**: Partner pode ser organization

4. **collect-yc-companies.py**
   - Campo: company_name
   - **Ação**: Criar organization_id + link funding

5. **collect-openalex.ts**
   - Campo: organization_name
   - **Ação**: Criar organization_id para instituições

---

## 📋 PARTE 3: COLLECTORS AMBÍGUOS (43)

**Status**: Precisam análise manual para determinar se são:
- Dados agregados (não precisam de entities)
- Precisam de normalização geográfica apenas
- Precisam de organizations/persons

**Exemplos**:
- collect-ai-arxiv-keywords.py → papers (não é entity)
- collect-bacen-sgs.py → séries temporais (não é entity)
- collect-brazil-ministries.py → dados governamentais
- collect-cni-indicators.py → indicadores industriais

---

## 🚀 PLANO DE IMPLEMENTAÇÃO

### FASE 1: Normalização Geográfica Alta Prioridade (15 collectors)

**Tempo estimado**: 2-3 dias

**Checklist por collector**:
- [ ] Adicionar import: `from shared.geo_helpers import normalize_location` (Python) ou `import { normalizeLocation } from './shared/geo-helpers'` (TS)
- [ ] Antes do INSERT, adicionar:
  ```python
  location = normalize_location(conn, {'country': country_name, 'state': state_name, 'city': city_name})
  country_id = location['country_id']
  state_id = location['state_id']
  city_id = location['city_id']
  ```
- [ ] Atualizar INSERT para incluir `country_id`, `state_id`, `city_id`
- [ ] Atualizar ON CONFLICT para atualizar os IDs
- [ ] Testar collector
- [ ] Verificar coverage no banco

**Ordem sugerida**:
1. collect-infojobs-web-scraper.py (mais fácil - só adicionar normalize)
2. collect-brazil-security.py (dados brasileiros importantes)
3. collect-acled-conflicts.py (dados de conflitos - alta relevância)
4. collect-catho-working.ts (jobs Brasil)
5. collect-google-maps-locations.ts (dados geográficos puros)
6. ... continuar pelos 10 restantes

### FASE 2: Migração para Organizations (5 collectors)

**Tempo estimado**: 1-2 dias

**Checklist por collector**:
- [ ] Adicionar import: `from shared.org_helpers import get_or_create_organization` (Python) ou similar (TS)
- [ ] Antes do INSERT:
  ```python
  organization_id = get_or_create_organization(conn, {
      'name': company_name,
      'country': country_name,
      'metadata': {...}
  })
  ```
- [ ] Atualizar INSERT para incluir `organization_id`
- [ ] Criar foreign key se não existir
- [ ] Testar collector

**Ordem sugerida**:
1. collect-yc-companies.py (já tem estrutura de companies)
2. collect-sec-edgar-funding.py (funding data)
3. collect-openalex.ts (instituições acadêmicas)
4. collect-sports-federations.py (federações esportivas)
5. collect-wto-trade.py (parceiros comerciais)

### FASE 3: Normalização Média Prioridade (34 collectors)

**Tempo estimado**: 3-5 dias

Seguir mesmo padrão da Fase 1.

### FASE 4: Backfill Dados Antigos

**Tempo estimado**: 1 dia

**Tabelas que precisam de backfill**:
- jobs (72.3% → objetivo 95%)
- persons (56.1% → objetivo 95%)
- Qualquer nova tabela migrada na Fase 1-3

**Script**:
```bash
npx tsx scripts/backfill-all-geographic-ids.ts
```

---

## 📊 MÉTRICAS DE SUCESSO

### Normalização Geográfica

| Métrica | Antes | Meta | Status Atual |
|:---|---:|---:|:---|
| Collectors normalizados | 24/73 | 73/73 | 32.9% |
| Coverage country_id | ~85% | >95% | Em progresso |
| Coverage state_id | ~60% | >90% | Em progresso |
| Coverage city_id | ~50% | >85% | Em progresso |

### Organizations

| Métrica | Meta |
|:---|---:|
| Collectors com organization_id | 5/5 (100%) |
| Deduplicação de companies | >95% |
| Link jobs ↔ organizations | >90% |

---

## ⚠️ RISCOS E MITIGAÇÕES

### Risco 1: API Rate Limits
**Mitigação**: Testar collectors individualmente, não rodar todos de uma vez

### Risco 2: Dados Antigos Sem Normalização
**Mitigação**: Backfill progressivo por tabela, com validação

### Risco 3: Performance de Lookups
**Mitigação**: geo_helpers já tem cache interno, monitorar tempo de execução

### Risco 4: Campos Geográficos Inconsistentes
**Mitigação**: CITY_NAME_FIXES e filtros já implementados, expandir conforme necessário

---

## 📝 TEMPLATE DE IMPLEMENTAÇÃO

### Python:
```python
#!/usr/bin/env python3
from shared.geo_helpers import normalize_location
# ... resto dos imports

def save_to_database(conn, records):
    cursor = conn.cursor()

    for record in records:
        # Normalizar localização
        location = normalize_location(conn, {
            'country': record.get('country_name'),
            'state': record.get('state_name'),
            'city': record.get('city_name')
        })

        country_id = location['country_id']
        state_id = location['state_id']
        city_id = location['city_id']

        cursor.execute("""
            INSERT INTO sofia.table_name
            (..., country, country_id, state, state_id, city, city_id, ...)
            VALUES (%s, %s, %s, %s, %s, %s, ...)
            ON CONFLICT (...) DO UPDATE SET
                value = EXCLUDED.value,
                country_id = EXCLUDED.country_id,
                state_id = EXCLUDED.state_id,
                city_id = EXCLUDED.city_id
        """, (..., country, country_id, state, state_id, city, city_id, ...))

    conn.commit()
```

### TypeScript:
```typescript
import { normalizeLocation } from './shared/geo-helpers';

async function saveToDatabase(records: any[]) {
  for (const record of records) {
    const location = await normalizeLocation(pool, {
      country: record.country,
      state: record.state,
      city: record.city
    });

    await pool.query(`
      INSERT INTO sofia.table_name
      (..., country, country_id, state, state_id, city, city_id, ...)
      VALUES ($1, $2, $3, $4, $5, $6, ...)
      ON CONFLICT (...) DO UPDATE SET
        value = EXCLUDED.value,
        country_id = EXCLUDED.country_id,
        state_id = EXCLUDED.state_id,
        city_id = EXCLUDED.city_id
    `, [..., country, location.countryId, state, location.stateId, city, location.cityId, ...]);
  }
}
```

---

## ✅ CHECKLIST GERAL

### Antes de Começar:
- [ ] Backup do banco de dados
- [ ] Documentar estado atual (MIGRATION_PLAN_COMPLETE.md) ✅
- [ ] Criar branch: `feature/complete-geo-normalization`

### Durante Implementação:
- [ ] Fase 1: 15 collectors alta prioridade
- [ ] Fase 2: 5 collectors organizations
- [ ] Fase 3: 34 collectors média prioridade
- [ ] Fase 4: Backfill dados antigos

### Após Implementação:
- [ ] Verificar coverage em todas as tabelas (>95%)
- [ ] Atualizar documentação
- [ ] Commit e push
- [ ] Deploy para produção
- [ ] Monitorar por 24h

---

**Status**: 🟡 PLANEJAMENTO COMPLETO
**Próximo Passo**: Iniciar Fase 1 (15 collectors alta prioridade)

*Última Atualização: 2025-12-26*
