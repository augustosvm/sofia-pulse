# 🌟 Sofia Finance Intelligence Hub

Geração automática de sinais de investimento usando dados de mercado em tempo real.

## 🚀 Quick Start (2 segundos!)

```bash
cd finance
npm run demo
```

**Não precisa de banco de dados!** Veja 10+ sinais de investimento instantaneamente.

## 📖 Documentação Completa

Veja [QUICK-START.md](./QUICK-START.md) para:
- Modo demo (sem banco)
- Setup com PostgreSQL
- Coleta de dados real (B3, NASDAQ, Funding)
- Troubleshooting

## 📊 Exemplo de Output

```
#1 | 🚀 AVAV Momentum +12.3%
════════════════════════════════════════════════════════════════════════════════
📊 Score: ████████████████████░ 95/100
🎯 Confidence: 88% | 🟡 Risk: MEDIUM
💰 Potential Return: 21.4%
📈 AVAV | $189.30 → $229.80

🏢 AeroVironment | Defense Tech | NASDAQ

✨ Why this matters:
   1. Contrato $450M com DoD anunciado
   2. Drones Switchblade em alta demanda
   3. Revenue beat de 18% vs consensus
   4. Insider buying de $2.3M
```

## 🎯 Features

- ✅ **Demo Mode:** Sinais instantâneos sem configuração
- ✅ **B3 Integration:** Stocks brasileiras em tempo real
- ✅ **NASDAQ Momentum:** Detecção de high-momentum stocks
- ✅ **IPO Tracking:** Análise de novos IPOs
- ✅ **Funding Rounds:** VC/PE investment tracking
- ✅ **Risk Assessment:** Análise automática de risco
- ✅ **JSON Export:** Integração fácil com outras ferramentas

## 📦 O que está incluído

```
finance/
├── scripts/
│   └── demo-signals.ts     # ⚡ Demo mode (roda sem banco!)
├── output/
│   └── *.json             # 📁 Sinais gerados
├── package.json           # 📦 Scripts npm
├── .env.example           # 🔑 Template de configuração
├── QUICK-START.md         # 📖 Guia completo
└── README.md              # 📄 Este arquivo
```

## 🔧 Scripts Disponíveis

| Comando | O que faz | Tempo |
|---------|-----------|-------|
| `npm run demo` | Demo sem banco | 2s |
| `npm run invest:quick` | B3 + sinais | 30s |
| `npm run invest:full` | Coleta completa | 2-3min |

Veja todos os comandos em [QUICK-START.md](./QUICK-START.md#-comandos-disponveis)

## 🌐 Fontes de Dados

- **B3 (Brasil):** Stocks, volumes, momentum
- **NASDAQ:** High-momentum tech stocks
- **Funding Rounds:** Crunchbase, TechCrunch
- **IPOs:** SEC filings, notícias
- **News Sentiment:** (futuro) Análise de sentimento

## 🛠️ Tech Stack

- **Runtime:** Node.js 18+ com TypeScript
- **Database:** PostgreSQL (opcional)
- **Data Collection:** Axios + Cheerio (web scraping)
- **Output:** JSON + Console formatado

## 📈 Roadmap

- [ ] Machine Learning scoring
- [ ] Real-time WebSocket feeds
- [ ] React dashboard
- [ ] Backtesting engine
- [ ] TradingView integration
- [ ] Mobile notifications
- [ ] Multi-language support

## 🤝 Contributing

PRs são bem-vindos! Veja issues abertas ou abra uma nova.

## 📄 License

MIT License - use como quiser!

---

**Made with 💙 by Sofia Intelligence Hub**
