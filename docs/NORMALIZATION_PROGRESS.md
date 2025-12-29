# 📊 Progresso da Normalização Geográfica

**Data**: 2025-12-26
**Status**: 🟡 EM PROGRESSO

---

## ✅ FASE 1 COMPLETA: Imports Adicionados

### Implementação Manual Completa (2 collectors)

✅ **collect-infojobs-web-scraper.py**
- Status: 100% completo
- Mudanças:
  - ✅ Import adicionado
  - ✅ normalize_location() implementado
  - ✅ INSERTs atualizados com country_id, state_id, city_id
  - ✅ ON CONFLICT atualizado
- Resultado: Pronto para produção

✅ **collect-brazil-security.py**
- Status: 100% completo
- Mudanças:
  - ✅ Import adicionado
  - ✅ ALTER TABLE para adicionar colunas (country_id, state_id, city_id)
  - ✅ normalize_location() implementado em 3 tipos de dados:
    - state_level (3 INSERTs)
    - city_level (1 INSERT)
    - datasus (1 INSERT)
  - ✅ ON CONFLICT atualizado
- Resultado: Pronto para produção

### Imports Automáticos Adicionados (25 collectors)

Script `auto-migrate-collectors.py` adicionou imports em:

| Collector | Import | INSERTs Pendentes |
|:---|:---:|:---:|
| collect-acled-conflicts.py | ✅ | 0 (já normalizado?) |
| collect-drugs-data.py | ✅ | 5 |
| collect-energy-global.py | ✅ | 1 |
| collect-mdic-comexstat.py | ✅ | 1 |
| collect-sports-regional.py | ✅ | 4 |
| collect-world-security.py | ✅ | 1 |
| collect-cepal-latam.py | ✅ | 2 |
| collect-electricity-consumption.py | ✅ | 0 (já normalizado?) |
| collect-fao-agriculture.py | ✅ | 1 |
| collect-hdx-humanitarian.py | ✅ | 1 |
| collect-ilostat.py | ✅ | 1 |
| collect-port-traffic.py | ✅ | 1 |
| collect-religion-data.py | ✅ | 1 |
| collect-semiconductor-sales.py | ✅ | 1 |
| collect-socioeconomic-indicators.py | ✅ | 1 |
| collect-sports-federations.py | ✅ | 2 |
| collect-unicef.py | ✅ | 1 |
| collect-who-health.py | ✅ | 1 |
| collect-women-brazil.py | ✅ | 3 |
| collect-women-ilostat.py | ✅ | 1 |
| collect-women-world-bank.py | ✅ | 1 |
| collect-world-bank-gender.py | ✅ | 1 |
| collect-world-sports.py | ✅ | 3 |
| collect-sec-edgar-funding.py | ✅ | 0 (tabela não existe?) |
| collect-world-ngos.py | ✅ | 0 (já normalizado?) |
| collect-women-fred.py | ✅ | 0 (já normalizado?) |

**Total de INSERTs pendentes**: ~34 INSERTs em 20 collectors

---

## ⏳ FASE 2 PENDENTE: Atualizar INSERTs

### Template de Implementação

Para cada collector que tem INSERTs pendentes:

```python
# ANTES do INSERT, adicionar:
location = normalize_location(conn, {
    'country': country_name_or_code,  # Ajustar variável conforme collector
    'state': state_name,              # Se houver
    'city': city_name                 # Se houver
})
country_id = location['country_id']
state_id = location['state_id']      # Se houver state
city_id = location['city_id']        # Se houver city

# NO INSERT, adicionar colunas:
INSERT INTO sofia.table_name
(..., country_code, country_id, state_id, city_id, ...)  # Adicionar IDs
VALUES (%s, %s, %s, %s, ...)

# NO ON CONFLICT, adicionar:
ON CONFLICT (...) DO UPDATE SET
    value = EXCLUDED.value,
    country_id = EXCLUDED.country_id,
    state_id = EXCLUDED.state_id,
    city_id = EXCLUDED.city_id
```

### Prioridade Alta (8 collectors - 5+ campos ou estratégicos)

1. **collect-drugs-data.py** (5 INSERTs)
   - Campos: state_name, state_code, region, country_name, country_code
   - Ação: Normalizar country_id e state_id

2. **collect-sports-regional.py** (4 INSERTs)
   - Campos: regional_federation, region, country_name, country_code
   - Ação: Normalizar country_id

3. **collect-world-sports.py** (3 INSERTs)
   - Campos: country_code
   - Ação: Normalizar country_id

4. **collect-women-brazil.py** (3 INSERTs)
   - Campos: region
   - Ação: Normalizar state_id (região = estado no Brasil)

5. **collect-sports-federations.py** (2 INSERTs)
   - Campos: country_name, country_code
   - Ação: Normalizar country_id + criar organization_id

6. **collect-cepal-latam.py** (2 INSERTs)
   - Campos: country_name, country_code
   - Ação: Normalizar country_id

7. **collect-mdic-comexstat.py** (1 INSERT)
   - Campos: state_code, country_name, country_code
   - Ação: Normalizar country_id e state_id

8. **collect-hdx-humanitarian.py** (1 INSERT)
   - Campos: country_codes (múltiplos)
   - Ação: Normalizar primary country_id

