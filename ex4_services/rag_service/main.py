"""
main.py — RAG Service
Exercise 4: Handles embedding + vector retrieval from ChromaDB
Port: 8001
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests, os, sys

app = FastAPI(title="ShopBot RAG Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHROMA_PATH = os.getenv("CHROMA_PATH", os.path.join(
    os.path.dirname(__file__), "..", "..", "ex2_knowledge_base", "chroma_db"))
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "shopbot_kb"
MIN_SIMILARITY = 0.3

import chromadb


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def embed(text: str) -> List[float]:
    for endpoint, payload_key, response_key in [
        ("/api/embed",      "input",  "embeddings"),
        ("/api/embeddings", "prompt", "embedding"),
    ]:
        try:
            r = requests.post(f"{OLLAMA_URL}{endpoint}",
                              json={"model": EMBED_MODEL, payload_key: text}, timeout=30)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            data = r.json()
            return data[response_key][0] if response_key == "embeddings" else data[response_key]
        except requests.exceptions.HTTPError:
            continue
    raise RuntimeError("Ollama embedding API unavailable")


class RetrieveRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3


class ChunkResult(BaseModel):
    text: str
    source: str
    type: str
    section: Optional[str] = ""
    similarity_score: float


class RetrieveResponse(BaseModel):
    question: str
    chunks: List[ChunkResult]
    context: str
    chunks_found: int


@app.get("/health")
def health():
    try:
        col = get_collection()
        count = col.count()
        return {"service": "rag-service", "status": "ok",
                "chroma_chunks": count, "embed_model": EMBED_MODEL, "port": 8001}
    except Exception as e:
        return {"service": "rag-service", "status": "degraded", "error": str(e)}


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest):
    try:
        collection = get_collection()
        query_embedding = embed(request.question)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=request.top_k,
            include=["documents", "metadatas", "distances"]
        )

        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            similarity = round(1 - dist, 4)
            if similarity >= MIN_SIMILARITY:
                chunks.append(ChunkResult(
                    text=doc,
                    source=meta.get("source", "unknown"),
                    type=meta.get("type", "unknown"),
                    section=meta.get("section", ""),
                    similarity_score=similarity,
                ))

        # Build context string
        if chunks:
            parts = [f"[Source: {c.source} | Type: {c.type}]\n{c.text}" for c in chunks]
            context = "\n\n---\n\n".join(parts)
        else:
            context = "No relevant information found in the knowledge base."

        return RetrieveResponse(
            question=request.question,
            chunks=chunks,
            context=context,
            chunks_found=len(chunks),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def stats():
    try:
        col = get_collection()
        return {"total_chunks": col.count(), "collection": COLLECTION_NAME,
                "embed_model": EMBED_MODEL, "chroma_path": CHROMA_PATH}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
