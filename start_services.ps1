# start_services.ps1 - Start all ShopBot microservices locally (Exercise 4)
# Run from: e:\projects\AIDevops\shopbot\

$ErrorActionPreference = "Stop"
[console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "        Starting ShopBot AI Microservices...            " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot
if (-not $root) {
    $root = "e:\projects\AIDevops\shopbot"
}

# Install dependencies
Write-Host "[*] Checking/installing dependencies..." -ForegroundColor Yellow
pip install fastapi uvicorn requests pydantic httpx chromadb --quiet
Write-Host ""

# Start Data Service (:8003)
Write-Host "[+] Starting Data Service    -> http://localhost:8003" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PYTHONUTF8='1'; Set-Location '$root\ex4_services\data_service'; python main.py" -WindowStyle Normal
Start-Sleep -Seconds 2

# Start RAG Service (:8001)
Write-Host "[+] Starting RAG Service     -> http://localhost:8001" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PYTHONUTF8='1'; Set-Location '$root\ex4_services\rag_service'; python main.py" -WindowStyle Normal
Start-Sleep -Seconds 2

# Start LLM Service (:8002)
Write-Host "[+] Starting LLM Service     -> http://localhost:8002" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PYTHONUTF8='1'; Set-Location '$root\ex4_services\llm_service'; python main.py" -WindowStyle Normal
Start-Sleep -Seconds 3

# Start App Service (:8000)
Write-Host "[+] Starting App Service     -> http://localhost:8000" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PYTHONUTF8='1'; Set-Location '$root\ex4_services\app_service'; python main.py" -WindowStyle Normal
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  All 4 Microservices Launched in Separate Windows!    " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor White
Write-Host "  * App (UI + Orchestrator) : http://localhost:8000"
Write-Host "  * RAG Service             : http://localhost:8001"
Write-Host "  * LLM Service             : http://localhost:8002"
Write-Host "  * Data Service            : http://localhost:8003"
Write-Host ""
Write-Host "Interactive Swagger API Docs:" -ForegroundColor White
Write-Host "  * http://localhost:8000/docs"
Write-Host "  * http://localhost:8001/docs"
Write-Host "  * http://localhost:8002/docs"
Write-Host "  * http://localhost:8003/docs"
Write-Host ""
