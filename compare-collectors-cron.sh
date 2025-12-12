#!/bin/bash
# Comparar coletores existentes vs crontab e mostrar os faltantes

echo "Coletores no servidor:"
find /home/ubuntu/sofia-pulse/scripts -type f \( -name 'collect-*.py' -o -name 'collect-*.ts' \) -exec basename {} \; | sort > /tmp/all-collectors.txt
wc -l /tmp/all-collectors.txt

echo ""
echo "Coletores no crontab:"
crontab -l | grep 'collect-' | grep -oP 'collect-[a-z0-9-]+\.(py|ts)' | sort -u > /tmp/cron-collectors.txt
wc -l /tmp/cron-collectors.txt

echo ""
echo "FALTANDO NO CRONTAB:"
comm -23 /tmp/all-collectors.txt /tmp/cron-collectors.txt

echo ""
echo "Total faltando:"
comm -23 /tmp/all-collectors.txt /tmp/cron-collectors.txt | wc -l
