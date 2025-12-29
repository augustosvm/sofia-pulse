# 🔐 Configuração de Secrets no GitHub

Para o SonarCloud funcionar automaticamente, você precisa configurar o token como secret no GitHub.

## 📋 Passo a Passo

### 1. Obter Token do SonarCloud

1. Acesse: https://sonarcloud.io
2. Login com GitHub
3. Click em "+" → "Analyze new project"
4. Selecione `sofia-pulse`
5. Click "Set Up"
6. Vá em "My Account" → "Security" → "Generate Token"
   - Name: `GitHub Actions`
   - Type: `Project Analysis Token`
   - Expires: `No expiration`
7. **Copie o token** (aparece só uma vez!)

### 2. Adicionar Secret no GitHub

1. Vá para: https://github.com/augustosvm/sofia-pulse/settings/secrets/actions
2. Click em "New repository secret"
3. Name: `SONAR_TOKEN`
4. Value: Cole o token do SonarCloud
5. Click "Add secret"

### 3. Testar

Faça um push qualquer:

```bash
git commit --allow-empty -m "test: trigger SonarCloud"
git push origin master
```

Veja o resultado em:
- **GitHub Actions**: https://github.com/augustosvm/sofia-pulse/actions
- **SonarCloud Dashboard**: https://sonarcloud.io/dashboard?id=augustosvm_sofia-pulse

---

## ✅ O Que Será Analisado

O workflow usa o `sonar-project.properties` que já está configurado:

**Analisa** (~16.5k linhas):
- ✅ 55 Collectors Python
- ✅ Helpers (geo, org, funding)
- ✅ WhatsApp Integration
- ✅ TypeScript Core

**Ignora** (~4.5k linhas):
- ❌ `.workspace/` (scripts temporários)
- ❌ `legacy/` (scripts one-time)
- ❌ `docs/` (documentação)
- ❌ `migrations/` (SQL)
- ❌ `scripts/automation/` (deploy scripts)

---

## 🔄 Quando Roda

- ✅ A cada `push` na branch `master`
- ✅ A cada `pull request` para `master`

---

## 📊 Métricas Esperadas

| Métrica | Valor Esperado |
|:---|:---|
| **Linhas de Código** | ~16,500 |
| **Arquivos** | ~61 |
| **Manutenibilidade** | A (51.5) |
| **Complexidade** | B (8.48) |
| **Duplicação** | < 3% |
| **Cobertura** | 0% (sem testes) |

---

*Configuração criada em: 2025-12-29*
