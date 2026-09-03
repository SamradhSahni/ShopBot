"""
app.py — ShopBot AI FastAPI Application (Exercise 1: Basic LLM)
User → Application → API → Ollama → Code Llama → Response
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os

from prompts import SYSTEM_PROMPT
from ollama_client import generate_response, check_ollama_health, list_available_models

# ── App Initialisation ─────────────────────────────────────────────────────────
app = FastAPI(
    title="ShopBot AI — TechMart Support",
    description="AI-powered e-commerce support assistant powered by Code Llama via Ollama",
    version="1.0.0",
)


# ── Request / Response Models ──────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "codellama"


class ChatResponse(BaseModel):
    response: str
    model: str
    latency_ms: int
    tokens_used: int
    prompt_tokens: int
    error: bool = False


class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    available_models: list[str]


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the chat UI."""
    ui_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(ui_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check server and Ollama connectivity."""
    ollama_ok = check_ollama_health()
    models = list_available_models() if ollama_ok else []
    return HealthResponse(
        status="ok" if ollama_ok else "degraded",
        ollama_connected=ollama_ok,
        available_models=models,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Accepts a user message, sends it to Code Llama via Ollama, returns response.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    result = generate_response(
        prompt=request.message,
        model=request.model or "codellama",
        system_prompt=SYSTEM_PROMPT,
        temperature=0.3,
    )

    return ChatResponse(
        response=result["response"],
        model=result["model"],
        latency_ms=result["latency_ms"],
        tokens_used=result["tokens_used"],
        prompt_tokens=result["prompt_tokens"],
        error=result.get("error", False),
    )


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ShopBot AI — Exercise 1: Basic LLM Application")
    print("📦 Model: Code Llama via Ollama")
    print("🌐 UI: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
