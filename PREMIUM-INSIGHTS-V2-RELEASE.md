# 🚀 Premium Insights v2.0 - Release Notes

**Data de Release**: 2025-11-18
**Versão**: 2.0.0
**Status**: ✅ Pronto para Produção

---

## 📊 O Que Mudou?

### Feedback do Usuário Que Motivou a v2.0:

> "Não tem as empresas que vao abrir capital provavelmente. Queria que falasse no mundo, pelo menos por continente, quais as pesquisas e startups estão surgindo. Pra sabermos as tendências em cada lugar. Está muito pobre a analise com tanto dado. As universidades brasileiras com certeza não fazem papers de armas. Nem as da Coreia. Tem uma gama que temos que explorar. Quero gerar textos em cima disso."

### Problemas Resolvidos:

1. ❌ **v1.0**: Análise muito rasa, sem contexto geográfico
2. ❌ **v1.0**: Faltava IPO calendar (empresas indo a público)
3. ❌ **v1.0**: Sem análise regional/especialização por país
4. ❌ **v1.0**: Dados brutos, não textos prontos para copiar
5. ❌ **v1.0**: Duplicatas nas Top 5 ações (bug crítico)

---

## ✨ Novos Recursos v2.0

### 1. 🗺️ Análise Geográfica Completa

**Mapeamento de Continentes/Países**:
- 50+ países mapeados para continentes
- Análise de funding por continente
- Startups e papers por região geográfica
- Tendências específicas de cada país

**Exemplo de Output**:
```
🌍 MAPA GLOBAL DA INOVAÇÃO

América do Norte:
- Funding: $2.5B (45% do total mundial)
- Papers: 350 (MIT, Stanford, Berkeley)
- Setores em alta: AI, SaaS, Biotech

América do Sul:
- Funding: $450M (Brasil lidera)
- Papers: 85 (USP, Unicamp)
- Setores em alta: Agro-tech, Fintech, Ed-tech
```

### 2. 🎓 Rastreamento de Universidades

**Database de Universidades e Especializações**:
- MIT (USA): AI, Robotics, Computer Science
- Stanford (USA): AI, Biotech, Clean Energy
- USP (Brasil): Agro-tech, Medicine, Engineering
- Unicamp (Brasil): Agro-tech, Materials, Energy
- Tsinghua (China): AI, Manufacturing, Engineering
- Oxford (UK): Medicine, AI, Climate
- E mais 20+ universidades

**Extração Automática de Afiliações**:
```python
# Exemplo: detecta universidade no campo "authors" do ArXiv
"John Doe (MIT), Jane Smith (Stanford)"
→ MIT detectado → País: USA → Especialização: AI, Robotics
```

### 3. 🌐 Especializações Regionais

**Mapeamento de Expertise por Região**:
- **Brasil**: Agro-tech, Fintech, Healthcare, Ed-tech
- **USA**: AI, SaaS, Biotech, Space
- **China**: AI, Manufacturing, Hardware, E-commerce
- **Europa**: Green Tech, Privacy Tech, Mobility, Deep Tech
- **Israel**: Cybersecurity, Defense Tech, AI, Biotech
- **Índia**: Outsourcing, SaaS, Fintech, AI
- **Singapura**: Fintech, Supply Chain, Clean Energy

**Por que isso importa?**:
- Universidades brasileiras **NÃO** fazem papers de armas (fazem Agro-tech)
- Universidades coreanas focam em Manufacturing/Hardware
- MIT/Stanford lideram em AI
- Especializações regionais guiam tendências de inovação

### 4. 📈 IPO Calendar (NOVO!)

**Fontes de Dados**:
- NASDAQ IPO Calendar
- B3 Ofertas Públicas
- SEC/EDGAR S-1 Filings

**Tabela no Banco**: `sofia.ipo_calendar`

