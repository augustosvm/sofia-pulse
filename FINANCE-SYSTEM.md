# 💰 Finance System - Sofia Pulse

**Módulo de inteligência financeira integrado ao Sofia Pulse.**

---

## 🎯 O Que É

O **Sofia Finance** é um **módulo do Sofia Pulse** que:

1. ✅ **Coleta dados de mercado** (B3, NASDAQ, Funding Rounds)
2. ✅ **Gera sinais de investimento** com score 0-100
3. ✅ **Funciona com OU sem banco de dados**
4. ✅ **Tem seu próprio Docker setup**
5. ✅ **Tem sua própria documentação** (README.md, QUICK-START.md)

---

## 📁 Estrutura

**Parte do Sofia Pulse monorepo:**

```
sofia-pulse/                    ← RAIZ DO PROJETO
├── scripts/                    ← Collectors principais (9)
│   ├── collect-cardboard-production.ts
│   ├── collect-arxiv-ai.ts
│   └── ... (patents, universities, etc.)
│
└── finance/                    ← MÓDULO FINANCE
    ├── scripts/                ← Collectors financeiros (3)
    │   ├── demo-signals.ts
    │   ├── collect-brazil-stocks.ts
    │   ├── collect-nasdaq-momentum.ts
    │   ├── collect-funding-rounds.ts
    │   └── generate-signals.ts
    ├── dbt/models/             ← Models de banco
    ├── output/                 ← Sinais JSON
    ├── package.json            ← Scripts npm finance
    ├── docker-run.sh           ← Docker helper
    └── QUICK-START.md          ← Docs finance
```

**Tudo integrado**: Mesmo banco, mesmo repo, mesmo projeto!

---

## 🚀 Como Usar (Quick Start)

### Opção 1: Demo Mode (SEM banco, 2 segundos!)

```bash
cd finance
npm run demo
```

**O que acontece**:
- ✅ Gera 10+ sinais de investimento
- ✅ Dados mock realistas (IPOs, NASDAQ, Funding)
- ✅ JSON salvo em `output/`
- ✅ **NÃO precisa de banco!**

---

### Opção 2: Produção (COM banco)

```bash
cd finance

# 1. Instalar dependências
npm install

# 2. Configurar .env
cp .env.example .env
nano .env  # Editar credenciais

# 3. Criar tabelas
npm run migrate:market

# 4. Coletar dados
npm run collect:brazil   # B3 (grátis)
npm run collect:nasdaq   # NASDAQ (precisa API key)
npm run collect:funding  # Funding rounds

# Ou tudo de uma vez:
npm run invest:full      # Coleta tudo + gera sinais

# 5. Ver sinais
cat output/sofia-signals-*.json | jq
```

---

## 📊 Scripts NPM Disponíveis

### Demo e Desenvolvimento:
```bash
npm run demo              # Demo sem banco (2s)
npm run dev               # Watch mode
```

### Coleta de Dados:
```bash
npm run collect:brazil    # B3 stocks (GRÁTIS!)
npm run collect:nasdaq    # NASDAQ momentum (API key)
npm run collect:funding   # Funding rounds (scraping)
npm run collect:all       # Todos os acima
npm run collect:free      # Só B3 (sem API keys)
```

### Geração de Sinais:
```bash
npm run signals           # Gera sinais do banco
npm run invest:full       # Coleta + sinais (2-3min)
npm run invest:quick      # Só B3 + sinais (30s)
```

### Database:
```bash
npm run migrate:market    # Cria tabelas (DBT)
```

---

## 🐳 Docker (Recomendado)

```bash
cd finance

# Demo (sem banco)
./docker-run.sh demo

# Produção completa
./docker-run.sh full

# Migrations
./docker-run.sh migrate

# Coletar dados
./docker-run.sh collect

# Gerar sinais
./docker-run.sh signals

# Ver logs
./docker-run.sh logs

# Shell no container
./docker-run.sh shell

# Parar tudo
./docker-run.sh stop

# Limpar tudo
./docker-run.sh clean
```

---

## 📈 Exemplo de Sinal Gerado

