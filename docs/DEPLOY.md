# 🚀 Sofia Pulse - Guia de Deploy

Guia completo para deploy do Sofia Pulse em produção.

---

## 📋 Pré-requisitos

- Ubuntu 20.04+ ou Debian 11+
- 4GB RAM mínimo (8GB recomendado)
- 50GB disk space mínimo
- Docker & Docker Compose
- Acesso root/sudo

---

## ⚡ Quick Deploy (5 minutos)

```bash
# 1. Clone repositório
git clone https://github.com/augustosvm/sofia-pulse.git
cd sofia-pulse

# 2. Configure environment
cp .env.example .env
nano .env  # Edit com suas credenciais

# 3. Deploy com Docker
docker-compose up -d

# 4. Verificar saúde
docker-compose ps
docker-compose logs -f

# 5. Configurar cron jobs
crontab -e
# Adicionar jobs (ver seção Automação)
```

---

## 🔧 Setup Detalhado

### 1. Servidor (VPS/Dedicated)

#### Providers Recomendados

- **DigitalOcean**: Droplet 4GB ($24/mês)
- **AWS**: t3.medium ($30/mês)
- **Hetzner**: CX31 (€8/mês) ✅ Melhor custo-benefício

#### Configuração Inicial

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y curl git vim htop

# Configurar timezone
sudo timedatectl set-timezone America/Sao_Paulo

# Configurar hostname
sudo hostnamectl set-hostname sofia-pulse
```

### 2. Docker & Docker Compose

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Instalar Docker Compose v2
sudo apt install docker-compose-plugin

# Verificar instalação
docker --version
docker compose version
```

### 3. PostgreSQL (via Docker)

```bash
# Criar rede Docker
docker network create sofia-network

# Subir PostgreSQL
docker run -d \
  --name sofia-postgres \
  --network sofia-network \
  -e POSTGRES_USER=sofia \
  -e POSTGRES_PASSWORD=SENHA_FORTE_AQUI \
  -e POSTGRES_DB=sofia_db \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  --restart unless-stopped \
  pgvector/pgvector:pg15

# Verificar
docker logs sofia-postgres
```

### 4. Aplicação Sofia Pulse

```bash
# Clone e configure
cd /opt
git clone https://github.com/augustosvm/sofia-pulse.git
cd sofia-pulse

# Configure .env
cp .env.example .env

# Edite com suas credenciais
nano .env
```

**`.env` exemplo**:
```bash
# PostgreSQL
POSTGRES_HOST=sofia-postgres
POSTGRES_PORT=5432
POSTGRES_USER=sofia
POSTGRES_PASSWORD=SUA_SENHA_FORTE
POSTGRES_DB=sofia_db
DATABASE_URL=postgresql://sofia:SUA_SENHA@sofia-postgres:5432/sofia_db

# APIs
ALPHA_VANTAGE_API_KEY=SUA_KEY_AQUI
GITHUB_TOKEN=ghp_XXXXXXXX

# App
NODE_ENV=production
LOG_LEVEL=info
```

```bash
# Instalar dependências
npm install

# Rodar migrações
npm run migrate

# Testar coleta
npm run collect:arxiv -- --limit=10
```

### 5. Finance Module

```bash
cd finance

# Instalar dependências
npm install

# Configurar .env
cat > .env << 'EOF'
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sofia
POSTGRES_PASSWORD=SUA_SENHA
POSTGRES_DB=sofia_db
ALPHA_VANTAGE_API_KEY=SUA_KEY
EOF

# Testar
npm run demo
npm run collect:brazil
npm run signals
```

---

## ⚙️ Automação com Cron

```bash
# Editar crontab
crontab -e
```

Adicionar jobs:

```bash
# Backup PostgreSQL - 2h
0 2 * * * /opt/sofia-pulse/scripts/backup-complete.sh >> /var/log/sofia-backup.log 2>&1

# Coleta diária - 6h
0 6 * * * cd /opt/sofia-pulse && ./cron-daily.sh >> /var/log/sofia-daily.log 2>&1

# Coleta semanal - domingo 3h
0 3 * * 0 cd /opt/sofia-pulse && ./cron-weekly.sh >> /var/log/sofia-weekly.log 2>&1

# Finance signals - dias úteis 18h
0 18 * * 1-5 cd /opt/sofia-pulse/finance && npm run invest:full >> /var/log/sofia-finance.log 2>&1

# Limpeza backups antigos - domingo 5h
0 5 * * 0 find /var/backups/postgres/ -name "*.sql.gz" -mtime +7 -delete
```

---

## 🔒 Segurança

### Firewall (UFW)

```bash
# Ativar UFW
sudo ufw enable

# Permitir SSH
sudo ufw allow 22/tcp

# Permitir apenas conexões locais ao PostgreSQL
# (já está na rede Docker, sem exposição pública)

# Verificar status
sudo ufw status
```

### SSL/TLS (Futuro - API)

```bash
# Certbot para Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d api.sofia-pulse.com
```

### Secrets Management

