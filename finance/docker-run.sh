#!/bin/bash

###############################################################################
# Sofia Finance - Docker Quick Run
###############################################################################

set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🌟 Sofia Finance Intelligence Hub - Docker Run 🌟       ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker não encontrado. Instale: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Verificar se docker-compose está instalado e definir comando correto
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    echo -e "${YELLOW}⚠️  docker-compose não encontrado. Instale: https://docs.docker.com/compose/install/${NC}"
    exit 1
fi

# Criar .env se não existir
if [ ! -f .env ]; then
    echo -e "${YELLOW}ℹ️  Criando .env a partir de .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env criado! Edite se necessário.${NC}"
fi

# Modo de execução
MODE=${1:-demo}

case $MODE in
    demo)
        echo -e "${BLUE}🚀 Rodando em modo DEMO (sem banco)${NC}"
        docker build -t sofia-finance:demo .
        docker run --rm -v "$(pwd)/output:/app/output" sofia-finance:demo npm run demo
        ;;

    full)
        echo -e "${BLUE}🗄️  Rodando com PostgreSQL (modo completo)${NC}"
        $DOCKER_COMPOSE up -d
        echo ""
        echo -e "${GREEN}✅ Containers iniciados!${NC}"
        echo ""
        echo -e "📊 Ver logs:     ${BLUE}$DOCKER_COMPOSE logs -f finance${NC}"
        echo -e "🛑 Parar:        ${BLUE}$DOCKER_COMPOSE down${NC}"
        echo -e "📁 Outputs em:   ${BLUE}./output/${NC}"
        ;;

    build)
        echo -e "${BLUE}🔨 Rebuilding containers...${NC}"
        $DOCKER_COMPOSE build --no-cache
        echo -e "${GREEN}✅ Build completo!${NC}"
        ;;

    migrate)
        echo -e "${BLUE}🗄️  Rodando migrations...${NC}"
        $DOCKER_COMPOSE run --rm finance npm run migrate:market
        echo -e "${GREEN}✅ Migrations completas!${NC}"
        ;;

    collect)
        echo -e "${BLUE}📊 Coletando dados de mercado...${NC}"
        $DOCKER_COMPOSE run --rm finance npm run collect:all
        echo -e "${GREEN}✅ Coleta completa!${NC}"
        ;;

    signals)
        echo -e "${BLUE}🎯 Gerando sinais...${NC}"
        $DOCKER_COMPOSE run --rm finance npm run signals
        echo -e "${GREEN}✅ Sinais gerados! Veja em ./output/${NC}"
        ;;

    shell)
        echo -e "${BLUE}🐚 Abrindo shell no container...${NC}"
        $DOCKER_COMPOSE run --rm finance /bin/bash
        ;;

    logs)
        echo -e "${BLUE}📋 Mostrando logs...${NC}"
        $DOCKER_COMPOSE logs -f finance
        ;;

    stop)
        echo -e "${BLUE}🛑 Parando containers...${NC}"
        $DOCKER_COMPOSE down
        echo -e "${GREEN}✅ Containers parados!${NC}"
        ;;

    clean)
        echo -e "${BLUE}🧹 Limpando containers, volumes e imagens...${NC}"
        $DOCKER_COMPOSE down -v --rmi all
        echo -e "${GREEN}✅ Limpeza completa!${NC}"
        ;;

    *)
        echo "Uso: $0 {demo|full|build|migrate|collect|signals|shell|logs|stop|clean}"
        echo ""
        echo "Comandos:"
        echo "  demo      - Roda demo sem banco (padrão)"
        echo "  full      - Inicia PostgreSQL + Finance (modo completo)"
        echo "  build     - Rebuild containers"
        echo "  migrate   - Roda migrations do banco"
        echo "  collect   - Coleta dados de mercado"
        echo "  signals   - Gera sinais de investimento"
        echo "  shell     - Abre shell no container"
        echo "  logs      - Mostra logs em tempo real"
        echo "  stop      - Para todos containers"
        echo "  clean     - Remove tudo (containers, volumes, imagens)"
        exit 1
        ;;
esac
