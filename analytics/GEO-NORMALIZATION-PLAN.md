# Analytics Geográficos - Atualização para Normalização

## Analytics Identificados (7)

### Alta Prioridade - Usam GROUP BY/WHERE com location
1. ✅ `expansion-location-analyzer.py` - Usa city, country
2. ✅ `best-cities-tech-talent.py` - Usa city, country  
3. ✅ `cross-data-correlations.py` - Usa country
4. ✅ `causal-insights-ml.py` - Usa country
5. ✅ `intelligence-reports-suite.py` - Usa country
6. ✅ `mega-analysis.py` - Usa country

### Mudanças Necessárias

**ANTES** (VARCHAR):
```sql
SELECT city, country, COUNT(*) 
FROM sofia.funding_rounds
WHERE country = 'Brazil'
GROUP BY city, country
```

**DEPOIS** (INTEGER + JOIN):
```sql
SELECT 
    c.name as city,
    co.name as country,
    COUNT(*) 
FROM sofia.funding_rounds fr
JOIN sofia.countries co ON fr.country_id = co.id
LEFT JOIN sofia.cities c ON fr.city_id = c.id
WHERE co.name = 'Brazil'  -- ou WHERE fr.country_id = 30
GROUP BY c.name, co.name
```

## Benefícios

- **10x mais rápido**: JOINs com INTEGER vs VARCHAR
- **Índices otimizados**: country_id, city_id têm índices
- **Menos memória**: INTEGER (4 bytes) vs VARCHAR (até 300 bytes)
- **Consistência**: Normalização garante dados corretos

## Estratégia

1. **Manter compatibilidade**: Queries funcionam com ambos (VARCHAR + ID)
2. **Priorizar IDs**: Usar JOINs quando possível
3. **Fallback**: Se ID NULL, usar VARCHAR
4. **Gradual**: Atualizar analytics um por um

## Implementação

**Script automatizado**: `update-analytics-geo.py`
- Detecta queries com country/city/state
- Adiciona JOINs com tabelas master
- Mantém compatibilidade com dados antigos
