# 📁 PROJECT STRUCTURE - SOFIA PULSE

**Reorganizado em**: 2025-12-29

---

## 🎯 Estrutura Atual

```
sofia-pulse/
├── 📄 README.md                          # Documentação principal
├── 📄 CLAUDE.md                          # Contexto do projeto (histórico)
├── 📦 package.json                       # Dependências Node.js
├── 📦 requirements-collectors.txt        # Dependências Python
├── 🔧 .env.example                       # Template de configuração
├── 🔧 .gitignore                         # Arquivos ignorados pelo Git
│
├── 📁 scripts/                           # 🟢 CÓDIGO ATIVO (Produção)
│   ├── collect.ts                        # CLI unificado
│   ├── generate-crontab.ts               # Gerador de cron
│   ├── collect-*.py                      # 55 collectors Python
│   ├── shared/                           # Helpers compartilhados
│   │   ├── geo_helpers.py                # Normalização geográfica
│   │   ├── org_helpers.py                # Normalização de empresas
│   │   └── jobs-inserter.ts              # Inserção de vagas
│   ├── configs/                          # Configurações dos collectors
│   │   ├── tech-trends-config.ts
│   │   ├── jobs-config.ts
│   │   ├── legacy-python-config.ts
│   │   └── ...
│   ├── utils/                            # Utilit

ários
│   │   └── sofia_whatsapp_integration.py
│   └── automation/                       # Scripts de automação (132 arquivos)
│       ├── run-*.sh
│       ├── setup-*.sh
│       ├── test-*.sh
│       └── ...
│
├── 📁 docs/                              # 📝 DOCUMENTAÇÃO ATIVA (101 arquivos)
│   ├── DEPLOY_GUIDE.md                   # Guia de deploy
│   ├── WHATSAPP_GUIDE.md                 # Integração WhatsApp
│   ├── QUICK_FIXES.md                    # Correções rápidas
│   ├── SERVER_SETUP.md                   # Setup do servidor
│   ├── ROADMAP.md                        # Roadmap do projeto
│   ├── VISION.md                         # Visão do produto
│   └── ... (95+ outros documentos)
│
├── 📁 legacy/                            # 📦 CÓDIGO ARQUIVADO (Não ativo)
│   ├── README.md                         # Explicação do arquivamento
│   ├── documentation/                    # Relatórios e análises antigas (27 arquivos)
│   │   ├── RAW-ANALYSIS-REPORTS.md
│   │   ├── ACTIVE-vs-LEGACY-CODE.md
│   │   ├── VALIDATION-TEST-REPORT.md
│   │   ├── DATABASE-INVENTORY-REPORT.txt
│   │   └── ... (crontabs, relatórios, etc.)
│   └── one-time-scripts/                 # Scripts executados 1x (46+ arquivos)
│       ├── analise/                      # 8 arquivos
│       ├── check/                        # 11+ arquivos
│       ├── fix/                          # 9 arquivos
│       ├── find/                         # 6+ arquivos
│       ├── migrate/                      # 5+ arquivos
│       ├── restore/                      # 4 arquivos
│       └── add-auto/                     # 3+ arquivos
│
├── 📁 migrations/                        # SQL migrations (101 arquivos)
├── 📁 data/                              # Dados brutos/cache
├── 📁 logs/                              # Logs dos collectors
└── 📁 node_modules/                      # Dependências (ignorado)
```

---

## 📊 Estatísticas

| Categoria | Quantidade | Localização |
|:---|---:|:---|
| **Collectors Ativos** | 55 | `scripts/collect-*.py` |
| **Scripts de Automação** | 132 | `scripts/automation/` |
| **Documentação Ativa** | 101 | `docs/` |
| **Scripts Legacy** | 46+ | `legacy/one-time-scripts/` |
| **Relatórios Arquivados** | 27 | `legacy/documentation/` |
| **Migrations SQL** | 101 | `migrations/` |

---

## 🟢 Código Ativo (Produção)

### Collectors (55 arquivos)
- `scripts/collect-*.py` - Collectors Python
- Executados via cron (hourly/daily)
- Configurados em `scripts/configs/`

### Core (3 arquivos)
- `scripts/collect.ts` - CLI unificado
- `scripts/generate-crontab.ts` - Gerador de cron
- `run-collectors-with-notifications.sh` - Runner com WhatsApp

### Helpers (3 arquivos)
- `scripts/shared/geo_helpers.py` - Normalização geográfica
- `scripts/shared/org_helpers.py` - Normalização de empresas
- `scripts/utils/sofia_whatsapp_integration.py` - Notificações

---

## 📝 Documentação

### Ativa (`docs/`)
- Guias de deploy, setup, configuração
- Roadmap, visão, arquitetura
- Quick starts, troubleshooting

### Arquivada (`legacy/documentation/`)
- Relatórios de análise de código
- Inventários de banco de dados
- Crontabs antigos
- Status reports históricos

---

## 📦 Scripts Legacy

### Categorias (`legacy/one-time-scripts/`)

**analise/** - Scripts de análise regional (executados 1x)
- Geraram `regional-research-data.json`

**restore/** - Scripts de restauração de dados (executados 1x)
- Importaram dados históricos

**migrate/** - Scripts de migração (executados 1x)
- Migraram collectors para nova arquitetura

**fix/** - Scripts de correções pontuais (executados 1x)
- Corrigiram bugs durante desenvolvimento

**check/** - Scripts de validação (executados 1x)
- Validaram dados e estruturas

**find/** - Utilitários de busca (executados 1x)
- Descobriram tabelas, duplicatas, etc.

**add-auto/** - Scripts auxiliares (executados 1x)
- Geraram código automaticamente

---

## 🚀 Arquivos Essenciais na Raiz

Apenas arquivos essenciais devem permanecer na raiz:

✅ **Permitidos**:
- `README.md` - Documentação principal
- `CLAUDE.md` - Contexto do projeto
- `package.json` - Dependências Node.js
- `package-lock.json` - Lock de dependências
- `tsconfig.json` - Configuração TypeScript
- `.env.example` - Template de configuração
- `.gitignore` - Arquivos ignorados
- `requirements-collectors.txt` - Dependências Python
- `run-collectors-with-notifications.sh` - Script principal
- `setup-server.sh` - Setup inicial
- `archive-legacy.sh` - Script de arquivamento

❌ **Movidos**:
- Todos os `.md` (exceto README e CLAUDE) → `docs/`
- Todos os `.sh` (exceto 3 essenciais) → `scripts/automation/`
- Todos os `.txt` de relatórios → `legacy/documentation/`
- Todos os `.py` de teste → `legacy/one-time-scripts/`

---

## 📋 Navegação Rápida

### Quero...

**...rodar os collectors**
```bash
npx tsx scripts/collect.ts [collector-name]
```

**...ver a documentação**
```bash
cd docs/
ls *.md
```

**...configurar o servidor**
```bash
./setup-server.sh
```

**...ver scripts de automação**
```bash
cd scripts/automation/
ls *.sh
```

**...recuperar um script legacy**
```bash
cp legacy/one-time-scripts/categoria/script.py ./
```

---

*Estrutura reorganizada em: 2025-12-29*
