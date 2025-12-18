# APIs Automotivas - Sofia Pulse

## Visão Geral
Implementação de 3 APIs automotivas para coletar dados de veículos.

## APIs Implementadas

### 1. VPIC (NHTSA) ✅ GRATUITA
**Arquivo**: `collect-vpic-vehicles.ts`

**Características:**
- ✅ API gratuita do governo dos EUA
- ✅ Não requer autenticação
- ✅ Dados oficiais de fabricantes
- ✅ Especificações técnicas
- ✅ Informações de segurança

**Dados Coletados:**
- Fabricante (Make)
- Modelo (Model)
- Ano
- Tipo de veículo
- Classe de carroceria
- Motor (modelo, cilindros, deslocamento)
- Tipo de combustível

**Endpoint**: `https://vpic.nhtsa.dot.gov/api/vehicles`

**Uso:**
```bash
npx tsx scripts/collect-vpic-vehicles.ts
```

**Tabela**: `sofia.vpic_vehicles`

---

### 2. CarsXE 💰 REQUER API KEY
**Arquivo**: `collect-carsxe-vehicles.ts`

**Características:**
- 💰 Requer API key (planos gratuitos disponíveis)
- 🔍 VIN decoding
- 💵 Market value
- 📊 Especificações detalhadas
- 📸 Imagens de veículos

**Dados Coletados:**
- Ano, Marca, Modelo, Trim
- Carroceria
- Motor
- Transmissão
- Tração
- Tipo de combustível
- MPG (cidade/rodovia)
- MSRP (preço sugerido)

**Endpoint**: `https://api.carsxe.com`

**Configuração:**
```bash
# Adicionar ao .env
CARSXE_API_KEY=sua_api_key_aqui
```

**Obter API Key**: https://carsxe.com/

**Uso:**
```bash
npx tsx scripts/collect-carsxe-vehicles.ts
```

**Tabela**: `sofia.carsxe_vehicles`

---

### 3. CarAPI 💰 REQUER JWT
**Arquivo**: `collect-carapi-vehicles.ts`

**Características:**
- 💰 Requer JWT (planos gratuitos disponíveis)
- 📚 90.000+ veículos
- 🗓️ Dados de 1990 até hoje
- 🔧 Especificações técnicas detalhadas
- 💪 Dados de performance (HP, torque)

**Dados Coletados:**
- Ano, Marca, Modelo, Trim
- Carroceria
- Motor (tipo, cilindros, deslocamento, HP, torque)
- Tipo de combustível
- Transmissão
- Tração
- MPG (cidade/rodovia/combinado)
- MSRP

**Endpoint**: `https://carapi.app/api`

**Configuração:**
```bash
# Adicionar ao .env
CARAPI_JWT=seu_jwt_token_aqui
```

**Obter JWT**:
1. Criar conta em https://carapi.app/
2. Gerar API Secret
3. Usar secret para obter JWT

**Uso:**
```bash
npx tsx scripts/collect-carapi-vehicles.ts
```

**Tabela**: `sofia.carapi_vehicles`

---

## Estrutura das Tabelas

### sofia.vpic_vehicles
```sql
- id (SERIAL PRIMARY KEY)
- make VARCHAR(100)
- model VARCHAR(100)
- year INTEGER
- vehicle_type VARCHAR(100)
- body_class VARCHAR(100)
- engine_model VARCHAR(100)
- engine_cylinders VARCHAR(50)
- displacement_l VARCHAR(50)
- fuel_type VARCHAR(100)
- manufacturer VARCHAR(200)
- collected_at TIMESTAMPTZ
- UNIQUE(make, model, year, body_class)
```

### sofia.carsxe_vehicles
```sql
- id (SERIAL PRIMARY KEY)
- year INTEGER
- make VARCHAR(100)
- model VARCHAR(100)
- trim VARCHAR(100)
- body VARCHAR(100)
- engine VARCHAR(200)
- transmission VARCHAR(100)
- drivetrain VARCHAR(50)
- fuel_type VARCHAR(50)
- mpg_city INTEGER
- mpg_highway INTEGER
- msrp NUMERIC
- collected_at TIMESTAMPTZ
- UNIQUE(year, make, model, trim)
```

### sofia.carapi_vehicles
```sql
- id (SERIAL PRIMARY KEY)
- carapi_id INTEGER UNIQUE
- year INTEGER
- make VARCHAR(100)
- model VARCHAR(100)
- trim VARCHAR(100)
- body VARCHAR(100)
- engine_type VARCHAR(100)
- engine_cylinders INTEGER
- engine_displacement NUMERIC
- engine_horsepower INTEGER
- engine_torque INTEGER
- fuel_type VARCHAR(50)
- transmission VARCHAR(100)
- drivetrain VARCHAR(50)
- mpg_city INTEGER
- mpg_highway INTEGER
- mpg_combined INTEGER
- msrp NUMERIC
- collected_at TIMESTAMPTZ
```

---

## Executar Todos os Coletores

```bash
# VPIC (gratuito)
npx tsx scripts/collect-vpic-vehicles.ts

# CarsXE (requer API key)
npx tsx scripts/collect-carsxe-vehicles.ts

# CarAPI (requer JWT)
npx tsx scripts/collect-carapi-vehicles.ts
```

---

## Casos de Uso

### Análise de Mercado Automotivo
- Tendências de preços por fabricante
- Evolução de especificações técnicas
- Comparação de eficiência de combustível
- Análise de performance (HP, torque)

### Dashboards
- Preço médio por marca/ano
- MPG médio por tipo de veículo
- Distribuição de tipos de combustível
- Evolução de HP ao longo dos anos

### Inteligência de Negócios
- Identificar tendências de mercado
- Análise competitiva de fabricantes
- Previsão de valores de revenda
- Análise de popularidade de modelos

---

## Rate Limits e Quotas

### VPIC (NHTSA)
- ✅ Sem limites (API pública)
- ✅ Disponível 24/7

### CarsXE
- 📊 Varia por plano
- 🆓 Plano gratuito disponível
- ⚠️ Verificar limites no dashboard

### CarAPI
- 📊 Varia por plano
- 🆓 Plano gratuito: 5000 requests/mês
- ⚠️ Rate limit: verificar documentação

---

## Próximos Passos

1. ✅ Implementar coletores
2. ⏳ Testar no servidor
3. ⏳ Configurar API keys
4. ⏳ Executar coleta inicial
5. ⏳ Criar dashboards de análise
6. ⏳ Configurar cron para atualização automática
