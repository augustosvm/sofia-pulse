# 🌍 Dados Socioeconômicos - Sofia Pulse

## 📊 Visão Geral

Coletor automático de **12 indicadores socioeconômicos** para todos os países usando **World Bank API** (gratuita, sem API key).

**Período**: 2015-2024
**Atualização**: Diária (junto com outros Python collectors)
**Fonte**: World Bank Open Data

---

## 📈 Indicadores Coletados

### 💰 Econômicos

#### 1. **GDP (PIB)**
- **Código**: `NY.GDP.MKTP.CD`
- **Nome**: GDP (current US$)
- **Unidade**: USD
- **O que mede**: Produto Interno Bruto total em dólares correntes

#### 2. **GDP per Capita**
- **Código**: `NY.GDP.PCAP.CD`
- **Nome**: GDP per capita (current US$)
- **Unidade**: USD
- **O que mede**: PIB dividido pela população

#### 3. **Inflation Rate**
- **Código**: `FP.CPI.TOTL.ZG`
- **Nome**: Inflation, consumer prices (annual %)
- **Unidade**: %
- **O que mede**: Variação anual do índice de preços ao consumidor

#### 4. **Unemployment Rate**
- **Código**: `SL.UEM.TOTL.ZS`
- **Nome**: Unemployment, total (% of total labor force)
- **Unidade**: %
- **O que mede**: Porcentagem da força de trabalho desempregada

---

### 👥 Sociais

#### 5. **Population**
- **Código**: `SP.POP.TOTL`
- **Nome**: Population, total
- **Unidade**: people
- **O que mede**: População total do país

#### 6. **Life Expectancy**
- **Código**: `SP.DYN.LE00.IN`
- **Nome**: Life expectancy at birth, total (years)
- **Unidade**: years
- **O que mede**: Expectativa de vida ao nascer

#### 7. **Literacy Rate**
- **Código**: `SE.ADT.LITR.ZS`
- **Nome**: Literacy rate, adult total (% of people ages 15+)
- **Unidade**: %
- **O que mede**: Porcentagem da população alfabetizada

#### 8. **Gini Index**
- **Código**: `SI.POV.GINI`
- **Nome**: Gini index (World Bank estimate)
- **Unidade**: index (0-100)
- **O que mede**: Desigualdade de renda (0 = perfeita igualdade, 100 = perfeita desigualdade)

---

### 🏥 Saúde e Educação

#### 9. **Health Expenditure**
- **Código**: `SH.XPD.CHEX.GD.ZS`
- **Nome**: Current health expenditure (% of GDP)
- **Unidade**: %
- **O que mede**: Gastos com saúde como % do PIB

#### 10. **Education Expenditure**
- **Código**: `SE.XPD.TOTL.GD.ZS`
- **Nome**: Government expenditure on education, total (% of GDP)
- **Unidade**: %
- **O que mede**: Gastos governamentais com educação como % do PIB

---

### 🌍 Meio Ambiente e Tecnologia

#### 11. **CO2 Emissions per Capita**
- **Código**: `EN.ATM.CO2E.PC`
- **Nome**: CO2 emissions (metric tons per capita)
- **Unidade**: tons
- **O que mede**: Emissões de CO2 por pessoa

#### 12. **Internet Users**
- **Código**: `IT.NET.USER.ZS`
- **Nome**: Individuals using the Internet (% of population)
- **Unidade**: %
- **O que mede**: Porcentagem da população com acesso à internet

---

## 🗄️ Estrutura do Banco

### Tabela: `sofia.socioeconomic_indicators`

```sql
CREATE TABLE sofia.socioeconomic_indicators (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(10) NOT NULL,          -- ISO3 (ex: BRA, USA, CHN)
    country_name VARCHAR(200),                  -- Nome completo do país
    year INTEGER NOT NULL,                       -- 2015-2024
    indicator_code VARCHAR(50) NOT NULL,         -- Código World Bank
    indicator_name VARCHAR(100),                 -- Nome amigável
    value DECIMAL(18,4),                         -- Valor do indicador
    unit VARCHAR(50),                            -- Unidade (USD, %, years, etc)
    data_source VARCHAR(100),                    -- 'World Bank'
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(country_code, year, indicator_code)
);
```

