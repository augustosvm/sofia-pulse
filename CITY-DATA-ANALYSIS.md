# 🏙️ Análise de Dados de Cidades - Sofia Pulse

**Data**: 2025-12-03
**Análise**: Verificação de dados de cidades disponíveis nos collectors

---

## 🔍 Status Atual

### ✅ Dados de Cidades Disponíveis

#### 1. **Universidades Asiáticas** (`asia_universities`)
- **36 universidades** com campo `city`
- Cidades: Tokyo, Seoul, Singapore, Beijing, Mumbai, etc.
- **Status**: ✅ **JÁ ESTÁ SENDO USADO** no STEM Education report
- **Collector**: `scripts/collect-asia-universities.ts`

#### 2. **Cidades Brasileiras - Segurança** (`brazil_security_cities`)
- **Tabela**: `sofia.brazil_security_cities`
- **Campos**: city, state, population, homicide_rate, robbery_rate
- **Status**: ⚠️  **NÃO ESTÁ SENDO USADO** em analytics
- **Collector**: `scripts/collect-brazil-security.py`

**Estrutura da tabela**:
```sql
CREATE TABLE sofia.brazil_security_cities (
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2),
    population_millions DECIMAL(10, 2),
    year INTEGER,
    homicide_rate DECIMAL(10, 2),
    robbery_rate DECIMAL(10, 2),
    source VARCHAR(200),
    UNIQUE(city, state, year)
)
```

---

## ❌ O Que Não Temos (Ainda)

### Dados Globais de Cidades

**Não temos dados de cidades para**:
- 🌍 Qualidade de vida por cidade
- 💰 Custo de vida por cidade
- 🌐 Internet speed por cidade
- 🏥 Healthcare quality por cidade
- 🏠 Housing prices por cidade
- 🚇 Transporte público por cidade
- 🌤️  Clima/Weather por cidade

**Por que é importante?**
O Digital Nomad report mostra países (Belarus, Moldova, Argentina), mas nômades digitais escolhem **cidades específicas** (Minsk, Chișinău, Buenos Aires).

---

## 💡 Como Melhorar

### Opção 1: Usar APIs de Cidades (Recomendado)

#### A. **Numbeo API** (Custo de Vida)
- 9,000+ cidades
- Custo de vida, rent, groceries, restaurants
- API: https://www.numbeo.com/api/
- **Custo**: ~$100-300/mês

#### B. **Teleport Cities API** (Qualidade de Vida)
- 266 cidades globais
- 17 categorias (housing, cost, internet, safety, etc.)
- API: https://developers.teleport.org/api/
- **Custo**: **GRÁTIS!** 🎉

#### C. **Nomad List API** (Digital Nomads)
- 1,500+ cidades
- Scores específicos para nômades
- Internet, cost, safety, weather, community
- API: https://nomadlist.com/api
- **Custo**: $99/mês

#### D. **OpenWeatherMap** (Clima)
- Clima por cidade
- API: https://openweathermap.org/api
- **Custo**: GRÁTIS (até 1000 calls/dia)

### Opção 2: Web Scraping

**Sites com dados de cidades**:
- Numbeo (scraping)
- Expatistan
- Cost of Living Index
- Mercer Quality of Living

**⚠️  Problemas**:
- Pode violar ToS
- Dados menos confiáveis
- Manutenção constante (se layout mudar)

### Opção 3: Datasets Estáticos

**Fontes**:
- World Cities Database (GitHub)
- UN Habitat dados de cidades
- OECD Metropolitan Database

**⚠️  Problemas**:
- Dados podem estar desatualizados
- Coverage limitada
- Não tem tudo que precisamos

---

## 🎯 Recomendação: Teleport API (GRÁTIS!)

### Por Que Teleport?

1. **✅ GRÁTIS** - sem custo
2. **✅ 266 cidades** - principais destinos
3. **✅ Dados ricos** - 17 categorias
4. **✅ API JSON** - fácil de integrar
5. **✅ Atualizado** - dados mantidos pela comunidade

### O Que Teríamos

**Dados por cidade**:
- Housing costs
- Cost of living
- Internet speed
- Safety
- Healthcare
- Education
- Environmental quality
- Economy
- Taxation
- Startups (!)
- Leisure & Culture
- Tolerance
- Outdoors
- ...e mais 17 categorias

### Exemplo de Collector

```python
#!/usr/bin/env python3
"""
Teleport Cities Collector
Colleta dados de qualidade de vida de 266 cidades
"""
import requests
import psycopg2

TELEPORT_API = "https://api.teleport.org/api/urban_areas/"

def collect_cities():
    # Get list of cities
    response = requests.get(TELEPORT_API)
    cities = response.json()['_links']['ua:item']

    for city in cities:
        city_url = city['href']
        scores_url = f"{city_url}scores/"

        # Get city scores
        scores_resp = requests.get(scores_url)
        scores = scores_resp.json()

        # Extract data
        city_name = scores['name']
        teleport_score = scores['teleport_city_score']
        categories = scores['categories']

        # Save to DB
        save_city_data(city_name, teleport_score, categories)

def save_city_data(name, score, categories):
    """Save to sofia.global_cities table"""
    # Implementation here
    pass

if __name__ == '__main__':
    collect_cities()
```

