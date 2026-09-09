"""
rebuild_kb_and_evaluate.py
Rebuilds ChromaDB with nomic-embed-text via Ollama, then evaluates tinyllama,
qwen2:0.5b, and deepseek-coder across 25 questions.

Run from the shopbot/ root:
    python evaluation/rebuild_kb_and_evaluate.py
"""

import sys, os, json, time, re, subprocess

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT          = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KB_DIR        = os.path.join(ROOT, "knowledge_base")
CHROMA_PATH   = os.path.join(ROOT, "ex2_knowledge_base", "chroma_db")
QUESTIONS     = os.path.join(ROOT, "evaluation", "questions.json")
RESULTS_DIR   = os.path.join(ROOT, "evaluation", "results")
OLLAMA_URL    = "http://localhost:11434"
EMBED_MODEL   = "nomic-embed-text"
COLLECTION    = "shopbot_kb"
MODELS        = ["tinyllama", "qwen2:0.5b", "deepseek-coder"]

os.makedirs(RESULTS_DIR, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "ex2_knowledge_base"))
sys.path.insert(0, os.path.join(ROOT, "ex3_rag"))

import requests
import chromadb

# ── Embedding via Ollama ──────────────────────────────────────────────────────

def embed(text: str):
    r = requests.post(f"{OLLAMA_URL}/api/embeddings",
                      json={"model": EMBED_MODEL, "prompt": text}, timeout=60)
    r.raise_for_status()
    return r.json()["embedding"]


# ── Build KB ─────────────────────────────────────────────────────────────────

def build_kb():
    print(f"\n{'='*60}")
    print("  STEP 1: Building ChromaDB with nomic-embed-text (768 dims)")
    print(f"{'='*60}")

    from chunker import (
        chunk_products, chunk_markdown, chunk_faq, chunk_shipping, load_all_chunks
    )

    all_chunks = load_all_chunks(KB_DIR)

    print(f"  Total chunks to embed: {len(all_chunks)}")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # Delete old collection if exists
    try:
        client.delete_collection(COLLECTION)
        print("  Deleted old collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

    ids, embeddings, documents, metadatas = [], [], [], []
    for i, chunk in enumerate(all_chunks):
        print(f"  Embedding chunk {i+1}/{len(all_chunks)}: {chunk['id'][:50]}", end="\r")
        emb = embed(chunk["text"])
        ids.append(chunk["id"])
        embeddings.append(emb)
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])

        if len(ids) >= 10:
            collection.add(ids=ids, embeddings=embeddings,
                           documents=documents, metadatas=metadatas)
            ids, embeddings, documents, metadatas = [], [], [], []

    if ids:
        collection.add(ids=ids, embeddings=embeddings,
                       documents=documents, metadatas=metadatas)

    count = collection.count()
    print(f"\n  Done! {count} chunks stored in ChromaDB.")
    return count


# ── Retrieve ──────────────────────────────────────────────────────────────────

def retrieve(question: str, k: int = 3):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(COLLECTION)
    q_emb = embed(question)
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        sim = round(1 - dist, 4)
        if sim >= 0.3:
            chunks.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "type": meta.get("type", "unknown"),
                "similarity_score": sim,
            })
    return chunks


# ── LLM Generate ─────────────────────────────────────────────────────────────

def generate(model: str, prompt: str):
    t0 = time.time()
    r = requests.post(f"{OLLAMA_URL}/api/generate",
                      json={"model": model, "prompt": prompt,
                            "stream": False, "options": {"temperature": 0.2}},
                      timeout=120)
    r.raise_for_status()
    data = r.json()
    elapsed = round((time.time() - t0) * 1000)
    return data.get("response", "").strip(), elapsed, data.get("eval_count", 0)


# ── Metrics ───────────────────────────────────────────────────────────────────

def score_correctness(actual, ground_truth):
    if not actual or not ground_truth:
        return 0.0
    stop = {"the","a","an","is","are","was","in","on","at","to","of","for","and","or","not","it","this","that","with"}
    gt_tokens = [t for t in re.findall(r'\b\w+\b', ground_truth.lower()) if t not in stop and len(t) > 2]
    if not gt_tokens:
        return 0.0
    matches = sum(1 for t in gt_tokens if t in actual.lower())
    ratio = matches / len(gt_tokens)
    return 1.0 if ratio >= 0.6 else (0.5 if ratio >= 0.3 else 0.0)


