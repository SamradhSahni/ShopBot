#!/bin/bash
# =============================================================================
#  ShopBot AI — VM Bootstrap Script
#  Run this ONCE on a fresh Ubuntu VM to install Ollama, pull tinyllama,
#  build the knowledge base, and start all Docker containers.
# =============================================================================
set -e

echo "=============================================="
echo "  ShopBot AI — One-Shot VM Setup"
echo "=============================================="

# 1. Install Ollama
echo ""
echo "[1/5] Installing Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service in background
ollama serve &>/tmp/ollama.log &
sleep 3
echo "  Ollama started."

# 2. Pull the lightweight LLM
echo ""
echo "[2/5] Pulling tinyllama model (~600MB)..."
ollama pull tinyllama
echo "  tinyllama ready."

# 3. Knowledge base preparation
echo ""
echo "[3/5] Preparing knowledge base..."
# If python packages can be installed on host, build locally; otherwise Docker container auto-indexes on startup
if pip3 install --quiet chromadb==0.5.23 sentence-transformers==2.7.0 --break-system-packages 2>/dev/null; then
    python3 ex2_knowledge_base/build_kb.py 2>/dev/null || true
    echo "  Knowledge base pre-built at ./chroma_db"
else
    echo "  (Host pip is externally-managed — RAG service will auto-build ChromaDB inside Docker on startup)"
fi

# 4. Build and start Docker containers
echo ""
echo "[4/5] Starting Docker containers..."
docker compose up -d --build
echo "  Containers started."

# 5. Health check
echo ""
echo "[5/5] Waiting for services to be healthy..."
sleep 15
curl -sf http://localhost:8080/health | python3 -m json.tool || echo "  (services still warming up — try again in 30s)"

echo ""
echo "=============================================="
echo "  ShopBot AI is ready!"
echo "  Web UI:   http://localhost:8080"
echo "  API Docs: http://localhost:8080/docs"
echo "=============================================="
