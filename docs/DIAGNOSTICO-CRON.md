# 🚨 Diagnóstico: Cron no Servidor Sofia Pulse

**Data**: 2025-12-12  
**Status**: ⚠️ **PROBLEMA IDENTIFICADO**

---

## 🔍 Problema Identificado

### Situação Atual
- ✅ Crontab tem 55 coletores de dados instalados
- ❌ **FALTAM os 7 coletores de VAGAS (jobs)**
- ❌ Quase nenhum coletor de vagas está rodando

### Coletores de Vagas Ausentes no Cron

Os seguintes coletores **NÃO estão** no crontab atual:

1. `collect-rapidapi-activejobs.py` ❌
2. `collect-rapidapi-linkedin.py` ❌
3. `collect-serpapi-googlejobs.py` ❌
4. `collect-theirstack-api.py` ❌
5. `collect-careerjet-api.py` ❌
6. `collect-himalayas-api.py` ❌
7. `collect-freejobs-api.py` ❌

---

## ✅ Solução Criada

### Novo Script: `install-crontab-complete-with-jobs.sh`

Criei um novo script que inclui **TODOS os coletores**:
- ✅ 55 coletores de dados (analytics, pesquisa, governo, etc.)
- ✅ 7 coletores de vagas (jobs)
- ✅ **TOTAL: 62 coletores**

### Estratégia de Execução dos Coletores de Vagas

Os coletores de vagas rodarão **3 vezes por dia**:

#### 1ª Execução - Manhã (10:00 BRT / 13:50 UTC)
```bash
13:50 UTC - collect-rapidapi-activejobs.py
13:55 UTC - collect-careerjet-api.py
14:55 UTC - collect-himalayas-api.py
15:50 UTC - collect-freejobs-api.py
```

#### 2ª Execução - Tarde (15:00 BRT / 18:30 UTC)
```bash
18:30 UTC - collect-rapidapi-activejobs.py
18:35 UTC - collect-careerjet-api.py
18:40 UTC - collect-himalayas-api.py
18:45 UTC - collect-freejobs-api.py
```

#### 3ª Execução - Noite (18:00 BRT / 21:50 UTC)
```bash
21:50 UTC - collect-rapidapi-activejobs.py
21:52 UTC - collect-rapidapi-linkedin.py
21:54 UTC - collect-serpapi-googlejobs.py
21:56 UTC - collect-theirstack-api.py
```

---

## 🚀 Como Aplicar a Correção

### Passo 1: Conectar ao Servidor

```bash
ssh ubuntu@91.98.158.19
cd /home/ubuntu/sofia-pulse
```

### Passo 2: Fazer Pull das Alterações

```bash
git pull origin main
```

### Passo 3: Aplicar o Novo Crontab

```bash
# Dar permissão de execução
chmod +x install-crontab-complete-with-jobs.sh

# Executar o script
bash install-crontab-complete-with-jobs.sh
```

### Passo 4: Verificar Instalação

```bash
# Ver o crontab instalado
crontab -l

# Contar coletores instalados
crontab -l | grep -c 'collect-'
# Deve mostrar: 62+

# Ver apenas os coletores de vagas
crontab -l | grep 'jobs-'
```

---

## 📊 Cronograma Completo

### Horários Principais (BRT)

| Horário BRT | Horário UTC | Atividade | Coletores |
|-------------|-------------|-----------|-----------|
| **03:00** | 06:00 | Dados Governamentais BR | 4 |
| **04:00** | 07:00 | Energia & Commodities | 5 |
| **05:00** | 08:00 | Tech News & Community | 3 |
| **07:00** | 10:00 | GitHub (rate limited) | 2 |
| **08:00** | 11:00 | Pesquisa (ArXiv, NIH, etc.) | 4 |
| **09:00** | 12:00 | Orgs Internacionais (Parte 1) | 4 |
| **10:00** | 13:00 | Orgs Internacionais (Parte 2) | 4 |
| **10:00** | 13:50 | 🆕 **VAGAS - 1ª execução** | 4 |
| **11:00** | 14:00 | Dados de Gênero | 6 |
| **12:00** | 15:00 | Dados Sociais | 4 |
| **13:00** | 16:00 | Turismo & Comércio | 3 |
| **14:00** | 17:00 | Esportes | 3 |
| **15:00** | 18:00 | Segurança BR & Ministérios | 2 |
| **15:00** | 18:30 | 🆕 **VAGAS - 2ª execução** | 4 |
| **16:00** | 19:00 | Patentes & IP | 3 |
| **17:00** | 20:00 | Espaço, Cyber, Eventos | 3 |
| **18:00** | 21:00 | Dados Especializados | 4 |
| **18:00** | 21:50 | 🆕 **VAGAS - 3ª execução** | 7 |
| **19:00** | 22:00 | Analytics (33 relatórios) | 1 |
| **19:30** | 22:30 | Envio de Email | 1 |

