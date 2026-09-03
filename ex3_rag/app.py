"""
app.py — ShopBot AI FastAPI Application (Exercise 3: Full RAG)
Now with /chat (RAG) and /chat-basic (no RAG) endpoints for comparison
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex1_basic"))
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List

from rag_pipeline import rag_chat, no_rag_chat
from ollama_client import check_ollama_health, list_available_models
from embedder_proxy import get_kb_stats

app = FastAPI(
    title="ShopBot AI — RAG Edition",
    description="E-commerce support assistant with Retrieval-Augmented Generation",
    version="3.0.0",
)


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "codellama"
    top_k: Optional[int] = 3
    use_rag: Optional[bool] = True


class RetrievedChunk(BaseModel):
    text: str
    source: str
    type: str
    similarity_score: float


class ChatResponse(BaseModel):
    response: str
    model: str
    rag_used: bool
    retrieved_chunks: List[RetrievedChunk]
    metrics: dict
    error: bool = False


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    ui_path = os.path.join(os.path.dirname(__file__), "..", "ex1_basic", "index.html")
    with open(ui_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health():
    ollama_ok = check_ollama_health()
    kb_stats = get_kb_stats()
    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama_connected": ollama_ok,
        "available_models": list_available_models() if ollama_ok else [],
        "knowledge_base": kb_stats,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    if request.use_rag:
        result = rag_chat(request.message, model=request.model, top_k=request.top_k)
    else:
        result = no_rag_chat(request.message, model=request.model)

    return ChatResponse(
        response=result["response"],
        model=result["model"],
        rag_used=result["rag_used"],
        retrieved_chunks=[RetrievedChunk(**c) for c in result["retrieved_chunks"]],
        metrics=result["metrics"],
    )


if __name__ == "__main__":
    import uvicorn
    print("🚀 ShopBot AI — Exercise 3: RAG Application")
    print("🌐 http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