```json
{
  "id": "AVAV-2025-11-17",
  "type": "NASDAQ_MOMENTUM",
  "title": "AVAV Momentum +12.3%",
  "score": 95,
  "confidence": 88,
  "potential_return": 21.4,
  "risk_level": "MEDIUM",
  "ticker": "AVAV",
  "company": "AeroVironment",
  "sector": "Defense Tech",
  "market": "NASDAQ",
  "recommendation": "STRONG_BUY",
  "reasoning": [
    "Contrato $450M com DoD anunciado",
    "Drones Switchblade em alta demanda",
    "Revenue beat de 18% vs consensus",
    "Insider buying de $2.3M"
  ],
  "indicators": {
    "revenue_growth": 18.2,
    "market_momentum": 12.3,
    "volume_spike": 3.5,
    "institutional_ownership": 76.8
  }
}
```

---

## 🗄️ Tabelas Criadas no Banco

Quando você roda `npm run migrate:market`, cria:

| Tabela | Descrição | Populada Por |
|--------|-----------|--------------|
| `market_data_brazil` | Stocks da B3 | `collect:brazil` |
| `market_data_nasdaq` | Stocks NASDAQ | `collect:nasdaq` |
| `funding_rounds` | Rounds de investimento | `collect:funding` |
| `market_signals` | Sinais gerados | `signals` |

---

## 🔗 Integração Total

### Um Sistema Unificado - Sofia Pulse:

```
SOFIA PULSE (Sistema Completo)
│
├── Collectors Econômicos (scripts/)
│   ├── cardboard_production      → Economic leading indicators
│   ├── wipo_china_patents        → Innovation tracking
│   ├── arxiv_ai_papers           → AI research trends
│   └── ... (9 collectors)
│
└── Collectors Financeiros (finance/scripts/)
    ├── market_data_brazil        → B3 stocks
    ├── market_data_nasdaq        → NASDAQ momentum
    └── funding_rounds            → VC/PE deals
         ↓
    market_signals (gerados)
         ↓
   Sofia IA (consome TUDO)
```

### Mesmo Banco de Dados:

- ✅ **UM PostgreSQL** para todo o Sofia Pulse
- ✅ **UM Schema**: `sofia` (compartilhado)
- ✅ **12 collectors** (9 econômicos + 3 finance)
- ✅ **29 tabelas total** (finance contribui com 3)

---

## 📊 Status Real (17/11/2025)

### Tabelas Populadas:

| Tabela | Registros | Última Coleta | Status |
|--------|-----------|---------------|--------|
| `market_data_brazil` | 32 | 2025-11-17 18:48 | ✅ Hoje |
| `market_data_nasdaq` | 14 | 2025-11-17 18:50 | ✅ Hoje |
| `funding_rounds` | 0 | N/A | ❌ Vazia |

**Total Finance**: 46 registros (5% do total do banco)

---

## 🔑 Variáveis de Ambiente

### Banco de Dados (compartilhado com Sofia Pulse):
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sofia
POSTGRES_PASSWORD=sofia123strong
POSTGRES_DB=sofia_db
```

### API Keys (opcional para demo):
```bash
# Alpha Vantage (NASDAQ)
ALPHA_VANTAGE_API_KEY=TM3DVH1A35DUPPZ9

# Finnhub (dados premium)
FINNHUB_API_KEY=your_key
```

---

## 🎯 Fontes de Dados

### B3 (Brasil) - GRÁTIS:
- Stocks brasileiras
- Volumes e momentum
- Sem necessidade de API key

### NASDAQ - Requer API Key:
- High-momentum tech stocks
- Alpha Vantage API (grátis até 25 requests/dia)

### Funding Rounds - Web Scraping:
- Crunchbase
- TechCrunch
- Venture Beat

---

## 📖 Documentação Completa

### Dentro do Finance:

1. **README.md**: Overview e features
2. **QUICK-START.md**: Guia passo a passo (339 linhas!)
   - Setup completo
   - Todos os comandos
   - Docker workflows
   - Troubleshooting

### Leia PRIMEIRO:
```bash
cd finance
cat README.md
cat QUICK-START.md
```

---

## 🔧 Como Adicionar ao Sofia Pulse Principal

### Já adicionados ao package.json da raiz:

```json
{
  "collect:brazil": "tsx finance/scripts/collect-brazil-stocks.ts",
  "collect:nasdaq": "tsx finance/scripts/collect-nasdaq-momentum.ts",
  "collect:funding": "tsx finance/scripts/collect-funding-rounds.ts",
  "collect:finance-all": "npm run collect:brazil && npm run collect:nasdaq && npm run collect:funding"
}
```

### Como rodar da raiz:
```bash
# Da raiz do sofia-pulse:
npm run collect:brazil
npm run collect:nasdaq
npm run collect:funding
npm run collect:finance-all

