#!/bin/bash
# Deploy AI Tech Radar to production server

set -e

SERVER="ubuntu@sofiapulse.com"
REMOTE_DIR="/home/ubuntu/sofia-pulse"

echo "🚀 Deploying AI Tech Radar to production..."

# Copy files to server
echo "📦 Copying files..."

# Migration
scp db/migrations/020_create_ai_tech_radar.sql ${SERVER}:${REMOTE_DIR}/db/migrations/

# SQL Views
scp sql/04-ai-tech-radar-views.sql ${SERVER}:${REMOTE_DIR}/sql/

# Collectors
scp scripts/collect-ai-github-trends.ts ${SERVER}:${REMOTE_DIR}/scripts/
scp scripts/collect-ai-pypi-packages.py ${SERVER}:${REMOTE_DIR}/scripts/
scp scripts/collect-ai-npm-packages.ts ${SERVER}:${REMOTE_DIR}/scripts/
scp scripts/collect-ai-huggingface-models.py ${SERVER}:${REMOTE_DIR}/scripts/
scp scripts/collect-ai-arxiv-keywords.py ${SERVER}:${REMOTE_DIR}/scripts/

# Analytics
scp analytics/ai-tech-radar-report.py ${SERVER}:${REMOTE_DIR}/analytics/

# Execution scripts
scp collect-ai-tech-radar.sh ${SERVER}:${REMOTE_DIR}/
scp test-ai-tech-radar.sh ${SERVER}:${REMOTE_DIR}/

echo "✅ Files copied"

# Run on server
echo ""
echo "🧪 Running quick test on server..."

ssh ${SERVER} << 'ENDSSH'
cd /home/ubuntu/sofia-pulse
chmod +x collect-ai-tech-radar.sh test-ai-tech-radar.sh
bash test-ai-tech-radar.sh
ENDSSH

echo ""
echo "✅ AI Tech Radar deployed successfully!"
echo ""
echo "To run full collection:"
echo "  ssh ${SERVER}"
echo "  cd ${REMOTE_DIR}"
echo "  bash collect-ai-tech-radar.sh"
