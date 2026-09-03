"""
codebase_indexer.py — Index ShopBot's own source code into ChromaDB (W4-E6)
Enables multi-file, cross-component Q&A about the ShopBot codebase itself.

Usage:
    python codebase_indexer.py --build     # Index all .py files
    python codebase_indexer.py --query "Which files handle RAG retrieval?"
    python codebase_indexer.py --demo      # Run all 8 cross-file demo questions
"""

import sys, os, re, json, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex1_basic"))

import requests
import chromadb
from pathlib import Path

SHOPBOT_ROOT    = Path(os.path.dirname(__file__)).parent
CHROMA_PATH     = str(SHOPBOT_ROOT / "ex6_codebase" / "codebase_chroma_db")
COLLECTION_NAME = "shopbot_codebase"
OLLAMA_URL      = "http://localhost:11434"
EMBED_MODEL     = "nomic-embed-text"
LLM_MODEL       = "codellama"

# Directories to index
INDEX_DIRS = [
    "ex1_basic",
    "ex2_knowledge_base",
    "ex3_rag",
    "ex4_services/app_service",
    "ex4_services/rag_service",
    "ex4_services/llm_service",
    "ex4_services/data_service",
    "evaluation",
]

# Cross-file demo questions for W4-E6
DEMO_QUESTIONS = [
    "Which files are involved in processing a user chat request end-to-end?",
    "Which service or module handles vector similarity search and retrieval?",
    "What happens after the user submits a message in the chat UI?",
    "Which components would break or be affected if ChromaDB becomes unavailable?",
    "Which files would need to change to add a new LLM model to ShopBot?",
    "How does the RAG service communicate with the LLM service?",
    "Which function is responsible for embedding user queries into vectors?",
    "What test or evaluation scripts exist and what do they measure?",
]


# ── Chunking Strategy: Split by function/class ────────────────────────────────

def chunk_python_file(filepath: Path, content: str) -> list[dict]:
    """
    Chunk a Python file by function and class definitions.
    Each function/class becomes one chunk, preserving its full source.
    """
    chunks = []
    lines = content.split("\n")
    current_chunk_lines = []
    current_name = f"module:{filepath.stem}"
    chunk_start = 0

    for i, line in enumerate(lines):
        # Detect function or class definition
        func_match = re.match(r'^(def |class )', line)
        if func_match and current_chunk_lines:
            # Save previous chunk
            chunk_text = "\n".join(current_chunk_lines).strip()
            if len(chunk_text) > 50:
                chunks.append(_make_chunk(filepath, current_name, chunk_text, chunk_start))
            current_chunk_lines = []
            current_name = line.strip().split("(")[0].replace("def ", "").replace("class ", "")
            chunk_start = i

        current_chunk_lines.append(line)

    # Save final chunk
    if current_chunk_lines:
        chunk_text = "\n".join(current_chunk_lines).strip()
        if len(chunk_text) > 50:
            chunks.append(_make_chunk(filepath, current_name, chunk_text, chunk_start))

    return chunks


def _make_chunk(filepath: Path, name: str, text: str, start_line: int) -> dict:
    rel_path = str(filepath.relative_to(SHOPBOT_ROOT)).replace("\\", "/")
    return {
        "id": f"{rel_path}::{name}".replace(" ", "_")[:100],
        "text": f"File: {rel_path}\nFunction/Class: {name}\n\n{text}",
        "metadata": {
            "file": rel_path,
            "name": name,
            "type": "python_code",
            "start_line": start_line,
            "service": rel_path.split("/")[0] if "/" in rel_path else "root",
        }
    }


# ── Embedding & Storage ───────────────────────────────────────────────────────

