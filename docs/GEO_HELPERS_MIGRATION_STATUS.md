# 📍 Status da Migração para geo_helpers

**Data**: 2025-12-26
**Status**: ✅ FASE 1 COMPLETA - Imports Adicionados

---

## ✅ O Que Foi Feito

### Fase 1: Adicionar Imports (COMPLETO)

**33 collectors Python** agora têm acesso a `geo_helpers`:

```python
from shared.geo_helpers import normalize_location
```

**Collectors migrados:**
- ✅ Dados de mulheres (6): central-banks-women, women-eurostat, women-ilostat, women-world-bank, women-brazil, women-fred
- ✅ Dados econômicos (8): cepal-latam, cni-indicators, fao-agriculture, fiesp-data, mdic-comexstat, port-traffic, electricity-consumption, energy-global
- ✅ Dados sociais (7): ilostat, socioeconomic-indicators, unicef, who-health, religion-data, hdx-humanitarian, drugs-data
- ✅ Dados regionais (3): brazil-ministries, brazil-security, basedosdados
- ✅ Dados de esportes (2): sports-federations, sports-regional
- ✅ Dados mundiais (4): world-ngos, world-security, world-sports, world-tourism
- ✅ Outros (3): world-bank-gender, yc-companies, sec-edgar-funding

---

## ⚠️ Próximos Passos

### Fase 2: Usar normalize_location() nos INSERTs

Cada collector agora precisa:

1. **Antes do INSERT**, normalizar os dados geográficos:
   ```python
   # Exemplo:
   conn = psycopg2.connect(**DB_CONFIG)

   # Normalizar localização
   location = normalize_location(conn, {
       'country': country_name,  # ex: "Brazil", "USA", "France"
       'state': state_name,      # ex: "California", "São Paulo"
       'city': city_name         # ex: "San Francisco", "Rio de Janeiro"
   })

   country_id = location['country_id']
   state_id = location['state_id']
   city_id = location['city_id']
   ```

2. **No INSERT**, incluir os IDs normalizados:
   ```python
   cursor.execute("""
       INSERT INTO sofia.tabela (
           ..., country, country_id, state_id, city_id, ...
       ) VALUES (%s, %s, %s, %s, ...)
   """, (..., country_name, country_id, state_id, city_id, ...))
   ```

---

## 📊 Cobertura Atual

| Tipo | Com Import | Com Normalização | %  |
|:---|---:|---:|---:|
| **Job Collectors** | 19/19 | 19/19 | 100% |
| **Outros Collectors** | 33/33 | 0/33 | 0% |
| **TOTAL** | 52/52 | 19/52 | 37% |

---

## 🎯 Benefícios da Normalização Completa

Quando todos os collectors usarem `normalize_location()`:

1. ✅ **Dados consistentes** - Todos os collectors usam os mesmos IDs geográficos
2. ✅ **Queries mais rápidas** - JOIN por INT é muito mais rápido que por VARCHAR
3. ✅ **Menos erros** - Nomes normalizados automaticamente (Brasil → Brazil, São Paulo → Sao Paulo)
4. ✅ **Filtros inteligentes** - Remove "Remote", países usados como cidades, etc.
5. ✅ **Agregações fáceis** - Contar dados por país/cidade sem duplicatas

---

## 🔧 Exemplo Completo: central-banks-women.py

**Antes:**
```python
cursor.execute("""
    INSERT INTO sofia.central_banks_women_data
    (region, central_bank_code, country_code, ...)
    VALUES (%s, %s, %s, ...)
""", (region, bank_code, country, ...))
```

**Depois:**
```python
# Normalizar país
location = normalize_location(conn, {'country': country})
country_id = location['country_id']

cursor.execute("""
    INSERT INTO sofia.central_banks_women_data
    (region, central_bank_code, country_code, country_id, ...)
    VALUES (%s, %s, %s, %s, ...)
""", (region, bank_code, country, country_id, ...))
```

---

## 📝 Próximas Ações Recomendadas

1. **Criar migrations** para adicionar `country_id`, `state_id`, `city_id` nas tabelas que não têm
2. **Atualizar collectors** para usar `normalize_location()` antes dos INSERTs
3. **Testar** cada collector após atualização
4. **Backfill** dados antigos com IDs normalizados

---

**Status**: 🟡 PARCIALMENTE AGNÓSTICO
**Próximo**: Fase 2 - Implementar normalização nos INSERTs
