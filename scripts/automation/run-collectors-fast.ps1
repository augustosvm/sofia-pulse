# Run All Sofia Pulse Collectors - FAST VERSION
# Pula collectors lentos, timeout de 2 minutos por collector

Write-Host "🚀 Sofia Pulse - Fast Collector Run" -ForegroundColor Cyan
Write-Host "Timeout: 2 minutos por collector"
Write-Host "========================================"
Write-Host ""

$collectors = @(
    # Tech Trends (rápidos)
    "github",
    "hackernews", 
    "stackoverflow",
    
    # Jobs (rápidos)
    "himalayas",
    "remoteok",
    
    # Organizations (rápidos)
    "ai-companies",
    "universities",
    "ngos",
    
    # Funding (rápidos)
    "yc-companies",
    
    # Industry Signals (rápidos)
    "nvd",
    "cisa",
    "gdelt",
    
    # Brazil (rápidos)
    "mdic-regional",
    "fiesp-data",
    
    # Legacy mais importantes (selecionados)
    "energy-global",
    "world-security",
    "commodity-prices",
    "fao-agriculture",
    "women-world-bank",
    "world-sports"
)

$total = $collectors.Count
$success = 0
$failed = 0
$skipped = 0

foreach ($i in 0..($collectors.Count - 1)) {
    $collector = $collectors[$i]
    $current = $i + 1
    
    Write-Host "[$current/$total] $collector" -ForegroundColor Yellow -NoNewline
    
    try {
        $job = Start-Job -ScriptBlock {
            param($c)
            Set-Location "c:\Users\augusto.moreira\Documents\sofia-pulse"
            npx tsx scripts/collect.ts $c 2>&1
        } -ArgumentList $collector
        
        # Wait max 2 minutes
        $completed = Wait-Job $job -Timeout 120
        
        if ($completed) {
            $output = Receive-Job $job
            $exitCode = $job.State
            
            if ($exitCode -eq "Completed") {
                Write-Host " ✅" -ForegroundColor Green
                $success++
            }
            else {
                Write-Host " ❌" -ForegroundColor Red
                $failed++
            }
        }
        else {
            Write-Host " ⏱️ TIMEOUT" -ForegroundColor Yellow
            Stop-Job $job
            $skipped++
        }
        
        Remove-Job $job -Force
        
    }
    catch {
        Write-Host " ❌ ERROR" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "✅ Success: $success" -ForegroundColor Green
Write-Host "❌ Failed: $failed" -ForegroundColor Red  
Write-Host "⏱️ Timeout: $skipped" -ForegroundColor Yellow
Write-Host "========================================"