```bash
# NUNCA commitar .env
echo ".env" >> .gitignore

# Usar variáveis de ambiente fortes
openssl rand -base64 32  # Gerar senhas
```

---

## 📊 Monitoramento

### Logs

```bash
# Criar diretório de logs
sudo mkdir -p /var/log/sofia-pulse
sudo chown $USER:$USER /var/log/sofia-pulse

# Ver logs em tempo real
tail -f /var/log/sofia-daily.log
tail -f /var/log/sofia-finance.log
```

### Grafana (Opcional)

```bash
# Deploy Grafana
docker run -d \
  --name grafana \
  --network sofia-network \
  -p 3000:3000 \
  -v grafana-storage:/var/lib/grafana \
  --restart unless-stopped \
  grafana/grafana:latest

# Acessar: http://SEU_IP:3000
# Login padrão: admin/admin
```

Adicionar datasource PostgreSQL:
- Host: `sofia-postgres:5432`
- Database: `sofia_db`
- User: `sofia`
- Password: `SUA_SENHA`

### Health Checks

```bash
# Script de health check
cat > /opt/sofia-pulse/health-check.sh << 'EOF'
#!/bin/bash

# PostgreSQL
docker exec sofia-postgres pg_isready -U sofia || echo "⚠️  PostgreSQL down"

# Disk space
DISK_USE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USE -gt 80 ]; then
  echo "⚠️  Disk usage: ${DISK_USE}%"
fi

# Last collection
LAST_COLLECT=$(find /opt/sofia-pulse/logs -name "sofia-daily.log" -mtime -1)
if [ -z "$LAST_COLLECT" ]; then
  echo "⚠️  No collection in last 24h"
fi

echo "✅ All systems operational"
EOF

chmod +x /opt/sofia-pulse/health-check.sh

# Rodar via cron a cada hora
# crontab: 0 * * * * /opt/sofia-pulse/health-check.sh >> /var/log/health-check.log 2>&1
```

---

## 🔄 Atualizações

### Pull & Deploy

```bash
cd /opt/sofia-pulse

# Pull latest
git pull origin main

# Reinstalar deps se necessário
npm install

# Restart services
docker-compose restart

# Ou apenas atualizar finance module
cd finance && npm install && cd ..
```

### Zero Downtime (Futuro)

```bash
# Blue-green deployment
docker-compose -f docker-compose.blue.yml up -d
# Swap traffic
docker-compose -f docker-compose.green.yml down
```

---

## 📦 Backup & Restore

### Backup

```bash
# Manual
/opt/sofia-pulse/scripts/backup-complete.sh

# Verificar backups
ls -lh /var/backups/postgres/
```

### Restore

```bash
# Último backup
LATEST_BACKUP=$(ls -t /var/backups/postgres/*.sql.gz | head -1)

# Restore
gunzip -c $LATEST_BACKUP | docker exec -i sofia-postgres \
  psql -U sofia -d sofia_db

# Verificar
docker exec sofia-postgres psql -U sofia -d sofia_db -c "\dt"
```

---

## 🚨 Troubleshooting

### Problema: PostgreSQL não inicia

```bash
# Ver logs
docker logs sofia-postgres

# Recriar container
docker stop sofia-postgres
docker rm sofia-postgres
# Rodar comando de criação novamente
```

### Problema: Coleta falhando

```bash
# Ver logs de erro
tail -100 /var/log/sofia-daily.log

# Testar manualmente
cd /opt/sofia-pulse
npm run collect:arxiv

# Verificar API keys
cat .env | grep API_KEY
```

### Problema: Disco cheio

```bash
# Ver uso
df -h

# Limpar logs antigos
sudo find /var/log -name "*.log" -mtime +30 -delete

# Limpar backups antigos
sudo find /var/backups/postgres -name "*.sql.gz" -mtime +7 -delete

# Limpar Docker
docker system prune -af
```

---

## 📊 Métricas de Performance

### Targets

- **Coleta diária**: < 30 minutos
- **Geração de sinais**: < 5 minutos
- **API response time**: < 200ms (p95)
- **Database queries**: < 100ms (p95)

### Otimização

```sql
-- Vacuum regular
VACUUM ANALYZE;

-- Reindex se necessário
REINDEX DATABASE sofia_db;

-- Ver slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## 🎯 Checklist de Deploy

- [ ] Servidor configurado (Ubuntu/Debian)
- [ ] Docker & Docker Compose instalados
- [ ] PostgreSQL rodando
- [ ] .env configurado com secrets
- [ ] Migrações executadas
- [ ] Teste de coleta bem-sucedido
- [ ] Cron jobs configurados
- [ ] Backups configurados
- [ ] Firewall ativado
- [ ] Logs configurados
- [ ] Monitoring setup (Grafana)
- [ ] Alertas configurados
- [ ] Documentação revisada

---

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/augustosvm/sofia-pulse/issues)
- **Docs**: [README.md](README.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

<p align="center">
  <strong>Deploy com confiança - Sofia Pulse production ready! 🚀</strong>
</p>