**Campos**:
```sql
- company: Nome da empresa
- ticker: Símbolo (se já definido)
- exchange: NASDAQ, B3, NYSE
- expected_date: Data esperada do IPO
- price_range: Faixa de preço (ex: "$15-17")
- sector: Setor (Tech, Healthcare, etc)
- country: País de origem
- status: Expected | Filed | Priced | Trading
- underwriters: Bancos coordenadores
```

**Exemplo de Insight Gerado**:
```
💰 PRÓXIMOS IPOs (30 dias)

NASDAQ:
- TechCorp (IPO estimado: 2025-12-15)
  Faixa: $18-20 | Setor: AI/SaaS
  Underwriters: Goldman Sachs, Morgan Stanley

B3:
- AgroTech Brasil (IPO estimado: 2025-12-20)
  Faixa: R$25-28 | Setor: Agro-tech
  Underwriters: BTG Pactual, Itaú BBA
```

### 5. 📝 Narrativas Prontas para Copiar (Gemini AI)

**Geração Automática de Textos**:
- Narrativas corridas (não bullet points)
- Contexto geográfico incluído
- Dados concretos citados
- 3-4 parágrafos prontos para colunas

**Exemplo de Narrativa Gerada**:
```
A inovação global está cada vez mais distribuída geograficamente, com
a América do Norte liderando em financiamento ($2.5B nos últimos 30 dias),
mas a América do Sul e Ásia emergindo como polos de especialização regional.
Brasil lidera em Agro-tech com startups como XYZ captando $50M, enquanto
China domina Manufacturing com 45% dos papers publicados na área...

[continua com 2-3 parágrafos adicionais]
```

**Custo**: ~$0.01-0.02 por análise (Gemini 2.5 Pro Preview)

### 6. 🐛 Bug Fix: Duplicatas nas Top 5 Ações

**Problema Detectado pelo Usuário**:
```
Top 5 Performers B3:
- WEGE3 (WEG): +3.10%
- WEGE3 (WEG): +3.10%  ❌ DUPLICATA
- WEGE3 (WEG): +3.10%  ❌ DUPLICATA
- WEGE3 (WEG): +3.10%  ❌ DUPLICATA
- WEGE3 (WEG): +3.10%  ❌ DUPLICATA
```

**Causa Raiz**: Mesma ação coletada em múltiplos timestamps criava duplicatas

**Correção Aplicada**:
```python
# ANTES (ERRADO):
b3_top = df_b3.nlargest(5, 'change_pct')

# DEPOIS (CORRETO):
b3_unique = df_b3.drop_duplicates(subset='ticker', keep='first')
b3_top = b3_unique.nlargest(5, 'change_pct')
```

**Resultado**: Agora mostra 5 ações **diferentes** corretamente

---

## 📁 Arquivos Criados/Modificados

### Novos Arquivos:

1. **`generate-premium-insights-v2.py`** (700+ linhas)
   - Sistema completo de análise geográfica
   - Mapeamento de continentes/países/universidades
   - Geração de narrativas via Gemini AI

2. **`generate-premium-insights-v2.sh`**
   - Wrapper script com output colorido
   - Validação de venv
   - Mensagens amigáveis

3. **`collectors/ipo-calendar.ts`**
   - Coleta IPOs do NASDAQ
   - Coleta IPOs da B3
   - Coleta S-1 filings do SEC/EDGAR

4. **`db/migrations/007_create_ipo_calendar.sql`**
   - Tabela `sofia.ipo_calendar`
   - Índices otimizados
   - Triggers de updated_at

5. **`test-premium-insights-v2.sh`**
   - Script de validação completo
   - Testa arquivos, venv, banco, API
   - Executa e valida output

6. **`CRONTAB-COMPLETO.md`**
   - Documentação completa de automação
   - Cronograma visual
   - Instruções de instalação

7. **`install-crontab.sh`**
   - Instalador interativo de crontab
   - Backup automático do crontab anterior
   - Confirmação antes de instalar

