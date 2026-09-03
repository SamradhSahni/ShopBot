# 🛒 ShopBot AI — E-Commerce Support Assistant

**ShopBot AI** is an advanced, AI-powered customer support microservices application built for "TechMart". It utilizes a state-of-the-art **Retrieval-Augmented Generation (RAG)** pipeline to answer customer queries accurately by grounding responses in the store's actual product catalog, FAQs, and policies, drastically reducing AI hallucinations.

This project is built using a modern AI stack: **FastAPI, ChromaDB, Ollama (Llama 3 / Code Llama), Sentence Transformers, and Docker**.

---

## 🏗️ Architecture Overview

The system runs on a microservices architecture orchestrated by Docker Compose:

1. **App Service (`:8080`)**: The frontend orchestrator. Serves the web-based Chat UI and handles the core pipeline logic between RAG and LLM services.
2. **RAG Service (`:8011`)**: The semantic search engine. Embeds user queries and performs fast vector similarity searches against ChromaDB to find relevant knowledge chunks.
3. **LLM Service (`:8012`)**: The generation engine. Communicates with your local Ollama instance to stream intelligent, conversational responses.
4. **Data Service (`:8013`)**: The catalog backend. Provides raw REST API access to products, policies, and shipping information.

```mermaid
flowchart TD
    User((User Browser)) <-->|HTTP :8080| AppService[App Service\n(UI + Orchestrator)]
    
    AppService <-->|Internal API| RAGService[RAG Service\n(Vector Search)]
    AppService <-->|Internal API| DataService[Data Service\n(Raw JSON/MD)]
    AppService <-->|Internal API| LLMService[LLM Service\n(Prompt Gen)]
    
    RAGService <--> ChromaDB[(ChromaDB)]
    LLMService <--> Ollama[(Local Ollama Host\n:11434)]
```

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your host machine:

1. **[Git](https://git-scm.com/)** - For cloning the repository.
2. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** - Ensure the Docker Engine is running and WSL2 integration is enabled (if on Windows).
3. **[Ollama](https://ollama.ai/)** - Must be installed and running locally on your host machine.

### Model Requirements
Once Ollama is running, open your terminal and pull the required models:
```bash
ollama pull llama3
ollama pull nomic-embed-text
```

---

## 🚀 Step-by-Step Running Guide

Follow these steps to clone, build, and run ShopBot AI locally.

### 1. Clone the Repository
```bash
git clone https://github.com/SamradhSahni/ShopBot.git
cd ShopBot
```

### 2. Build the Knowledge Base (Optional but recommended)
If you need to re-index the 500+ products into ChromaDB for the first time:
```bash
# Requires Python 3.10+
pip install -r ex2_knowledge_base/requirements.txt
python ex2_knowledge_base/build_kb.py
```
*(Note: A pre-built `chroma_db` folder might already be included in the repository depending on your branch).*

### 3. Start the Microservices
Ensure Docker Desktop is open and the engine is running (green indicator). Then, in the root `shopbot/` directory, run:
```bash
docker compose up -d --build
```
This will build the Docker images for all 4 microservices and start them in the background. It maps them safely to host ports to avoid conflicts with your local system.

### 4. Access the Application
Once the containers report as `Started`, open your web browser and go to:

👉 **[http://localhost:8080](http://localhost:8080)**

You can now chat with ShopBot! Ask questions like:
- *"I need a durable camping tent for 4 people"*
- *"What is the battery life of the Pro Wireless Mouse?"*
- *"Do you have any noise-canceling headphones under $150?"*

### 5. Accessing the Backend APIs (Swagger UI)
If you wish to test the individual microservices, each comes with an interactive OpenAPI (Swagger) interface:
* **App Orchestrator:** [http://localhost:8080/docs](http://localhost:8080/docs)
* **RAG Service:** [http://localhost:8011/docs](http://localhost:8011/docs)
* **LLM Service:** [http://localhost:8012/docs](http://localhost:8012/docs)
* **Data Service:** [http://localhost:8013/docs](http://localhost:8013/docs)

---

## 🛑 Stopping the Application

To gracefully stop the containers and release the ports, run:
```bash
docker compose down
```

If you wish to completely wipe the Docker volumes (like the persistent ChromaDB storage), you can run:
```bash
docker compose down -v
```

---

## 📂 Project Structure

```text
shopbot/
├── knowledge_base/          # Shared knowledge documents (Products, FAQs, Policies)
├── chroma_db/               # Persistent Vector Database storage
├── ex2_knowledge_base/      # Scripts for Chunking + Embeddings + ChromaDB indexing
├── ex3_rag/                 # Retrieval + RAG Pipeline standalone tests
├── ex4_services/            # Microservices Architecture source code
│   ├── app_service/         # Frontend Web UI & Orchestrator
│   ├── data_service/        # Static knowledge API
│   ├── llm_service/         # LLM Generation wrapper
│   └── rag_service/         # Semantic Search wrapper
├── docker-compose.yml       # Docker orchestration configuration
└── README.md                # Project documentation (You are here!)
```
