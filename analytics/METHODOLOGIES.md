# 📊 SOFIA PULSE - METHODOLOGIES REFERENCE

Este documento lista as metodologias consagradas usadas nos relatórios Sofia Pulse.

**Princípio**: Usar índices e fórmulas reconhecidas internacionalmente sempre que possível, ao invés de criar metodologias próprias.

---

## 1. HDI (Human Development Index) - UNDP

**Fonte**: United Nations Development Programme (UNDP)
**URL**: https://hdr.undp.org/data-center/human-development-index
**Última Versão**: HDR 2023/2024

### Componentes:

1. **Health (Saúde)**: Life expectancy at birth
   - Min: 20 years, Max: 85 years

2. **Education (Educação)**:
   - Mean years of schooling (adults 25+): Min 0, Max 15 years
   - Expected years of schooling: Min 0, Max 18 years

3. **Standard of Living (Padrão de Vida)**: GNI per capita (PPP $)
   - Min: $100, Max: $75,000
   - **Usa logaritmo** para refletir importância decrescente de renda

### Fórmula:

```
Dimension Index = (actual value - minimum value) / (maximum value - minimum value)

Health Index = (Life Expectancy - 20) / (85 - 20)
Education Index = (Mean Years Index + Expected Years Index) / 2
Income Index = (ln(GNI per capita) - ln(100)) / (ln(75000) - ln(100))

HDI = (Health Index × Education Index × Income Index)^(1/3)  # Geometric mean
```

**Aplicado em**:
- `expansion-location-analyzer.py` (Healthcare component)
- `intelligence-reports-suite.py` (STEM Education)

---

## 2. Global Innovation Index (GII) - WIPO/Cornell

**Fonte**: World Intellectual Property Organization (WIPO) / Cornell University
**URL**: https://www.wipo.int/global_innovation_index/
**Última Versão**: GII 2024

### Componentes:

**Innovation Inputs (50%)**:
1. Institutions
2. Human capital and research
3. Infrastructure
4. Market sophistication
5. Business sophistication

**Innovation Outputs (50%)**:
6. Knowledge and technology outputs
7. Creative outputs

### Fórmula Simplificada (usando dados disponíveis):

```
Innovation Score =
  (R&D expenditure % GDP × 40) +
  (Research output (papers) × 30) +
  (Funding deals × 20) +
  (Tertiary enrollment × 10)

Normalizado para 0-100
```

**Aplicado em**:
- `intelligence-reports-suite.py` (Innovation Hubs)
- `expansion-location-analyzer.py` (Innovation dimension)

---

## 3. Quality of Life Index - Numbeo/Mercer

**Fonte**: Numbeo (crowdsourced) e Mercer Quality of Living Survey
**URLs**:
- https://www.numbeo.com/quality-of-life/
- https://mobilityexchange.mercer.com/quality-of-living-rankings

### Componentes Numbeo (8 dimensões):

1. **Purchasing Power Index** (GDP per capita)
2. **Safety Index** (crime rates, suicide, injuries)
3. **Health Care Index** (life expectancy, physicians, hospital beds)
4. **Cost of Living Index** (inverted)
5. **Property Price to Income Ratio**
6. **Traffic Commute Time Index**
7. **Pollution Index** (air quality PM2.5)
8. **Climate Index**

### Componentes Mercer (10 categorias):

1. Political and social environment
2. Economic environment
3. Socio-cultural environment
4. Medical and health considerations
5. Schools and education
6. Public services and transport
7. Recreation
8. Consumer goods
9. Housing
10. Natural environment

### Fórmula Adaptada (dados disponíveis):

```
QoL Score (0-100) = Weighted Average:
  Education (20%):       Literacy + Tertiary enrollment
  Infrastructure (20%):  Internet + Broadband + Electricity
  Healthcare (15%):      Life expectancy + Physicians + Hospital beds
  Safety (15%):          Low suicide + Low injuries
  Environment (10%):     Air quality (low PM2.5) + Forest area
  Innovation (10%):      R&D expenditure
  Economic (10%):        GDP/capita + Low unemployment + FDI
```

**Aplicado em**:
- `expansion-location-analyzer.py` (Quality of Life Score)
- `remote-work-quality-index.py`

---

## 4. Ease of Doing Business - World Bank (descontinuado 2021)

**Fonte**: World Bank (até 2021)
**URL**: https://archive.doingbusiness.org/

**Nota**: Índice descontinuado em 2021, mas metodologia ainda relevante.

### Componentes (10 indicadores):

