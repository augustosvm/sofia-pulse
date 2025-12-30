# Guia de Configuração - Novas APIs de Vagas

## 📋 Resumo

Foram implementados/corrigidos 3 coletores de vagas:

1. ✅ **Himalayas** - Corrigido (schema API mudou)
2. ✅ **Adzuna** - Novo (50k+ vagas, 20+ países)
3. ✅ **USAJOBS** - Novo (5k+ vagas gov USA)

## 🔑 API Keys Necessárias

### 1. Adzuna API (Gratuita - 5000 calls/mês)

**Registrar em**: https://developer.adzuna.com/

**Passos**:
1. Criar conta gratuita
2. Criar aplicação
3. Copiar `Application ID` e `Application Key`

**Adicionar ao `.env`**:
```bash
ADZUNA_APP_ID=seu_app_id_aqui
ADZUNA_API_KEY=sua_api_key_aqui
```

### 2. USAJOBS API (Gratuita - sem limite)

**Registrar em**: https://developer.usajobs.gov/APIRequest/Index

**Passos**:
1. Preencher formulário de requisição
2. Aguardar email com API key (geralmente instantâneo)
3. Copiar API key

**Adicionar ao `.env`**:
```bash
USAJOBS_API_KEY=sua_api_key_aqui
USAJOBS_EMAIL=seu_email@gmail.com
```

## 🚀 Executar no Servidor

### 1. Fazer commit e push das mudanças

```bash
git add .
git commit -m "feat: Fix Himalayas + Add Adzuna and USAJOBS collectors"
git push origin main
```

### 2. Conectar ao servidor e atualizar

```bash
ssh root@91.98.158.19
cd /home/ubuntu/sofia-pulse
git pull
```

### 3. Adicionar API keys ao .env do servidor

```bash
nano .env
# Adicionar as 4 variáveis acima
```

### 4. Testar cada coletor

```bash
# Testar Himalayas (corrigido)
npx tsx scripts/collect-jobs-himalayas.ts

# Testar Adzuna (requer API key)
npx tsx scripts/collect-jobs-adzuna.ts

# Testar USAJOBS (requer API key)
npx tsx scripts/collect-jobs-usajobs.ts
```

### 5. Verificar resultados no banco

```bash
psql -U sofia -d sofia_db -c "
SELECT 
    platform,
    COUNT(*) as vagas,
    COUNT(DISTINCT company) as empresas,
    COUNT(CASE WHEN salary_min IS NOT NULL THEN 1 END) as com_salario
FROM sofia.jobs
WHERE platform IN ('himalayas', 'adzuna', 'usajobs')
GROUP BY platform
ORDER BY vagas DESC;
"
```

## 📊 Resultados Esperados

- **Himalayas**: 20-50 vagas (remote jobs)
- **Adzuna**: 500-1000 vagas (10 países × 3 keywords × 20 vagas)
- **USAJOBS**: 100-400 vagas (4 ocupações tech × 100 vagas)

**Total**: +620 a +1450 vagas adicionais! 🎉

## 🔄 Adicionar ao Cron (Opcional)

Editar `scripts/collect-jobs-with-api.sh`:

```bash
#!/bin/bash
# Coletores que requerem API key
npx tsx scripts/collect-jobs-himalayas.ts
npx tsx scripts/collect-jobs-adzuna.ts
npx tsx scripts/collect-jobs-usajobs.ts
```

Adicionar ao cron:
```bash
# Executar diariamente às 6h
0 6 * * * /home/ubuntu/sofia-pulse/scripts/collect-jobs-with-api.sh
```

## ⚠️ Notas Importantes

1. **Adzuna**: Limite de 5000 calls/mês
   - 10 países × 3 keywords = 30 calls/dia
   - 30 calls × 30 dias = 900 calls/mês ✅ (dentro do limite)

2. **USAJOBS**: Sem limite de rate
   - 4 ocupações = 4 calls/dia
   - Sem problemas de quota

3. **Himalayas**: API pública, sem key necessária
   - 1 call/dia = 20 vagas

## 🐛 Troubleshooting

**Erro: "ADZUNA_APP_ID is required"**
- Verificar se as variáveis estão no `.env`
- Executar `source .env` antes de rodar o script

**Erro: "ECONNREFUSED"**
- PostgreSQL não está rodando
- Verificar: `sudo systemctl status postgresql`

**Erro: "401 Unauthorized" (USAJOBS)**
- API key inválida ou expirada
- Verificar email de confirmação

**Erro: "429 Too Many Requests" (Adzuna)**
- Limite de 5000 calls/mês excedido
- Aguardar próximo mês ou reduzir frequência