### Índices
```sql
idx_socio_country          -- country_code
idx_socio_year             -- year DESC
idx_socio_indicator        -- indicator_code
idx_socio_country_year     -- country_code, year DESC (compound)
```

---

## 📊 Exemplos de Queries

### 1. PIB dos BRICS (2023)
```sql
SELECT
    country_name,
    value / 1e12 as gdp_trillion_usd
FROM sofia.socioeconomic_indicators
WHERE indicator_code = 'NY.GDP.MKTP.CD'
  AND year = 2023
  AND country_code IN ('BRA', 'RUS', 'IND', 'CHN', 'ZAF')
ORDER BY value DESC;
```

### 2. Evolução da expectativa de vida no Brasil
```sql
SELECT
    year,
    value as life_expectancy_years
FROM sofia.socioeconomic_indicators
WHERE indicator_code = 'SP.DYN.LE00.IN'
  AND country_code = 'BRA'
  AND year >= 2015
ORDER BY year;
```

### 3. Países com maior desigualdade (Gini Index)
```sql
SELECT
    country_name,
    value as gini_index,
    year
FROM sofia.socioeconomic_indicators
WHERE indicator_code = 'SI.POV.GINI'
  AND year = (SELECT MAX(year) FROM sofia.socioeconomic_indicators WHERE indicator_code = 'SI.POV.GINI')
ORDER BY value DESC
LIMIT 10;
```

### 4. Comparação Brasil vs USA vs China (2023)
```sql
SELECT
    country_name,
    indicator_name,
    value,
    unit
FROM sofia.socioeconomic_indicators
WHERE country_code IN ('BRA', 'USA', 'CHN')
  AND year = 2023
  AND indicator_code IN (
      'NY.GDP.PCAP.CD',     -- PIB per capita
      'SP.DYN.LE00.IN',      -- Expectativa de vida
      'IT.NET.USER.ZS',      -- Usuários de internet
      'SL.UEM.TOTL.ZS'       -- Desemprego
  )
ORDER BY country_name, indicator_name;
```

### 5. Top 20 países por acesso à internet (2023)
```sql
SELECT
    country_name,
    value as internet_users_pct
FROM sofia.socioeconomic_indicators
WHERE indicator_code = 'IT.NET.USER.ZS'
  AND year = 2023
ORDER BY value DESC
LIMIT 20;
```

### 6. Correlação PIB per capita vs Expectativa de vida
```sql
WITH gdp AS (
    SELECT country_code, value as gdp_per_capita
    FROM sofia.socioeconomic_indicators
    WHERE indicator_code = 'NY.GDP.PCAP.CD' AND year = 2023
),
life AS (
    SELECT country_code, value as life_expectancy
    FROM sofia.socioeconomic_indicators
    WHERE indicator_code = 'SP.DYN.LE00.IN' AND year = 2023
)
SELECT
    g.country_code,
    g.gdp_per_capita,
    l.life_expectancy
FROM gdp g
JOIN life l ON g.country_code = l.country_code
WHERE g.gdp_per_capita IS NOT NULL
  AND l.life_expectancy IS NOT NULL
ORDER BY g.gdp_per_capita DESC;
```

---

## 🚀 Como Executar

### Teste Manual
```bash
cd /home/ubuntu/sofia-pulse
source venv-analytics/bin/activate
python3 scripts/collect-socioeconomic-indicators.py
```

### Execução Automática
O coletor roda automaticamente todos os dias às **13:00 UTC (10:00 BRT)** via crontab:

```cron
0 13 * * * cd /home/ubuntu/sofia-pulse && ./run-all-with-venv.sh
```

