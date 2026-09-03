"""
retriever.py — Vector similarity search for ShopBot RAG
Exercise 3: Query embedding → ChromaDB → Relevant chunks
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex2_knowledge_base"))

from embedder import query_collection, get_embedding
from typing import List, Dict

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "ex2_knowledge_base", "chroma_db")
DEFAULT_TOP_K = 3
MIN_SIMILARITY = 0.3  # Discard chunks below this similarity threshold


def retrieve(question: str, k: int = DEFAULT_TOP_K) -> List[Dict]:
    """
    Retrieve the top-K most relevant knowledge base chunks for a question.

    Pipeline:
      Question → Embed (nomic-embed-text) → Cosine Similarity → Top-K Chunks

    Args:
        question: User's natural language question
        k: Number of chunks to retrieve
    Returns:
        List of dicts: {text, source, type, similarity_score}
    """
    results = query_collection(question, n_results=k, persist_path=CHROMA_PATH)

    retrieved = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        similarity = round(1 - dist, 4)  # cosine distance → similarity score
        if similarity >= MIN_SIMILARITY:
            retrieved.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "type": meta.get("type", "unknown"),
                "section": meta.get("section", ""),
                "similarity_score": similarity,
            })

    return retrieved


def build_context(chunks: List[Dict]) -> str:
    """Format retrieved chunks into a clean context string for the LLM."""
    if not chunks:
        return "No relevant information found in the knowledge base."

    parts = []
    for i, chunk in enumerate(chunks):
        source_label = f"[Source: {chunk['source']} | Type: {chunk['type']}]"
        parts.append(f"{source_label}\n{chunk['text']}")

    return "\n\n---\n\n".join(parts)
