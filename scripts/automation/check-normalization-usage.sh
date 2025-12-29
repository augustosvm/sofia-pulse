#!/bin/bash
echo "=== Collectors com dados geográficos mas SEM normalização ==="
echo ""

for file in scripts/collect-*.py; do
  if grep -q "country\|cidade\|state" "$file" 2>/dev/null && ! grep -q "geo_helpers" "$file" 2>/dev/null; then
    echo "❌ $(basename "$file")"
  fi
done

echo ""
echo "=== Tabelas que DEVERIAM usar normalização ==="
echo ""
echo "Tables com country_name mas sem country_id:"
psql postgresql://sofia:sofia123strong@91.98.158.19:5432/sofia_db -c "
SELECT table_name
FROM information_schema.columns
WHERE table_schema = 'sofia'
AND column_name LIKE '%country%'
AND column_name NOT LIKE '%country_id%'
AND table_name NOT IN (SELECT table_name FROM information_schema.columns WHERE table_schema = 'sofia' AND column_name = 'country_id')
ORDER BY table_name
LIMIT 10;" 2>/dev/null || echo "Não conseguiu conectar ao DB"
