"""
embedder_proxy.py — Thin proxy to access ex2 embedder from ex3
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex2_knowledge_base"))
from embedder import get_collection_stats

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "ex2_knowledge_base", "chroma_db")

def get_kb_stats():
    try:
        return get_collection_stats(persist_path=CHROMA_PATH)
    except Exception as e:
        return {"error": str(e), "total_chunks": 0}