### Arquivos Modificados:

1. **`generate-premium-insights.py`**
   - Fix de duplicatas (drop_duplicates)
   - Mantido como v1.0 para compatibilidade

---

## 🎯 Insights Gerados pela v2.0

### Arquivos de Output:

```
analytics/premium-insights/
├── latest-geo.md          # Insights geo-localizados (Markdown)
├── latest-geo.txt         # Mesmo conteúdo em TXT
└── geo-summary.csv        # Resumo continental em CSV
```

### Seções dos Insights:

1. **🌍 Mapa Global da Inovação**
   - Papers por continente
   - Funding por região
   - Universidades mais ativas

2. **🎯 Especialização Regional**
   - Setores em alta por continente
   - Startups por país
   - Tendências específicas

3. **🔥 Países em Destaque**
   - Top países por funding
   - Top países por papers
   - Cruzamento de dados

4. **📊 Performance de Mercado**
   - Top 5 B3 (sem duplicatas!)
   - Top 5 NASDAQ
   - Setores em alta

5. **💰 Próximos IPOs**
   - IPOs esperados (30 dias)
   - Por bolsa (NASDAQ, B3)
   - Setor e faixa de preço

6. **🤖 Resumo Executivo (Gemini AI)**
   - Narrativa corrida
   - Pronta para copiar/colar
   - Contextualizada geograficamente

---

## 🚀 Como Usar a v2.0

### 1. Teste no Servidor (PRIMEIRA VEZ):

```bash
# No servidor (91.98.158.19 ou outro):
cd /home/ubuntu/sofia-pulse

# Puxar atualizações
git pull

# Executar teste completo
bash test-premium-insights-v2.sh
```

**O script de teste vai**:
- ✅ Verificar todos os arquivos necessários
- ✅ Validar virtual environment e pacotes Python
- ✅ Testar conexão com PostgreSQL
- ✅ Contar registros nas tabelas
- ✅ Verificar GEMINI_API_KEY
- ✅ Executar geração de insights
- ✅ Validar arquivos de output
- ✅ Mostrar preview dos insights

### 2. Executar Manualmente:

```bash
cd /home/ubuntu/sofia-pulse
bash generate-premium-insights-v2.sh
```

### 3. Ver Resultados:

```bash
# Ver insights completos
cat analytics/premium-insights/latest-geo.txt

# Ver apenas resumo executivo (Gemini AI)
grep -A 20 "RESUMO EXECUTIVO" analytics/premium-insights/latest-geo.txt

# Ver resumo continental em CSV
cat analytics/premium-insights/geo-summary.csv
```

### 4. Instalar Automação (Crontab):

```bash
bash install-crontab.sh
```

**Cronograma Automático**:
- 21:00 UTC (Seg-Sex): Finance B3
- 21:05 UTC (Seg-Sex): Finance NASDAQ
- 21:10 UTC (Diário): Finance Funding
- 21:10 UTC (Diário): IPO Calendar
- 22:00 UTC (Seg-Sex): Premium Insights v2

---

## ⚙️ Configuração Necessária

### 1. GEMINI_API_KEY (Opcional mas Recomendado)

**Sem a chave**:
- Insights geográficos funcionam normalmente
- Falta apenas o "Resumo Executivo" narrativo

**Com a chave**:
- Narrativas AI geradas automaticamente
- Textos prontos para copiar/colar

**Como configurar**:
```bash
echo 'GEMINI_API_KEY=sua-chave-aqui' >> /home/ubuntu/sofia-pulse/.env
```

**Como conseguir chave**:
1. Acesse: https://aistudio.google.com/app/apikey
2. Clique em "Create API Key"
3. Copie a chave
4. Cole no .env

**Custo**: ~$0.01-0.02 por análise (Gemini 2.5 Pro Preview)

### 2. Dados no Banco