# Ou entrar no finance:
cd finance
npm run demo
npm run invest:full
```

---

## 🚀 Roadmap

### Implementado:
- ✅ Demo mode sem banco
- ✅ Coleta B3 (grátis)
- ✅ Coleta NASDAQ (com API)
- ✅ Geração de sinais
- ✅ Docker setup
- ✅ JSON export

### Próximo (Roadmap):
- [ ] Machine Learning scoring
- [ ] Real-time WebSocket feeds
- [ ] React dashboard
- [ ] Backtesting engine
- [ ] TradingView integration
- [ ] Mobile notifications

---

## 💡 Sofia Pulse = Econômico + Finance (Integrado)

### SOFIA PULSE COMPLETO:

**12 Collectors em 2 Módulos**:

#### Módulo Econômico (scripts/):
- **Foco**: Leading indicators, research, innovation
- **Collectors**: 9 (cardboard, patents, AI, universities, biotech)
- **Dados**: Global, multi-fonte, tendências de longo prazo

#### Módulo Finance (finance/scripts/):
- **Foco**: Sinais de investimento, mercados
- **Collectors**: 3 (B3, NASDAQ, funding rounds)
- **Dados**: Financial markets, oportunidades de curto prazo

### Tudo Unificado:
- ✅ **UM projeto**: Sofia Pulse
- ✅ **UM banco**: PostgreSQL
- ✅ **UM schema**: `sofia`
- ✅ **UM objetivo**: Alimentar Sofia IA com intelligence completa

---

## 📊 Comandos Rápidos (Cheat Sheet)

### Demo (2 segundos):
```bash
cd finance && npm run demo
```

### Produção Completa (3 minutos):
```bash
cd finance
npm run invest:full
cat output/sofia-signals-*.json | jq '.signals[] | select(.score > 85)'
```

### Só B3 (30 segundos):
```bash
cd finance
npm run invest:quick
```

### Docker (Recomendado):
```bash
cd finance
./docker-run.sh demo       # Demo
./docker-run.sh full       # Produção
```

---

## 🔍 Verificar Status Finance

### Ver tabelas populadas:
```bash
# No banco:
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "
SELECT 'market_data_brazil' as tabela, COUNT(*) FROM market_data_brazil
UNION ALL
SELECT 'market_data_nasdaq', COUNT(*) FROM market_data_nasdaq
UNION ALL
SELECT 'funding_rounds', COUNT(*) FROM funding_rounds;
"
```

### Ver sinais gerados:
```bash
cd finance
ls -lh output/
cat output/sofia-signals-*.json | jq '.signals | length'
```

---

## 🎉 Conclusão

O **Finance** é um **módulo integrado** do Sofia Pulse:

```
✅ Parte do Sofia Pulse (mesmo projeto)
✅ Mesmo banco de dados PostgreSQL
✅ Mesmo schema (sofia)
✅ Package.json próprio (conveniência)
✅ Docker helper próprio (facilita uso)
✅ Documentação específica (QUICK-START.md)
✅ 3 collectors financeiros
✅ Gerador de sinais de investimento
✅ Demo mode sem banco
```

**Total Sofia Pulse**: 12 collectors (9 econômicos + 3 finance)
**Total Documentação Finance**: 5 scripts TypeScript + 339 linhas de docs

---

**Documentação Finance**: `finance/QUICK-START.md`
**Documentação Geral**: Ver `INDEX-DOCUMENTACAO.md` na raiz
**Criado**: 2025-11-17
**Status**: ✅ Módulo funcionando (2/3 tabelas populadas)
