"""
embedder.py — Embedding generation and ChromaDB storage for ShopBot
Uses sentence-transformers (all-MiniLM-L6-v2) — lightweight, no Ollama needed.
80MB model, runs on CPU, ideal for low-RAM VMs.
"""

import chromadb
from typing import List, Dict
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-MiniLM-L6-v2"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "shopbot_kb"

# Singleton model instance
_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"  Loading embedding model '{EMBED_MODEL}'...")
        _model = SentenceTransformer(EMBED_MODEL)
        print(f"  Model loaded.")
    return _model


def get_embedding(text: str) -> List[float]:
    """Generate a vector embedding using sentence-transformers."""
    return get_model().encode(text, normalize_embeddings=True).tolist()


def get_chroma_collection(persist_path: str = CHROMA_PATH):
    """Return (or create) the ChromaDB persistent collection."""
    client = chromadb.PersistentClient(path=persist_path)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return client, collection


def store_chunks(chunks: List[Dict], persist_path: str = CHROMA_PATH) -> int:
    """Embed all chunks and store them in ChromaDB."""
    client, collection = get_chroma_collection(persist_path)

    # Check existing IDs to avoid duplicates
    existing = set(collection.get()["ids"])

    ids, embeddings, documents, metadatas = [], [], [], []
    skipped = 0

    print(f"\n  Generating embeddings for {len(chunks)} chunks using '{EMBED_MODEL}'...")

    texts = []
    new_chunks = []
    for chunk in chunks:
        if chunk["id"] in existing:
            skipped += 1
        else:
            new_chunks.append(chunk)
            texts.append(chunk["text"])

    if texts:
        # Batch encode all texts at once — much faster than one-by-one
        all_embeddings = get_model().encode(texts, normalize_embeddings=True, show_progress_bar=True)

        for chunk, emb in zip(new_chunks, all_embeddings):
            ids.append(chunk["id"])
            embeddings.append(emb.tolist())
            documents.append(chunk["text"])
            metadatas.append(chunk["metadata"])

            # Batch insert every 50 chunks
            if len(ids) >= 50:
                collection.add(ids=ids, embeddings=embeddings,
                               documents=documents, metadatas=metadatas)
                ids, embeddings, documents, metadatas = [], [], [], []

        if ids:
            collection.add(ids=ids, embeddings=embeddings,
                           documents=documents, metadatas=metadatas)

    total = collection.count()
    print(f"\n  Done! {total} chunks stored ({skipped} skipped as duplicates)")
    return total


def query_collection(query_text: str, n_results: int = 3, persist_path: str = CHROMA_PATH) -> Dict:
    """Embed a query and retrieve the top-N most similar chunks."""
    _, collection = get_chroma_collection(persist_path)
    query_embedding = get_embedding(query_text)
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )


def get_collection_stats(persist_path: str = CHROMA_PATH) -> Dict:
    """Return stats about the knowledge base."""
    _, collection = get_chroma_collection(persist_path)
    return {
        "total_chunks": collection.count(),
        "collection_name": COLLECTION_NAME,
        "embed_model": EMBED_MODEL,
        "persist_path": persist_path,
    }
