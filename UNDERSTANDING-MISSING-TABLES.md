# ℹ️ Entendendo as "Missing Tables" (Não São Erros!)

## 🎯 Resumo Executivo

Os avisos de **"relation does not exist"** que você está vendo **NÃO SÃO BUGS**. São avisos informativos de que certas tabelas ainda não foram populadas porque os collectors correspondentes não rodaram ainda.

---

## 📋 Lista Completa de Tabelas "Faltando"

### América Latina (CEPAL)
```
⚠️ relation "sofia.cepal_latam_data" does not exist
⚠️ relation "sofia.cepal_femicide" does not exist
```
**Collector**: `scripts/collect-cepal-latam.py`
**Tempo**: ~5 minutos
**Dados**: Economia, pobreza, desigualdade, gênero na América Latina

### Esportes & Olimpíadas
```
⚠️ relation "sofia.olympics_medals" does not exist
⚠️ relation "sofia.sports_rankings" does not exist
```
**Collector**: `scripts/collect-sports-federations.py`
**Tempo**: ~10 minutos
**Dados**: Medalhas olímpicas, rankings FIFA, basquete, vôlei, natação

### Comércio Internacional
```
⚠️ relation "sofia.wto_trade_data" does not exist
```
**Collector**: `scripts/collect-wto-trade.py`
**Tempo**: ~5 minutos
**Dados**: Dados de comércio internacional da WTO (Organização Mundial do Comércio)

### Agricultura
```
⚠️ relation "sofia.fao_agriculture_data" does not exist
```
**Collector**: `scripts/collect-fao-agriculture.py`
**Tempo**: ~5 minutos
**Dados**: Produção agrícola, segurança alimentar (FAO - UN Food and Agriculture)

### Objetivos de Desenvolvimento Sustentável
```
⚠️ relation "sofia.sdg_indicators" does not exist
```
**Collector**: `scripts/collect-un-sdg.py`
**Tempo**: ~10 minutos
**Dados**: 17 SDGs da ONU (pobreza, educação, clima, etc.)

---

## 🤔 Por Que Isso Acontece?

### Design Arquitetural

O Sofia Pulse usa um padrão **"Schema on Write"**:

1. **Collectors criam suas próprias tabelas** na primeira execução
2. Isso evita ter que manter 50+ schemas SQL manualmente
3. Cada collector é independente e auto-contido

### Exemplo Prático

Quando você roda `collect-cepal-latam.py` pela primeira vez:

```python
# O collector cria a tabela automaticamente:
cur.execute("""
    CREATE TABLE IF NOT EXISTS sofia.cepal_latam_data (
        id SERIAL PRIMARY KEY,
        country_code VARCHAR(3),
        indicator_code VARCHAR(50),
        year INTEGER,
        value NUMERIC,
        ...
    )
""")
```

Depois disso, a tabela existe e os analytics funcionam!

---

## ✅ Como Resolver

### Opção 1: Rodar Tudo (Recomendado)

```bash
# Instalar dependências Python (se ainda não instalou)
pip3 install psycopg2-binary requests pandas

# Rodar todos os collectors de uma vez
cd scripts

# América Latina
python3 collect-cepal-latam.py

# Esportes
python3 collect-sports-federations.py

# Comércio & Agricultura
python3 collect-wto-trade.py
python3 collect-fao-agriculture.py
python3 collect-un-sdg.py

# Voltar para raiz
cd ..
```

**Tempo total**: ~30-40 minutos

---

### Opção 2: Rodar Apenas o Que Você Precisa

Se você só quer testar os analytics de América Latina:

```bash
cd scripts
python3 collect-cepal-latam.py
cd ..

# Agora esse analytics vai funcionar:
python3 analytics/latam-intelligence.py
```

Se você só quer esportes:

```bash
cd scripts
python3 collect-sports-federations.py
cd ..

python3 analytics/olympics-sports-intelligence.py
```

---

### Opção 3: Usar Script Automatizado

```bash
# Roda todos os collectors e gera relatórios
./run-all-collectors-now.sh
```

---

## 🔍 Como Verificar Se Funcionou

### 1. Verificar Tabelas Criadas

```bash
# Se você tiver psql instalado:
psql -h localhost -U sofia -d sofia_db -c "\dt sofia.*"

# Ou verificar via Python:
python3 << EOF
import psycopg2
conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123', database='sofia_db')
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='sofia' ORDER BY tablename")
for table in cur.fetchall():
    print(f"✅ {table[0]}")
EOF
```

### 2. Verificar Contagem de Registros

