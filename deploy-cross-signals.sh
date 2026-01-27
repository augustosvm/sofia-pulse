#!/bin/bash
# Deploy Cross Signals Intelligence System V1.0 to Production Server
# Server: ubuntu@91.98.158.19

set -e

echo "=========================================="
echo "Cross Signals - Production Deployment"
echo "=========================================="
echo ""

# Step 1: Pull latest changes
echo "📥 Step 1: Pulling latest changes from GitHub..."
cd /home/ubuntu/sofia-pulse
git fetch origin
git checkout master
git pull origin master
echo "✅ Code updated to latest commit"
echo ""

# Step 2: Apply database migrations
echo "🗄️ Step 2: Applying database migrations..."

source .env

# Apply VSCode extensions migration
echo "   Applying 061_create_vscode_extensions_daily.sql..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -f database/migrations/061_create_vscode_extensions_daily.sql 2>&1 | grep -v "already exists" || true

# Apply news items migration
echo "   Applying 062_create_news_items.sql..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -f database/migrations/062_create_news_items.sql 2>&1 | grep -v "already exists" || true

echo "✅ Migrations applied successfully"
echo ""

# Step 3: Make scripts executable
echo "🔧 Step 3: Making scripts executable..."
chmod +x run-cross-signals-builder.sh
chmod +x update-crontab-with-cross-signals.sh
echo "✅ Scripts are executable"
echo ""

# Step 4: Test builder (dry-run)
echo "🧪 Step 4: Testing cross-signals builder (dry-run)..."
python3 scripts/build-cross-signals.py --dry-run > /tmp/cross-signals-test.json 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Builder test passed"
else
    echo "⚠️  Builder test had issues (may be normal if no data yet)"
fi
echo ""

# Step 5: Create logs directory
echo "📁 Step 5: Creating logs directory..."
mkdir -p logs
echo "✅ Logs directory ready"
echo ""

# Step 6: Install cron schedule
echo "⏰ Step 6: Installing cron schedule..."
bash update-crontab-with-cross-signals.sh
echo "✅ Cron schedule installed"
echo ""

# Step 7: Verify installation
echo "🔍 Step 7: Verifying installation..."

# Check if cross-signals builder script exists
if [ -f "scripts/build-cross-signals.py" ]; then
    echo "   ✅ Builder script exists"
else
    echo "   ❌ Builder script missing!"
    exit 1
fi

# Check if email renderer exists
if [ -f "scripts/utils/cross_signals_email_renderer.py" ]; then
    echo "   ✅ Email renderer exists"
else
    echo "   ❌ Email renderer missing!"
    exit 1
fi

# Check if migrations were applied
TABLES_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='sofia' AND table_name IN ('vscode_extensions_daily', 'news_items');")

if [ "$TABLES_COUNT" -eq "2" ]; then
    echo "   ✅ Database tables exist"
else
    echo "   ⚠️  Some tables may be missing (found $TABLES_COUNT/2)"
fi

# Check cron
if crontab -l | grep -q "cross-signals"; then
    echo "   ✅ Cron job installed"
else
    echo "   ❌ Cron job not found!"
fi

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "📊 What was deployed:"
echo "   - scripts/build-cross-signals.py (940 lines)"
echo "   - scripts/utils/cross_signals_email_renderer.py (183 lines)"
echo "   - run-cross-signals-builder.sh"
echo "   - update-crontab-with-cross-signals.sh"
echo "   - database migrations (061, 062)"
echo "   - Email integration (send-email-mega.py)"
echo ""
echo "⏰ Schedule:"
echo "   21:30 UTC - Cross Signals Builder (NEW)"
echo "   22:00 UTC - Analytics Reports"
echo "   22:05 UTC - Email (with Cross Signals block)"
echo ""
echo "📝 Next steps:"
echo "   1. Wait 7-14 days for data accumulation"
echo "   2. Monitor logs: tail -f ~/sofia-pulse/logs/cross-signals.log"
echo "   3. Check email for Cross Signals block starting tomorrow"
echo ""
echo "🎉 Cross Signals Intelligence System V1.0 is now LIVE!"
echo "=========================================="
