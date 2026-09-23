"""
main.py — LLM Service
Supports starcoder, codellama, deepseek-coder (and any Ollama-compatible model).
Default model is set via DEFAULT_MODEL env var (falls back to deepseek-coder).
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
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-coder")

SYSTEM_PROMPT = """You are ShopBot, TechMart's helpful customer support assistant.
Answer in plain, friendly English. Do NOT use markdown headers.
Do NOT start with 'I'm sorry', 'As an AI', 'I don't have access', or 'I cannot access files'.
The store data is already provided to you — just use it to answer directly.
Give a direct, complete answer in 2-5 sentences. Never invent prices or policies not shown."""

RAG_PROMPT_TEMPLATE = """You are ShopBot, TechMart's customer support assistant.
The following is TechMart's live store data — product specs, prices, policies, and shipping info.
This is NOT a file you need to access; this data is already loaded for you to use directly.
Answer the customer question using ONLY this store data. Be friendly and direct.
Do NOT say 'I don't have access to' or reference file names in your answer.

TechMart Store Data:
{context}

Customer: {question}
ShopBot:"""

NORAG_PROMPT_TEMPLATE = """You are ShopBot, TechMart's helpful customer support assistant.
Answer the customer's question based on your general knowledge of electronics retail and e-commerce.
Be friendly, helpful, and give your best answer even without store-specific data.
If you genuinely cannot help, suggest the customer contact TechMart support.
Do NOT say 'I don't have access to real-time data' or 'I'm an AI' — just answer helpfully.

Customer: {question}
ShopBot:"""


class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None          # Defaults to DEFAULT_MODEL env var
    context: Optional[str] = None        # If provided, uses RAG prompt
    question: Optional[str] = None       # Original question for RAG prompt
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = -1       # -1 = unlimited, let the LLM decide response length


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
        # No RAG context — use a structured no-RAG prompt so code models give helpful answers
        question = request.question or request.prompt
        final_prompt = NORAG_PROMPT_TEMPLATE.format(question=question)

    # Per-model token cap — code models (starcoder, deepseek-coder) run forever
    # without a cap on open-ended chat questions, causing ReadTimeout in the UI.
    # If caller passes max_tokens > 0, use that. Otherwise use a sensible per-model default.
    if request.max_tokens and request.max_tokens > 0:
        num_predict = request.max_tokens
    else:
        # Code models need a cap — they don't know when to stop for chat prompts
        model_lower = model.lower()
        if "codellama" in model_lower:
            num_predict = 768    # CodeLlama handles chat better, allow longer
        elif "starcoder" in model_lower or "deepseek" in model_lower:
            num_predict = 512    # Code models cap at 512 for chat use-case
        else:
            num_predict = 512    # Safe default for any other model

    payload = {
        "model": model,
        "prompt": final_prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": request.temperature,
            "num_predict": num_predict,
            "num_ctx": 4096,   # Full context window for detailed responses
            "num_thread": 4,   # 4 threads out of 6 vCPUs — fast without hogging the desktop
            # Use newline-prefixed stop tokens so the model is never stopped immediately
            # on its first token (TinyLlama often begins with "Customer:" or "ShopBoT:")
            "stop": ["\n\n\n", "\nHuman:", "\nCustomer:", "\nUser:"],
        }
    }

    start = time.time()
    try:
        print(f"[LLM] Calling Ollama at {OLLAMA_URL} with model '{model}'...")
        r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=180)
        r.raise_for_status()
        data = r.json()
        latency = int((time.time() - start) * 1000)
        raw_text = data.get("response", "").strip()

        # Strip leading role-prefix that some small models inject
        # e.g. "ShopBoT: Yes..." → "Yes..." / "Customer: ..." → "..."
        import re as _re
        raw_text = _re.sub(r'^(ShopBot|ShopBoT|Customer|Human|User)\s*:\s*', '', raw_text, flags=_re.IGNORECASE).strip()

        print(f"[LLM] Success! Generated {len(raw_text)} chars in {latency}ms")
        return GenerateResponse(
            text=raw_text,
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
