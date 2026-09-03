# stop_services.ps1 - Stop all ShopBot microservices running on ports 8000-8003
Write-Host "Stopping ShopBot AI microservices..." -ForegroundColor Yellow

$ports = @(8000, 8001, 8002, 8003)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($p in $pids) {
            try {
                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
                Write-Host "  [-] Terminated process $p on port $port" -ForegroundColor Green
            } catch {}
        }
    } else {
        Write-Host "  [.] Port $port is already free" -ForegroundColor DarkGray
    }
}

Write-Host "All ShopBot services stopped." -ForegroundColor Green
