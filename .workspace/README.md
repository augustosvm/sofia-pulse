# .workspace/

Esta pasta contém scripts temporários, relatórios de auditoria e ferramentas de desenvolvimento que **não devem ser analisados** pelo SonarCloud ou outras ferramentas de qualidade de código.

## 📂 Estrutura

```
.workspace/
├── reports/          # Relatórios de auditoria e análise
│   └── DATA_QUALITY_REPORT.md
├── scripts/          # Scripts de auditoria e validação
│   ├── audit-normalization-coverage.py
│   ├── validate-referential-integrity.py
│   ├── run-cleanup-duplicates.py
│   └── run-fix-orphaned-cities.py
└── README.md         # Este arquivo
```

## 🎯 Propósito

**Scripts de auditoria e validação**:
- Scripts executados uma vez para análise
- Ferramentas de debug e investigação
- Relatórios temporários
- Testes exploratórios

**Por que não analisar?**:
- ❌ Código temporário/descartável
- ❌ Não está em produção
- ❌ Pode ter qualidade inferior (é só para investigação)
- ❌ Polui métricas de qualidade do código ativo

## 🚫 Ignorado Por

- ✅ SonarCloud (`sonar-project.properties`)
- ✅ Git (`.gitignore`)
- ✅ Pylint/Flake8 (análises de qualidade)

## 📝 Como Usar

### Adicionar novo script de auditoria

```bash
# Mover para workspace
mv meu-script-de-teste.py .workspace/scripts/

# Ou criar diretamente
nano .workspace/scripts/novo-audit.py
```

### Gerar relatório

```bash
# Executar script
python .workspace/scripts/audit-something.py

# Salvar relatório
python .workspace/scripts/audit-something.py > .workspace/reports/REPORT.md
```

## ⚠️ Importante

- **Não commitar** arquivos grandes ou sensíveis
- **Não colocar** código de produção aqui
- **Usar** apenas para desenvolvimento/investigação
- **Mover** para `scripts/` se o código for para produção

---

*Criado em: 2025-12-29*
