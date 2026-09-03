"""
embedder.py — Embedding generation and ChromaDB storage for ShopBot
Exercise 2: Convert chunks → embeddings → vector store
"""

import sys, io
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import chromadb
from chromadb.config import Settings
from typing import List, Dict
import time


OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "shopbot_kb"


def get_embedding(text: str) -> List[float]:
    """
    Generate a vector embedding for the given text using Ollama's
    nomic-embed-text model.

    Args:
        text: The text to embed
    Returns:
        A list of floats representing the embedding vector
    """
    # Try new Ollama API first (/api/embed, Ollama >= 0.1.26)
    # Fall back to old API (/api/embeddings) if 404
    for endpoint, payload_key, response_key in [
        ("/api/embed",       "input",  "embeddings"),
        ("/api/embeddings",  "prompt", "embedding"),
    ]:
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}{endpoint}",
                json={"model": EMBED_MODEL, payload_key: text},
                timeout=30,
            )
            if response.status_code == 404:
                continue
            response.raise_for_status()
            data = response.json()
            # /api/embed returns {"embeddings": [[...]]}, /api/embeddings returns {"embedding": [...]}
            if response_key == "embeddings":
                return data[response_key][0]
            return data[response_key]
        except requests.exceptions.HTTPError:
            continue
    raise RuntimeError(f"Ollama embedding API not available at {OLLAMA_BASE_URL}. "
                       f"Is Ollama running? Is nomic-embed-text pulled?")


def get_chroma_collection(persist_path: str = CHROMA_PATH):
    """Return (or create) the ChromaDB persistent collection."""
    client = chromadb.PersistentClient(path=persist_path)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # Use cosine similarity
    )
    return client, collection


def store_chunks(chunks: List[Dict], persist_path: str = CHROMA_PATH) -> int:
    """
    Embed all chunks and store them in ChromaDB.

    Args:
        chunks: List of dicts with keys: id, text, metadata
        persist_path: Where to persist the ChromaDB database
    Returns:
        Number of chunks stored
    """
    client, collection = get_chroma_collection(persist_path)

    # Check existing IDs to avoid duplicates
    existing = set(collection.get()["ids"])

    ids, embeddings, documents, metadatas = [], [], [], []
    skipped = 0

    print(f"\n🔢 Generating embeddings using '{EMBED_MODEL}'...")

    for i, chunk in enumerate(chunks):
        if chunk["id"] in existing:
            skipped += 1
            continue

        print(f"  [{i+1}/{len(chunks)}] Embedding: {chunk['id'][:60]}...", end="\r")

        embedding = get_embedding(chunk["text"])

        ids.append(chunk["id"])
        embeddings.append(embedding)
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])

        # Batch insert every 10 chunks
        if len(ids) >= 10:
            collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
            ids, embeddings, documents, metadatas = [], [], [], []
            time.sleep(0.1)  # small pause to avoid overwhelming Ollama

    # Insert remaining
    if ids:
        collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    total = collection.count()
    print(f"\n✅ Done! {total} chunks stored in ChromaDB ({skipped} skipped as duplicates)")
    return total


def query_collection(query_text: str, n_results: int = 3, persist_path: str = CHROMA_PATH) -> Dict:
    """
    Embed a query and retrieve the top-N most similar chunks.

    Args:
        query_text: The user's question
        n_results: Number of results to retrieve
        persist_path: Path to ChromaDB database
    Returns:
        ChromaDB query result dict
    """
    _, collection = get_chroma_collection(persist_path)
    query_embedding = get_embedding(query_text)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    return results


def get_collection_stats(persist_path: str = CHROMA_PATH) -> Dict:
    """Return stats about the knowledge base."""
    _, collection = get_chroma_collection(persist_path)
    count = collection.count()
    return {
        "total_chunks": count,
        "collection_name": COLLECTION_NAME,
        "embed_model": EMBED_MODEL,
        "persist_path": persist_path,
    }