def score_relevance(question, actual):
    if not actual:
        return 0.0
    q_tokens = re.findall(r'\b\w{4,}\b', question.lower())
    if not q_tokens:
        return 0.0
    matches = sum(1 for t in q_tokens if t in actual.lower())
    return round(min(matches / len(q_tokens), 1.0), 3)


def score_retrieval(question, chunks, source_doc):
    if not chunks:
        return 0.0
    sources = [c["source"] for c in chunks]
    if source_doc in sources:
        return 1.0
    if any(source_doc.split(".")[0] in s for s in sources):
        return 0.5
    return 0.0


def detect_hallucination(actual, is_trap, trap_type, ground_truth):
    if not actual:
        return False
    if is_trap and trap_type == "product_not_in_kb":
        deny_words = ["don't", "do not", "not available", "not found",
                      "not carry", "not sell", "cannot find", "no information"]
        return not any(w in actual.lower() for w in deny_words)
    if is_trap and trap_type in ("service_not_offered", "policy_not_exist"):
        deny_words = ["no", "not", "don't", "do not", "cannot", "unavailable"]
        return not any(w in actual.lower() for w in deny_words)
    return False


# ── Evaluate one model ────────────────────────────────────────────────────────

def evaluate_model(model, questions):
    print(f"\n{'='*60}")
    print(f"  EVALUATING: {model.upper()}  ({len(questions)} questions)")
    print(f"{'='*60}")

    results = []
    for i, q in enumerate(questions):
        print(f"\n[{i+1:02d}/{len(questions)}] {q['question'][:70]}...")

        # Retrieve
        t_ret0 = time.time()
        chunks = retrieve(q["question"])
        ret_ms = round((time.time() - t_ret0) * 1000)

        # Build context
        if chunks:
            context = "\n\n---\n\n".join(
                f"[Source: {c['source']}]\n{c['text']}" for c in chunks
            )
        else:
            context = "No relevant information found."

        # Build prompt
        prompt = (
            "You are ShopBot, a helpful assistant for TechMart electronics store.\n"
            "Answer ONLY based on the context provided. If information is not in the context, say so.\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION: {q['question']}\n\nANSWER:"
        )

        # Generate
        try:
            actual, llm_ms, tokens = generate(model, prompt)
            total_ms = ret_ms + llm_ms
            error = None
        except Exception as e:
            actual, llm_ms, tokens, total_ms = "", 0, 0, 0
            error = str(e)
            print(f"  ERROR: {e}")

        # Score
        correct  = score_correctness(actual, q["ground_truth"])
        relevance = score_relevance(q["question"], actual)
        retrieval = score_retrieval(q["question"], chunks, q["source_doc"])
        hallucinated = detect_hallucination(
            actual, q["hallucination_trap"], q.get("trap_type",""), q["ground_truth"]
        )

        flag = "GREEN" if correct == 1.0 else ("YELLOW" if correct == 0.5 else "RED")
        hall = "HALLUCINATED" if hallucinated else "OK"
        print(f"  [{flag}] Correct:{correct:.1f} Relevance:{relevance:.2f} Retrieval:{retrieval:.2f} {hall}")
        print(f"  Total:{total_ms}ms | LLM:{llm_ms}ms | Tokens:{tokens}")

        results.append({
            "question_id": q["id"],
            "category": q["category"],
            "question": q["question"],
            "ground_truth": q["ground_truth"],
            "actual_response": actual,
            "model": model,
            "hallucination_trap": q["hallucination_trap"],
            "trap_type": q.get("trap_type", ""),
            "error": error,
            "correctness": correct,
            "relevance": relevance,
            "retrieval_quality": retrieval,
            "hallucinated": hallucinated,
            "chunks_retrieved": len(chunks),
            "top_similarity": chunks[0]["similarity_score"] if chunks else 0,
            "chunk_sources": [c["source"] for c in chunks],
            "latency_ms": total_ms,
            "retrieve_ms": ret_ms,
            "llm_ms": llm_ms,
            "tokens_used": tokens,
        })
        time.sleep(0.3)

    return summarise(model, results)


# ── Summarise ─────────────────────────────────────────────────────────────────

