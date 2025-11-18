# 🚀 Sofia Pulse - Quick Start

Geração automática de insights de mercado + email diário.

## ⚡ Executar TUDO Automaticamente

```bash
cd /home/ubuntu/sofia-pulse
bash run-all.sh
```

**Isso vai:**
1. ✅ Coletar dados do mercado (B3, NASDAQ, Funding)
2. ✅ Gerar insights premium
3. ✅ Exportar CSVs
4. ✅ Enviar email para **augustosvm@gmail.com**

## 📧 O que você recebe no email

1. **Insights prontos** (TXT/MD) - Análise executiva completa
2. **Dados RAW (CSVs)**:
   - `funding_rounds_30d.csv` - Rodadas de investimento
   - `market_b3_30d.csv` - Ações B3 (performance)

Você pode usar os insights prontos **OU** pegar os CSVs e mandar para ChatGPT/Claude gerar análises customizadas!

## 🔄 Automatizar (Diário)

```bash
crontab -e
```

Adicione:
```bash
# Sofia Pulse - Email diário às 20:00 BRT
0 23 * * 1-5 cd /home/ubuntu/sofia-pulse && bash run-all.sh >> /var/log/sofia-pulse.log 2>&1
```

## 🛠️ Configuração (apenas primeira vez)

### 1. Instalar dependências

```bash
# Node.js (finance collectors)
cd finance
npm install

# Python (insights generator)
cd ..
python3 -m venv venv-analytics
source venv-analytics/bin/activate
pip install psycopg2-binary python-dotenv google-generativeai
```

### 2. Configurar .env

Já está configurado! Mas se precisar:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sofia_db
DB_USER=sofia
DB_PASSWORD=sofia123strong
ALPHA_VANTAGE_API_KEY=TM3DVH1A35DUPPZ9
GEMINI_API_KEY=AIzaSyAS1uHXDupa5nEzbpnq7BGrZ4M-iD9nsv8

# Email
EMAIL_TO=augustosvm@gmail.com
SMTP_USER=augustosvm@gmail.com
SMTP_PASS=msnxttcudgfhveel
```

### 3. PostgreSQL

```bash
# Iniciar PostgreSQL
sudo service postgresql start

# Criar banco (se necessário)
sudo -u postgres psql -c "CREATE DATABASE sofia_db OWNER sofia;"
```

## 📊 Ver Insights Localmente

```bash
cat analytics/premium-insights/latest-geo.txt
```

## 🧪 Testar Email

```bash
source venv-analytics/bin/activate
python3 send-email.py
```

## 🎯 Estrutura do Projeto

```
sofia-pulse/
├── finance/                    # Collectors (B3, NASDAQ, Funding)
│   └── scripts/
│       ├── collect-brazil-stocks.ts
│       ├── collect-nasdaq-momentum.ts
│       └── collect-funding-rounds.ts
│
├── analytics/
│   └── premium-insights/       # Insights gerados
│       ├── latest-geo.txt      # Insights (texto)
│       ├── latest-geo.md       # Insights (markdown)
│       ├── funding_rounds_30d.csv
│       └── market_b3_30d.csv
│
├── generate-insights-simple.py # Gerador de insights
├── send-email.py              # Envio de email
├── run-all.sh                 # Script all-in-one
└── .env                       # Configurações
```

## 💡 Casos de Uso

### Investidor
- Recebe insights diários de mercado
- Identifica setores em alta
- Monitora rodadas de funding

### Analista
- Usa CSVs para análise customizada
- Integra com outras ferramentas
- Gera relatórios próprios

### Automação
- Configura crontab
- Recebe email automático
- Sem intervenção manual

## 🐛 Troubleshooting

### Email não envia

```bash
# Verificar SMTP_PASS
grep SMTP_PASS .env

# Testar manualmente
python3 send-email.py
```

### PostgreSQL não conecta

```bash
# Verificar se está rodando
sudo service postgresql status

# Iniciar
sudo service postgresql start
```

### Dados vazios

```bash
# Executar collectors manualmente
cd finance
npm run collect:all
```

## 📞 Suporte

Ver `CLAUDE.md` para documentação completa.

---

**Última atualização**: 2025-11-18
**Versão**: 1.0
**Email**: augustosvm@gmail.com
