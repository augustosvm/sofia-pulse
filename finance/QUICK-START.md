# 🚀 Sofia Finance Intelligence Hub - Quick Start

Sistema de geração de sinais de investimento com dados de mercado em tempo real.

## ⚡ Modo Demo (2 segundos!)

**NÃO precisa de banco de dados!** Rode instantaneamente:

```bash
npm run demo
```

### O que o demo faz:

✅ Gera 10+ sinais de investimento com dados realistas
✅ Mostra TOP 10 no console formatado com score bars
✅ Salva JSON em `output/sofia-signals-YYYY-MM-DD.json`
✅ NÃO precisa de banco - roda instantaneamente

### Sinais gerados:

- **3 IPOs Brasil** (NovaTech AI, GreenPower, HealthTech+)
- **4 NASDAQ momentum** (NVDA +8.5%, AVAV +12.3%, MRNA +6.7%, TSLA +5.2%)
- **3 Funding rounds** (Anduril $1.5B, Nubank $750M, Shield AI $500M)

---

## 🗄️ Modo Produção (com PostgreSQL)

### Pré-requisitos

- PostgreSQL rodando (container `sofia-postgres` ou `postgres`)
- Node.js 18+
- npm 9+

### Setup

1. **Instalar dependências**

```bash
npm install
```

2. **Configurar environment**

```bash
cp .env.example .env
# Editar .env com suas credenciais
```

3. **Rodar migrations (criar tabelas)**

```bash
npm run migrate:market
```

### Coleta de Dados

#### Opção 1: Coleta completa (B3 + NASDAQ + Funding)

```bash
npm run invest:full
```

**O que faz:**
- Coleta dados da B3 (stocks brasileiras)
- Coleta momentum do NASDAQ
- Coleta funding rounds recentes
- Gera sinais baseados nos dados coletados
- **Tempo:** ~2-3 minutos

#### Opção 2: Coleta rápida (só B3 - dados gratuitos)

```bash
npm run invest:quick
```

**O que faz:**
- Coleta apenas B3 stocks (~30s)
- Gera sinais baseados em dados brasileiros
- **Tempo:** ~30 segundos

#### Opção 3: Comandos separados

```bash
# Coletar dados
npm run collect:brazil   # B3 stocks (gratuito)
npm run collect:nasdaq   # NASDAQ momentum (requer API key)
npm run collect:funding  # Funding rounds (scraping)
npm run collect:all      # Todos os acima

# Gerar sinais (após coleta)
npm run signals
```

---

## 📊 Estrutura dos Sinais

Cada sinal contém:

```typescript
{
  id: string;
  type: 'IPO' | 'NASDAQ_MOMENTUM' | 'FUNDING_ROUND' | 'B3_STOCK';
  title: string;
  score: number;              // 0-100
  confidence: number;         // 0-100
  potential_return: number;   // %
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  ticker?: string;
  company: string;
  sector: string;
  market: string;
  recommendation: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'WATCH';
  reasoning: string[];
  indicators: {
    revenue_growth?: number;
    market_momentum?: number;
    volume_spike?: number;
    // ...
  };
}
```

---

## 📁 Estrutura do Projeto

```
finance/
├── scripts/
│   ├── demo-signals.ts           # Demo sem banco
│   ├── collect-brazil-stocks.ts  # Coleta B3
│   ├── collect-nasdaq-momentum.ts
│   ├── collect-funding-rounds.ts
│   └── generate-signals.ts       # Geração de sinais
├── dbt/
│   ├── models/
│   │   └── market_data/          # Tabelas do banco
│   └── dbt_project.yml
├── output/
│   └── sofia-signals-*.json      # Sinais gerados
├── package.json
├── .env.example
└── QUICK-START.md (este arquivo)
```

---

## 🔑 Variáveis de Ambiente (.env)

```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=seu_password
POSTGRES_DB=sofia_db

# APIs (opcional para demo)
ALPHA_VANTAGE_API_KEY=your_key  # Para NASDAQ
FINNHUB_API_KEY=your_key         # Para dados premium
```

---

## 🎯 Exemplos de Uso

### Ver sinais no terminal

```bash
npm run demo
```

### Ver sinais em JSON formatado

```bash
npm run demo
cat output/sofia-signals-*.json | jq '.signals[] | select(.score > 85)'
```

### Filtrar sinais por tipo

```bash
cat output/sofia-signals-*.json | jq '.signals[] | select(.type == "NASDAQ_MOMENTUM")'
```

### Top 5 sinais por score

```bash
cat output/sofia-signals-*.json | jq '.signals | sort_by(-.score) | .[0:5]'
```

---

## 🐛 Troubleshooting

### `npm run migrate:market` falha

**Problema:** Banco de dados não acessível

```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Testar conexão
psql -h localhost -U postgres -d sofia_db
```

### `npm run collect:brazil` timeout

**Problema:** Site da B3 pode estar lento

```bash
# Aumentar timeout no script
# Ou rodar apenas o demo
npm run demo
```

### `Missing API key` error

**Problema:** Faltam keys para NASDAQ/Funding

**Solução:** Use apenas dados gratuitos:

```bash
npm run collect:brazil  # Só B3, sem API keys
```

---

## 📚 Comandos Disponíveis

| Comando | Descrição | Tempo | Requer DB |
|---------|-----------|-------|-----------|
| `npm run demo` | Gera sinais demo (sem DB) | 2s | ❌ |
| `npm run invest:quick` | B3 + sinais | 30s | ✅ |
| `npm run invest:full` | Tudo + sinais | 2-3min | ✅ |
| `npm run collect:brazil` | Só coleta B3 | 30s | ✅ |
| `npm run collect:all` | Coleta tudo | 2min | ✅ |
| `npm run signals` | Gera sinais do DB | 5s | ✅ |
| `npm run migrate:market` | Cria tabelas | 10s | ✅ |

---

## 🚀 Roadmap

- [ ] Integração com APIs pagas (Bloomberg, Reuters)
- [ ] Machine Learning para score prediction
- [ ] Backtesting de sinais
- [ ] Dashboard React em tempo real
- [ ] Webhooks para notificações
- [ ] Export para TradingView

---

## 📞 Suporte

Problemas? Abra uma issue ou veja os logs:

```bash
# Logs detalhados
DEBUG=* npm run collect:brazil

# Teste de conexão
npm run test
```

---

**Happy Investing! 📈🚀**
