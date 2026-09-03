# run_week4.ps1 - Master runner for all Week 4 exercises
# Run from: e:\projects\AIDevops\shopbot\

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "        ShopBot AI - Week 4 Evaluation Suite          " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

$root = "e:\projects\AIDevops\shopbot"

# Prerequisites
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install psutil chromadb httpx --quiet
Write-Host ""

# Pull additional models
Write-Host "Pulling evaluation models (this may take a while)..." -ForegroundColor Yellow
Write-Host "   Pulling starcoder2..."
ollama pull starcoder2
Write-Host "   Pulling deepseek-coder..."
ollama pull deepseek-coder
Write-Host ""

# W4-E2: Show evaluation dataset
Write-Host "----------------------------------------------" -ForegroundColor White
Write-Host "  W4-E2: Evaluation Dataset (25 questions)" -ForegroundColor Green
Write-Host "----------------------------------------------" -ForegroundColor White
python -c "import json; qs = json.load(open('$root/evaluation/questions.json', encoding='utf-8')); from collections import Counter; cats = Counter(q['category'] for q in qs); print(f'Total questions: {len(qs)}'); [print(f'  {cat}: {count}') for cat, count in cats.items()]"
Write-Host ""

# W4-E1 + E3: Run evaluation for all 3 models
Write-Host "----------------------------------------------" -ForegroundColor White
Write-Host "  W4-E1 + E3: Multi-Model Evaluation" -ForegroundColor Green
Write-Host "----------------------------------------------" -ForegroundColor White
Write-Host "  Running all 3 models against 25 questions..."
Set-Location "$root\evaluation"
python evaluator.py --all
Write-Host ""

# W4-E4: Generate analysis report
Write-Host "----------------------------------------------" -ForegroundColor White
Write-Host "  W4-E4: Generating Analysis Report" -ForegroundColor Green
Write-Host "----------------------------------------------" -ForegroundColor White
python generate_report.py
Write-Host ""

# W4-E5: RAG pipeline analysis
Write-Host "----------------------------------------------" -ForegroundColor White
Write-Host "  W4-E5: RAG Pipeline Analysis (10 traced examples)" -ForegroundColor Green
Write-Host "----------------------------------------------" -ForegroundColor White
python rag_analysis.py codellama
Write-Host ""

# W4-E6: Build codebase index and run demo
Write-Host "----------------------------------------------" -ForegroundColor White
Write-Host "  W4-E6: Codebase Understanding" -ForegroundColor Green
Write-Host "----------------------------------------------" -ForegroundColor White
Set-Location "$root\ex6_codebase"
python codebase_indexer.py --build
python codebase_indexer.py --demo
Write-Host ""

Write-Host "======================================================" -ForegroundColor Green
Write-Host "  Week 4 Complete! Output files:                      " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  evaluation/results/codellama_results.json"
Write-Host "  evaluation/results/starcoder2_results.json"
Write-Host "  evaluation/results/deepseek-coder_results.json"
Write-Host "  evaluation/analysis_report.md"
Write-Host "  evaluation/rag_analysis_report.md"
Write-Host "  ex6_codebase/codebase_qa_results.json"
Write-Host ""
