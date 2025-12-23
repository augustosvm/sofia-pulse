# Run All Sofia Pulse Collectors
# This script executes all 89 collectors sequentially

Write-Host "🚀 Sofia Pulse - Running All Collectors" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host ""

$collectors = @(
    # Tech Trends
    "github",
    "hackernews", 
    "npm",
    "pypi",
    "stackoverflow",
    
    # Research
    "arxiv",
    
    # Jobs
    "himalayas",
    "remoteok",
    
    # Organizations
    "ai-companies",
    "universities",
    "ngos",
    
    # Funding
    "yc-companies",
    "producthunt",
    
    # Industry Signals
    "nvd",
    "cisa",
    "space",
    "gdelt",
    "ai_regulation",
    
    # Brazil
    "mdic-regional",
    "fiesp-data",
    
    # Legacy Python (43 collectors)
    "acled-conflicts",
    "brazil-security",
    "world-security",
    "bacen-sgs",
    "central-banks-women",
    "commodity-prices",
    "cni-indicators",
    "electricity-consumption",
    "energy-global",
    "fao-agriculture",
    "ipea-api",
    "mdic-comexstat",
    "port-traffic",
    "semiconductor-sales",
    "socioeconomic-indicators",
    "wto-trade",
    "drugs-data",
    "who-health",
    "religion-data",
    "unicef",
    "un-sdg",
    "world-ngos",
    "women-brazil",
    "women-eurostat",
    "women-fred",
    "women-ilostat",
    "women-world-bank",
    "world-bank-gender",
    "sports-federations",
    "sports-regional",
    "world-sports",
    "careerjet-api",
    "freejobs-api",
    "infojobs-brasil",
    "rapidapi-activejobs",
    "rapidapi-linkedin",
    "serpapi-googlejobs",
    "theirstack-api",
    "hdx-humanitarian",
    "cepal-latam",
    "brazil-ministries",
    "world-tourism"
)

$total = $collectors.Count
$success = 0
$failed = 0
$current = 0

foreach ($collector in $collectors) {
    $current++
    Write-Host "[$current/$total] Running: $collector" -ForegroundColor Yellow
    
    try {
        npx tsx scripts/collect.ts $collector 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Success" -ForegroundColor Green
            $success++
        }
        else {
            Write-Host "  ❌ Failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
            $failed++
        }
    }
    catch {
        Write-Host "  ❌ Error: $_" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "✅ Completed: $success/$total collectors" -ForegroundColor Green
Write-Host "❌ Failed: $failed/$total collectors" -ForegroundColor Red
Write-Host "========================================"
