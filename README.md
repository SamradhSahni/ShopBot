# 🛒 ShopBot AI — E-Commerce Support Assistant

**ShopBot AI** is an AI-powered customer support application for "TechMart" built with a microservices architecture. It uses a **Retrieval-Augmented Generation (RAG)** pipeline to answer customer queries accurately, grounding responses in actual product data, FAQs, and store policies.

Optimized for **low-RAM environments** (Ubuntu VM / cloud instance with 2–4GB RAM) using:
- **tinyllama** (1.1B LLM — ~600MB RAM via Ollama)
- **all-MiniLM-L6-v2** (80MB sentence-transformers embedding model, runs in-container)
- Memory-limited Docker containers

---

## 🏗️ Architecture

```
Browser ──► App Service :8080 (Orchestrator + Web UI)
                  │                   │
        RAG Service :8011     LLM Service :8012
          (ChromaDB +           (tinyllama via
        Sentence Transformers)   Ollama on Host)
                                      │
                              Ollama :11434 (Host)
```

| Service | Host Port | Container Port | RAM Limit |
|---|---|---|---|
| App Service | 8080 | 8000 | 256 MB |
| RAG Service | 8011 | 8001 | 512 MB |
| LLM Service | 8012 | 8002 | 256 MB |
| Data Service | 8013 | 8003 | 256 MB |

---

## 📋 Prerequisites

- **Ubuntu VM** (or any Linux machine) with at least **2GB RAM** free
- **Docker & Docker Compose** installed
- **Python 3.10+** for building the knowledge base
- **Git** for cloning the repository

---

## 🚀 Complete VM Setup Guide

### Step 1 — Install Dependencies

```bash
# Update apt
sudo apt update && sudo apt install -y git python3 python3-pip curl

# Verify Docker is working
docker --version
docker compose version
```

### Step 2 — Install Ollama

```bash
# Install Ollama (handles its own systemd service)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama as a background service
sudo systemctl enable ollama
sudo systemctl start ollama

# Verify it is running
curl http://localhost:11434/api/tags
```

### Step 3 — Pull the Lightweight LLM

```bash
# tinyllama = 1.1B params, ~637MB download, ~600MB RAM usage
ollama pull tinyllama

# Verify the model is available
ollama list
```

> **Note:** To use a slightly better quality model if you have 4GB+ free RAM, use `phi3:mini` instead:
> ```bash
> ollama pull phi3:mini
> # Then edit docker-compose.yml: DEFAULT_MODEL=phi3:mini
> ```

### Step 4 — Clone the Repository

```bash
git clone https://github.com/SamradhSahni/ShopBot.git
cd ShopBot
```

### Step 5 — Build the Knowledge Base (Optional — Docker Does This Automatically!)

> **💡 Note:** The **RAG Service container automatically indexes the knowledge base on its very first startup**! You can skip directly to **Step 6** without installing any Python packages on your host machine.

If you prefer to build the knowledge base manually on your Ubuntu host VM:

> **Important (Ubuntu PEP 668):** Modern Ubuntu versions block direct `pip install` with `error: externally-managed-environment`. Choose either Option A or Option B:

**Option A — Direct install flag (Quickest):**
```bash
pip3 install chromadb==0.5.23 sentence-transformers==2.7.0 --break-system-packages
python3 ex2_knowledge_base/build_kb.py
```

**Option B — Using a virtual environment (Cleanest):**
```bash
sudo apt install -y python3-venv
python3 -m venv venv
source venv/bin/activate
pip install chromadb==0.5.23 sentence-transformers==2.7.0
python3 ex2_knowledge_base/build_kb.py
deactivate
```

Expected output:
```
  Total chunks to embed: ~44
  Done! Chunks stored in ChromaDB
  KB built successfully!
```

### Step 6 — Start the Microservices

```bash
# Build all Docker images and start containers in background
docker compose up -d --build

# Watch container startup logs (Ctrl+C to exit watching)
docker compose logs -f
```

> **First run note:** The RAG service Docker image downloads and bakes in the `all-MiniLM-L6-v2` model (~80MB) during build. This takes a few minutes but only happens once.

### Step 7 — Verify Everything Is Running

```bash
# Check all containers are healthy
docker compose ps

# Check the aggregate health endpoint
curl -s http://localhost:8080/health | python3 -m json.tool
```

Expected response:
```json
{
  "status": "ok",
  "services": {
    "rag_service": {"status": "ok", ...},
    "llm_service": {"status": "ok", ...},
    "data_service": {"status": "ok", ...}
  }
}
```

### Step 8 — Open the Web UI

Open your browser and navigate to:
👉 **`http://<YOUR_VM_IP>:8080`**

Try asking:
- *"Do you have any waterproof tents under $100?"*
- *"What is the return policy for opened items?"*
- *"What headphones do you recommend for gaming?"*

---

## 🔧 Useful Commands

```bash
# Stop all containers
docker compose down

# Restart a single container
docker compose restart rag-service

# View logs for a specific service
docker compose logs -f llm-service

# Rebuild after code changes
docker compose up -d --build

# Check memory usage of containers
docker stats --no-stream

# Rebuild the knowledge base (if products.json changes)
python3 ex2_knowledge_base/build_kb.py
```

---

## 📂 Project Structure

```text
ShopBot/
├── knowledge_base/            # Source documents (products, FAQs, policies)
│   ├── products.json          # 18 products across 8 categories
│   ├── faqs.md                # 25 frequently asked questions
│   ├── policies.md            # Return, warranty, and shipping policies
│   └── shipping_zones.json    # Shipping zones and rates
│
├── chroma_db/                 # Generated ChromaDB vector store (NOT in git)
│                              # → created by running build_kb.py
│
├── ex2_knowledge_base/        # KB builder scripts
│   ├── build_kb.py            # Run this to (re)build the vector database
│   ├── chunker.py             # Document chunking strategies
│   └── embedder.py            # Sentence-transformers embedding + ChromaDB storage
│
├── ex4_services/              # Microservice source code
│   ├── app_service/           # Web UI + Orchestrator (Port 8080)
│   ├── rag_service/           # Semantic Search (Port 8011)
│   ├── llm_service/           # LLM Generation (Port 8012)
│   └── data_service/          # Raw Data API (Port 8013)
│
├── docker-compose.yml         # Orchestrates all 4 containers
├── setup.sh                   # One-shot VM bootstrap script
└── README.md                  # You are here
```

---

## 🤖 Models Used

| Purpose | Model | Size | RAM Usage |
|---|---|---|---|
| LLM Generation | `tinyllama` (via Ollama) | ~637 MB | ~600 MB |
| Embeddings (RAG) | `all-MiniLM-L6-v2` (sentence-transformers) | ~80 MB | ~150 MB |

---

## ⚙️ Configuration

Environment variables can be changed in `docker-compose.yml`:

| Variable | Service | Default | Description |
|---|---|---|---|
| `DEFAULT_MODEL` | llm-service | `tinyllama` | Ollama model to use for generation |
| `OLLAMA_URL` | llm-service | `http://host.docker.internal:11434` | Ollama host URL |
| `CHROMA_PATH` | rag-service | `/app/chroma_db` | Path to ChromaDB vector store |
| `KB_DIR` | data-service | `/app/knowledge_base` | Path to knowledge base files |
