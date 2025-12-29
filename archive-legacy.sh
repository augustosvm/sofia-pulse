#!/bin/bash

echo "🧹 Arquivando scripts legacy..."

# Cria estrutura de arquivo com legacy/ como raiz
mkdir -p legacy/one-time-scripts/{analise,restore,migrate,fix,check,find,add-auto}

# Move scripts por categoria (da raiz do projeto)
mv analise-*.py legacy/one-time-scripts/analise/ 2>/dev/null
mv ANALISE-*.py legacy/one-time-scripts/analise/ 2>/dev/null
mv restore-*.py legacy/one-time-scripts/restore/ 2>/dev/null
mv migrate-*.py legacy/one-time-scripts/migrate/ 2>/dev/null
mv auto-migrate-*.py legacy/one-time-scripts/migrate/ 2>/dev/null
mv fix-*.py legacy/one-time-scripts/fix/ 2>/dev/null
mv debug-*.py legacy/one-time-scripts/fix/ 2>/dev/null
mv check-*.py legacy/one-time-scripts/check/ 2>/dev/null
mv find-*.py legacy/one-time-scripts/find/ 2>/dev/null
mv add-*.py legacy/one-time-scripts/add-auto/ 2>/dev/null
mv add_*.py legacy/one-time-scripts/add-auto/ 2>/dev/null
mv auto-*.py legacy/one-time-scripts/add-auto/ 2>/dev/null
mv final-*.py legacy/one-time-scripts/fix/ 2>/dev/null

# Cria README explicando
cat > legacy/README.md << 'ARCHIVE'
# 📦 Archived Legacy Scripts

Scripts executados uma única vez durante desenvolvimento e mantidos apenas para referência histórica.

**NÃO fazem parte do código ativo em produção.**

## Estrutura

- `one-time-scripts/analise/` - Scripts de análise regional (executados 1x)
- `one-time-scripts/restore/` - Scripts de restauração de dados (executados 1x)
- `one-time-scripts/migrate/` - Scripts de migração de schema (executados 1x)
- `one-time-scripts/fix/` - Scripts de fixes pontuais (executados 1x)
- `one-time-scripts/check/` - Scripts de validação (executados 1x)
- `one-time-scripts/find/` - Utilitários de busca (executados 1x)
- `one-time-scripts/add-auto/` - Scripts auxiliares de geração (executados 1x)

## Total

**74 arquivos** | **~4,500 linhas** de código descartável

## Recuperação

Se precisar de algum script:
```bash
cp legacy/one-time-scripts/categoria/script.py ./
```

## Por que foram arquivados?

Estes scripts foram criados para tarefas pontuais durante o desenvolvimento:
- Importação inicial de dados históricos
- Migrações de schema antigas
- Análises exploratórias
- Correções de bugs já resolvidos
- Validações de dados já concluídas

**Código ativo em produção**: Ver `ACTIVE-vs-LEGACY-CODE.md`
ARCHIVE

echo "✅ Legacy arquivado em legacy/one-time-scripts/"
echo ""
echo "📊 Código Python ativo restante:"
find scripts/ -name "*.py" -type f 2>/dev/null | wc -l
echo ""
echo "📦 Scripts arquivados:"
find legacy/ -name "*.py" -type f 2>/dev/null | wc -l
