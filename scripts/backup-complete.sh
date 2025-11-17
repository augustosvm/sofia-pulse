#!/bin/bash

###############################################################################
# Sofia Intelligence Hub - Backup Completo
# Faz backup de todos os databases e volumes Docker
# Upload automático para Google Drive com rclone
###############################################################################

set -e

# Configurações
BACKUP_DIR="/tmp/sofia-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="sofia-backup-${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
RCLONE_REMOTE="gdrive:Backups/Sofia-Intelligence-Hub"
RETENTION_DAYS=30

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logging
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Criar diretório de backup
mkdir -p "${BACKUP_PATH}"

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 Sofia Intelligence Hub - Backup Completo"
echo "════════════════════════════════════════════════════════════════"
echo ""

###############################################################################
# 1. BACKUP DOS DATABASES
###############################################################################

log_info "Iniciando backup dos databases..."

# Auto-detectar containers Postgres disponíveis
POSTGRES_CONTAINERS=$(docker ps --filter "ancestor=postgres" --format "{{.Names}}" 2>/dev/null || \
                     docker ps --filter "name=postgres" --format "{{.Names}}" 2>/dev/null)

if [ -z "$POSTGRES_CONTAINERS" ]; then
    log_warning "Nenhum container Postgres encontrado em execução"
else
    log_info "Containers Postgres encontrados: $(echo $POSTGRES_CONTAINERS | tr '\n' ' ')"
fi

# Tentar múltiplos nomes de container Postgres
POSTGRES_CANDIDATES=("sofia-postgres" "postgres" "bressan-postgres" $POSTGRES_CONTAINERS)
POSTGRES_CONTAINER=""

for candidate in "${POSTGRES_CANDIDATES[@]}"; do
    if docker exec "$candidate" pg_isready -U postgres &>/dev/null; then
        POSTGRES_CONTAINER="$candidate"
        log_success "Container Postgres ativo encontrado: $POSTGRES_CONTAINER"
        break
    fi
done

if [ -z "$POSTGRES_CONTAINER" ]; then
    log_error "Nenhum container Postgres acessível encontrado!"
else
    # Listar todos os databases disponíveis
    log_info "Listando databases no container $POSTGRES_CONTAINER..."
    DATABASES=$(docker exec "$POSTGRES_CONTAINER" psql -U postgres -t -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres');" 2>/dev/null | grep -v '^$' | xargs)

    if [ -n "$DATABASES" ]; then
        log_info "Databases encontrados: $DATABASES"

        # Fazer backup de cada database
        for db in $DATABASES; do
            log_info "Backupeando database: $db..."
            if docker exec "$POSTGRES_CONTAINER" pg_dump -U postgres "$db" > "${BACKUP_PATH}/${db}_db.sql" 2>/dev/null; then
                DB_SIZE=$(du -h "${BACKUP_PATH}/${db}_db.sql" | cut -f1)
                log_success "Database '$db' backed up: ${db}_db.sql ($DB_SIZE)"
            else
                log_warning "Falha ao backupear database: $db"
            fi
        done
    else
        log_warning "Nenhum database de usuário encontrado"
    fi
fi

###############################################################################
# 2. BACKUP DOS VOLUMES DOCKER
###############################################################################

log_info "Iniciando backup dos volumes Docker..."

# 2.1 Sofia Mastra RAG volumes
MASTRA_VOLUMES=(
    "sofia-mastra-rag_mastra_db"
    "sofia-mastra-rag_postgres_data"
    "sofia-rag_mastra-data"
)

for volume in "${MASTRA_VOLUMES[@]}"; do
    if docker volume inspect "$volume" &> /dev/null; then
        log_info "Backupeando volume: $volume..."
        docker run --rm \
            -v "$volume:/data" \
            -v "${BACKUP_PATH}:/backup" \
            alpine tar czf "/backup/${volume}.tar.gz" -C /data . 2>/dev/null
        log_success "Volume backed up: ${volume}.tar.gz"
    else
        log_warning "Volume não encontrado: $volume"
    fi
done

# 2.2 n8n volume
if docker volume inspect sofia-pulse_n8n_data &> /dev/null; then
    log_info "Backupeando n8n workflows e dados..."
    docker run --rm \
        -v sofia-pulse_n8n_data:/data \
        -v "${BACKUP_PATH}:/backup" \
        alpine tar czf /backup/n8n_data.tar.gz -C /data . 2>/dev/null
    log_success "n8n data backed up: n8n_data.tar.gz"
else
    log_warning "Volume n8n_data não encontrado"
fi

# 2.3 postgres_data volume principal
if docker volume inspect postgres_data &> /dev/null; then
    log_info "Backupeando postgres_data volume..."
    docker run --rm \
        -v postgres_data:/data \
        -v "${BACKUP_PATH}:/backup" \
        alpine tar czf /backup/postgres_data.tar.gz -C /data . 2>/dev/null
    log_success "postgres_data backed up: postgres_data.tar.gz"
else
    log_warning "Volume postgres_data não encontrado"
fi

###############################################################################
# 3. BACKUP DO CÓDIGO E CONFIGURAÇÕES
###############################################################################

log_info "Backupeando código e configurações do Mastra RAG..."

# Backup dos arquivos do Mastra RAG
MASTRA_RAG_DIR="/home/ubuntu/sofia-mastra-rag"
if [ -d "$MASTRA_RAG_DIR" ]; then
    tar czf "${BACKUP_PATH}/mastra-rag-files.tar.gz" \
        -C "$MASTRA_RAG_DIR" \
        --exclude='node_modules' \
        --exclude='.next' \
        --exclude='dist' \
        --exclude='.git' \
        . 2>/dev/null || log_warning "Alguns arquivos podem não ter sido backupeados"
    log_success "Mastra RAG files backed up: mastra-rag-files.tar.gz"
else
    log_warning "Diretório Mastra RAG não encontrado: $MASTRA_RAG_DIR"
fi

###############################################################################
# 4. COMPACTAR TUDO
###############################################################################

log_info "Compactando backup completo..."
cd "${BACKUP_DIR}"
tar czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"
BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
log_success "Backup compactado: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"

###############################################################################
# 5. UPLOAD PARA GOOGLE DRIVE
###############################################################################

log_info "Enviando backup para Google Drive..."
if rclone copy "${BACKUP_NAME}.tar.gz" "${RCLONE_REMOTE}/" --progress 2>&1 | tail -1; then
    log_success "Backup enviado para Google Drive: ${RCLONE_REMOTE}/${BACKUP_NAME}.tar.gz"
else
    log_error "Falha ao enviar backup para Google Drive"
    exit 1
fi

###############################################################################
# 6. LIMPEZA LOCAL
###############################################################################

log_info "Limpando arquivos temporários..."
rm -rf "${BACKUP_PATH}"
rm -f "${BACKUP_NAME}.tar.gz"
log_success "Backup local removido (${BACKUP_SIZE} economizados)"

###############################################################################
# 7. ROTAÇÃO DE BACKUPS NO GOOGLE DRIVE
###############################################################################

log_info "Removendo backups antigos (> ${RETENTION_DAYS} dias)..."
rclone delete "${RCLONE_REMOTE}/" \
    --min-age "${RETENTION_DAYS}d" \
    --include "sofia-backup-*.tar.gz" 2>/dev/null || true
log_success "Backups antigos removidos"

###############################################################################
# RESUMO
###############################################################################

echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "  ${GREEN}✓ BACKUP COMPLETO FINALIZADO COM SUCESSO!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📦 Arquivo: ${BACKUP_NAME}.tar.gz"
echo "📊 Tamanho: ${BACKUP_SIZE}"
echo "☁️  Local: ${RCLONE_REMOTE}/"
echo "🗑️  Retenção: ${RETENTION_DAYS} dias"
echo ""
echo "Conteúdo backupeado:"
if [ -n "$POSTGRES_CONTAINER" ]; then
    echo "  ✓ Postgres Databases do container '$POSTGRES_CONTAINER':"
    for db in $DATABASES; do
        if [ -f "${BACKUP_PATH}/${db}_db.sql" ]; then
            echo "    - $db"
        fi
    done
fi
echo "  ✓ Sofia Mastra RAG volumes (3)"
echo "  ✓ n8n workflows e dados"
echo "  ✓ postgres_data volume"
echo "  ✓ Mastra RAG código e configs"
echo ""
echo "════════════════════════════════════════════════════════════════"
