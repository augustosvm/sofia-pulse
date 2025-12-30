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

**~74 arquivos** | **~4,500 linhas** de código descartável

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

**Código ativo em produção**: Ver `ACTIVE-vs-LEGACY-CODE.md` na raiz do projeto.

---

*Arquivado em: 2025-12-29*
