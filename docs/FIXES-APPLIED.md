# ✅ Correções Aplicadas - 2025-12-03

## 🐛 Problemas Identificados e Corrigidos

### 1. ✅ Duplicação de Dados no Cross-Data Correlations

**Problema**:
```
Singapore    GDP: $90,674 | Security: 1.4
Singapore    GDP: $90,674 | Security: 2.0  ← DUPLICADO!
Singapore    GDP: $90,674 | Security: 2.7  ← DUPLICADO!
```

**Causa**: JOIN sem GROUP BY causando múltiplas linhas por país.

**Correção**: `analytics/cross-data-correlations.py`
- Refatorado query SQL usando CTEs (Common Table Expressions)
- Agrupamento explícito por país com AVG() para métricas de segurança
- LEFT JOIN para incluir países sem dados de segurança
- Resultado: **1 linha por país** garantido

**Arquivo**: `/analytics/cross-data-correlations.py` linhas 28-57

---

### 2. ⚠️ Tabelas SQL Faltando (NÃO É ERRO!)

**Warnings nos Analytics**:
```
⚠️ relation "sofia.cepal_latam_data" does not exist
⚠️ relation "sofia.olympics_medals" does not exist
⚠️ relation "sofia.sports_rankings" does not exist
```

**Explicação**:
Isso **NÃO É UM BUG!** As tabelas são criadas automaticamente pelos collectors na **primeira execução**.

**Collectors que criam essas tabelas**:
- `scripts/collect-cepal-latam.py` → cria `cepal_latam_data` + `cepal_femicide`
- `scripts/collect-sports-federations.py` → cria `olympics_medals` + `sports_rankings`

**Solução**: Rodar os collectors uma vez para criar as tabelas (instruções abaixo).

---

## 🚀 Como Rodar Tudo Agora

### Pré-requisitos

1. **PostgreSQL deve estar rodando**:
```bash
# Verificar se está rodando
sudo systemctl status postgresql

# Se não estiver, iniciar
sudo systemctl start postgresql
```

2. **Python 3 instalado** (collectors Python):
```bash
python3 --version
```

3. **Node.js instalado** (collectors TypeScript):
```bash
node --version
npm --version
```

---

### Opção 1: Rodar Todos os Collectors (Completo)

**⚠️ AVISO**: Isso pode levar 1-2 horas e faz MUITAS requisições a APIs externas.

```bash
# Collectors TypeScript (GitHub, etc.)
npm run collect:github-trending
npm run collect:github-niches

# Collectors Python (dados globais)
cd scripts

# CEPAL (América Latina) - ~5 min
python3 collect-cepal-latam.py

# Esportes & Olimpíadas - ~10 min
python3 collect-sports-federations.py

# Dados Brasileiros - ~15 min cada
python3 collect-ibge-api.py
python3 collect-bacen-sgs.py
python3 collect-ipea-api.py

# Dados de Gênero - ~10 min cada
python3 collect-women-world-bank.py
python3 collect-women-eurostat.py
python3 collect-women-ilostat.py

# Organizações Internacionais - ~5 min cada
python3 collect-who-health.py
python3 collect-fao-agriculture.py
python3 collect-wto-trade.py
python3 collect-unicef.py

# Segurança e outros
python3 collect-world-security.py
python3 collect-world-tourism.py
```

---

### Opção 2: Rodar Apenas o Essencial (Rápido - 10 minutos)

```bash
# 1. Criar tabelas manualmente (opcional)
./create-special-tables.sh

# 2. Collectors críticos para os analytics funcionarem
cd scripts

# CEPAL (América Latina) - precisa para latam-intelligence.py
python3 collect-cepal-latam.py

# Esportes - precisa para olympics-sports-intelligence.py
python3 collect-sports-federations.py

# Volta para raiz
cd ..

# 3. GitHub (essencial)
npm run collect:github-trending
npm run collect:github-niches
```

---

### Opção 3: Rodar Apenas 1 Collector para Testar (1 minuto)

```bash
# Testar se tudo está configurado corretamente
cd scripts
python3 collect-cepal-latam.py

# Se rodar sem erros → SUCESSO!
# Se der erro de DB → verificar PostgreSQL
# Se der erro de permissão → chmod +x collect-cepal-latam.py
```

---

## 📊 Testar Analytics Após Coleta

Depois de rodar os collectors, testar os analytics:

```bash
cd analytics

# Cross-data correlations (CORRIGIDO!)
python3 cross-data-correlations.py

# América Latina (precisa CEPAL)
python3 latam-intelligence.py

# Esportes (precisa Sports Federations)
python3 olympics-sports-intelligence.py

# Outros analytics
python3 brazil-economy-intelligence.py
python3 women-global-analysis.py
python3 security-intelligence-report.py
```

---

## ✅ Checklist de Validação

### 1. Duplicação Corrigida?
```bash
cd analytics
python3 cross-data-correlations.py | grep "Singapore"
```
**Esperado**: Apenas 1 linha por país (não 7!)

### 2. Tabelas Criadas?
```bash
# Conectar ao PostgreSQL
psql -h localhost -U sofia -d sofia_db

# Listar tabelas
\dt sofia.*

# Verificar tabelas específicas
SELECT COUNT(*) FROM sofia.cepal_latam_data;
SELECT COUNT(*) FROM sofia.olympics_medals;
```
**Esperado**: Contagens > 0 após rodar collectors

### 3. Analytics Rodando Sem Erros?
```bash
cd analytics
python3 cross-data-correlations.py > test-output.txt 2>&1
grep "⚠️" test-output.txt | wc -l
```
**Esperado**: 0 warnings de tabelas faltando (ou poucos, apenas de tabelas que você não coletou)

---

## 🔍 Troubleshooting

### Erro: "psycopg2 not found"
```bash
pip3 install psycopg2-binary
# OU
pip3 install -r requirements-collectors.txt
```

### Erro: "connect ECONNREFUSED 127.0.0.1:5432"
PostgreSQL não está rodando:
```bash
sudo systemctl start postgresql
```

### Erro: "pip3: command not found"
```bash
sudo apt update
sudo apt install python3-pip -y
```

### Erro: "permission denied"
```bash
chmod +x scripts/*.py
chmod +x analytics/*.py
chmod +x *.sh
```

### Collectors muito lentos?
Alguns collectors fazem muitas requisições. É normal levar tempo.
Use `Ctrl+C` para cancelar se necessário.

---

## 📋 Resumo

**✅ Corrigido**:
- Duplicação no cross-data correlations

**⚠️ Não é erro**:
- Tabelas faltando (normal antes da primeira coleta)

**🚀 Próximos passos**:
1. Escolher uma das 3 opções de coleta acima
2. Rodar os collectors
3. Testar os analytics
4. Validar que não há mais duplicações

---

**Criado por**: Claude Code
**Data**: 2025-12-03 15:00 UTC
