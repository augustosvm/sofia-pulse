# 🔍 SonarCloud Setup - Sofia Pulse

## Configuração Otimizada

Analisa **apenas código ativo** (~16.5k linhas)  
Ignora **legacy e one-time scripts** (~4.5k linhas)

---

## 📋 Passo a Passo

### 1. Criar Projeto no SonarCloud

1. Acesse: https://sonarcloud.io
2. Login com GitHub
3. Click em "+" → "Analyze new project"
4. Selecione `sofia-pulse`
5. Click "Set Up"

### 2. Obter Token

1. No SonarCloud, vá em "My Account" → "Security"
2. Generate Token:
   - Name: `sofia-pulse-analysis`
   - Type: `Project Analysis Token`
   - Expires: `No expiration`
3. **Copie o token** (só aparece uma vez!)

### 3. Configurar no Servidor

```bash
# SSH no servidor
ssh root@91.98.158.19

# Ir para o projeto
cd /home/ubuntu/sofia-pulse

# Pull do código atualizado
git pull origin master

# Adicionar token ao .env
echo "SONAR_TOKEN='seu_token_aqui'" >> .env

# Dar permissão ao script
chmod +x scripts/automation/sonar-scan.sh
```

### 4. Instalar SonarScanner (se necessário)

```bash
# Verificar se já está instalado
sonar-scanner --version

# Se não estiver, instalar:
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
unzip sonar-scanner-cli-5.0.1.3006-linux.zip
sudo mv sonar-scanner-5.0.1.3006-linux /opt/sonar-scanner
sudo ln -s /opt/sonar-scanner/bin/sonar-scanner /usr/local/bin/sonar-scanner
```

### 5. Executar Análise

```bash
# Executar scan
./scripts/automation/sonar-scan.sh

# Ou manualmente:
sonar-scanner \
  -Dsonar.host.url=https://sonarcloud.io \
  -Dsonar.login=$SONAR_TOKEN
```

### 6. Ver Resultados

Dashboard: https://sonarcloud.io/dashboard?id=augustosvm_sofia-pulse

---

## 📊 O Que Será Analisado

### ✅ Código Ativo (~16.5k linhas)

**Collectors Python** (55 arquivos, ~14,755 linhas):
- `scripts/collect-*.py`

**Helpers** (~900 linhas):
- `scripts/shared/geo_helpers.py`
- `scripts/shared/org_helpers.py`
- `scripts/shared/funding_helpers.py`

**Integrações** (~423 linhas):
- `scripts/utils/sofia_whatsapp_integration.py`

**TypeScript Core** (~548 linhas):
- `scripts/collect.ts`
- `scripts/generate-crontab.ts`
- `scripts/collectors/*.ts`
- `scripts/configs/*.ts`

### ❌ Código Ignorado (~4.5k linhas)

- `legacy/` - Scripts one-time (115 arquivos)
- `migrations/` - SQL migrations (101 arquivos)
- `scripts/automation/` - Scripts de deploy (140 arquivos)
- `scripts/normalize-*.py` - Scripts de manutenção
- `scripts/backfill-*.py` - Scripts de backfill
- `docs/` - Documentação (104 arquivos)

---

## 🎯 Métricas Esperadas

| Métrica | Valor Esperado |
|:---|:---|
| **Linhas de Código** | ~16,500 |
| **Arquivos** | ~61 |
| **Manutenibilidade** | A (51.5) |
| **Complexidade** | B (8.48) |
| **Duplicação** | < 3% |
| **Cobertura** | 0% (sem testes ainda) |

---

## 🔧 Troubleshooting

### Token Inválido
```bash
# Verificar se token está no .env
grep SONAR_TOKEN .env

# Reexportar
export SONAR_TOKEN='seu_token'
```

### SonarScanner Não Encontrado
```bash
# Verificar instalação
which sonar-scanner

# Reinstalar se necessário
# (ver passo 4)
```

### Análise Muito Lenta
```bash
# Verificar se está analisando apenas código ativo
cat sonar-project.properties | grep sources

# Deve mostrar apenas:
# scripts/collect-*.py, scripts/shared, etc.
```

---

## 📅 Automação (Futuro)

### GitHub Actions

```yaml
# .github/workflows/sonar.yml
name: SonarCloud
on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

jobs:
  sonar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: SonarCloud Scan
        uses: SonarSource/sonarcloud-github-action@master
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

### Cron Job

```bash
# Análise semanal
0 2 * * 0 cd /home/ubuntu/sofia-pulse && ./scripts/automation/sonar-scan.sh
```

---

*Configuração criada em: 2025-12-29*
