#!/bin/bash

###############################################################################
# Sofia Finance - Server Setup Script
# Para servidor com PostgreSQL já configurado
###############################################################################

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     🌟 Sofia Finance Intelligence Hub - Server Setup 🌟     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Pull latest code
echo -e "${BLUE}📥 Pulling latest code...${NC}"
cd /home/ubuntu/sofia-pulse
git config --global --add safe.directory /home/ubuntu/sofia-pulse
git pull origin claude/resume-context-demo-01Jwa7QikzGJHnTZjJLMp5AE
cd finance

# 2. Create .env
echo -e "${BLUE}⚙️  Configurando environment...${NC}"
cat > .env << 'EOF'
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=sofia
POSTGRES_PASSWORD=sofia123strong
POSTGRES_DB=sofia_db
DATABASE_URL=postgresql://sofia:sofia123strong@localhost:5432/sofia_db
NODE_ENV=production
EOF
echo -e "${GREEN}✅ .env criado${NC}"

# 3. Install dependencies
echo -e "${BLUE}📦 Instalando dependências...${NC}"
npm install

# 4. Create database if not exists
echo -e "${BLUE}🗄️  Criando database...${NC}"
docker exec sofia-postgres psql -U postgres -c "CREATE DATABASE IF NOT EXISTS sofia_db;" 2>/dev/null || true
docker exec sofia-postgres psql -U postgres -c "CREATE USER IF NOT EXISTS sofia WITH PASSWORD 'sofia123strong';" 2>/dev/null || true
docker exec sofia-postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE sofia_db TO sofia;" 2>/dev/null || true
echo -e "${GREEN}✅ Database configurado${NC}"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✅ Setup Completo!                        ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "🚀 Agora execute:"
echo -e ""
echo -e "   ${BLUE}npm run collect:brazil${NC}  # Coletar dados B3"
echo -e "   ${BLUE}npm run signals${NC}         # Gerar sinais"
echo -e "   ${BLUE}cat output/sofia-signals-*.json | jq .signals[0:3]${NC}"
echo -e ""