def summarise(model, results):
    n = len(results)
    traps = [r for r in results if r["hallucination_trap"]]
    s = {
        "avg_correctness":       round(sum(r["correctness"]       for r in results)/n, 3),
        "avg_relevance":         round(sum(r["relevance"]         for r in results)/n, 3),
        "avg_retrieval_quality": round(sum(r["retrieval_quality"] for r in results)/n, 3),
        "hallucination_rate":    round(sum(1 for r in results if r["hallucinated"])/n, 3),
        "hallucination_count":   sum(1 for r in results if r["hallucinated"]),
        "trap_hallucination_rate": round(sum(1 for r in traps if r["hallucinated"])/max(len(traps),1),3),
        "correct_count":   sum(1 for r in results if r["correctness"]==1.0),
        "partial_count":   sum(1 for r in results if r["correctness"]==0.5),
        "incorrect_count": sum(1 for r in results if r["correctness"]==0.0),
        "avg_latency_ms":    round(sum(r["latency_ms"]  for r in results)/n, 1),
        "avg_retrieve_ms":   round(sum(r["retrieve_ms"] for r in results)/n, 1),
        "avg_llm_ms":        round(sum(r["llm_ms"]      for r in results)/n, 1),
        "avg_tokens_used":   round(sum(r["tokens_used"] for r in results)/n, 1),
        "total_tokens":      sum(r["tokens_used"] for r in results),
        "total_questions": n,
        "model": model,
    }
    return {"model": model, "total_questions": n, "results": results, "summary": s}


# ── Save & Print ──────────────────────────────────────────────────────────────

def save(model, data):
    safe = model.replace(":", "_").replace("/", "_")
    path = os.path.join(RESULTS_DIR, f"{safe}_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\n  Results saved: {path}")
    return path


def print_summary(data):
    s = data["summary"]
    m = data["model"]
    print(f"\n{'─'*55}")
    print(f"  SUMMARY -- {m.upper()}")
    print(f"{'─'*55}")
    print(f"  Correctness:       {s['avg_correctness']:.3f}  ({s['correct_count']} correct, {s['partial_count']} partial, {s['incorrect_count']} wrong)")
    print(f"  Relevance:         {s['avg_relevance']:.3f}")
    print(f"  Retrieval Quality: {s['avg_retrieval_quality']:.3f}")
    print(f"  Hallucination:     {s['hallucination_rate']:.1%}  ({s['hallucination_count']}/{s['total_questions']})")
    print(f"  Trap Hallucin.:    {s['trap_hallucination_rate']:.1%}")
    print(f"  Avg Latency:       {s['avg_latency_ms']:.0f}ms  (LLM:{s['avg_llm_ms']:.0f}ms | Retrieve:{s['avg_retrieve_ms']:.0f}ms)")
    print(f"  Avg Tokens:        {s['avg_tokens_used']:.0f} | Total: {s['total_tokens']}")
    print(f"{'─'*55}")


def print_comparison(all_data):
    summaries = [d["summary"] for d in all_data]
    models    = [d["model"]   for d in all_data]
    col_w = 18
    print(f"\n{'='*70}")
    print("  CROSS-MODEL COMPARISON (Lightweight Models)")
    print(f"{'='*70}")
    header = f"  {'Metric':<25}" + "".join(f"{m:<{col_w}}" for m in models)
    print(header)
    print("  " + "-" * (25 + col_w * len(models)))
    rows = [
        ("Correctness",        "avg_correctness",       ".3f"),
        ("Relevance",          "avg_relevance",         ".3f"),
        ("Retrieval Quality",  "avg_retrieval_quality", ".3f"),
        ("Hallucination Rate", "hallucination_rate",    ".1%"),
        ("Correct Answers",    "correct_count",         "d"),
        ("Avg Latency (ms)",   "avg_latency_ms",        ".0f"),
        ("Avg Tokens",         "avg_tokens_used",       ".0f"),
    ]
    for label, key, fmt in rows:
        vals = "".join(f"{format(s[key], fmt):<{col_w}}" for s in summaries)
        print(f"  {label:<25}{vals}")
    print(f"{'='*70}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Step 1: Build KB
    build_kb()

    # Step 2: Load questions
    with open(QUESTIONS, encoding="utf-8") as f:
        questions = json.load(f)

    # Step 3: Evaluate each model
    all_data = []
    for model in MODELS:
        data = evaluate_model(model, questions)
        print_summary(data)
        save(model, data)
        all_data.append(data)

    # Step 4: Comparison table
    print_comparison(all_data)
    print("\nAll done! Results saved to evaluation/results/")


if __name__ == "__main__":
    main()