---

## 📝 Logs dos Coletores de Vagas

Após a instalação, você pode monitorar os logs:

```bash
# Ver logs em tempo real
tail -f /var/log/sofia/jobs-*.log

# Ver log específico
tail -f /var/log/sofia/jobs-activejobs.log
tail -f /var/log/sofia/jobs-linkedin.log
tail -f /var/log/sofia/jobs-googlejobs.log

# Ver todas as execuções do cron
grep CRON /var/log/syslog | grep collect-rapidapi
```

---

## 🔧 Verificações Importantes

### 1. Verificar se os scripts existem

```bash
cd /home/ubuntu/sofia-pulse
ls -la scripts/collect-rapidapi-activejobs.py
ls -la scripts/collect-rapidapi-linkedin.py
ls -la scripts/collect-serpapi-googlejobs.py
ls -la scripts/collect-theirstack-api.py
ls -la scripts/collect-careerjet-api.py
ls -la scripts/collect-himalayas-api.py
ls -la scripts/collect-freejobs-api.py
```

### 2. Verificar variáveis de ambiente

```bash
# Verificar se as API keys estão configuradas
cat .env | grep -E "RAPIDAPI|SERPAPI|THEIRSTACK"
```

### 3. Testar manualmente um coletor

```bash
cd /home/ubuntu/sofia-pulse
source venv/bin/activate
python3 scripts/collect-rapidapi-activejobs.py
```

---

## 📈 Resultado Esperado

Após a instalação e primeira execução:

### Banco de Dados `sofia.jobs`
- Novas vagas coletadas 3x por dia
- Dados de múltiplas fontes (RapidAPI, LinkedIn, Google Jobs, etc.)
- Atualização constante ao longo do dia

### Logs
```
/var/log/sofia/jobs-activejobs.log      # RapidAPI ActiveJobs
/var/log/sofia/jobs-activejobs-2.log    # 2ª execução
/var/log/sofia/jobs-activejobs-3.log    # 3ª execução
/var/log/sofia/jobs-linkedin.log        # LinkedIn via RapidAPI
/var/log/sofia/jobs-googlejobs.log      # Google Jobs via SerpAPI
/var/log/sofia/jobs-theirstack.log      # TheirStack API
/var/log/sofia/jobs-careerjet.log       # Careerjet API
/var/log/sofia/jobs-himalayas.log       # Himalayas API
/var/log/sofia/jobs-freejobs.log        # FreeJobs API
```

---

## 🆘 Troubleshooting

### Problema: Cron não executa os coletores

```bash
# Verificar se o cron está ativo
systemctl status cron

# Ver logs do cron
grep CRON /var/log/syslog | tail -20

# Verificar permissões
ls -la scripts/collect-*.py
```

### Problema: Erro de conexão com banco de dados

```bash
# Verificar se o .env está correto
cat .env | grep DATABASE_URL

# Testar conexão manualmente
cd /home/ubuntu/sofia-pulse
source venv/bin/activate
python3 -c "import psycopg2, os; from dotenv import load_dotenv; load_dotenv(); print('Conectando...'); c = psycopg2.connect(os.getenv('DATABASE_URL')); print('✅ Conexão OK'); c.close()"
```

### Problema: API keys inválidas

```bash
# Verificar se as keys estão no .env
cat .env | grep -E "RAPIDAPI_KEY|SERPAPI_KEY"

# Testar manualmente
curl -H "X-RapidAPI-Key: YOUR_KEY" https://api.rapidapi.com/...
```

---

## 📋 Checklist de Instalação

- [ ] Conectar ao servidor via SSH
- [ ] Fazer pull do repositório
- [ ] Dar permissão de execução ao script
- [ ] Executar `install-crontab-complete-with-jobs.sh`
- [ ] Verificar instalação com `crontab -l`
- [ ] Confirmar 62+ coletores instalados
- [ ] Verificar logs em `/var/log/sofia/jobs-*.log`
- [ ] Aguardar próxima execução automática
- [ ] Monitorar logs em tempo real
- [ ] Verificar dados no banco `sofia.jobs`

---

## 🎯 Próximos Passos

1. **Aplicar o novo crontab** no servidor
2. **Monitorar a primeira execução** (próximo horário: ver tabela acima)
3. **Verificar logs** para confirmar sucesso
4. **Validar dados** no banco de dados
5. **Ajustar frequência** se necessário

---

**Criado**: 2025-12-12  
**Última Atualização**: 2025-12-12  
**Versão**: 2.0 - Com coletores de vagas incluídos

---

## 📞 Suporte

Se precisar de ajuda:
1. Verificar logs: `/var/log/sofia/jobs-*.log`
2. Verificar cron: `grep CRON /var/log/syslog`
3. Testar manualmente os scripts
4. Verificar variáveis de ambiente no `.env`
