# ShopBot AI - Complete Project Reference Guide

> **Project:** E-Commerce Product & Policy Support Bot (TechMart)
> **Stack:** Python - FastAPI - Ollama - TinyLlama - sentence-transformers - ChromaDB - Docker
> **Purpose:** This document explains every exercise, every concept, every file, and every command - in plain language.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Key Concepts Explained](#2-key-concepts-explained)
3. [Ubuntu and Linux Command Reference](#3-ubuntu-and-linux-command-reference)
4. [VM Setup and Docker Guide](#4-vm-setup-and-docker-guide)
5. [Week 3 - Building the Pipeline](#5-week-3--building-the-pipeline)
6. [Week 4 - Evaluation and Analysis](#6-week-4--evaluation-and-analysis)
7. [Full File Reference](#7-full-file-reference)
8. [How to Run Everything on VM](#8-how-to-run-everything-on-vm)
9. [Concept to File Map](#9-concept-to-file-map)

---

## 1. Project Overview

**ShopBot AI** is an intelligent customer support assistant for **TechMart**, a fictional online electronics store.
Customers and support agents ask it questions like:

- "What is the warranty on the Dell XPS 15?"
- "Can I return an opened laptop?"
- "How much does express shipping cost?"

The application is progressively built from a simple chat app (W3-E1) all the way to a fully
Dockerised, multi-service, RAG-powered system.

### What Changed for VM / Low-RAM Operation

The original project used **Code Llama (7B)** as its LLM and **nomic-embed-text via Ollama** for embeddings.
For running on Ubuntu VirtualBox VMs with limited RAM (2-4 GB), the following changes were made:

| Area | Before | After | Why |
|---|---|---|---|
| LLM Model | codellama (7B, ~4GB RAM) | tinyllama (1.1B, ~600MB RAM) | 6x smaller, same features |
| Embeddings | nomic-embed-text via Ollama | all-MiniLM-L6-v2 (sentence-transformers) | In-process, 80MB, no Ollama needed |
| Context Window | 2048 tokens | 512 tokens | Reduces KV-cache RAM by 75% |
| Max Tokens | 256 | 128 | Faster, avoids VM freezing |
| CPU Threads | All cores | 2 threads | Keeps desktop responsive |
| Products in KB | 500 products | 18 products | Reduces embed+search time |
| ChromaDB Build | Host Python required | Auto-indexed inside Docker | No host dependencies needed |

---

## 2. Key Concepts Explained

### Ollama
**What it is:** Runs large language models locally - no cloud, no paid API.
**How we use it:** Ollama runs on http://localhost:11434. We send HTTP POST requests with a prompt and get back the LLM response.

### TinyLlama (1.1B)
**What it is:** An open-source LLM with only 1.1 billion parameters - the lightweight alternative to Code Llama (7B).
**RAM usage:** ~600 MB (vs ~4 GB for Code Llama).
**Trade-off:** Shorter, simpler responses. Fine for a support chatbot.

### sentence-transformers (all-MiniLM-L6-v2)
**What it is:** An open-source embedding model that runs directly inside Python - no Ollama needed.
**Size:** 80 MB download.
**Why we switched:** Previously used nomic-embed-text via Ollama, requiring Ollama just for embeddings. Now embeddings run inside the RAG container with zero host dependencies.

### Knowledge Base
A collection of 4 documents containing TechMart information:

- products.json - 18 products with specs, price, warranty, stock
- policies.md - Return policy, warranty, shipping, payment info
- faqs.md - 25 common Q&A pairs
- shipping_zones.json - Domestic and international shipping costs and times

> **Note:** The original project had 500 products. Trimmed to 18 for VM performance.

### Chunking
Breaking large documents into smaller pieces so they can be individually embedded and searched.
Each document type uses a different strategy (per-product, paragraph+overlap, Q&A pair, per-zone).

### ChromaDB
A vector database that stores and searches embeddings (vectors).
- **Storage:** Persisted to disk in chroma_db/ at the project root.
- **Auto-indexing:** If ChromaDB is empty when the RAG service starts, it automatically builds the index from knowledge_base/ inside Docker.

### RAG - Retrieval-Augmented Generation
Before asking the LLM a question, first RETRIEVE relevant documents and provide them as context.

Full pipeline:
1. User asks a question
2. RAG service embeds the question using all-MiniLM-L6-v2 (inside container)
3. ChromaDB returns the top-3 most similar knowledge chunks
4. App service sends (context + question) to the LLM service
5. LLM service calls Ollama on the host (TinyLlama)
6. Response returned to browser with source citations

**Without RAG:** LLM guesses from training data - often wrong or hallucinated
**With RAG:** LLM sees actual TechMart policies - accurate, grounded responses

### FastAPI
A Python web framework for building REST APIs. Every ShopBot service is a FastAPI app.
Auto-docs available at /docs on each service port.

### Docker
Packages an app with all its dependencies into a container that runs the same on any machine.
Docker Compose defines and runs all 4 services together.

---

## 3. Ubuntu and Linux Command Reference

### Why sudo?

`sudo` stands for **"superuser do"**. On Linux, administrative operations (installing software, modifying system files, managing services, running Docker) are restricted to the `root` (administrator) user.

Adding `sudo` before a command temporarily grants root privileges for just that one command. This is safer than being permanently logged in as root.

```bash
# Without sudo - permission denied
docker compose up      # Error: permission denied

# With sudo - works fine
sudo docker compose up

# Permanently fix Docker permissions (do once, then relogin):
sudo usermod -aG docker $USER
newgrp docker
# After this, docker commands work without sudo
```

---

### Package Management (apt)

`apt` is the Ubuntu package manager - it installs, updates, and removes software.

| Command | What It Does | When to Use |
|---|---|---|
| `sudo apt update` | Downloads latest list of available packages from Ubuntu servers | Run FIRST before any install |
| `sudo apt upgrade` | Installs newer versions of already-installed packages | Periodically to keep system patched |
| `sudo apt install -y git curl` | Installs git and curl (-y auto-confirms) | When you need a new tool |
| `sudo apt remove git` | Uninstalls a package | When removing software |
| `sudo apt autoremove` | Removes orphan packages no longer needed | Frees disk space |
| `sudo apt clean` | Deletes downloaded .deb installer files from cache | Frees disk space (safe anytime) |

```bash
# Typical first-time VM setup:
sudo apt update
sudo apt install -y git curl python3 python3-pip python3-venv
```

---

### File and Directory Commands

| Command | What It Does | Example |
|---|---|---|
| `ls` | List files in current directory | `ls` |
| `ls -lh` | List with file sizes (human readable) | `ls -lh` |
| `pwd` | Print current directory path | `pwd` |
| `cd folder` | Change into a directory | `cd shopbot` |
| `cd ~` | Go to your home directory | `cd ~` |
| `cd ..` | Go up one directory | `cd ..` |
| `mkdir name` | Create a new directory | `mkdir myproject` |
| `rm file` | Delete a file | `rm old.log` |
| `rm -rf folder` | Delete a folder and all contents | `rm -rf shopbot_old` |
| `cp src dest` | Copy a file | `cp a.txt b.txt` |
| `mv src dest` | Move or rename a file | `mv old.txt new.txt` |
| `cat file` | Show file contents | `cat docker-compose.yml` |
| `df -h` | Show disk space usage | `df -h /` |
| `free -h` | Show RAM and swap usage | `free -h` |
| `du -sh folder` | Show folder size | `du -sh ~/.cache` |

---

### Process and System Commands

| Command | What It Does | Example |
|---|---|---|
| `top` or `htop` | Live CPU and RAM usage dashboard | `htop` |
| `ps aux` | List all running processes | `ps aux` |
| `kill PID` | Terminate a process by its ID | `kill 12345` |
| Ctrl + C | Stop a running command in the terminal | - |
| Ctrl + Z | Pause a running process | - |
| `fg` | Resume a paused process | `fg` |
| `command &` | Run a command in the background | `ollama serve &` |

---

### Systemd Service Commands (for Ollama)

`systemd` is Ubuntu's service manager. Ollama installs itself as a systemd service.

| Command | What It Does |
|---|---|
| `sudo systemctl start ollama` | Start the Ollama service |
| `sudo systemctl stop ollama` | Stop the Ollama service |
| `sudo systemctl restart ollama` | Restart (applies config changes) |
| `sudo systemctl status ollama` | Check if Ollama is running |
| `sudo systemctl enable ollama` | Auto-start Ollama on boot |
| `sudo journalctl -u ollama -n 50` | Show last 50 log lines from Ollama |

---

### Networking Commands

| Command | What It Does |
|---|---|
| `curl http://localhost:8080/health` | Test if a web service is responding |
| `ip addr` or `hostname -I` | Show your VM's IP address |
| `ping 8.8.8.8` | Test internet connectivity |
| `sudo ss -tlnp` | List all open ports and listening services |

---

### Git Commands

| Command | What It Does |
|---|---|
| `git clone URL` | Download a repository from GitHub |
| `git pull` | Download and apply latest changes |
| `git status` | Show what files have changed locally |
| `git log --oneline -5` | Show last 5 commits |
| `git add -A` | Stage all changes for commit |
| `git commit -m "message"` | Save staged changes with a description |
| `git push origin main` | Upload commits to GitHub |

---

### Disk Space Management

Low disk space is the most common VM problem. Run these to reclaim space:

```bash
# 1. How much space do I have?
df -h /

# 2. What is using the most space?
du -sh ~/shopbot_old ~/.cache /tmp/* 2>/dev/null | sort -h

# 3. Clean Docker build cache (usually frees 3-10 GB)
sudo docker system prune -af

# 4. Clean apt package cache
sudo apt clean && sudo apt autoremove -y

# 5. Clean pip download cache
rm -rf ~/.cache/pip

# 6. Shrink system logs to 50MB
sudo journalctl --vacuum-size=50M
```

---

### Swap Memory (Virtual RAM)

Swap allows Linux to use disk space as emergency RAM when physical RAM runs out.
Adding swap prevents the VM from freezing when Ollama runs inference.

```bash
# Create a 1GB swap file (safe on any VM with 5GB+ disk)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make swap permanent across reboots
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify swap is active
free -h
# Under "Swap:" you will see 1.0Gi available
```

---

## 4. VM Setup and Docker Guide

### Why Docker on the VM?

On Ubuntu 24+, `pip install` is blocked for system Python (PEP 668 - externally-managed-environment).
Building packages like `chromadb` or `sentence-transformers` from source takes 20+ minutes and often fails.

**Docker solves this** by using Python 3.11 inside containers, where pre-built wheel files exist and install in seconds. You never need to install Python packages on your Ubuntu host.

### Why host.docker.internal?

Docker containers run in an isolated network. When `llm-service` inside Docker needs to talk to Ollama on the Ubuntu host (port 11434), it cannot use `localhost` (which refers to the container itself, not the host).

`host.docker.internal` is a special hostname Docker resolves to the host machine's IP. On Linux this requires adding to docker-compose.yml:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### Why Configure OLLAMA_HOST=0.0.0.0?

By default on Linux, Ollama only listens on 127.0.0.1 (loopback). Docker containers connect from a different network so they cannot reach it.

Setting `OLLAMA_HOST=0.0.0.0` tells Ollama to listen on all network interfaces:

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0"\n' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

---

## 5. Week 3 - Building the Pipeline

### W3-E1 - Basic LLM Application

**Goal:** Build the simplest working chat app that talks to an LLM.
**Concepts:** Ollama, TinyLlama, FastAPI, REST API, System Prompt

Pipeline:
```
User types question --> Browser --> FastAPI /chat --> Ollama API --> TinyLlama --> Response
```

| Concept | Explanation | File |
|---|---|---|
| System Prompt | Hidden instruction telling TinyLlama it is ShopBot | ex1_basic/prompts.py |
| Ollama Client | Python wrapper around Ollama REST API with timing | ex1_basic/ollama_client.py |
| FastAPI App | /chat, /health, / (UI) endpoints | ex1_basic/app.py |
| Chat UI | Dark-themed browser chat with model selector + stats | ex1_basic/index.html |

**At this stage:** LLM has NO TechMart knowledge - answers from training data (often inaccurate).

---

### W3-E2 - Knowledge Base (Chunking + Embeddings)

**Goal:** Create TechMart knowledge base from documents and store as vector embeddings in ChromaDB.
**Concepts:** Chunking, Embeddings, Vector Representation, ChromaDB, sentence-transformers

Pipeline:
```
Documents (JSON/Markdown) --> Chunker --> Text Chunks --> all-MiniLM-L6-v2 --> Vectors --> ChromaDB
```

Knowledge base breakdown (~44 total chunks):
- products.json: 18 products (18 chunks)
- policies.md: Return/warranty/shipping/payment policies (~12 chunks)
- faqs.md: 25 customer Q&A pairs
- shipping_zones.json: Domestic + international zones (~9 chunks)

---

### W3-E3 - RAG Pipeline

**Goal:** Find relevant chunks for each user question and provide as context to TinyLlama.
**Concepts:** RAG, Vector Similarity Search, Cosine Similarity, Context Injection, Hallucination Prevention

RAG vs No-RAG example:

| Question | Without RAG | With RAG |
|---|---|---|
| "Warranty on Dell XPS 15?" | "Usually 1-3 years" [guess] | "2 years mfr warranty" [exact] |
| "How much is express shipping?" | "$5-15 typically" [guess] | "$9.99 for 2-3 days" [exact] |
| "Can I return an opened laptop?" | "Depends on policy" [vague] | "Yes, 30 days if resalable" [exact] |

---

### W3-E4 - APIs, Services and Orchestration

**Goal:** Split the monolith into 4 microservices communicating via REST APIs.
**Concepts:** Microservices, REST APIs, Orchestration, FastAPI, httpx (async HTTP)

Architecture:
```
Browser --> [App Service :8080] (Orchestrator)
                |                      |
      [RAG Service :8001]    [Data Service :8003]
                |
      [LLM Service :8002]
                |
        Ollama :11434 (on HOST machine)
```

Service details:

| Service | Host Port | RAM Limit | Role |
|---|---|---|---|
| App Service | 8080 | 256 MB | Orchestrator: receives request, calls RAG+LLM, returns result |
| RAG Service | 8011 | 512 MB | POST /retrieve: embed question + ChromaDB search + context |
| LLM Service | 8012 | 256 MB | POST /generate: wraps Ollama, supports model switching |
| Data Service | 8013 | 256 MB | GET /products /policies /faqs /shipping |

Orchestration flow:
```
User: "Warranty on Dell XPS 15?"
Step 1: App Service receives POST /chat
Step 2: App Service --> POST rag-service:8001/retrieve --> gets 3 chunks + citations
Step 3: App Service --> POST llm-service:8002/generate (context + question)
Step 4: LLM Service --> POST host.docker.internal:11434/api/generate (Ollama on host)
Step 5: Response flows back to Browser (with source badges)
```

---

### W3-E5 - Docker

**Goal:** Containerise every service. Show the complete application works through Docker.
**Concepts:** Docker, Docker Compose, Dockerfile, Containers, Volumes, Networks, Health Checks

Key Docker Compose features:

| Feature | How We Use It |
|---|---|
| Named Network | shopbot-net: containers find each other by service name |
| Health Checks | Each service checks /health; App waits until all 3 deps are healthy |
| depends_on | App Service waits for RAG + LLM + Data |
| Volume Mounts | ./chroma_db and ./knowledge_base mounted into RAG service |
| Environment Vars | Service URLs injected via env vars (RAG_SERVICE_URL, OLLAMA_URL) |
| extra_hosts | host.docker.internal:host-gateway enables Linux containers to reach host Ollama |
| Memory Limits | Each container capped at 256-512 MB to prevent VM OOM crashes |

**Auto-indexing on startup:**
The RAG service detects on startup if ChromaDB is empty and automatically builds it from the mounted
knowledge_base/ directory. No host Python or pip required.

---

## 6. Week 4 - Evaluation and Analysis

### W4-E1 - Multi-Model Evaluation

**Goal:** Evaluate the same application with different LLMs. Everything else stays identical.
**Concepts:** Model comparison, LLM benchmarking, controlled experiment design

Models for comparison:

| Model | Ollama Name | Params | Notes |
|---|---|---|---|
| TinyLlama | tinyllama | 1.1B | Default for VM (low RAM) |
| Phi-3 Mini | phi3:mini | 3.8B | Better quality, needs 4GB+ RAM |
| Qwen2 | qwen2:0.5b | 0.5B | Ultra-lightweight, fastest |

### W4-E2 - Evaluation Dataset

**Goal:** 25 representative real-world questions used for all models.
**File:** evaluation/questions.json

5 categories (5 questions each): Product Information, Return Policy, Shipping, Cross-domain, Hallucination Traps.

### W4-E3 - Quantitative Evaluation

**Goal:** Measure each model on 8 metrics across 25 questions.
**File:** evaluation/evaluator.py

Quality Metrics: Correctness, Relevance, Retrieval Quality, Hallucination Rate
Performance Metrics: Response Latency, LLM Latency, Token Usage, Memory Usage

### W4-E4 - Results Analysis

**Goal:** Analyse results and draw evidence-based conclusions about trade-offs.
**Files:** evaluation/generate_report.py --> evaluation/analysis_report.md

### W4-E5 - RAG Pipeline Analysis

**Goal:** Trace 10 specific questions through the pipeline and classify each outcome.
**Files:** evaluation/rag_analysis.py --> evaluation/rag_analysis_report.md

### W4-E6 - Codebase Understanding

**Goal:** Use ShopBot's own LLM+RAG to answer questions ABOUT ShopBot's own source code.
**File:** ex6_codebase/codebase_indexer.py

---

## 7. Full File Reference

```
shopbot/
|
+-- knowledge_base/                     Shared docs (all exercises use these)
|   +-- products.json                   18 TechMart products (trimmed from 500 for VM)
|   +-- policies.md                     Return, warranty, shipping, payment policies
|   +-- faqs.md                         25 customer Q&A pairs
|   +-- shipping_zones.json             Shipping costs and times
|
+-- ex1_basic/                          W3-E1: Basic LLM Chat App
|   +-- prompts.py
|   +-- ollama_client.py
|   +-- app.py
|   +-- index.html
|   +-- requirements.txt
|
+-- ex2_knowledge_base/                 W3-E2: Chunking + Embeddings + ChromaDB
|   +-- chunker.py
|   +-- embedder.py                     sentence-transformers embeddings to ChromaDB
|   +-- build_kb.py
|   +-- requirements.txt
|
+-- ex3_rag/                            W3-E3: Full RAG Pipeline
|   +-- retriever.py
|   +-- rag_pipeline.py
|   +-- compare_demo.py
|   +-- app.py
|
+-- ex4_services/                       W3-E4+E5: Microservices + Docker
|   +-- app_service/
|   |   +-- main.py                     Orchestrator
|   |   +-- index.html                  Chat UI (TinyLlama default, shows RAG citations)
|   |   +-- Dockerfile
|   |   +-- requirements.txt
|   +-- rag_service/
|   |   +-- main.py                     POST /retrieve: all-MiniLM-L6-v2 + ChromaDB
|   |   +-- chunker.py                  Used at startup for auto-KB-build
|   |   +-- Dockerfile                  CPU-only torch + sentence-transformers
|   |   +-- requirements.txt
|   +-- llm_service/
|   |   +-- main.py                     POST /generate: Ollama wrapper (tinyllama)
|   |   +-- Dockerfile
|   |   +-- requirements.txt
|   +-- data_service/
|       +-- main.py                     GET /products /policies /faqs /shipping
|       +-- Dockerfile
|       +-- requirements.txt
|
+-- chroma_db/                          Vector DB (auto-created at runtime, gitignored)
+-- docker-compose.yml                  4 containers + memory limits + network
+-- setup.sh                            VM one-shot bootstrap script
+-- .gitignore
+-- .dockerignore
+-- README.md
+-- PROJECT_REFERENCE.md               THIS FILE
|
+-- evaluation/
|   +-- questions.json                  25 Q&A with ground truth + trap flags
|   +-- evaluator.py                    8-metric evaluator across models
|   +-- generate_report.py             Results JSON --> analysis_report.md
|   +-- rag_analysis.py                Trace 10 Q->Context->Response examples
|   +-- results/
|       +-- tinyllama_results.json
|
+-- ex6_codebase/
    +-- codebase_indexer.py            Index .py files + cross-file Q&A via LLM
```

---

## 8. How to Run Everything on VM

### First-Time VM Setup (run in order)

```bash
# Step 1: Install basic tools
sudo apt update && sudo apt install -y git curl

# Step 2: Install Ollama (handles its own service)
curl -fsSL https://ollama.ai/install.sh | sh

# Step 3: Configure Ollama to accept Docker connections
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0"\n' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload && sudo systemctl restart ollama

# Step 4: Download the lightweight LLM
ollama pull tinyllama

# Step 5: Add yourself to docker group (so sudo not needed every time)
sudo usermod -aG docker $USER
newgrp docker

# Step 6: Add swap memory (prevents VM crashes during inference)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Step 7: Clone the repository
git clone https://github.com/SamradhSahni/ShopBot.git shopbot
cd shopbot

# Step 8: Start everything (ChromaDB auto-builds on first start)
docker compose up -d --build
```

### Daily Usage

```bash
# Check all containers are running
docker compose ps

# Start stopped containers (no rebuild)
docker compose up -d

# Get latest code changes and rebuild
git pull && docker compose up -d --build

# Check health endpoint
curl -s http://localhost:8080/health

# Watch live logs from a specific service
docker compose logs -f rag-service
docker compose logs -f llm-service

# Stop all containers
docker compose down

# Free up disk space (Docker build cache)
docker system prune -af
```

### Test Queries via curl

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the return policy?"}'
```

Or open the web UI: **http://localhost:8080**

---

## 9. Concept to File Map

| Concept | First Used | Key Files |
|---|---|---|
| Ollama API call | W3-E1 | ex1_basic/ollama_client.py |
| System prompt | W3-E1 | ex1_basic/prompts.py |
| FastAPI REST endpoint | W3-E1 | ex1_basic/app.py |
| Document chunking | W3-E2 | ex2_knowledge_base/chunker.py |
| sentence-transformers embeddings | W3-E2 | ex2_knowledge_base/embedder.py |
| ChromaDB storage | W3-E2 | ex2_knowledge_base/embedder.py |
| Cosine similarity search | W3-E3 | ex3_rag/retriever.py |
| RAG prompt building | W3-E3 | ex3_rag/rag_pipeline.py |
| RAG vs No-RAG comparison | W3-E3 | ex3_rag/compare_demo.py |
| Microservice separation | W3-E4 | ex4_services/*/main.py |
| Service orchestration | W3-E4 | ex4_services/app_service/main.py |
| Async inter-service HTTP | W3-E4 | ex4_services/app_service/main.py (httpx) |
| Dockerfile | W3-E5 | ex4_services/*/Dockerfile |
| Docker Compose | W3-E5 | docker-compose.yml |
| Docker health checks | W3-E5 | docker-compose.yml |
| host.docker.internal | W3-E5 | docker-compose.yml (extra_hosts) |
| Container memory limits | W3-E5 | docker-compose.yml (deploy.resources) |
| Auto ChromaDB indexing | W3-E5 | ex4_services/rag_service/main.py |
| TinyLlama model | VM Optimization | ex4_services/llm_service/main.py |
| CPU thread limiting | VM Optimization | ex4_services/llm_service/main.py (num_thread) |
| Multi-model switching | W4-E1 | ex4_services/llm_service/main.py |
| Evaluation dataset | W4-E2 | evaluation/questions.json |
| Correctness metric | W4-E3 | evaluation/evaluator.py |
| Hallucination detection | W4-E3 | evaluation/evaluator.py |
| Report generation | W4-E4 | evaluation/generate_report.py |
| RAG trace analysis | W4-E5 | evaluation/rag_analysis.py |
| Code chunking by function | W4-E6 | ex6_codebase/codebase_indexer.py |
| Cross-file codebase Q&A | W4-E6 | ex6_codebase/codebase_indexer.py |
