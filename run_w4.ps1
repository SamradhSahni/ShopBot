# run_w4.ps1
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8="1"
[console]::OutputEncoding = [System.Text.Encoding]::UTF8
[console]::InputEncoding = [System.Text.Encoding]::UTF8

$root = "e:\projects\AIDevops\shopbot"

function Run-Py($cmd) {
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Command failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Running Week 4 Evaluation...                " -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

Set-Location "$root\evaluation"
Write-Host "1. Running multi-model evaluator (this takes 20-30 mins)..."
Run-Py "python -u evaluator.py --all"

Write-Host "2. Generating analysis report..."
Run-Py "python -u generate_report.py"

Write-Host "3. Running RAG pipeline analysis..."
Run-Py "python -u rag_analysis.py codellama"

Set-Location "$root\ex6_codebase"
Write-Host "4. Indexing codebase..."
Run-Py "python -u codebase_indexer.py --build"
Run-Py "python -u codebase_indexer.py --demo"

Write-Host "==============================================" -ForegroundColor Green
Write-Host "  Complete!                                   " -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