---

## 📈 Resultado Esperado

```
================================================================================
🌍 SOCIOECONOMIC INDICATORS COLLECTOR
================================================================================

📊 Collecting 12 indicators from World Bank (2015-2024)

📈 GDP (current US$)
   Fetching NY.GDP.MKTP.CD... ✅ 1847 records
   ✅ Processed 1847 valid records

📈 GDP per capita (current US$)
   Fetching NY.GDP.PCAP.CD... ✅ 1847 records
   ✅ Processed 1847 valid records

... (outros 10 indicadores)

💾 Inserting to database...
✅ Inserted/updated 18,250 records

📊 Summary:
   Total indicators: 12
   Total records: 18,250
   Inserted/updated: 18,250

📈 Records by indicator:
   co2_emissions_per_capita: 1520
   education_expenditure_gdp: 986
   gdp_current_usd: 1847
   gdp_per_capita: 1847
   gini_index: 723
   health_expenditure_gdp: 1689
   inflation_rate: 1726
   internet_users: 1835
   life_expectancy: 1910
   literacy_rate: 1245
   population: 1922
   unemployment_rate: 1000

================================================================================
✅ COMPLETE - Inserted 18,250 records
================================================================================

💡 Data covers 2015-2024 for all countries
   Source: World Bank Open Data (api.worldbank.org)
```

**Total de registros**: ~18,000-20,000 (varia por disponibilidade de dados)

---

## 🎯 Casos de Uso

### 1. **Análise Econômica**
- Comparar PIB de países emergentes vs desenvolvidos
- Analisar correlação entre desemprego e crescimento econômico
- Identificar países com maior inflação

### 2. **Desenvolvimento Social**
- Mapear países com melhor expectativa de vida
- Analisar investimentos em saúde e educação
- Identificar países com maior desigualdade (Gini)

### 3. **Meio Ambiente**
- Ranking de países por emissões de CO2 per capita
- Correlação entre desenvolvimento econômico e emissões

### 4. **Tecnologia e Conectividade**
- Mapear penetração de internet por país
- Correlação entre acesso à internet e PIB per capita

### 5. **Investimento**
- Identificar mercados emergentes (alto crescimento + baixa desigualdade)
- Analisar estabilidade econômica (inflação + desemprego)
- Avaliar desenvolvimento social (saúde + educação)

---

## 📊 Dados por Região

Aproximadamente:
- **América Latina**: ~30 países × 12 indicadores × 10 anos = 3,600 records
- **Europa**: ~50 países × 12 indicadores × 10 anos = 6,000 records
- **Ásia**: ~40 países × 12 indicadores × 10 anos = 4,800 records
- **África**: ~50 países × 12 indicadores × 10 anos = 6,000 records
- **Outros**: ~30 países × 12 indicadores × 10 anos = 3,600 records

**Total**: ~24,000 records (alguns dados podem não estar disponíveis para todos os anos)

---

## 💡 Melhorias Futuras

### Indicadores Adicionais (World Bank disponível)
- HDI (Human Development Index)
- Taxa de pobreza
- Acesso à água potável
- Acesso à eletricidade
- Mortalidade infantil
- Fertilidade
- Urbanização
- Gastos militares
- Dívida pública
- Reservas internacionais

### Outras Fontes
- **IMF** (World Economic Outlook)
- **OECD** (países desenvolvidos)
- **UN Data** (indicadores sociais)
- **WHO** (saúde global)

---

## ✅ Status

- ✅ Coletor criado
- ✅ Tabela no banco criada
- ✅ 12 indicadores configurados
- ✅ Integrado ao `run-all-with-venv.sh`
- ✅ Documentação completa
- ⏰ Execução automática (crontab)

**Sistema pronto para uso! 🚀**

---

**Última atualização**: 2025-11-19
**Fonte**: World Bank Open Data API
**Licença**: Dados públicos (World Bank Open License)
