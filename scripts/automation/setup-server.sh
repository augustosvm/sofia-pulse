#!/bin/bash
# Sofia Pulse - Server Setup Script
# Run this on your server to configure automatic collector execution

set -e

echo "🚀 Sofia Pulse - Server Configuration"
echo "======================================"
echo ""

# 1. Install dependencies
echo "📦 Installing dependencies..."
npm install

# 2. Create log directory
mkdir -p logs

# 3. Create collector runner script
cat > run-collectors.sh << 'EOF'
#!/bin/bash
# Sofia Pulse Collector Runner
# Runs all collectors and logs output

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

LOG_FILE="logs/collectors-$(date +%Y%m%d-%H%M%S).log"

echo "🚀 Starting collectors at $(date)" | tee -a "$LOG_FILE"

# Fast collectors (run every hour)
COLLECTORS=(
    "github"
    "hackernews"
    "stackoverflow"
    "himalayas"
    "remoteok"
    "ai-companies"
    "universities"
    "ngos"
    "yc-companies"
    "nvd"
    "cisa"
    "gdelt"
    "mdic-regional"
    "fiesp-data"
)

SUCCESS=0
FAILED=0

for collector in "${COLLECTORS[@]}"; do
    echo "[$((SUCCESS+FAILED+1))/${#COLLECTORS[@]}] Running: $collector" | tee -a "$LOG_FILE"
    
    if timeout 300 npx tsx scripts/collect.ts "$collector" >> "$LOG_FILE" 2>&1; then
        echo "  ✅ Success" | tee -a "$LOG_FILE"
        ((SUCCESS++))
    else
        echo "  ❌ Failed" | tee -a "$LOG_FILE"
        ((FAILED++))
    fi
done

echo "" | tee -a "$LOG_FILE"
echo "✅ Completed: $SUCCESS/${#COLLECTORS[@]}" | tee -a "$LOG_FILE"
echo "❌ Failed: $FAILED/${#COLLECTORS[@]}" | tee -a "$LOG_FILE"
echo "Finished at $(date)" | tee -a "$LOG_FILE"

# Keep only last 7 days of logs
find logs -name "collectors-*.log" -mtime +7 -delete
EOF

chmod +x run-collectors.sh

# 4. Setup cron job
echo ""
echo "📅 Setting up cron job..."
echo "Add this line to your crontab (crontab -e):"
echo ""
echo "# Sofia Pulse - Run collectors every hour"
echo "0 * * * * cd $(pwd) && ./run-collectors.sh"
echo ""

# 5. Setup systemd service (optional, better than cron)
cat > sofia-pulse-collectors.service << EOF
[Unit]
Description=Sofia Pulse Data Collectors
After=network.target postgresql.service

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/run-collectors.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

cat > sofia-pulse-collectors.timer << EOF
[Unit]
Description=Sofia Pulse Collectors Timer
Requires=sofia-pulse-collectors.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Unit=sofia-pulse-collectors.service

[Install]
WantedBy=timers.target
EOF

echo ""
echo "🔧 Systemd service files created!"
echo "To install systemd timer (recommended):"
echo ""
echo "  sudo cp sofia-pulse-collectors.service /etc/systemd/system/"
echo "  sudo cp sofia-pulse-collectors.timer /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable sofia-pulse-collectors.timer"
echo "  sudo systemctl start sofia-pulse-collectors.timer"
echo ""
echo "To check status:"
echo "  sudo systemctl status sofia-pulse-collectors.timer"
echo "  sudo journalctl -u sofia-pulse-collectors.service -f"
echo ""
echo "======================================"
echo "✅ Setup complete!"
echo "======================================"
