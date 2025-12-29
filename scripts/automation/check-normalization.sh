#!/bin/bash
echo "=== Checking ALL job collectors for normalization ==="
echo ""

for file in scripts/collect-jobs-*.ts; do
    collector=$(basename "$file" .ts | sed 's/collect-jobs-//')

    has_country_id=$(grep -q "country_id" "$file" && echo "✅" || echo "❌")
    has_state_id=$(grep -q "state_id" "$file" && echo "✅" || echo "❌")
    has_city_id=$(grep -q "city_id" "$file" && echo "✅" || echo "❌")
    has_org_id=$(grep -q "organization_id" "$file" && echo "✅" || echo "❌")

    printf "%-20s country_id:%s state_id:%s city_id:%s org_id:%s\n" "$collector" "$has_country_id" "$has_state_id" "$has_city_id" "$has_org_id"
done
