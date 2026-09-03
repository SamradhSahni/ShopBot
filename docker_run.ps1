# docker_run.ps1 - Build and run ShopBot with Docker Compose (Exercise 5)
# Run from: e:\projects\AIDevops\shopbot\

$ErrorActionPreference = "Stop"
[console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  ShopBot AI - Exercise 5: Docker Deployment      " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot
if (-not $root) {
    $root = "e:\projects\AIDevops\shopbot"
}

# Free local ports 8000-8003 if local microservices from start_services.ps1 are running
Write-Host "[*] Checking for port conflicts on 8000-8003..." -ForegroundColor Yellow
$localPorts = @(8000, 8001, 8002, 8003)
foreach ($p in $localPorts) {
    $conns = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pidToKill in $pids) {
            try {
                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                Write-Host "    Freed local port $p (stopped PID $pidToKill)" -ForegroundColor DarkGray
            } catch {}
        }
    }
}

# Step 1: Build images
Write-Host ""
Write-Host "[+] Step 1: Building Docker images..." -ForegroundColor Yellow
docker compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Docker build failed. Check Dockerfiles." -ForegroundColor Red
    exit 1
}

# Step 2: Start Ollama container and pull models
Write-Host ""
Write-Host "[+] Step 2: Starting Ollama container..." -ForegroundColor Yellow
docker compose up -d ollama

Write-Host "    Waiting for Ollama to become healthy..."
$retries = 0
while ($retries -lt 15) {
    $status = docker inspect --format="{{.State.Health.Status}}" shopbot-ollama 2>$null
    if ($status -eq "healthy") {
        Write-Host "    Ollama is ready!" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
    $retries++
}

Write-Host "    Pulling codellama into Ollama container..."
docker exec shopbot-ollama ollama pull codellama
Write-Host "    Pulling nomic-embed-text into Ollama container..."
docker exec shopbot-ollama ollama pull nomic-embed-text

# Step 3: Start RAG service and populate ChromaDB
Write-Host ""
Write-Host "[+] Step 3: Preparing ChromaDB knowledge base in RAG service..." -ForegroundColor Yellow
docker compose up -d rag-service
Start-Sleep -Seconds 3

# Fast sync pre-built knowledge base into container
$hostChroma = Join-Path $root "ex2_knowledge_base\chroma_db"
if (Test-Path $hostChroma) {
    Write-Host "    Syncing pre-indexed ChromaDB (500 products) into shopbot-rag..." -ForegroundColor Green
    docker exec shopbot-rag mkdir -p /app/chroma_db
    docker cp "$hostChroma\." shopbot-rag:/app/chroma_db/
}

# Step 4: Start all services
Write-Host ""
Write-Host "[+] Step 4: Starting all remaining microservices..." -ForegroundColor Yellow
docker compose up -d
Start-Sleep -Seconds 5

# Step 5: Show status
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Service Status:                                 " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
docker compose ps

Write-Host ""
Write-Host "ShopBot is running in Docker!" -ForegroundColor Green
Write-Host ""
Write-Host "Web Application:" -ForegroundColor White
Write-Host "  * Storefront & Chat UI : http://localhost:8000"
Write-Host ""
Write-Host "Service APIs & Docs:" -ForegroundColor White
Write-Host "  * App Service API      : http://localhost:8000/docs"
Write-Host "  * RAG Service API      : http://localhost:8001/docs"
Write-Host "  * LLM Service API      : http://localhost:8002/docs"
Write-Host "  * Data Service API     : http://localhost:8003/docs"
Write-Host ""
Write-Host "Helpful Commands:" -ForegroundColor White
Write-Host "  * Stream logs : docker compose logs -f"
Write-Host "  * Stop all    : docker compose down"
Write-Host ""