def embed(text: str) -> list[float]:
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


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client, client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def build_index():
    """Index all Python files in the ShopBot project."""
    print(f"\n{'='*60}")
    print(f"  ShopBot Codebase Indexer — W4-E6")
    print(f"  Root: {SHOPBOT_ROOT}")
    print(f"{'='*60}\n")

    all_chunks = []
    for dir_name in INDEX_DIRS:
        dir_path = SHOPBOT_ROOT / dir_name
        if not dir_path.exists():
            continue
        py_files = list(dir_path.glob("*.py"))
        print(f"📁 {dir_name}/ — {len(py_files)} Python files")
        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            chunks = chunk_python_file(py_file, content)
            all_chunks.extend(chunks)
            print(f"   ✓ {py_file.name} → {len(chunks)} chunks")

    print(f"\n📊 Total chunks to index: {len(all_chunks)}")

    client, collection = get_collection()
    existing_ids = set(collection.get()["ids"])

    ids, embeddings, docs, metas = [], [], [], []
    skipped = 0

    print(f"\n🔢 Embedding code chunks using '{EMBED_MODEL}'...")
    for i, chunk in enumerate(all_chunks):
        if chunk["id"] in existing_ids:
            skipped += 1
            continue
        print(f"  [{i+1}/{len(all_chunks)}] {chunk['id'][:60]}...", end="\r")
        emb = embed(chunk["text"])
        ids.append(chunk["id"])
        embeddings.append(emb)
        docs.append(chunk["text"])
        metas.append(chunk["metadata"])

        if len(ids) >= 10:
            collection.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metas)
            ids, embeddings, docs, metas = [], [], [], []

    if ids:
        collection.add(ids=ids, embeddings=embeddings, documents=docs, metadatas=metas)

    total = collection.count()
    print(f"\n✅ Codebase indexed: {total} chunks ({skipped} skipped)\n")
    return total


# ── Query ─────────────────────────────────────────────────────────────────────

def query_codebase(question: str, top_k: int = 5) -> dict:
    """Retrieve relevant code chunks and ask Code Llama about them."""
    _, collection = get_collection()

    query_emb = embed(question)
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        chunks.append({
            "text": doc,
            "file": meta.get("file", ""),
            "name": meta.get("name", ""),
            "service": meta.get("service", ""),
            "similarity": round(1 - dist, 3)
        })

    # Build context
    context = "\n\n---\n\n".join(c["text"] for c in chunks)

    prompt = f"""You are a code understanding assistant. Analyse the following ShopBot AI source code 
and answer the question about the codebase architecture and relationships.

SOURCE CODE CONTEXT:
{context}

QUESTION ABOUT THE CODEBASE:
{question}

Provide a clear, specific answer that references actual file names and function names from the context."""

    r = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 400}
    }, timeout=120)
    r.raise_for_status()
    answer = r.json().get("response", "").strip()

    return {
        "question": question,
        "answer": answer,
        "relevant_files": list(set(c["file"] for c in chunks)),
        "relevant_functions": [c["name"] for c in chunks],
        "chunks_used": len(chunks),
    }


def run_demo():
    """Run all 8 cross-file demo questions."""
    print(f"\n{'='*65}")
    print(f"  ShopBot W4-E6: Cross-File Codebase Understanding Demo")
    print(f"{'='*65}\n")

    results = []
    for i, question in enumerate(DEMO_QUESTIONS):
        print(f"\n[{i+1}/{len(DEMO_QUESTIONS)}] {question}")
        print("─" * 60)
        result = query_codebase(question)
        print(f"📁 Files referenced: {result['relevant_files']}")
        print(f"🔧 Functions: {result['relevant_functions']}")
        print(f"\n💬 Answer:\n{result['answer']}\n")
        results.append(result)

    # Save results
    out_path = SHOPBOT_ROOT / "ex6_codebase" / "codebase_qa_results.json"
    os.makedirs(out_path.parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved: {out_path}")


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ShopBot Codebase Indexer & Q&A (W4-E6)")
    parser.add_argument("--build",  action="store_true", help="Index all Python files")
    parser.add_argument("--query",  type=str,            help="Ask a question about the codebase")
    parser.add_argument("--demo",   action="store_true", help="Run all 8 demo questions")
    args = parser.parse_args()

    if args.build:
        build_index()
    elif args.query:
        result = query_codebase(args.query)
        print(f"\n❓ {result['question']}")
        print(f"📁 Relevant files: {result['relevant_files']}")
        print(f"\n💬 Answer:\n{result['answer']}")
    elif args.demo:
        run_demo()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
