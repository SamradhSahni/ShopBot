"""
main.py — App Service (Orchestrator)
Exercise 4: Entry point — orchestrates RAG + LLM services for each user request
Port: 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import httpx, asyncio, time, os

app = FastAPI(title="ShopBot App Service", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

RAG_SERVICE_URL  = os.getenv("RAG_SERVICE_URL",  "http://localhost:8001")
LLM_SERVICE_URL  = os.getenv("LLM_SERVICE_URL",  "http://localhost:8002")
DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8003")

TIMEOUT = httpx.Timeout(120.0)


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "tinyllama"
    top_k: Optional[int] = 3
    use_rag: Optional[bool] = True


class ChatResponse(BaseModel):
    response: str
    model: str
    rag_used: bool
    retrieved_chunks: list
    orchestration_trace: dict
    metrics: dict
    error: bool = False


HTML_PATH = os.path.join(os.path.dirname(__file__), "index.html")


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health():
    """Aggregate health check across all services."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
        results = {}
        for name, url in [
            ("rag_service", RAG_SERVICE_URL),
            ("llm_service", LLM_SERVICE_URL),
            ("data_service", DATA_SERVICE_URL),
        ]:
            try:
                r = await client.get(f"{url}/health")
                results[name] = r.json()
            except Exception as e:
                results[name] = {"status": "unreachable", "error": str(e)}

    all_ok = all(v.get("status") == "ok" for v in results.values())
    ollama_ok = results.get("llm_service", {}).get("ollama") == "connected"
    return {
        "status": "ok" if all_ok else "degraded",
        "ollama_connected": ollama_ok,
        "services": results
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Orchestration flow for one user request:
      1. Call RAG Service → retrieve context
      2. Call LLM Service → generate response with context
      3. Return combined result with full trace
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    pipeline_start = time.time()
    trace = {"steps": []}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:

        # ── Step 1: Retrieve context (if RAG enabled) ───────────────────────
        context = ""
        chunks = []
        rag_ms = 0

        if request.use_rag:
            try:
                t0 = time.time()
                rag_resp = await client.post(
                    f"{RAG_SERVICE_URL}/retrieve",
                    json={"question": request.message, "top_k": request.top_k}
                )
                rag_ms = int((time.time() - t0) * 1000)
                rag_data = rag_resp.json()
                context = rag_data.get("context", "")
                chunks = rag_data.get("chunks", [])
                trace["steps"].append({
                    "step": 1, "service": "rag-service", "action": "retrieve",
                    "chunks_found": len(chunks), "latency_ms": rag_ms
                })
            except Exception as e:
                trace["steps"].append({"step": 1, "service": "rag-service", "error": str(e)})

        # ── Step 2: Generate response ───────────────────────────────────────
        try:
            t0 = time.time()
            llm_payload = {
                "prompt": request.message,
                "model": request.model,
                "temperature": 0.2,
            }
            if context:
                llm_payload["context"] = context
                llm_payload["question"] = request.message

        try:
            llm_resp = await client.post(f"{LLM_SERVICE_URL}/generate", json=llm_payload)
            llm_ms = int((time.time() - t0) * 1000)
            if llm_resp.status_code != 200:
                raise HTTPException(status_code=503, detail=f"LLM Service HTTP {llm_resp.status_code}: {llm_resp.text}")
            llm_data = llm_resp.json()
            trace["steps"].append({
                "step": 2, "service": "llm-service", "action": "generate",
                "model": llm_data.get("model"), "latency_ms": llm_ms,
                "tokens_used": llm_data.get("tokens_used", 0)
            })
        except HTTPException:
            raise
        except Exception as e:
            err_msg = str(e).strip() or repr(e)
            raise HTTPException(status_code=503, detail=f"LLM Service error: {err_msg}")

    total_ms = int((time.time() - pipeline_start) * 1000)

    return ChatResponse(
        response=llm_data.get("text", ""),
        model=llm_data.get("model", request.model),
        rag_used=request.use_rag and bool(context),
        retrieved_chunks=chunks,
        orchestration_trace=trace,
        metrics={
            "rag_latency_ms": rag_ms,
            "llm_latency_ms": llm_data.get("latency_ms", 0),
            "total_latency_ms": total_ms,
            "tokens_used": llm_data.get("tokens_used", 0),
            "chunks_retrieved": len(chunks),
        },
        error=llm_data.get("error", False),
    )


if __name__ == "__main__":
    import uvicorn
    print("🚀 ShopBot App Service (Orchestrator) — Exercise 4")
    print("📡 RAG Service:", RAG_SERVICE_URL)
    print("🤖 LLM Service:", LLM_SERVICE_URL)
    print("📦 Data Service:", DATA_SERVICE_URL)
    uvicorn.run(app, host="0.0.0.0", port=8000)
