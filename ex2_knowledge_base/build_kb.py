"""
build_kb.py - Build the ShopBot knowledge base
Exercise 2: Run this script ONCE to chunk all documents and populate ChromaDB

Usage:
    python build_kb.py

This will:
1. Load all documents from ../knowledge_base/
2. Chunk them using appropriate strategies
3. Generate embeddings using nomic-embed-text via Ollama
4. Store everything in ./chroma_db/
"""

import sys
import os

# Fix Windows cp1252 terminal encoding - force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path so we can import from ex2
sys.path.insert(0, os.path.dirname(__file__))

from chunker import load_all_chunks
from embedder import store_chunks, get_collection_stats, get_chroma_collection

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")


def print_sample_chunks(chunks, n=3):
    print(f"\n  Sample chunks ({n} shown):")
    for chunk in chunks[:n]:
        print(f"\n  ID: {chunk['id']}")
        print(f"  Type: {chunk['metadata']['type']}")
        print(f"  Text preview: {chunk['text'][:120]}...")


def main():
    print("=" * 60)
    print("  ShopBot AI - Knowledge Base Builder")
    print("  Exercise 2: Chunking + Embeddings + ChromaDB")
    print("=" * 60)

    # Step 1: Load & chunk all documents
    print("\n[Step 1] Loading and chunking documents...")
    chunks = load_all_chunks(KB_DIR)

    # Show chunk breakdown
    type_counts = {}
    for c in chunks:
        t = c["metadata"]["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print("\n  Chunk breakdown by type:")
    for doc_type, count in type_counts.items():
        print(f"    {doc_type:20s}: {count} chunks")

    print(f"\n  Total chunks to embed: {len(chunks)}")
    print_sample_chunks(chunks)

    # Step 2: Embed and store
    print(f"\n[Step 2] Embedding and storing in ChromaDB at '{CHROMA_PATH}'...")
    print("  This may take several minutes for 500+ products...")
    total = store_chunks(chunks, persist_path=CHROMA_PATH)

    # Step 3: Verify
    print("\n[Step 3] Verification")
    stats = get_collection_stats(persist_path=CHROMA_PATH)
    print(f"  Collection: {stats['collection_name']}")
    print(f"  Total chunks stored: {stats['total_chunks']}")
    print(f"  Embedding model: {stats['embed_model']}")
    print(f"  Storage path: {stats['persist_path']}")

    # Step 4: Quick test query
    print("\n[Step 4] Quick test query")
    test_query = "What is the return policy for opened products?"
    print(f"  Query: '{test_query}'")

    from embedder import query_collection
    results = query_collection(test_query, n_results=3, persist_path=CHROMA_PATH)

    print("\n  Top 3 retrieved chunks:")
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        similarity = 1 - dist
        print(f"\n  [{i+1}] Source: {meta['source']} | Type: {meta['type']} | Similarity: {similarity:.3f}")
        print(f"       Preview: {doc[:120]}...")

    print("\n" + "=" * 60)
    print("  KB built successfully! Ready for Exercise 3 (RAG Pipeline)")
    print("=" * 60)


if __name__ == "__main__":
    main()