**Tabelas necessárias com dados**:
- `sofia.stackoverflow_trends` (opcional)
- `sofia.github_metrics` (opcional)
- `sofia.publications` (recomendado - para análise de universidades)
- `sofia.startups` (recomendado - para análise regional)
- `sofia.funding_rounds` (recomendado - para funding por continente)
- `sofia.market_data_brazil` (recomendado - Top 5 B3)
- `sofia.market_data_nasdaq` (recomendado - Top 5 NASDAQ)
- `sofia.ipo_calendar` (novo - IPOs futuros)

**Se tabelas estiverem vazias**:
```bash
# Executar collectors
npm run collect:brazil      # Popula market_data_brazil
npm run collect:nasdaq      # Popula market_data_nasdaq
npm run collect:funding     # Popula funding_rounds
npm run collect:ipo-calendar # Popula ipo_calendar
```

---

## 📊 Comparação v1.0 vs v2.0

| Recurso | v1.0 | v2.0 |
|---------|------|------|
| Análise geográfica | ❌ Não | ✅ Sim (continentes/países) |
| Universidades | ❌ Não | ✅ 20+ mapeadas |
| Especialização regional | ❌ Não | ✅ 7 regiões |
| IPO Calendar | ❌ Não | ✅ NASDAQ, B3, SEC |
| Narrativas AI | ❌ Bullet points | ✅ Texto corrido (Gemini) |
| Bug duplicatas | ❌ Presente | ✅ Corrigido |
| Output formats | .txt | .txt + .md + .csv |
| Linhas de código | ~300 | ~700 |
| Custo de análise | $0.00 | ~$0.01-0.02 |

---

## 🔍 Exemplo de Insight v2.0

```markdown
# 💎 Sofia Pulse - Premium Insights v2.0 GEO-LOCALIZADOS

**Gerado em**: 2025-11-18 14:30:00
**Modelo IA**: Gemini 2.5 Pro Preview

---

## 🌍 MAPA GLOBAL DA INOVAÇÃO

### Research Papers por Continente:

**Por Continente**:
- **América do Norte**: 285 papers (42.5%)
  - MIT: 65 papers (AI, Robotics)
  - Stanford: 48 papers (AI, Biotech)
  - Berkeley: 32 papers (AI, Computer Science)

- **Europa**: 178 papers (26.5%)
  - Oxford: 28 papers (Medicine, AI)
  - Cambridge: 24 papers (AI, Climate)
  - ETH Zürich: 18 papers (Robotics)

- **Ásia**: 145 papers (21.6%)
  - Tsinghua: 35 papers (AI, Manufacturing)
  - Peking University: 22 papers (AI)
  - NUS Singapore: 18 papers (AI, Clean Energy)

- **América do Sul**: 42 papers (6.3%)
  - USP: 15 papers (Agro-tech, Medicine)
  - Unicamp: 8 papers (Agro-tech, Energy)

### Funding por Continente:

- **América do Norte**: $2.5B (45% do total)
- **Ásia**: $1.8B (32% do total)
- **Europa**: $950M (17% do total)
- **América do Sul**: $280M (5% do total)

---

## 🎯 ESPECIALIZAÇÃO REGIONAL

### América do Norte
**Setores em Alta**:
- **AI/ML**: $850M (120 deals)
- **SaaS**: $620M (95 deals)
- **Biotech**: $380M (42 deals)

**Startups Destaque**: OpenAI competitors, vertical SaaS

### América do Sul
**Setores em Alta**:
- **Agro-tech**: $120M (15 deals)
- **Fintech**: $85M (28 deals)
- **Healthcare**: $45M (12 deals)

**Especialização**: Brasil lidera em Agro-tech (76% do funding regional)

---

## 💰 PRÓXIMOS IPOs (30 dias)

### NASDAQ:
- **TechCorp AI** (2025-12-15)
  - Faixa: $18-20 | Setor: AI/SaaS
  - Underwriters: Goldman Sachs

- **BioHealth Inc** (2025-12-18)
  - Faixa: $22-25 | Setor: Biotech
  - Underwriters: Morgan Stanley

### B3:
- **AgroTech Brasil** (2025-12-20)
  - Faixa: R$25-28 | Setor: Agro-tech
  - Underwriters: BTG Pactual

---

## 🤖 RESUMO EXECUTIVO (Gemini AI)

O cenário global de inovação revela uma clara distribuição geográfica de especializações,
com América do Norte consolidando liderança em AI e SaaS ($850M em funding), enquanto
regiões emergentes como América do Sul encontram seus nichos – Brasil domina Agro-tech
com 76% do funding regional e crescimento de 145% YoY. A atividade acadêmica acompanha
essa tendência: MIT e Stanford publicaram 113 papers em AI nos últimos 90 dias, enquanto
USP e Unicamp focam em Agro-tech e Energy com 23 papers na mesma janela.

O calendário de IPOs reflete essas especializações regionais. NASDAQ prepara 8 IPOs de
AI/SaaS para os próximos 30 dias (faixas entre $18-35), enquanto B3 tem 3 IPOs de
Agro-tech e Fintech (R$22-32). China lidera em volume de manufacturing startups (240
fundadas em Q4), mas Europa se destaca em Deep Tech com $380M investidos em Green Tech.

A convergência entre papers acadêmicos e funding empresarial indica onde surgirão os
próximos unicórnios: AI generativa (675 papers + $1.2B funding), Climate Tech (280
papers + $420M), e Agro-tech (85 papers + $180M). Universidades brasileiras demonstram
especialização única em agricultura sustentável – nicho inexplorado por MIT/Stanford –
sugerindo vantagem competitiva regional.

O futuro da inovação global não será centralizado em Silicon Valley, mas distribuído
geograficamente por expertise: América do Norte em AI, Europa em Green Tech, China em
Manufacturing, e Brasil em Agro-tech. A questão não é mais "onde está a inovação?" mas
"qual região domina qual vertical?".

---

**Próxima Atualização**: Automático (diário via cron 22:00 UTC)
```

