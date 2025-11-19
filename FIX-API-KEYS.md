# 🔑 FIX: Configuração de API Keys

## Problema Identificado

As API keys não foram encontradas no `.env` durante os testes:

```
❌ EIA_API_KEY not found in .env
❌ API_NINJAS_KEY not found in .env
```

Isso causou falhas nos collectors que dependem dessas APIs:
- ❌ Commodity Prices (usando dados placeholder)
- ❌ Electricity Consumption (se os dados fossem via API)

## Solução

### Método 1: Script Automático (RECOMENDADO)

Execute o script de configuração:

```bash
./setup-api-keys-final.sh
```

Este script:
1. ✅ Detecta automaticamente o ambiente (servidor ou local)
2. ✅ Cria `.env` do `.env.example` se não existir
3. ✅ Remove linhas antigas das API keys
4. ✅ Adiciona as novas API keys
5. ✅ Valida que foram configuradas corretamente

### Método 2: Manual

Se preferir configurar manualmente:

```bash
cd /home/ubuntu/sofia-pulse  # ou /home/user/sofia-pulse

# Editar .env
nano .env

# Adicionar estas linhas:
EIA_API_KEY=QKUixUcUGWnmT7ffUKPeIzeS7OrInmtd471qboys
API_NINJAS_KEY=IsggR55vW5kTD5w71PKRzg==DU8KUx0G1gYwbO2I
```

## Testar

Depois de configurar, teste se funcionou:

```bash
python3 test-apis.py
```

Resultado esperado:

```
✅ EIA API working! Status: 200
✅ API Ninjas working! Gold price: $2050.00
✅ World Bank API working!
```

## Executar Collectors

Agora você pode executar os collectors que dependem de API:

```bash
# Commodity Prices (requer API_NINJAS_KEY)
python3 scripts/collect-commodity-prices.py

# Electricity Consumption (requer EIA_API_KEY)
python3 scripts/collect-electricity-consumption.py

# Todos os collectors
./collect-all-data.sh
```

## Arquivos Relacionados

- `setup-api-keys-final.sh` - Script de configuração automática (NOVO)
- `fix-env-direct.sh` - Script anterior (usa sed, pode falhar)
- `add-api-keys.sh` - Script original (mais antigo)
- `test-apis.py` - Testa se as APIs estão funcionando
- `.env.example` - Template do arquivo de configuração

## Problemas Resolvidos

1. ✅ **SQL Syntax Error** (`semiconductor_sales`)
   - Problema: `UNIQUE(region, year, COALESCE(quarter, ''), ...)`
   - Solução: Mudamos para `DEFAULT ''` nas colunas

2. ✅ **API Keys Não Encontradas**
   - Problema: `.env` não tinha as keys ou tinha valores placeholder
   - Solução: Script que remove linhas antigas e adiciona as corretas

## Status dos Collectors

Após o fix, você deve ter:

| Collector | Status | Registros |
|-----------|--------|-----------|
| Electricity Consumption | ✅ Funcionando | 239 países |
| Port Traffic | ✅ Funcionando | 2,462 registros |
| Commodity Prices | ⚠️ Aguardando API | 4 placeholder |
| Semiconductor Sales | ✅ Funcionando | 4 registros Q1 2025 |

## Próximos Passos

1. Rodar `setup-api-keys-final.sh` no servidor
2. Testar com `python3 test-apis.py`
3. Executar `python3 scripts/collect-commodity-prices.py`
4. Verificar que os preços reais aparecem (não placeholder)