1. Starting a business
2. Dealing with construction permits
3. Getting electricity
4. Registering property
5. Getting credit
6. Protecting minority investors
7. Paying taxes
8. Trading across borders
9. Enforcing contracts
10. Resolving insolvency

### Adaptação para Startups:

```
Startup Friendliness Score (0-100):
  Funding ecosystem (35%):  Number of deals + Total funding
  Cost of operations (25%): Low GDP per capita = low costs
  Talent availability (20%): Literacy + Tertiary enrollment
  Infrastructure (20%):      Internet + Electricity access
```

**Aplicado em**:
- `intelligence-reports-suite.py` (Startup Founders)
- `expansion-location-analyzer.py` (Funding Activity)

---

## 5. Digital Nomad Index - Nomad List

**Fonte**: Nomad List (https://nomadlist.com/)
**Baseado em**: Crowdsourced data + objective metrics

### Componentes:

1. **Cost** (30%): Living costs
2. **Internet** (30%): Speed + Reliability
3. **Safety** (20%): Crime rates
4. **Healthcare** (10%): Quality + Accessibility
5. **Environment** (10%): Air quality + Weather

### Fórmula:

```
Nomad Score (0-100):
  Internet (30%):     Internet users % + Broadband subscriptions
  Cost (30%):         Low GDP per capita (inverted)
  Safety (20%):       Life expectancy + Low suicide + Low injuries
  Healthcare (10%):   Physicians per 1000
  Environment (10%):  Low PM2.5 pollution
```

**Aplicado em**:
- `intelligence-reports-suite.py` (Digital Nomad Index)
- `remote-work-quality-index.py`

---

## 6. Tech Talent Competitiveness Index

**Fonte**: Inspirado em INSEAD Global Talent Competitiveness Index
**URL**: https://www.insead.edu/gtci

### Componentes:

1. **Enable**: Regulatory environment, business environment
2. **Attract**: External openness, internal openness
3. **Grow**: Formal education, lifelong learning, access to growth opportunities
4. **Retain**: Sustainability, lifestyle

### Adaptação:

```
Tech Talent Score (0-100):
  Job Opportunities (30%):  Funding deals (hiring proxy)
  Education (25%):          Literacy + Tertiary enrollment
  Infrastructure (20%):     Internet + Broadband
  Safety & QoL (15%):       Life expectancy + Low crime
  Cost Advantage (10%):     Low cost of living
```

**Aplicado em**:
- `best-cities-tech-talent.py`

---

## 7. STEM Education Quality - PISA/TIMSS inspired

**Fonte**: OECD PISA (Programme for International Student Assessment)
**URL**: https://www.oecd.org/pisa/

**Nota**: PISA mede proficiência em matemática, ciência e leitura de estudantes de 15 anos.

### Adaptação (dados disponíveis):

```
STEM Education Score (0-100):
  University Enrollment (30%):  Tertiary enrollment %
  R&D Investment (30%):         R&D expenditure % GDP
  Research Output (25%):        Published papers
  Basic Education (15%):        Literacy rate
```

**Aplicado em**:
- `intelligence-reports-suite.py` (STEM Education Leaders)

---

## Resumo de Aplicações

| Relatório | Metodologias Usadas |
|-----------|---------------------|
| **Expansion Location Analyzer** | HDI (Health), GII (Innovation), Numbeo QoL, Ease of Doing Business |
| **Best Cities for Tech Talent** | INSEAD Talent Index, Ease of Doing Business |
| **Remote Work Quality Index** | Nomad List Index, Numbeo QoL |
| **Innovation Hubs Ranking** | Global Innovation Index (GII) |
| **Startup Founders** | Ease of Doing Business, GII |
| **Digital Nomad Index** | Nomad List Index |
| **STEM Education Leaders** | PISA/TIMSS inspired |

---

## Referências

1. UNDP (2024). Human Development Report 2023/2024. https://hdr.undp.org/
2. WIPO (2024). Global Innovation Index. https://www.wipo.int/global_innovation_index/
3. Numbeo (2024). Quality of Life Index. https://www.numbeo.com/quality-of-life/
4. Mercer (2024). Quality of Living Survey. https://mobilityexchange.mercer.com/
5. World Bank (2021). Doing Business Report (archived). https://archive.doingbusiness.org/
6. Nomad List (2024). Digital Nomad Index. https://nomadlist.com/
7. INSEAD (2024). Global Talent Competitiveness Index. https://www.insead.edu/gtci
8. OECD (2024). PISA Programme. https://www.oecd.org/pisa/

---

**Última Atualização**: 2025-11-21
**Versão**: 1.0
