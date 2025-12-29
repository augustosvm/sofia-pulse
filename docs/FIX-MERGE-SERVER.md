# Comandos para Resolver Merge no Servidor

Execute estes comandos no servidor (você já está conectado):

```bash
# 1. Remover arquivo que está bloqueando o merge
rm scripts/add-cities-to-funding.py

# 2. Fazer pull novamente
git pull

# 3. Verificar se os arquivos novos existem
ls -la scripts/collect-jobs-*.ts

# 4. Testar Himalayas (agora com código corrigido)
npx tsx scripts/collect-jobs-himalayas.ts

# 5. Testar USAJOBS
npx tsx scripts/collect-jobs-usajobs.ts

# 6. Se tiver Adzuna configurado
npx tsx scripts/collect-jobs-adzuna.ts
```

## Por que o erro aconteceu?

O arquivo `scripts/add-cities-to-funding.py` existe no servidor mas não está no git. Quando tentou fazer pull, o git não quis sobrescrever.

## Solução

Remover o arquivo e fazer pull novamente.