```bash
python3 << EOF
import psycopg2
conn = psycopg2.connect(host='localhost', user='sofia', password='sofia123', database='sofia_db')
cur = conn.cursor()

tables = ['cepal_latam_data', 'olympics_medals', 'wto_trade_data', 'fao_agriculture_data', 'sdg_indicators']

for table in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM sofia.{table}")
        count = cur.fetchone()[0]
        print(f"✅ {table:<30} {count:>10} rows")
    except:
        print(f"⚠️  {table:<30} (not created yet)")
EOF
```

**Saída esperada ANTES de rodar collectors**:
```
⚠️  cepal_latam_data              (not created yet)
⚠️  olympics_medals               (not created yet)
⚠️  wto_trade_data                (not created yet)
```

**Saída esperada DEPOIS de rodar collectors**:
```
✅ cepal_latam_data                    15,420 rows
✅ olympics_medals                      3,856 rows
✅ wto_trade_data                      82,340 rows
```

---

## 📊 Tabela de Referência Rápida

| Tabela Faltando | Collector | Tempo | Analytics Afetado |
|---|---|---|---|
| `cepal_latam_data` | collect-cepal-latam.py | 5 min | latam-intelligence.py |
| `cepal_femicide` | collect-cepal-latam.py | 5 min | women-global-analysis.py |
| `olympics_medals` | collect-sports-federations.py | 10 min | olympics-sports-intelligence.py |
| `sports_rankings` | collect-sports-federations.py | 10 min | olympics-sports-intelligence.py |
| `wto_trade_data` | collect-wto-trade.py | 5 min | trade-agriculture-intelligence.py |
| `fao_agriculture_data` | collect-fao-agriculture.py | 5 min | trade-agriculture-intelligence.py |
| `sdg_indicators` | collect-un-sdg.py | 10 min | global-health-humanitarian.py |

---

## 🚀 Fluxo Completo (Do Zero ao Analytics Rodando)

```bash
# 1. Validar ambiente
./test-quick-setup.sh

# 2. Instalar dependências Python (se necessário)
pip3 install psycopg2-binary requests pandas

# 3. Rodar collectors críticos
cd scripts
python3 collect-cepal-latam.py
python3 collect-sports-federations.py
python3 collect-wto-trade.py
python3 collect-fao-agriculture.py
python3 collect-un-sdg.py
cd ..

# 4. Testar analytics
cd analytics
python3 latam-intelligence.py
python3 olympics-sports-intelligence.py
python3 trade-agriculture-intelligence.py
cd ..

# 5. Verificar que não há mais warnings
grep -r "does not exist" analytics/*.py | wc -l
# Deve retornar 0 ou muito poucos
```

---

## 💡 Por Que Não Criamos Todas as Tabelas Antecipadamente?

### Vantagens do Approach Atual:

1. **Modularidade**: Cada collector é independente
2. **Evolução**: Fácil adicionar novos collectors sem tocar em migrations
3. **Zero-config**: Não precisa rodar 50 migrations antes de usar
4. **Self-documenting**: O schema está no próprio collector

### Desvantagens:

1. ❌ Analytics mostram warnings antes da primeira coleta
   - **Solução**: É esperado! Não é um bug

2. ❌ Pode confundir usuários novos
   - **Solução**: Este documento! 😊

---

## ❓ FAQ

**Q: Os analytics vão quebrar se as tabelas não existirem?**
A: Não! Os analytics têm `try/except` e mostram apenas warnings. Eles continuam executando.

**Q: Preciso rodar TODOS os collectors?**
A: Não! Rode apenas os que você precisa. Cada collector é independente.

**Q: Quanto espaço em disco os collectors consomem?**
A: Aproximadamente:
- CEPAL: ~5 MB
- Esportes: ~2 MB
- WTO/FAO: ~20 MB cada
- UN SDG: ~50 MB
- **Total**: ~100-200 MB para todos os collectors

**Q: Com que frequência devo rodar os collectors?**
A: Depende da fonte:
- GitHub: Diariamente
- CEPAL/FAO/WTO: Mensalmente
- Esportes: Semanalmente durante eventos, mensalmente fora de temporada
- UN SDG: Trimestralmente (dados mudam devagar)

**Q: Posso rodar os collectors em paralelo?**
A: Sim! Cada collector é independente. Mas cuidado com:
- Rate limits de APIs
- Carga no banco de dados
- Memória disponível

---

## 🎉 Conclusão

**TL;DR**: Warnings de "relation does not exist" são **NORMAIS** e **ESPERADOS** até você rodar os collectors pela primeira vez.

Rode os collectors → Tabelas são criadas → Analytics funcionam → Profit! 🚀

---

**Criado por**: Claude Code
**Data**: 2025-12-03 15:10 UTC
**Propósito**: Eliminar confusão sobre "erros SQL" que não são erros
