# ⚠️ AÇÃO NECESSÁRIA: Migração de Credenciais

## 🔐 Credenciais que Precisam Ser Adicionadas ao .env

As seguintes credenciais foram **removidas do código** por segurança e precisam ser adicionadas manualmente ao arquivo `.env`:

### 1. Gemini API Key (CRÍTICO)
```env
GEMINI_API_KEY=sua_nova_key_aqui
```

**Como obter**:
1. Ir em: https://aistudio.google.com/app/apikey
2. Revogar a key antiga (se ainda existir)
3. Criar nova key
4. Copiar para `.env`

---

### 2. PostgreSQL Password (CRÍTICO)
```env
POSTGRES_PASSWORD=sua_senha_segura_aqui
```

**Ação**:
- Usar a nova senha que você criou no servidor
- **NÃO** usar a senha antiga que estava exposta
- **NÃO** usar a senha que foi postada no chat

---

### 3. APIs Gratuitas (Opcional - Já Expostas)

Estas APIs são gratuitas e já estavam expostas. Você pode manter ou renovar:

```env
# EIA API (Energia)
EIA_API_KEY=sua_key_aqui

# API Ninjas (Commodities)
API_NINJAS_KEY=sua_key_aqui

# Outras APIs gratuitas
SERPAPI_API_KEY=sua_key_aqui
```

**Como obter novas keys** (se quiser renovar):
- EIA: https://www.eia.gov/opendata/register.php
- API Ninjas: https://api-ninjas.com/profile
- Serpapi: https://serpapi.com/manage-api-key

---

## 📝 Template Completo do .env

```env
# ============================================================================
# Sofia Pulse - Environment Variables
# ============================================================================

# Database (CRÍTICO)
POSTGRES_HOST=91.98.158.19
POSTGRES_PORT=5432
POSTGRES_USER=sofia
POSTGRES_PASSWORD=sua_senha_segura_aqui
POSTGRES_DB=sofia_db

# Google APIs (CRÍTICO)
GEMINI_API_KEY=sua_nova_gemini_key_aqui
GOOGLE_API_KEY=sua_google_key_aqui

# WhatsApp
WHATSAPP_API_URL=https://graph.facebook.com/v17.0/YOUR_PHONE_ID/messages
WHATSAPP_TOKEN=seu_token_aqui
WHATSAPP_PHONE_ID=seu_phone_id_aqui
WHATSAPP_RECIPIENT=5511XXXXXXXXX

# Data APIs (Gratuitas - Opcional renovar)
EIA_API_KEY=sua_key_aqui
API_NINJAS_KEY=sua_key_aqui
SERPAPI_API_KEY=sua_key_aqui

# Job APIs (Gratuitas)
USAJOBS_API_KEY=sua_key_aqui
USAJOBS_EMAIL=seu_email@gmail.com
ADZUNA_APP_ID=seu_app_id_aqui
ADZUNA_API_KEY=sua_key_aqui

# Finance APIs (Gratuitas)
ALPHA_VANTAGE_API_KEY=sua_key_aqui
COINGECKO_API_KEY=sua_key_aqui

# Research APIs (Gratuitas)
KAGGLE_USERNAME=seu_username
KAGGLE_KEY=sua_key_aqui
```

---

## ✅ Checklist de Migração

### No Servidor (91.98.158.19)

- [ ] SSH no servidor: `ssh root@91.98.158.19`
- [ ] Ir para o projeto: `cd /home/ubuntu/sofia-pulse`
- [ ] Editar .env: `nano .env`
- [ ] Adicionar credenciais críticas:
  - [ ] `POSTGRES_PASSWORD` (nova senha)
  - [ ] `GEMINI_API_KEY` (nova key)
- [ ] Salvar e sair: `Ctrl+X`, `Y`, `Enter`
- [ ] Testar conexão: `python3 -c "import psycopg2; print('OK')"`

### No Local (Seu Computador)

- [ ] Editar: `C:\Users\augusto.moreira\Documents\sofia-pulse\.env`
- [ ] Adicionar mesmas credenciais
- [ ] Testar collectors localmente

---

## 🚨 Arquivos Removidos por Segurança

Os seguintes arquivos foram **deletados do histórico do Git** porque continham credenciais expostas:

- ❌ `docs/FIX-API-KEYS.md` (continha Gemini API key)
- ❌ `scripts/automation/fix-env-direct.sh` (continha EIA key)
- ❌ `scripts/automation/add-api-keys.sh`
- ❌ `scripts/automation/setup-api-keys-final.sh`
- ❌ `scripts/automation/update-gemini-key.sh`
- ❌ `scripts/automation/add-bea-key.sh`

**Não tente restaurar esses arquivos!** Eles continham credenciais comprometidas.

---

## 🎯 Próximos Passos

1. **Adicionar credenciais ao .env** (servidor e local)
2. **Testar que tudo funciona**
3. **Deletar este arquivo** (após migração completa)

---

*Criado em: 2025-12-29 17:05 BRT*
*Após migração, delete este arquivo: `rm MIGRATION_REQUIRED.md`*
