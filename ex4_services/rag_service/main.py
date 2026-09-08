"""
main.py — RAG Service
Uses sentence-transformers (all-MiniLM-L6-v2) for lightweight in-process embedding.
No Ollama dependency for retrieval — saves significant RAM on low-resource VMs.
Port: 8001
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="ShopBot RAG Service", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CHROMA_PATH = os.getenv("CHROMA_PATH", os.path.join(
    os.path.dirname(__file__), "..", "..", "chroma_db"))
COLLECTION_NAME = "shopbot_kb"
EMBED_MODEL = "all-MiniLM-L6-v2"
MIN_SIMILARITY = 0.2

import chromadb
from sentence_transformers import SentenceTransformer

# Load model once at startup — cached in memory
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def embed(text: str) -> List[float]:
    return get_model().encode(text, normalize_embeddings=True).tolist()


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
            n_results=min(request.top_k, collection.count()),
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
