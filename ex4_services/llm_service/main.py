"""
main.py — LLM Service
Uses tinyllama (1.1B) as default — extremely lightweight, runs on ~600MB RAM.
Supports any Ollama-compatible model via the 'model' request field.
Port: 8002
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import requests, time, os

app = FastAPI(title="ShopBot LLM Service", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "tinyllama")

SYSTEM_PROMPT = """You are ShopBot, TechMart's helpful customer support assistant.
Answer in plain, friendly English. Do NOT include markdown headers (##, ###), source labels,
or phrases like 'STORE INFORMATION'. Give a direct, complete answer in 2-4 sentences.
Never invent product names, prices, or policies. If unsure, say so."""

RAG_PROMPT_TEMPLATE = """You are ShopBot, TechMart's AI support assistant.
Using ONLY the store information below, write a short, friendly plain-English answer.
Do NOT repeat source labels or markdown formatting. Do NOT start with "Sure" or "Certainly".
If the information is not in the context, say: "I don't have that information."

Store Information:
{context}

Customer: {question}
ShopBot:"""


class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None          # Defaults to DEFAULT_MODEL env var
    context: Optional[str] = None        # If provided, uses RAG prompt
    question: Optional[str] = None       # Original question for RAG prompt
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 128      # Keep short for low-RAM VMs


class GenerateResponse(BaseModel):
    text: str
    model: str
    latency_ms: int
    tokens_used: int
    prompt_tokens: int
    error: bool = False


@app.get("/health")
def health():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        return {"service": "llm-service", "status": "ok", "ollama": "connected",
                "default_model": DEFAULT_MODEL, "available_models": models, "port": 8002}
    except Exception as e:
        return {"service": "llm-service", "status": "degraded", "ollama": str(e)}


@app.get("/models")
def list_models():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return {"models": [m["name"] for m in r.json().get("models", [])]}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    model = request.model or DEFAULT_MODEL

    if request.context and request.question:
        final_prompt = RAG_PROMPT_TEMPLATE.format(
            context=request.context,
            question=request.question
        )
    else:
        final_prompt = request.prompt

    payload = {
        "model": model,
        "prompt": final_prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": request.temperature,
            "num_predict": min(request.max_tokens or 192, 192),  # 192 tokens — enough for a full answer without truncation
            "num_ctx": 768,                                      # Slightly larger context fits prompt + answer cleanly
            "num_thread": 2,                                     # Limit to 2 CPU threads so VM desktop never freezes
        }
    }

    start = time.time()
    try:
        print(f"[LLM] Calling Ollama at {OLLAMA_URL} with model '{model}'...")
        r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=180)
        r.raise_for_status()
        data = r.json()
        latency = int((time.time() - start) * 1000)
        print(f"[LLM] Success! Generated in {latency}ms")
        return GenerateResponse(
            text=data.get("response", "").strip(),
            model=data.get("model", model),
            latency_ms=latency,
            tokens_used=data.get("eval_count", 0),
            prompt_tokens=data.get("prompt_eval_count", 0),
        )
    except requests.exceptions.ConnectionError as e:
        print(f"[LLM] ConnectionError to Ollama at {OLLAMA_URL}: {e}")
        return GenerateResponse(text="Cannot connect to Ollama. Is it running?", model=model,
                                latency_ms=0, tokens_used=0, prompt_tokens=0, error=True)
    except Exception as e:
        print(f"[LLM] Error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
