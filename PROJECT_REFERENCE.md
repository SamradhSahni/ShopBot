# ShopBot AI — Complete Project Reference Guide

> **Project:** E-Commerce Product & Policy Support Bot (TechMart)
> **Stack:** Python · FastAPI · Ollama · Code Llama · ChromaDB · Docker
> **Purpose:** This document explains every exercise, every concept, and every file — in plain language.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Key Concepts Explained](#2-key-concepts-explained)
3. [Week 3 — Building the Pipeline](#3-week-3)
4. [Week 4 — Evaluation and Analysis](#4-week-4)
5. [Full File Reference](#5-full-file-reference)
6. [How to Run Everything](#6-how-to-run)
7. [Concept to File Map](#7-concept-to-file-map)

---

## 1. Project Overview

**ShopBot AI** is an intelligent customer support assistant for **TechMart**, a fictional online electronics store.
Customers and support agents ask it questions like:

- "What is the warranty on the Dell XPS 15?"
- "Can I return an opened laptop?"
- "How much does express shipping cost?"

The application is progressively built from a simple chat app (W3-E1) all the way to a fully
Dockerised, multi-service, RAG-powered system evaluated across 3 LLM models (W4).

---

## 2. Key Concepts Explained

### Ollama
**What it is:** Runs large language models locally on your machine — no cloud, no paid API.
**How we use it:** Ollama runs on http://localhost:11434. We send HTTP POST requests with a prompt and get back the LLM response.
**Why it matters:** Lets us run Code Llama, StarCoder2, and DeepSeek-Coder locally for free.

  Your App  -->  POST /api/generate  -->  Ollama  -->  Code Llama  -->  Response text

### Code Llama (and other LLMs)
**What it is:** A large language model by Meta, specialised in code and structured text. Good at reading JSON and Markdown — perfect for an e-commerce support bot.
**Other models used for comparison:**
- starcoder2 — Code model by HuggingFace/ServiceNow
- deepseek-coder — Code model by DeepSeek, strong at reasoning

### Knowledge Base
**What it is:** A collection of 4 documents containing all real TechMart information.

  products.json       - 18 products with specs, price, warranty, stock
  policies.md         - Return policy, warranty, shipping, payment info
  faqs.md             - 25 common Q&A pairs
  shipping_zones.json - Domestic and international shipping costs and times

### Chunking
**What it is:** Breaking large documents into smaller pieces so they can be individually embedded and searched.
**Why we need it:** LLMs have a limited context window. We cannot feed the entire knowledge base for every question. We find only RELEVANT chunks and feed those.

  Document Type       Strategy                    Why
  products.json       One chunk per product        Already atomic — splitting loses context
  policies.md         Paragraph + 50-char overlap  Preserves sentence boundaries
  faqs.md             One chunk per Q&A pair       Each pair is self-contained
  shipping_zones.json One chunk per shipping zone  Each zone has independent pricing

### Embeddings
**What it is:** Converting text into a list of numbers (a vector) that represents its MEANING. Similar texts produce similar vectors.
**Model used:** nomic-embed-text (via Ollama)
**How it works:**

  "What is the return policy?"  -->  [0.12, -0.45, 0.78, ...]   (768 numbers)
  "Can I return a product?"     -->  [0.11, -0.43, 0.76, ...]   (very similar!)
  "How much is shipping?"       -->  [0.89,  0.22, -0.11, ...]  (very different)

### ChromaDB
**What it is:** A vector database — stores and searches embeddings (vectors).
**How we use it:** Store all knowledge base chunk embeddings. When a user asks a question, search for the most similar chunks.
**Similarity measure:** Cosine similarity — score of 1.0 = identical meaning, 0.0 = completely unrelated.
**Storage:** Persisted to disk in ex2_knowledge_base/chroma_db/

### RAG — Retrieval-Augmented Generation
**What it is:** Before asking the LLM a question, first RETRIEVE relevant documents and provide them as context.
**The full pipeline:**

  User Question
       |
  Embed the question (nomic-embed-text)
       |
  Search ChromaDB --> Top 3 most similar chunks
       |
  Build context string from those chunks
       |
  Send (context + question) to Code Llama
       |
  LLM generates answer GROUNDED in real store data
       |
  Response

**Without RAG:** LLM guesses from training data --> often wrong or hallucinated
**With RAG:** LLM sees actual TechMart policies --> accurate, grounded response

### FastAPI
**What it is:** A Python web framework for building REST APIs — fast, automatic documentation.
**How we use it:** Every ShopBot service is a FastAPI app. Auto-docs at /docs.

### Docker
**What it is:** Packages an app with all dependencies into a container — runs the same on any machine.
**Docker Compose:** Defines and runs multiple containers together.
**How we use it:** Each service (App, RAG, LLM, Data, Ollama) runs in its own container on a shared network.

---

## 3. Week 3 — Building the Pipeline

### W3-E1 — Basic LLM Application

**Goal:** Build the simplest working chat app that talks to Code Llama.
**Concepts:** Ollama, Code Llama, FastAPI, REST API, System Prompt

**Pipeline:**
  User types question --> Browser --> FastAPI /chat --> Ollama API --> Code Llama --> Response

**What we built:**

  CONCEPT           EXPLANATION                                              FILE
  System Prompt     Hidden instruction telling Code Llama it is ShopBot     ex1_basic/prompts.py
  Ollama Client     Python wrapper around Ollama REST API with timing        ex1_basic/ollama_client.py
  FastAPI App       /chat, /health, / (UI) endpoints                         ex1_basic/app.py
  Chat UI           Dark-themed browser chat with model selector + stats     ex1_basic/index.html

**What this demonstrates:**
- How an application communicates with a local LLM via HTTP
- The role of a system prompt in shaping LLM behaviour
- How to capture latency and token count from Ollama responses

**At this stage:** LLM has NO TechMart knowledge — answers from training data (often inaccurate).

**To run:**
  cd shopbot/ex1_basic
  python app.py
  Open http://localhost:8000

---

### W3-E2 — Knowledge Base (Chunking + Embeddings)

**Goal:** Create TechMart knowledge base from documents and store as vector embeddings in ChromaDB.
**Concepts:** Chunking, Embeddings, Vector Representation, ChromaDB, nomic-embed-text

**Pipeline:**
  Documents (JSON/Markdown) --> Chunker --> Text Chunks --> Embedder --> Vectors --> ChromaDB

**What we built:**

  CONCEPT      EXPLANATION                                                  FILE
  Chunker      4 strategies: per-product, paragraph+overlap, Q&A pair,     ex2_knowledge_base/chunker.py
               per-shipping-zone
  Embedder     Calls Ollama /api/embeddings with nomic-embed-text,          ex2_knowledge_base/embedder.py
               stores vectors in ChromaDB with cosine similarity index
  build_kb.py  One-shot: load docs --> chunk --> embed --> store --> verify  ex2_knowledge_base/build_kb.py

**Knowledge base breakdown:**
  products.json       18 products (Dell XPS, MacBook, Sony headphones, Samsung TV...)  18 chunks
  policies.md         Return/warranty/shipping/payment policies                         ~12 chunks
  faqs.md             25 customer Q&A pairs                                            25 chunks
  shipping_zones.json Domestic + international shipping zones                           9 chunks

**To run:**
  ollama pull nomic-embed-text
  cd shopbot/ex2_knowledge_base
  python build_kb.py

---

### W3-E3 — RAG Pipeline

**Goal:** Find relevant chunks for each user question and provide as context to Code Llama. Show RAG vs No-RAG difference.
**Concepts:** RAG, Vector Similarity Search, Cosine Similarity, Context Injection, Hallucination Prevention

**Pipeline:**
  Question --> Embed --> ChromaDB search --> Top-3 chunks --> Context --> Code Llama --> Grounded response

**What we built:**

  CONCEPT         EXPLANATION                                              FILE
  Retriever       Embeds question, queries ChromaDB top-3, filters        ex3_rag/retriever.py
                  similarity < 0.3
  RAG Pipeline    Retriever + LLM: retrieves context, builds RAG prompt,  ex3_rag/rag_pipeline.py
                  returns response with full trace (chunks, scores, timing)
  No-RAG Baseline Same but skips retrieval — direct LLM for comparison    ex3_rag/rag_pipeline.py
  Compare Demo    CLI: 5 questions x RAG vs No-RAG side by side           ex3_rag/compare_demo.py
  RAG App         FastAPI with /chat accepting use_rag flag                ex3_rag/app.py

**RAG vs No-RAG example:**
  QUESTION                              WITHOUT RAG                 WITH RAG
  "Warranty on Dell XPS 15?"           "Usually 1-3 years" [guess] "2 years mfr warranty" [exact]
  "How much is express shipping?"      "$5-15 typically"   [guess] "$9.99 for 2-3 days"   [exact]
  "Can I return an opened laptop?"     "Depends on policy" [vague] "Yes, 30 days if resalable" [exact]

**To run:**
  cd shopbot/ex3_rag
  python compare_demo.py

---

### W3-E4 — APIs, Services and Orchestration

**Goal:** Split the monolith into 4 microservices communicating via REST APIs. Show orchestration.
**Concepts:** Microservices, REST APIs, Orchestration, FastAPI, httpx (async HTTP)

**Architecture:**
  Browser --> [App Service :8000] (Orchestrator)
                 |                      |
       [RAG Service :8001]    [Data Service :8003]
                 |
       [LLM Service :8002]
                 |
           Ollama :11434

**What each service does:**

  SERVICE         PORT  ROLE                                                    FILE
  App Service     8000  Orchestrator: receives request, calls RAG+LLM,          ex4_services/app_service/main.py
                        returns combined result with trace
  RAG Service     8001  POST /retrieve: embed question, query ChromaDB,         ex4_services/rag_service/main.py
                        return top-3 chunks + context string
  LLM Service     8002  POST /generate: wraps Ollama, supports model switching  ex4_services/llm_service/main.py
  Data Service    8003  GET /products /policies /faqs /shipping — raw data API  ex4_services/data_service/main.py

**Orchestration flow for one request:**
  User: "Warranty on Dell XPS 15?"
  Step 1: App Service receives POST /chat
  Step 2: App Service --> POST rag-service:8001/retrieve --> gets 3 chunks
  Step 3: App Service --> POST llm-service:8002/generate (context + question)
  Step 4: LLM Service --> POST ollama:11434/api/generate
  Step 5: Response flows back: Ollama --> LLM --> App Service --> Browser

**To run:**
  .\start_services.ps1

---

### W3-E5 — Docker

**Goal:** Containerise every service. Show the complete application works through Docker.
**Concepts:** Docker, Docker Compose, Dockerfile, Containers, Volumes, Networks, Health Checks

**What we built:**

  FILE                 PURPOSE
  Dockerfile x4        One per service — defines Python environment, installs deps, runs main.py
  docker-compose.yml   5 containers + health checks + volumes + shared network
  docker_run.ps1       Build images --> pull models into Ollama --> start everything
  .dockerignore        Excludes __pycache__, chroma_db, .git from images

**Key Docker Compose features:**

  FEATURE              HOW WE USE IT
  Named Network        shopbot-net: containers find each other by name (http://rag-service:8001)
  Health Checks        Each service checks /health. Dependents wait until deps are healthy
  depends_on           App Service waits for RAG+LLM+Data. RAG+LLM wait for Ollama
  Volumes              ollama_data persists models. chroma_data persists vector DB
  Environment Vars     Service URLs injected via env vars (RAG_SERVICE_URL, OLLAMA_URL)

**To run:**
  .\docker_run.ps1
  OR: docker compose up --build

---

## 4. Week 4 — Evaluation and Analysis

### W4-E1 — Multi-Model Evaluation

**Goal:** Evaluate the same application with 3 different LLMs. Everything else stays identical.
**Concepts:** Model comparison, LLM benchmarking, controlled experiment design

**Models compared:**

  MODEL             OLLAMA NAME       PARAMS  SPECIALISATION
  Code Llama        codellama         7B      Code + structured text (Meta)
  StarCoder2        starcoder2        7B      Code generation (HuggingFace)
  DeepSeek-Coder    deepseek-coder    6.7B    Code reasoning (DeepSeek AI)

**What stays the same:** Application, prompts, 25 questions, knowledge base, temperature (0.2), hardware
**Model switching** is in: ex4_services/llm_service/main.py (/generate endpoint, model parameter)

  ollama pull starcoder2
  ollama pull deepseek-coder

---

### W4-E2 — Evaluation Dataset

**Goal:** 25 representative real-world questions used for ALL THREE models.
**File:** evaluation/questions.json

**5 categories (5 questions each):**

  CATEGORY               EXAMPLE                                   TESTS
  Product Information    "Specs of Dell XPS 15?"                   Product recall from products.json
  Return Policy          "How many days to return?"                Policy retrieval from policies.md
  Shipping               "How much is express shipping?"           Numeric facts from shipping_zones.json
  Cross-domain           "Dell XPS + overnight total cost?"        Multi-document reasoning
  Hallucination Traps    "Price of iPhone 15 Pro?" (not in KB)     Model honesty when info missing

**Each question has:** ground_truth, requires_rag, source_doc, hallucination_trap, trap_type

---

### W4-E3 — Quantitative Evaluation

**Goal:** Measure each model on 8 metrics across 25 questions. Quantitative evidence, not opinion.
**File:** evaluation/evaluator.py

**Quality Metrics:**

  METRIC              DEFINITION                                    HOW MEASURED
  Correctness         Does answer match ground truth key facts?     Keyword overlap: >=60%=1.0, >=30%=0.5, else 0.0
  Relevance           Is response topically relevant?              Question keyword presence in response, 0.0-1.0
  Retrieval Quality   Were correct source docs in top-3?           Source doc match — 1.0 correct, 0.5 partial, 0.0 missed
  Hallucination Rate  Did model invent false facts?                Trap detection + false claim detection, % of answers

**Performance Metrics:**

  METRIC              DEFINITION                                    HOW MEASURED
  Response Latency    Total time request to response                time.time() wall clock, milliseconds
  LLM Latency         Time inside LLM alone                        Timer around Ollama /api/generate call
  Token Usage         Output tokens generated                       Ollama eval_count field in response
  Memory Usage        RAM used by Python process                    psutil.Process().memory_info().rss in MB
  CPU Usage           CPU load during inference                     psutil.cpu_percent(interval=0.5)

**To run:**
  cd evaluation
  python evaluator.py --model codellama
  python evaluator.py --all                  # All 3 models
**Output:** evaluation/results/{model}_results.json

---

### W4-E4 — Results Analysis

**Goal:** Analyse results and draw evidence-based conclusions about trade-offs.
**Files:** evaluation/generate_report.py --> evaluation/analysis_report.md

**Report contains:**
1. Evaluation setup summary
2. All 8 metric definitions
3. Quality metrics comparison table (3 models)
4. Performance metrics comparison table (3 models)
5. Per-category breakdown
6. Key analysis questions answered with data:
   - Which model is most accurate?
   - Which model hallucinates least?
   - Is the best model also the fastest?
   - What is the quality-latency-resource trade-off?
7. Conclusion framework

**To generate:**
  cd evaluation
  python generate_report.py

---

### W4-E5 — RAG Pipeline Analysis

**Goal:** Trace 10 specific questions through the pipeline. Classify each retrieval and response outcome.
**Files:** evaluation/rag_analysis.py --> evaluation/rag_analysis_report.md

**10 cases traced:**

  CASE                                  RETRIEVAL    RESPONSE     REVEALS
  Return policy question                Relevant     Correct      When everything works perfectly
  Express shipping cost                 Relevant     Correct      Numeric fact retrieval
  Dell XPS + express total              Mixed        LLM correct  LLM can reason across chunks
  Defective item return                 Relevant     Correct      Policy edge case
  iPhone 15 price (trap - not in KB)   Not in KB    Uncertain?   Tests model honesty
  Longest warranty (multi-product)      Partial      Partial      Depends which products retrieved
  Same-day delivery (trap)             Shipping      Should deny  Context found but answer is "no"
  Payment + financing options           Relevant     Correct      Multi-fact from one source
  P.O. Box + express (detail in text)  May miss      Varies       Fine-grained detail retrieval
  Live order status (trap)              Not in KB    Should defer  Model must acknowledge limits

**Key relationship this reveals:**
  Retrieval Quality --> Context Quality --> LLM Response Quality

  Relevant context   --> LLM usually answers correctly
  Partial context    --> LLM may give partial/slightly wrong answer
  Missing context    --> LLM either hallucinates OR correctly says "I don't know"
  Irrelevant context --> LLM may be misled

**To run:**
  cd evaluation
  python rag_analysis.py codellama

---

### W4-E6 — Codebase Understanding

**Goal:** Use ShopBot's own LLM+RAG to answer questions ABOUT ShopBot's own source code.
**File:** ex6_codebase/codebase_indexer.py

**How it works:**
1. Scans all .py files in 8 ShopBot directories
2. Chunks each file by function/class (each function = one chunk)
3. Embeds each code chunk using nomic-embed-text
4. Stores in separate ChromaDB collection (shopbot_codebase)
5. For a cross-file question: embed it, retrieve relevant code chunks, ask Code Llama

**8 cross-file questions tested:**

  QUESTION                                                    TESTS
  "Which files are involved in processing a chat request?"    Full pipeline trace
  "Which service handles vector similarity search?"           Component identification
  "What happens after the user submits a message?"            Event flow understanding
  "Which components break if ChromaDB is unavailable?"        Dependency analysis
  "Which files need to change to add a new LLM model?"        Impact analysis
  "How does RAG service communicate with LLM service?"        Inter-service communication
  "Which function embeds user queries into vectors?"           Function-level search
  "What evaluation scripts exist and what do they measure?"   Documentation discovery

**To run:**
  cd ex6_codebase
  python codebase_indexer.py --build     # Index all source files (run once)
  python codebase_indexer.py --demo      # Run all 8 questions
  python codebase_indexer.py --query "Which function handles retrieval?"

---

## 5. Full File Reference

  shopbot/
  |
  +-- knowledge_base/                     Shared docs (all exercises use these)
  |   +-- products.json                   18 TechMart products with specs, price, warranty
  |   +-- policies.md                     Return, warranty, shipping, payment policies
  |   +-- faqs.md                         25 customer Q&A pairs
  |   +-- shipping_zones.json             Domestic + international shipping costs/times
  |
  +-- ex1_basic/                          W3-E1: Basic LLM Chat App
  |   +-- prompts.py                      System prompt + RAG prompt template
  |   +-- ollama_client.py                Ollama API wrapper (health, generate, metrics)
  |   +-- app.py                          FastAPI: /chat, /health, / (UI)
  |   +-- index.html                      Dark chat UI with model selector + session stats
  |   +-- requirements.txt               fastapi, uvicorn, requests, pydantic
  |
  +-- ex2_knowledge_base/                 W3-E2: Chunking + Embeddings + ChromaDB
  |   +-- chunker.py                      4 chunking strategies
  |   +-- embedder.py                     nomic-embed-text embeddings to ChromaDB
  |   +-- build_kb.py                     One-shot: chunk + embed + store + verify
  |   +-- chroma_db/                      ChromaDB vector database (auto-created)
  |   +-- requirements.txt               + chromadb
  |
  +-- ex3_rag/                            W3-E3: Full RAG Pipeline
  |   +-- retriever.py                    Embed question + ChromaDB search + top-3 chunks
  |   +-- rag_pipeline.py                 Full RAG chain + no-RAG baseline
  |   +-- compare_demo.py                 CLI: 5 questions x RAG vs No-RAG
  |   +-- app.py                          FastAPI with RAG-enabled /chat endpoint
  |   +-- embedder_proxy.py              Imports ChromaDB stats from ex2 into ex3
  |
  +-- ex4_services/                       W3-E4: Microservices
  |   +-- app_service/main.py             Orchestrator: request + call RAG + call LLM
  |   +-- rag_service/main.py             POST /retrieve: embed + ChromaDB + context
  |   +-- llm_service/main.py             POST /generate: Ollama wrapper + model switch
  |   +-- data_service/main.py            GET /products /policies /faqs /shipping
  |   +-- */Dockerfile                    Container definition per service
  |
  +-- docker-compose.yml                  W3-E5: 5 containers + network + volumes + healthchecks
  +-- docker_run.ps1                      W3-E5: Build + pull models + start Docker stack
  +-- start_services.ps1                  W3-E4: Start all 4 services locally (no Docker)
  +-- .dockerignore                       Excludes pycache, chroma_db, .git from images
  |
  +-- evaluation/                         W4 Exercises
  |   +-- questions.json                  W4-E2: 25 Q&A with ground truth + trap flags
  |   +-- evaluator.py                    W4-E3: 8-metric evaluator across 3 models
  |   +-- generate_report.py              W4-E4: Results JSON --> analysis_report.md
  |   +-- rag_analysis.py                 W4-E5: Trace 10 Q->Context->Response examples
  |   +-- analysis_report.md              W4-E4 output (generated after running models)
  |   +-- rag_analysis_report.md          W4-E5 output (generated by rag_analysis.py)
  |   +-- results/
  |       +-- codellama_results.json      W4-E3 output for Code Llama
  |       +-- starcoder2_results.json     W4-E3 output for StarCoder2
  |       +-- deepseek-coder_results.json W4-E3 output for DeepSeek-Coder
  |
  +-- ex6_codebase/                       W4-E6: Codebase Understanding
  |   +-- codebase_indexer.py             Index .py files + cross-file Q&A via Code Llama
  |   +-- codebase_chroma_db/            Separate ChromaDB for source code (auto-created)
  |   +-- codebase_qa_results.json        Output: answers to 8 architectural questions
  |
  +-- run_week4.ps1                       Master: run all W4 exercises in sequence
  +-- README.md                           Project setup and quick-start guide
  +-- PROJECT_REFERENCE.md               THIS FILE

---

## 6. How to Run Everything

### Prerequisites
  ollama pull codellama
  ollama pull nomic-embed-text
  ollama pull starcoder2
  ollama pull deepseek-coder
  pip install fastapi uvicorn requests pydantic chromadb httpx psutil

### Week 3
  # Exercise 1 — Basic Chat App
  cd shopbot/ex1_basic && python app.py
  # Open http://localhost:8000

  # Exercise 2 — Build Knowledge Base (run ONCE)
  cd shopbot/ex2_knowledge_base && python build_kb.py

  # Exercise 3 — RAG Comparison Demo
  cd shopbot/ex3_rag && python compare_demo.py

  # Exercise 4 — All Microservices Locally
  cd shopbot && .\start_services.ps1

  # Exercise 5 — Docker Stack
  cd shopbot && .\docker_run.ps1

### Week 4
  # All exercises in one command
  cd shopbot && .\run_week4.ps1

  # OR step by step:
  cd evaluation
  python evaluator.py --all           # E1+E3: run 3 models
  python generate_report.py           # E4: analysis report
  python rag_analysis.py codellama    # E5: RAG trace analysis
  cd ../ex6_codebase
  python codebase_indexer.py --build  # E6: index source code
  python codebase_indexer.py --demo   # E6: run 8 cross-file questions

---

## 7. Concept to File Map

  CONCEPT                       FIRST USED  KEY FILES
  Ollama API call               W3-E1       ex1_basic/ollama_client.py
  System prompt                 W3-E1       ex1_basic/prompts.py
  FastAPI REST endpoint         W3-E1       ex1_basic/app.py
  Document chunking             W3-E2       ex2_knowledge_base/chunker.py
  Text embeddings               W3-E2       ex2_knowledge_base/embedder.py
  ChromaDB storage              W3-E2       ex2_knowledge_base/embedder.py
  Cosine similarity search      W3-E3       ex3_rag/retriever.py
  RAG prompt building           W3-E3       ex3_rag/rag_pipeline.py
  RAG vs No-RAG comparison      W3-E3       ex3_rag/compare_demo.py
  Microservice separation       W3-E4       ex4_services/*/main.py
  Service orchestration         W3-E4       ex4_services/app_service/main.py
  Async inter-service HTTP      W3-E4       ex4_services/app_service/main.py (httpx)
  Dockerfile                    W3-E5       ex4_services/*/Dockerfile
  Docker Compose                W3-E5       docker-compose.yml
  Docker health checks          W3-E5       docker-compose.yml
  Multi-model switching         W4-E1       ex4_services/llm_service/main.py
  Evaluation dataset            W4-E2       evaluation/questions.json
  Correctness metric            W4-E3       evaluation/evaluator.py (score_correctness)
  Hallucination detection       W4-E3       evaluation/evaluator.py (detect_hallucination)
  Memory/CPU measurement        W4-E3       evaluation/evaluator.py (psutil)
  Report generation             W4-E4       evaluation/generate_report.py
  RAG trace analysis            W4-E5       evaluation/rag_analysis.py
  Code chunking by function     W4-E6       ex6_codebase/codebase_indexer.py
  Cross-file codebase Q&A       W4-E6       ex6_codebase/codebase_indexer.py