### Prioridade Média (12 collectors - 1 campo country)

9. collect-energy-global.py (1 INSERT)
10. collect-world-security.py (1 INSERT)
11. collect-fao-agriculture.py (1 INSERT)
12. collect-ilostat.py (1 INSERT)
13. collect-port-traffic.py (1 INSERT)
14. collect-religion-data.py (1 INSERT)
15. collect-semiconductor-sales.py (1 INSERT)
16. collect-socioeconomic-indicators.py (1 INSERT)
17. collect-unicef.py (1 INSERT)
18. collect-who-health.py (1 INSERT)
19. collect-women-ilostat.py (1 INSERT)
20. collect-women-world-bank.py (1 INSERT)
21. collect-world-bank-gender.py (1 INSERT)

---

## 📊 COLLECTORS TYPESCRIPT (18 pendentes)

### Alta Prioridade (7 collectors)

1. **collect-catho-stealth.ts** - country, location, city
2. **collect-catho-working.ts** - location, company
3. **collect-google-maps-locations.ts** - formatted_address, country, location, address, city
4. **collect-openalex.ts** - country, location, organization_name
5. **collect-space-industry.ts** - country, location
6. **collect-cardboard-production.ts** - country
7. **collect-epo-patents.ts** - country

### Média Prioridade (11 collectors)

8. collect-arxiv-ai.ts
9. collect-gdelt.ts
10. collect-rest-countries.ts
11. collect-wipo-china-patents.ts
12. collect-ai-github-trends.ts
13. collect-ai-npm-packages.ts
14. collect-arxiv-ai-v2.ts
15. collect-gitguardian-incidents.ts
16. collect-github-trending.ts
17. collect-npm-stats.ts
18. collect-pypi-stats.ts

---

## 📈 ESTATÍSTICAS FINAIS

| Métrica | Valor | % |
|:---|---:|---:|
| **Total collectors com localização** | 73 | 100% |
| **Com import normalize_location** | 51 | 69.9% |
| **Totalmente normalizados** | 24 | 32.9% |
| **Precisam atualizar INSERTs** | 27 | 37.0% |
| **Sem localização** | 21 | N/A |

### Breakdown por Tipo

| Tipo | Total | Completo | Import Apenas | Sem Import |
|:---|---:|---:|---:|---:|
| **Python** | 55 | 12 | 25 | 18 |
| **TypeScript** | 39 | 12 | 0 | 27 |
| **TOTAL** | 94 | 24 | 25 | 45 |

---

## 🚀 PRÓXIMOS PASSOS RECOMENDADOS

### Opção 1: Continuar Manualmente (Mais Confiável)

**Tempo estimado**: 4-6 horas
**Vantagem**: Controle total, pode testar cada um
**Desvantagem**: Trabalhoso

1. Pegar lista de "Prioridade Alta" (8 Python + 7 TypeScript = 15)
2. Implementar um por um seguindo template
3. Testar cada collector após mudança
4. Commit incremental

### Opção 2: Script Semi-Automatizado (Mais Rápido)

**Tempo estimado**: 2-3 horas
**Vantagem**: Mais rápido
**Desvantagem**: Precisa revisar tudo depois

1. Criar script que modifica padrões comuns
2. Rodar em batch nos collectors similares
3. Revisar e testar todos
4. Corrigir manualmente os que quebraram

### Opção 3: Faseada (Recomendada)

**Tempo estimado**: 6-8 horas distribuídas
**Vantagem**: Incremental, menor risco
**Desvantagem**: Leva mais tempo total

**Fase 2A**: Alta prioridade Python (8 collectors)
- Implementar manualmente
- Testar e comitar
- Deploy e monitorar

**Fase 2B**: Alta prioridade TypeScript (7 collectors)
- Implementar manualmente
- Testar e comitar
- Deploy e monitorar

**Fase 2C**: Média prioridade (23 collectors)
- Usar scripts semi-automatizados
- Revisar e testar em batch
- Deploy final

---

## ✅ VALIDAÇÃO

Para verificar se um collector está 100% normalizado:

```bash
# 1. Verificar import
grep "normalize_location" scripts/collect-*.py

# 2. Verificar uso em INSERTs
grep -A5 "normalize_location(conn" scripts/collect-*.py

# 3. Verificar campos no INSERT
grep -A3 "country_id" scripts/collect-*.py

# 4. Testar collector
python3 scripts/collect-<nome>.py

# 5. Verificar no banco
SELECT COUNT(*), COUNT(country_id) FROM sofia.<tabela>;
```

---

## 📝 NOTAS

- **Scripts criados**:
  - `auto-migrate-collectors.py` - Adiciona imports automaticamente
  - `analyze-collectors-data-model.py` - Análise completa dos collectors
  - `MIGRATION_PLAN_COMPLETE.md` - Plano detalhado

- **Arquivos atualizados**:
  - `collect-infojobs-web-scraper.py` ✅
  - `collect-brazil-security.py` ✅
  - 25 collectors com imports adicionados

- **Próximo bloqueador**: Tempo manual para atualizar INSERTs

---

**Status**: 🟡 69.9% imports adicionados, 32.9% totalmente normalizado
**Próxima Ação**: Decidir entre Opção 1, 2 ou 3 para continuar

*Última Atualização: 2025-12-26 20:00*
