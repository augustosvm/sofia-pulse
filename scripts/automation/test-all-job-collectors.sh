#!/bin/bash
# Test all job collectors and show summary

echo "🧪 Testing All Job Collectors"
echo "======================================"
echo ""

COLLECTORS=(
  "adzuna"
  "arbeitnow"
  "findwork"
  "github"
  "greenhouse"
  "himalayas"
  "themuse"
  "usajobs"
  "weworkremotely"
)

RESULTS_FILE="/tmp/job-collectors-test-results.txt"
> $RESULTS_FILE

for collector in "${COLLECTORS[@]}"; do
  echo "📋 Testing: $collector"
  echo "-----------------------------------"

  # Run collector with timeout
  OUTPUT=$(timeout 60 npx tsx scripts/collect-jobs-${collector}.ts 2>&1)
  EXIT_CODE=$?

  # Extract key info
  COLLECTED=$(echo "$OUTPUT" | grep -oP "✅ Collected: \K\d+" | head -1)
  WARNINGS=$(echo "$OUTPUT" | grep -c "⚠️")
  ERRORS=$(echo "$OUTPUT" | grep -c "❌ Error inserting")

  # Status
  if [ $EXIT_CODE -eq 0 ]; then
    STATUS="✅ SUCCESS"
  elif [ $EXIT_CODE -eq 124 ]; then
    STATUS="⏱️  TIMEOUT"
  else
    STATUS="❌ FAILED"
  fi

  # Save results
  echo "$collector|$STATUS|$COLLECTED|$WARNINGS|$ERRORS" >> $RESULTS_FILE

  # Display
  echo "  Status: $STATUS"
  echo "  Collected: ${COLLECTED:-N/A}"
  echo "  Warnings: $WARNINGS"
  echo "  Errors: $ERRORS"
  echo ""

  # Wait between collectors
  sleep 2
done

echo ""
echo "======================================"
echo "📊 SUMMARY"
echo "======================================"
echo ""
printf "%-15s %-12s %-10s %-10s %-10s\n" "Collector" "Status" "Collected" "Warnings" "Errors"
echo "--------------------------------------------------------------"

while IFS='|' read -r name status collected warnings errors; do
  printf "%-15s %-12s %-10s %-10s %-10s\n" "$name" "$status" "${collected:-N/A}" "$warnings" "$errors"
done < $RESULTS_FILE

echo ""
echo "✅ Test completed!"