---

## 📊 Nova Tabela Proposta: `global_cities`

```sql
CREATE TABLE IF NOT EXISTS sofia.global_cities (
    id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    continent VARCHAR(50),

    -- Overall Score
    teleport_score DECIMAL(5, 2),  -- 0-100

    -- Categories (0-10 scale)
    housing_cost DECIMAL(3, 2),
    cost_of_living DECIMAL(3, 2),
    internet_speed DECIMAL(3, 2),
    safety DECIMAL(3, 2),
    healthcare DECIMAL(3, 2),
    education DECIMAL(3, 2),
    environmental_quality DECIMAL(3, 2),
    economy DECIMAL(3, 2),
    taxation DECIMAL(3, 2),
    startups DECIMAL(3, 2),
    leisure_culture DECIMAL(3, 2),
    tolerance DECIMAL(3, 2),
    outdoors DECIMAL(3, 2),

    -- Metadata
    population BIGINT,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),

    -- Timestamps
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(city_name, country)
);

CREATE INDEX idx_cities_country ON sofia.global_cities(country);
CREATE INDEX idx_cities_score ON sofia.global_cities(teleport_score DESC);
```

---

## 🚀 Roadmap de Implementação

### Fase 1: Teleport API (1 dia)
- [x] Analisar disponibilidade de dados de cidades
- [ ] Criar collector `collect-teleport-cities.py`
- [ ] Criar tabela `sofia.global_cities`
- [ ] Rodar collector inicial (266 cidades)
- [ ] Validar dados

### Fase 2: Integração com Analytics (1 dia)
- [ ] Modificar `generate_digital_nomad_report()` para usar cidades
- [ ] Criar ranking de top 50 cidades (não países)
- [ ] Adicionar filtros (região, custo, etc.)

### Fase 3: Outros Collectors de Cidades (2-3 dias)
- [ ] Numbeo API (se decidir pagar)
- [ ] OpenWeatherMap (clima)
- [ ] Dados brasileiros de cidades (já temos!)
  - [ ] Integrar `brazil_security_cities` nos analytics

### Fase 4: Analytics Avançados (1 semana)
- [ ] City comparison tool
- [ ] Best cities for specific profiles
  - Developers
  - Founders
  - Families
  - Retirees
- [ ] Cost/benefit analysis
- [ ] Relocation recommendations

---

## 📈 Impacto Esperado

### Antes (Países)
```
#1 - Belarus
   Nomad Score: 89.5/100
   Internet: 94%
   Cost Level: Low
```

### Depois (Cidades)
```
#1 - Minsk, Belarus
   🏙️  Teleport Score: 58/100
   💰 Cost of Living: $800/month
   🌐 Internet: 50 Mbps avg
   🏠 Rent (1BR center): $350/month
   ⭐ RATING: 🟢 EXCELLENT - Top nomad city

   📊 Breakdown:
   - Housing: 8.2/10 (very affordable)
   - Internet: 7.5/10 (fast & reliable)
   - Safety: 8.9/10 (very safe)
   - Startups: 4.2/10 (limited scene)
```

**Muito mais útil e específico!**

---

## ❓ FAQ

**Q: Por que não fizemos isso antes?**
A: Focamos primeiro em dados nacionais (mais fácil de coletar). Cidades são o próximo passo lógico.

**Q: Teleport tem todas as cidades que precisamos?**
A: Tem as 266 principais. Para outras, podemos adicionar Numbeo (pago) ou scraping.

**Q: E para cidades brasileiras?**
A: Já temos `brazil_security_cities`! Falta apenas integrar nos analytics.

**Q: Quanto tempo leva para implementar?**
A: Teleport collector: 1 dia. Integração com analytics: 1 dia. Total: 2 dias.

**Q: Vai quebrar os reports existentes?**
A: Não! Vamos criar novos reports de cidades. Os existentes (países) continuam funcionando.

---

## ✅ Conclusão

**Status Atual**:
- ✅ Temos dados de 36 cidades (universidades asiáticas) - **já em uso**
- ✅ Temos dados de cidades brasileiras (segurança) - **não em uso**
- ❌ Não temos dados globais de cidades para nomad/expansion

**Solução**:
- 🎯 **Teleport API (GRÁTIS)** - 266 cidades, 17 categorias
- 📦 Criar `global_cities` table
- 📊 Modificar analytics para usar cidades

**ROI**: **MUITO ALTO!**
- Dados GRÁTIS
- Implementação rápida (2 dias)
- Valor enorme para usuários (cidades > países)

**Ação Recomendada**: Implementar Teleport collector ASAP!

---

**Criado por**: Claude Code
**Data**: 2025-12-03
**Análise**: Baseada em verificação completa dos collectors