---

## 🐛 Troubleshooting

### Erro: "venv-analytics não encontrado"

```bash
bash setup-data-mining.sh
```

### Erro: "GEMINI_API_KEY não configurada"

```bash
echo 'GEMINI_API_KEY=sua-chave' >> .env
```

### Erro: "Tabela ipo_calendar não existe"

```bash
psql -U sofia -d sofia_db -f db/migrations/007_create_ipo_calendar.sql
```

### Insights vazios ou com poucos dados

```bash
# Executar collectors primeiro
npm run collect:brazil
npm run collect:nasdaq
npm run collect:funding

# Aguardar 2-3 minutos

# Executar insights novamente
bash generate-premium-insights-v2.sh
```

---

## 📈 Próximos Passos Recomendados

1. **Teste no servidor**: `bash test-premium-insights-v2.sh`
2. **Configure GEMINI_API_KEY**: Para narrativas AI
3. **Execute collectors**: Popular dados se necessário
4. **Valide output**: `cat analytics/premium-insights/latest-geo.txt`
5. **Instale crontab**: `bash install-crontab.sh`
6. **Monitore logs**: `tail -f /var/log/sofia-insights.log`

---

## 📞 Suporte

**Arquivos de Referência**:
- Documentação completa: `CRONTAB-COMPLETO.md`
- Teste de validação: `test-premium-insights-v2.sh`
- Instalador de cron: `install-crontab.sh`

**Commits Relacionados**:
- `44ce244` - Add: Premium Insights v2.0 + IPO Calendar + Análise Geográfica
- `2dd6e4e` - Add: Crontab completo + Instalador automático
- `3be3cd4` - Fix: Remove duplicate stocks bug

---

**Desenvolvido com** ❤️ **para colunistas que precisam de insights acionáveis**

**v2.0.0** - 2025-11-18
