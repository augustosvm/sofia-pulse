#!/bin/bash

################################################################################
# Check Crontab for Duplicates
################################################################################

echo "════════════════════════════════════════════════════════════════"
echo "🔍 CHECKING CRONTAB FOR DUPLICATES"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Export current crontab
crontab -l > /tmp/current-crontab.txt 2>/dev/null || echo "# Empty crontab" > /tmp/current-crontab.txt

echo "📋 Current crontab:"
echo ""
cat /tmp/current-crontab.txt
echo ""

# Count sofia-pulse entries
echo "════════════════════════════════════════════════════════════════"
echo "📊 ANALYSIS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Count each type of job
fast_apis=$(grep -c "collect-fast-apis.sh" /tmp/current-crontab.txt || echo "0")
limited_apis=$(grep -c "collect-limited-apis" /tmp/current-crontab.txt || echo "0")
analytics=$(grep -c "run-mega-analytics" /tmp/current-crontab.txt || echo "0")
email=$(grep -c "send-email-mega.sh" /tmp/current-crontab.txt || echo "0")

echo "Fast APIs collection: $fast_apis times"
echo "Limited APIs collection: $limited_apis times"
echo "Analytics execution: $analytics times"
echo "Email sending: $email times"
echo ""

# Check for problems
problems=0

if [ "$fast_apis" -gt 1 ]; then
    echo "⚠️  WARNING: Fast APIs collection appears $fast_apis times (should be 1)"
    problems=$((problems + 1))
fi

if [ "$limited_apis" -gt 1 ]; then
    echo "⚠️  WARNING: Limited APIs collection appears $limited_apis times (should be 1)"
    problems=$((problems + 1))
fi

if [ "$analytics" -gt 1 ]; then
    echo "⚠️  WARNING: Analytics appears $analytics times (should be 1)"
    problems=$((problems + 1))
fi

if [ "$email" -gt 1 ]; then
    echo "⚠️  WARNING: Email sending appears $email times (should be 1)"
    problems=$((problems + 1))
fi

echo ""

if [ "$problems" -gt 0 ]; then
    echo "════════════════════════════════════════════════════════════════"
    echo "❌ PROBLEM DETECTED: Duplicated cron jobs found!"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "This explains why you received reports 3 times."
    echo ""
    echo "🔧 SOLUTION:"
    echo ""
    echo "1. Backup current crontab:"
    echo "   crontab -l > ~/crontab-backup-\$(date +%Y%m%d).txt"
    echo ""
    echo "2. Re-apply clean crontab:"
    echo "   bash update-crontab-with-whatsapp.sh"
    echo ""
    echo "3. Verify (should show each job only once):"
    echo "   bash check-crontab.sh"
    echo ""
else
    echo "════════════════════════════════════════════════════════════════"
    echo "✅ NO DUPLICATES FOUND"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "Crontab looks clean!"
    echo ""
fi
