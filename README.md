# 🌟 Sofia Pulse - Plataforma de Inteligência Agregada Multi-Fonte

[![Status](https://img.shields.io/badge/status-production-green.svg)](https://github.com/augustosvm/sofia-pulse)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Node](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen.svg)](https://nodejs.org)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15%2B-blue.svg)](https://postgresql.org)

**Sofia Pulse** é um ecossistema integrado de inteligência que coleta, processa e gera insights a partir de múltiplas fontes de dados sobre inovação, pesquisa acadêmica, tecnologia e mercado financeiro.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Fontes de Dados](#-fontes-de-dados)
- [Quick Start](#-quick-start)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Automação](#-automação)
- [API & Schema](#-api--schema)
- [Dashboards](#-dashboards)
- [Desenvolvimento](#-desenvolvimento)
- [Deploy](#-deploy)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

---

## 🎯 Visão Geral

Sofia Pulse combina dados de **11+ fontes diferentes** para gerar inteligência acionável sobre:

- 📚 **Pesquisa Acadêmica**: Papers, teses, artigos científicos
- 🏥 **Inovação em Saúde**: Ensaios clínicos, patentes médicas
- 💻 **Tecnologia**: Repositórios GitHub, pacotes npm/pip, Q&A
- 💰 **Mercado Financeiro**: Ações B3/NASDAQ, funding rounds
- 🔬 **Propriedade Intelectual**: Patentes de inovação

### Diferenciais

✅ **Multi-fonte**: Correlaciona dados de diferentes domínios
✅ **Automático**: Coleta e processamento agendados via cron
✅ **Escalável**: Arquitetura modular e extensível
✅ **Open Data**: Foco em fontes públicas e gratuitas
✅ **Insights Únicos**: Detecção de tendências cross-domain

---

## 🚀 Funcionalidades

### Coleta de Dados

| Módulo | Fonte | Tipo | Frequência |
|--------|-------|------|------------|
| **Academia** | ArXiv | Papers científicos | Diária |
| | BDTD | Teses/dissertações BR | Mensal |
| | SciELO | Artigos peer-reviewed | Semanal |
| **Inovação** | Clinical Trials | Ensaios clínicos | Semanal |
| | Patents | Patentes USPTO/INPI | Mensal |
| **Tech** | GitHub | Repositórios trending | Diária |
| | NPM/PyPI | Downloads de pacotes | Semanal |
| | StackOverflow | Perguntas Q&A | Diária |
| **Finance** | B3 | Ações brasileiras | Diária |
| | NASDAQ | Stocks US | Diária |
| | Funding Rounds | Rodadas investimento | Semanal |

### Processamento & Insights

- 🎯 **Geração de Sinais**: Scores compostos de inovação/investimento
- 📊 **Correlações**: Cruzamento entre fontes para insights únicos
- 🔍 **Tendências**: Detecção de tecnologias e áreas emergentes
- 📈 **Predições**: Identificação de startups/empresas promissoras
- 🎨 **Visualizações**: Dashboards Grafana integrados

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    FONTES DE DADOS                          │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  Academia   │  Inovação   │  Tech       │  Finance        │
│  • ArXiv    │  • Trials   │  • GitHub   │  • B3           │
│  • BDTD     │  • Patents  │  • Packages │  • NASDAQ       │
│  • SciELO   │             │  • Stack    │  • Funding      │
└──────┬──────┴──────┬──────┴──────┬──────┴────────┬─────────┘
       │             │             │                │
       └─────────────┴─────────────┴────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  COLETA & PROCESSAMENTO                     │
│  • Scripts TypeScript (.ts)                                 │
│  • Rate limiting & retry logic                              │
│  • Data validation & cleaning                               │
│  • Metadata extraction                                      │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              ARMAZENAMENTO (PostgreSQL)                     │
│  • sofia_db (11+ tabelas especializadas)                    │
│  • Indexes otimizados para queries                          │
│  • Backup automatizado diário                               │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               ANÁLISE & INTELIGÊNCIA                        │
│  • Correlações multi-fonte                                  │
│  • Score de inovação composto                               │
│  • Detecção de tendências                                   │
│  • Sinais de investimento                                   │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                      OUTPUTS                                │
│  • JSON reports (diários/semanais)                          │
│  • Dashboards Grafana                                       │
│  • API REST (integração externa)                            │
│  • Alertas (Telegram/Discord)                               │
└─────────────────────────────────────────────────────────────┘
```

### Stack Tecnológica

- **Backend**: Node.js 18+, TypeScript 5.3+
- **Database**: PostgreSQL 15+ (com pgvector)
- **Containerização**: Docker & Docker Compose
- **Orquestração**: Cron jobs (daily/weekly/monthly)
- **Visualização**: Grafana, Metabase
- **Backup**: Automated PostgreSQL dumps (gzip)

---

## 📊 Fontes de Dados

### 1. Academia & Pesquisa

#### ArXiv (`collect-arxiv.ts`)
- **URL**: https://arxiv.org
- **Dados**: Pre-prints científicos
- **Categorias**: Physics, Math, CS, Biology, Economics
- **Volume**: ~200k papers/ano
- **API**: ArXiv API (gratuita)
- **Frequência**: Diária (novos submissions)

**Schema:**
```sql
CREATE TABLE arxiv_papers (
  id SERIAL PRIMARY KEY,
  arxiv_id VARCHAR(50) UNIQUE,
  title TEXT,
  abstract TEXT,
  authors TEXT[],
  categories VARCHAR(100)[],
  published_date DATE,
  updated_date DATE,
  citation_count INT,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

#### BDTD (`collect-bdtd.ts`)
- **URL**: https://bdtd.ibict.br
- **Dados**: Teses e dissertações brasileiras
- **Instituições**: 100+ universidades
- **Volume**: ~500k documentos
- **Frequência**: Mensal

**Schema:**
```sql
CREATE TABLE bdtd_theses (
  id SERIAL PRIMARY KEY,
  bdtd_id VARCHAR(100) UNIQUE,
  title TEXT,
  author VARCHAR(255),
  advisor VARCHAR(255),
  university VARCHAR(255),
  program VARCHAR(255),
  degree_type VARCHAR(50), -- mestrado/doutorado
  area VARCHAR(100),
  abstract TEXT,
  keywords TEXT[],
  defense_date DATE,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

#### SciELO (`collect-scielo.ts`)
- **URL**: https://scielo.org
- **Dados**: Artigos científicos revisados por pares
- **Região**: América Latina e Caribe
- **Journals**: 1,200+
- **Frequência**: Semanal

**Schema:**
```sql
CREATE TABLE scielo_articles (
  id SERIAL PRIMARY KEY,
  doi VARCHAR(100) UNIQUE,
  title TEXT,
  authors TEXT[],
  journal VARCHAR(255),
  issue VARCHAR(50),
  year INT,
  abstract TEXT,
  keywords TEXT[],
  citations INT,
  url TEXT,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 2. Inovação & Saúde

#### Clinical Trials (`collect-clinical-trials.ts`)
- **URLs**:
  - ClinicalTrials.gov (global)
  - REBEC (Brasil)
- **Dados**: Estudos clínicos em andamento
- **Fases**: I, II, III, IV
- **Frequência**: Semanal

**Schema:**
```sql
CREATE TABLE clinical_trials (
  id SERIAL PRIMARY KEY,
  trial_id VARCHAR(50) UNIQUE,
  title TEXT,
  sponsor VARCHAR(255),
  phase VARCHAR(20),
  condition TEXT,
  intervention TEXT,
  status VARCHAR(50),
  start_date DATE,
  completion_date DATE,
  enrollment INT,
  country VARCHAR(100),
  collected_at TIMESTAMP DEFAULT NOW()
);
```

**Insights possíveis:**
- Áreas de pesquisa médica em alta
- Empresas farmacêuticas mais ativas
- Doenças com mais investimento em P&D

#### Patents (`collect-patents.ts`)
- **URLs**:
  - USPTO (EUA)
  - EPO (Europa)
  - INPI (Brasil)
- **Dados**: Patentes de invenção
- **Frequência**: Mensal

**Schema:**
```sql
CREATE TABLE patents (
  id SERIAL PRIMARY KEY,
  patent_number VARCHAR(50) UNIQUE,
  title TEXT,
  abstract TEXT,
  inventors TEXT[],
  assignee VARCHAR(255), -- empresa/instituição
  filing_date DATE,
  grant_date DATE,
  classifications VARCHAR(50)[],
  citations_count INT,
  country VARCHAR(10),
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 3. Tecnologia & Desenvolvimento

#### GitHub (`collect-github.ts`)
- **API**: GitHub REST API v3
- **Dados**: Repositórios trending, stars, forks
- **Rate Limit**: 5000 requests/hora (autenticado)
- **Frequência**: Diária

**Schema:**
```sql
CREATE TABLE github_repos (
  id SERIAL PRIMARY KEY,
  repo_id BIGINT UNIQUE,
  full_name VARCHAR(255),
  description TEXT,
  language VARCHAR(50),
  stars INT,
  forks INT,
  watchers INT,
  issues_count INT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  topics TEXT[],
  license VARCHAR(50),
  collected_at TIMESTAMP DEFAULT NOW()
);
```

#### Software Packages (`collect-packages.ts`)
- **Registries**: npm, PyPI, RubyGems, Maven
- **Dados**: Downloads, versões, dependências
- **Frequência**: Semanal

**Schema:**
```sql
CREATE TABLE software_packages (
  id SERIAL PRIMARY KEY,
  package_name VARCHAR(255),
  registry VARCHAR(20), -- npm, pypi, etc
  version VARCHAR(50),
  downloads_week BIGINT,
  downloads_month BIGINT,
  dependencies JSONB,
  description TEXT,
  keywords TEXT[],
  collected_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(package_name, registry, collected_at)
);
```

#### StackOverflow (`collect-stackoverflow.ts`)
- **API**: StackExchange API
- **Dados**: Perguntas, respostas, tags
- **Rate Limit**: 10000 requests/dia
- **Frequência**: Diária

**Schema:**
```sql
CREATE TABLE stackoverflow_questions (
  id SERIAL PRIMARY KEY,
  question_id BIGINT UNIQUE,
  title TEXT,
  tags VARCHAR(50)[],
  score INT,
  view_count INT,
  answer_count INT,
  is_answered BOOLEAN,
  created_at TIMESTAMP,
  collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 4. Finance (Já Implementado)

Ver documentação detalhada em [`finance/README.md`](finance/README.md)

---

## ⚡ Quick Start

### Pré-requisitos

- Node.js 18+ e npm 9+
- PostgreSQL 15+
- Docker & Docker Compose (opcional)
- Git

### Instalação Rápida

```bash
# 1. Clone o repositório
git clone https://github.com/augustosvm/sofia-pulse.git
cd sofia-pulse

# 2. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 3. Instale dependências
npm install

# 4. Configure banco de dados
npm run migrate

# 5. Teste coleta (finance module - mais rápido)
cd finance
npm install
npm run demo

# 6. Ver resultados
cat output/sofia-signals-*.json | jq
```

---

## 💾 Instalação

### Opção 1: Docker (Recomendado)

```bash
# Subir PostgreSQL + serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Executar coleta
docker-compose exec sofia npm run collect:all

# Parar serviços
docker-compose down
```

### Opção 2: Instalação Local

#### 1. PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql-15 postgresql-contrib

# macOS
brew install postgresql@15

# Iniciar serviço
sudo systemctl start postgresql
```

#### 2. Criar Database

```bash
sudo -u postgres psql

CREATE DATABASE sofia_db;
CREATE USER sofia WITH PASSWORD 'sofia123strong';
GRANT ALL PRIVILEGES ON DATABASE sofia_db TO sofia;
\q
```

#### 3. Node.js & Dependências

```bash
# Instalar Node.js 18+
# Via nvm (recomendado)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Instalar dependências
npm install
```

#### 4. Rodar Migrações

```bash
npm run migrate
```

---

## 🎮 Uso

### Coleta de Dados

#### Comandos Disponíveis

```bash
# Academia
npm run collect:arxiv          # Papers ArXiv
npm run collect:bdtd           # Teses BDTD
npm run collect:scielo         # Artigos SciELO

# Inovação
npm run collect:clinical       # Clinical Trials
npm run collect:patents        # Patentes

# Tech
npm run collect:github         # GitHub trending
npm run collect:packages       # NPM/PyPI downloads
npm run collect:stackoverflow  # Stack Q&A

# Finance (módulo separado)
cd finance
npm run collect:brazil         # B3 stocks
npm run collect:nasdaq         # NASDAQ
npm run collect:funding        # Funding rounds

# Coletar tudo
npm run collect:all
```

#### Coleta Manual

```bash
# Exemplo: Coletar papers do ArXiv
npm run collect:arxiv

# Com filtros (editar script)
npm run collect:arxiv -- --category=cs.AI --since=2024-01-01
```

### Geração de Insights

```bash
# Gerar sinais de investimento (finance module)
cd finance
npm run signals

# Gerar score de inovação multi-fonte
npm run analyze:innovation

# Detectar tendências tech
npm run analyze:trends

# Correlação pesquisa → mercado
npm run analyze:research-to-market
```

### Queries & Análises

```bash
# Conectar ao banco
docker exec -it sofia-postgres psql -U sofia -d sofia_db

# Ou localmente
psql -U sofia -d sofia_db
```

#### Exemplos de Queries

**Top empresas inovadoras (patentes + funding):**
```sql
SELECT
  p.assignee as company,
  COUNT(DISTINCT p.patent_number) as patents,
  f.round_type,
  f.amount_usd / 1000000000 as funding_billions
FROM patents p
JOIN funding_rounds f ON p.assignee = f.company
WHERE p.grant_date > NOW() - INTERVAL '2 years'
GROUP BY p.assignee, f.round_type, f.amount_usd
HAVING COUNT(DISTINCT p.patent_number) > 10
ORDER BY patents DESC, funding_billions DESC
LIMIT 20;
```

**Tecnologias emergentes (GitHub + StackOverflow):**
```sql
SELECT
  g.language,
  SUM(g.stars) as total_stars,
  COUNT(DISTINCT g.repo_id) as repos,
  COUNT(DISTINCT sq.question_id) as so_questions
FROM github_repos g
LEFT JOIN stackoverflow_questions sq
  ON g.language = ANY(sq.tags)
WHERE g.created_at > NOW() - INTERVAL '6 months'
GROUP BY g.language
ORDER BY total_stars DESC
LIMIT 15;
```

**Pipeline pesquisa → produto (ArXiv → Patents → Funding):**
```sql
SELECT
  a.categories[1] as research_area,
  COUNT(DISTINCT a.arxiv_id) as papers,
  COUNT(DISTINCT p.patent_number) as patents,
  COUNT(DISTINCT f.company) as funded_companies,
  AVG(f.amount_usd) as avg_funding
FROM arxiv_papers a
LEFT JOIN patents p ON a.categories && p.classifications
LEFT JOIN funding_rounds f ON p.assignee = f.company
WHERE a.published_date > '2023-01-01'
GROUP BY research_area
HAVING COUNT(DISTINCT a.arxiv_id) > 100
ORDER BY papers DESC;
```

---

## ⚙️ Automação

### Cron Jobs

#### Setup

```bash
# Editar crontab
crontab -e
```

#### Jobs Recomendados

```bash
# 1. Backup PostgreSQL - 2h da manhã
0 2 * * * /home/ubuntu/sofia-pulse/scripts/backup-complete.sh >> /var/log/sofia-backup.log 2>&1

# 2. Coleta diária - 6h da manhã
0 6 * * * cd /home/ubuntu/sofia-pulse && ./cron-daily.sh >> /var/log/sofia-daily.log 2>&1

# 3. Coleta semanal - domingo 3h
0 3 * * 0 cd /home/ubuntu/sofia-pulse && ./cron-weekly.sh >> /var/log/sofia-weekly.log 2>&1

# 4. Coleta mensal - dia 1, 4h
0 4 1 * * cd /home/ubuntu/sofia-pulse && ./cron-monthly.sh >> /var/log/sofia-monthly.log 2>&1

# 5. Finance signals - dias úteis 18h
0 18 * * 1-5 cd /home/ubuntu/sofia-pulse/finance && npm run invest:full >> /var/log/sofia-finance.log 2>&1

# 6. Limpeza de backups antigos - domingo 5h
0 5 * * 0 find /var/backups/postgres/ -name "*.sql.gz" -mtime +7 -delete

# 7. Limpeza de logs antigos - domingo 6h
0 6 * * 0 find /home/ubuntu/sofia-pulse/logs/ -name "*.log" -mtime +30 -delete
```

### Scripts de Automação

#### `cron-daily.sh` - Coleta Diária

```bash
#!/bin/bash
set -e

# ArXiv papers novos
npm run collect:arxiv

# GitHub trending
npm run collect:github

# StackOverflow questions
npm run collect:stackoverflow

# Finance (B3 + NASDAQ)
cd finance && npm run collect:all && cd ..

echo "✅ Daily collection completed at $(date)"
```

#### `cron-weekly.sh` - Coleta Semanal

```bash
#!/bin/bash
set -e

# SciELO articles
npm run collect:scielo

# Clinical trials updates
npm run collect:clinical

# Package stats
npm run collect:packages

# Funding rounds
cd finance && npm run collect:funding && cd ..

echo "✅ Weekly collection completed at $(date)"
```

#### `cron-monthly.sh` - Coleta Mensal

```bash
#!/bin/bash
set -e

# BDTD theses
npm run collect:bdtd

# Patents
npm run collect:patents

# Generate monthly report
npm run report:monthly

echo "✅ Monthly collection completed at $(date)"
```

---

## 📡 API & Schema

### REST API (Em Desenvolvimento)

#### Endpoints Planejados

```
GET  /api/v1/signals              # Investment signals
GET  /api/v1/trends               # Technology trends
GET  /api/v1/innovation/:company  # Innovation score
GET  /api/v1/research/areas       # Research areas trending
GET  /api/v1/patents/:company     # Company patents
GET  /api/v1/clinical-trials      # Active trials
```

### Database Schema Completo

Ver [`docs/SCHEMA.md`](docs/SCHEMA.md) para schema completo com todos os índices e constraints.

**Resumo das tabelas:**

```
sofia_db
├── Academia (3 tabelas)
│   ├── arxiv_papers
│   ├── bdtd_theses
│   └── scielo_articles
├── Inovação (2 tabelas)
│   ├── clinical_trials
│   └── patents
├── Tech (3 tabelas)
│   ├── github_repos
│   ├── software_packages
│   └── stackoverflow_questions
└── Finance (3 tabelas)
    ├── market_data_brazil
    ├── market_data_nasdaq
    └── funding_rounds
```

---

## 📊 Dashboards

### Grafana

#### Setup

```bash
# Adicionar datasource PostgreSQL
docker exec -it grafana grafana-cli plugins install postgres

# Import dashboard
# Ver dashboards/ para JSONs prontos
```

#### Dashboards Disponíveis

1. **Innovation Overview**
   - Top companies by innovation score
   - Patents vs Funding correlation
   - Research areas trending

2. **Tech Trends**
   - GitHub languages popularity
   - NPM/PyPI downloads
   - StackOverflow questions by tag

3. **Finance Intelligence**
   - Investment signals
   - B3 vs NASDAQ performance
   - Funding rounds timeline

4. **Research Pipeline**
   - ArXiv publications by category
   - Clinical trials by phase
   - BDTD theses by university

---

## 🛠️ Desenvolvimento

### Estrutura de Projeto

```
sofia-pulse/
├── src/                    # Código core
│   ├── collectors/         # Módulos de coleta
│   ├── analyzers/          # Análise e insights
│   ├── utils/              # Utilitários
│   └── types/              # TypeScript types
├── scripts/                # Scripts executáveis
├── migrations/             # Migrações SQL
├── tests/                  # Testes automatizados
├── docs/                   # Documentação
├── finance/                # Módulo finance separado
└── workflows/              # GitHub Actions CI/CD
```

### Adicionar Nova Fonte de Dados

#### 1. Criar Collector

```typescript
// scripts/collect-nova-fonte.ts
import { Client } from 'pg';
import axios from 'axios';

interface NovaFonteData {
  id: string;
  title: string;
  // ... outros campos
}

async function collectNovaFonte() {
  const client = new Client({
    host: process.env.POSTGRES_HOST,
    // ...config
  });

  try {
    await client.connect();

    // Criar tabela se não existir
    await client.query(`
      CREATE TABLE IF NOT EXISTS nova_fonte (
        id SERIAL PRIMARY KEY,
        external_id VARCHAR(100) UNIQUE,
        title TEXT,
        collected_at TIMESTAMP DEFAULT NOW()
      );
    `);

    // Coletar dados
    const response = await axios.get('https://api.novafonte.com/data');
    const data: NovaFonteData[] = response.data;

    // Inserir no banco
    for (const item of data) {
      await client.query(`
        INSERT INTO nova_fonte (external_id, title)
        VALUES ($1, $2)
        ON CONFLICT (external_id) DO NOTHING
      `, [item.id, item.title]);
    }

    console.log(`✅ ${data.length} items coletados`);
  } finally {
    await client.end();
  }
}

collectNovaFonte();
```

#### 2. Adicionar ao package.json

```json
{
  "scripts": {
    "collect:nova-fonte": "tsx scripts/collect-nova-fonte.ts"
  }
}
```

#### 3. Adicionar ao cron

```bash
# Em cron-daily.sh
npm run collect:nova-fonte
```

### Testes

```bash
# Rodar todos testes
npm test

# Teste específico
npm test -- collect-arxiv

# Coverage
npm run test:coverage
```

---

## 🚀 Deploy

### Deploy Produção (Docker)

```bash
# Build images
docker-compose build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Verificar saúde
docker-compose ps
docker-compose logs -f
```

### Deploy em VPS

Ver guia completo em [`DEPLOY.md`](DEPLOY.md)

**Resumo:**

1. Configurar servidor (Ubuntu 20.04+)
2. Instalar Docker & Docker Compose
3. Configurar firewall e SSL
4. Deploy via docker-compose
5. Configurar cron jobs
6. Setup monitoring (Grafana + Prometheus)

---

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão PostgreSQL

```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Testar conexão
docker exec -it sofia-postgres psql -U sofia -d sofia_db -c "SELECT 1;"

# Ver logs
docker logs sofia-postgres --tail 100
```

#### 2. Rate Limit em APIs

```bash
# GitHub: Verificar rate limit
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/rate_limit

# Solução: Aguardar reset ou usar autenticação
```

#### 3. Backup Falhando

```bash
# Verificar permissões
ls -la /var/backups/postgres/

# Criar diretório se necessário
sudo mkdir -p /var/backups/postgres
sudo chown -R $(whoami) /var/backups/postgres

# Rodar backup manualmente
./scripts/backup-complete.sh
```

#### 4. Coleta Travando

```bash
# Ver processos Node rodando
ps aux | grep node

# Matar processo travado
kill -9 <PID>

# Ver logs para debugar
tail -f logs/sofia-*.log
```

### Logs

```bash
# Logs de coleta
tail -f /var/log/sofia-daily.log
tail -f /var/log/sofia-weekly.log

# Logs PostgreSQL
docker logs sofia-postgres --tail 100 -f

# Logs de backup
tail -f /var/log/sofia-backup.log
```

---

## 🗺️ Roadmap

### Q1 2025

- [x] Finance module completo (B3, NASDAQ, Funding)
- [x] Backup automatizado PostgreSQL
- [x] Docker & Docker Compose setup
- [ ] API REST v1
- [ ] Dashboard Grafana completo
- [ ] Testes automatizados

### Q2 2025

- [ ] Machine Learning para predição de scores
- [ ] Backtesting de sinais financeiros
- [ ] Integração n8n para workflows
- [ ] Alertas Telegram/Discord
- [ ] Mobile app (React Native)

### Q3 2025

- [ ] Coleta de criptomoedas (Binance, Coinbase)
- [ ] Análise de sentimento (Twitter, Reddit)
- [ ] Sistema de recomendação personalizado
- [ ] Export para TradingView

### Q4 2025

- [ ] Multi-tenancy
- [ ] API pública (freemium model)
- [ ] Marketplace de sinais
- [ ] Integração Bloomberg Terminal

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, leia nosso [Guia de Contribuição](CONTRIBUTING.md).

### Como Contribuir

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Code Style

- TypeScript com strict mode
- ESLint + Prettier
- Commits semânticos: `Add:`, `Fix:`, `Update:`, `Remove:`

---

## 📄 Licença

Este projeto está sob a licença MIT. Ver [`LICENSE`](LICENSE) para mais detalhes.

---

## 📞 Suporte & Contato

- **Issues**: [GitHub Issues](https://github.com/augustosvm/sofia-pulse/issues)
- **Discussões**: [GitHub Discussions](https://github.com/augustosvm/sofia-pulse/discussions)
- **Email**: contato@sofia-pulse.com

---

## 🙏 Agradecimentos

- ArXiv por fornecer API gratuita
- BDTD e SciELO pela pesquisa científica brasileira
- GitHub, npm, PyPI por dados abertos
- Comunidade open source

---

## 📚 Documentação Adicional

- [Architecture](docs/ARCHITECTURE.md) - Arquitetura detalhada
- [API Reference](docs/API.md) - Referência completa da API
- [Database Schema](docs/SCHEMA.md) - Schema e relacionamentos
- [Finance Module](finance/README.md) - Documentação do módulo finance
- [Deployment Guide](DEPLOY.md) - Guia de deploy em produção
- [Contributing Guide](CONTRIBUTING.md) - Como contribuir
- [Changelog](CHANGELOG.md) - Histórico de versões

---

<p align="center">
  <strong>🌟 Sofia Pulse - Transformando dados em inteligência acionável</strong>
</p>

<p align="center">
  Feito com ❤️ pela comunidade Sofia
</p>
