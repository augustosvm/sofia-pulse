#!/bin/bash
################################################################################
# SOFIA PULSE - SETUP MONITORING INFRASTRUCTURE
# Creates log directories, permissions, and monitoring tools
################################################################################

echo "════════════════════════════════════════════════════════════════"
echo "🔧 SOFIA PULSE - SETUP MONITORING"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. Create log directories
echo "📁 Creating log directories..."
sudo mkdir -p /var/log/sofia/collectors
sudo mkdir -p /var/log/sofia/analytics
sudo mkdir -p /var/log/sofia/healthchecks

# 2. Set permissions
echo "🔐 Setting permissions..."
sudo chown -R $USER:$USER /var/log/sofia
chmod -R 755 /var/log/sofia

# 3. Create log rotation config
echo "🔄 Setting up log rotation..."
sudo tee /etc/logrotate.d/sofia > /dev/null <<'EOF'
/var/log/sofia/*/*.log {
    daily
    rotate 60
    compress
    delaycompress
    notifempty
    create 0644 ubuntu ubuntu
    sharedscripts
    postrotate
        # Optional: restart services if needed
    endscript
}
EOF

# 4. Make scripts executable
echo "⚙️  Making scripts executable..."
chmod +x healthcheck-collectors.sh
chmod +x scripts/sanity-check.py
chmod +x scripts/utils/logger.py
chmod +x scripts/utils/retry.py
chmod +x scripts/utils/alerts.py

# 5. Test log directory
echo "✅ Testing log directory..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] SETUP: Monitoring infrastructure created" > /var/log/sofia/collectors/setup.log
cat /var/log/sofia/collectors/setup.log

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ MONITORING SETUP COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Log directories created:"
echo "  • /var/log/sofia/collectors/"
echo "  • /var/log/sofia/analytics/"
echo "  • /var/log/sofia/healthchecks/"
echo ""
echo "Next steps:"
echo "  1. Configure Telegram: export TELEGRAM_BOT_TOKEN=..."
echo "  2. Configure Telegram: export TELEGRAM_CHAT_ID=..."
echo "  3. Run healthcheck: bash healthcheck-collectors.sh"
echo "  4. Run sanity check: python3 scripts/sanity-check.py"
echo ""
echo "════════════════════════════════════════════════════════════════"
