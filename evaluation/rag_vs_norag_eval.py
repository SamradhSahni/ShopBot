"""
rag_vs_norag_eval.py — RAG vs No-RAG Evaluation
=================================================
Evaluates ShopBot on all 25 questions in TWO modes:
  1. RAG mode    — question -> ChromaDB retrieval -> LLM with context
  2. No-RAG mode — question -> LLM directly (no retrieval)

Usage (run from shopbot/ root):
    python evaluation/rag_vs_norag_eval.py
    python evaluation/rag_vs_norag_eval.py --model deepseek-coder
    python evaluation/rag_vs_norag_eval.py --model codellama --top-k 5

Outputs:
    evaluation/results/rag_vs_norag_<model>.json
    evaluation/rag_vs_norag_report_<model>.md
"""

import os, sys, json, time, re, argparse, requests

EVAL_DIR       = os.path.dirname(os.path.abspath(__file__))
SHOPBOT_ROOT   = os.path.join(EVAL_DIR, "..")
QUESTIONS_PATH = os.path.join(EVAL_DIR, "questions.json")
RESULTS_DIR    = os.path.join(EVAL_DIR, "results")
CHROMA_PATH    = os.path.join(SHOPBOT_ROOT, "ex3_rag", "chroma_db")
OLLAMA_URL     = os.getenv("OLLAMA_URL", "http://localhost:11434")
os.makedirs(RESULTS_DIR, exist_ok=True)

SYSTEM_PROMPT = """You are ShopBot, TechMart's helpful customer support assistant.
Answer in plain, friendly English. Do NOT include markdown headers or source labels.
Give a direct, complete answer. Never invent product names, prices, or policies. If unsure, say so."""

RAG_PROMPT = """You are ShopBot, TechMart's AI support assistant.
Using ONLY the store information below, write a friendly plain-English answer.
Do NOT repeat source labels or markdown. If not in context, say so.

Store Information:
{context}

Customer: {question}
ShopBot:"""

NORAG_PROMPT = """You are ShopBot, TechMart's AI support assistant.
Answer the following customer question based on your knowledge.
If unsure about specifics, say so clearly.

Customer: {question}
ShopBot:"""


def score_correctness(actual, ground_truth):
    if not actual or not ground_truth: return 0.0
    stop = {"the","a","an","is","are","was","in","on","at","to","of","for","and","or","not","it","this","that","with"}
    gt_tokens = [t for t in re.findall(r'\b\w+\b', ground_truth.lower()) if t not in stop and len(t) > 2]
    if not gt_tokens: return 0.0
    matches = sum(1 for t in gt_tokens if t in actual.lower())
    ratio = matches / len(gt_tokens)
    return 1.0 if ratio >= 0.6 else (0.5 if ratio >= 0.3 else 0.0)


def score_relevance(question, actual):
    if not actual: return 0.0
    q_tokens = re.findall(r'\b\w{4,}\b', question.lower())
    if not q_tokens: return 0.5
    matches = sum(1 for t in q_tokens if t in actual.lower())
    return round(min(matches / len(q_tokens) * 1.2, 1.0), 2)


def detect_hallucination(actual, is_trap, trap_type=""):
    al = actual.lower()
    deny = ["don't have","do not have","not available","unable to","cannot access",
            "no information","i don't know","contact support","not listed","not offered"]
    if is_trap:
        if trap_type == "requires_live_data":
            admitted = any(p in al for p in deny)
            return not admitted, "Should admit no live access" if not admitted else "Correctly deferred"
        elif trap_type == "product_not_in_catalogue":
            m = re.search(r'\$\d+|\d+ dollars', al)
            return (True, f"Invented price: {m.group()}") if m else (False, "Correctly acknowledged")
        elif trap_type in ("policy_not_offered","policy_not_in_kb"):
            admitted = any(p in al for p in deny)
            return not admitted, "Should say not available" if not admitted else "Correctly uncertain"
    return False, "Standard factual question"


def embed_query(question):
    r = requests.post(f"{OLLAMA_URL}/api/embeddings",
                      json={"model": "nomic-embed-text", "prompt": question}, timeout=60)
    r.raise_for_status()
    return r.json()["embedding"]


def retrieve(collection, question, top_k):
    emb = embed_query(question)
    res = collection.query(query_embeddings=[emb], n_results=top_k,
                           include=["documents","metadatas","distances"])
    chunks, parts = [], []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        sim = round(1 - dist, 4)
        chunks.append({"text": doc[:200], "source": meta.get("source","?"), "similarity": sim})
        parts.append(f"[{meta.get('source','?')}] {doc}")
    return "\n\n".join(parts), chunks


def call_llm(prompt, model):
    payload = {"model": model, "prompt": prompt, "system": SYSTEM_PROMPT,
               "stream": False, "options": {"temperature": 0.2, "num_predict": -1, "num_ctx": 4096, "num_thread": 4}}
    t0 = time.time()
    r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=300)
    r.raise_for_status()
    d = r.json()
    return d.get("response","").strip(), int((time.time()-t0)*1000), d.get("eval_count", 0)


def eval_rag(q, model, col, top_k):
    try:
        ctx, chunks = retrieve(col, q["question"], top_k)
        resp, ms, tok = call_llm(RAG_PROMPT.format(context=ctx, question=q["question"]), model)
    except Exception as e:
        return {"mode":"rag","response":f"ERROR:{e}","latency_ms":0,"tokens_used":0,"chunks_retrieved":0,"chunks":[],
                "correctness":0.0,"relevance":0.0,"hallucinated":False,"hallucination_notes":str(e)}
    hal, note = detect_hallucination(resp, q["hallucination_trap"], q.get("trap_type",""))
    return {"mode":"rag","response":resp,"latency_ms":ms,"tokens_used":tok,"chunks_retrieved":len(chunks),"chunks":chunks,
            "correctness":score_correctness(resp,q["ground_truth"]),
            "relevance":score_relevance(q["question"],resp),
            "hallucinated":hal,"hallucination_notes":note}


def eval_norag(q, model):
    try:
        resp, ms, tok = call_llm(NORAG_PROMPT.format(question=q["question"]), model)
    except Exception as e:
        return {"mode":"no_rag","response":f"ERROR:{e}","latency_ms":0,"tokens_used":0,"chunks_retrieved":0,
                "correctness":0.0,"relevance":0.0,"hallucinated":False,"hallucination_notes":str(e)}
    hal, note = detect_hallucination(resp, q["hallucination_trap"], q.get("trap_type",""))
    return {"mode":"no_rag","response":resp,"latency_ms":ms,"tokens_used":tok,"chunks_retrieved":0,
            "correctness":score_correctness(resp,q["ground_truth"]),
            "relevance":score_relevance(q["question"],resp),
            "hallucinated":hal,"hallucination_notes":note}


def save_report(data, model_slug):
    model = data["model"]; rm = data["rag_summary"]; nm = data["no_rag_summary"]
    n = data["total_questions"]; per_q = data["per_question"]
    def pct(v): return f"{v*100:.1f}%"
    def delta(a,b): return f"{a-b:+.3f}"
    def iw(a,b,lb=False): return ("RAG" if (a<b if lb else a>b) else ("No-RAG" if (b<a if lb else b>a) else "Tie"))

    lines = [
        f"# ShopBot RAG vs No-RAG Evaluation Report",
        f"",
        f"> **Model:** `{model}` | **Questions:** {n} | **Top-K:** {data['top_k']} | **Date:** {data['evaluated_at']}",
        f"",
        f"---", f"",
        f"## Summary Comparison", f"",
        f"| Metric | RAG | No-RAG | Delta | Winner |",
        f"|---|---|---|---|---|",
        f"| Avg Correctness | {rm['avg_correctness']:.3f} | {nm['avg_correctness']:.3f} | {delta(rm['avg_correctness'],nm['avg_correctness'])} | {iw(rm['avg_correctness'],nm['avg_correctness'])} |",
        f"| Avg Relevance | {rm['avg_relevance']:.3f} | {nm['avg_relevance']:.3f} | {delta(rm['avg_relevance'],nm['avg_relevance'])} | {iw(rm['avg_relevance'],nm['avg_relevance'])} |",
        f"| Hallucination Rate | {pct(rm['hallucination_rate'])} | {pct(nm['hallucination_rate'])} | {delta(nm['hallucination_rate'],rm['hallucination_rate'])} | {iw(rm['hallucination_rate'],nm['hallucination_rate'],True)} |",
        f"| Correct Answers | {rm['correct_count']}/{n} | {nm['correct_count']}/{n} | {rm['correct_count']-nm['correct_count']:+d} | {iw(rm['correct_count'],nm['correct_count'])} |",
        f"| Avg Latency | {rm['avg_latency_ms']:.0f}ms | {nm['avg_latency_ms']:.0f}ms | {rm['avg_latency_ms']-nm['avg_latency_ms']:+.0f}ms | {iw(rm['avg_latency_ms'],nm['avg_latency_ms'],True)} |",
        f"| Avg Tokens | {rm['avg_tokens']:.0f} | {nm['avg_tokens']:.0f} | {rm['avg_tokens']-nm['avg_tokens']:+.0f} | — |",
        f"", f"---", f"",
        f"## Per-Question Results", f"",
        f"| ID | Question | RAG | No-RAG | RAG Hallu | NoRAG Hallu |",
        f"|---|---|---|---|---|---|",
    ]
    for r in per_q:
        qsh = (r["question"][:38]+"…") if len(r["question"])>38 else r["question"]
        rc  = {1.0:"Full",0.5:"Partial",0.0:"Miss"}[r["rag"]["correctness"]]
        nc  = {1.0:"Full",0.5:"Partial",0.0:"Miss"}[r["no_rag"]["correctness"]]
        lines.append(f"| {r['id']} | {qsh} | {rc} | {nc} | {'Yes' if r['rag']['hallucinated'] else 'No'} | {'Yes' if r['no_rag']['hallucinated'] else 'No'} |")

    lines += [f"", f"---", f"", f"## Detailed Responses", f""]
    for r in per_q:
        lines += [
            f"### {r['id']}: {r['question']}",
            f"**Ground Truth:** {r['ground_truth']}",
            f"",
            f"**RAG** (C:{r['rag']['correctness']} R:{r['rag']['relevance']} H:{'Yes' if r['rag']['hallucinated'] else 'No'} {r['rag']['latency_ms']}ms {r['rag']['chunks_retrieved']}chunks)",
            f"> {r['rag']['response'][:600]}",
            f"",
            f"**No-RAG** (C:{r['no_rag']['correctness']} R:{r['no_rag']['relevance']} H:{'Yes' if r['no_rag']['hallucinated'] else 'No'} {r['no_rag']['latency_ms']}ms)",
            f"> {r['no_rag']['response'][:600]}",
            f"", f"---", f"",
        ]

    rag_wins   = sum(1 for r in per_q if r["rag"]["correctness"] > r["no_rag"]["correctness"])
    norag_wins = sum(1 for r in per_q if r["no_rag"]["correctness"] > r["rag"]["correctness"])
    lines += [
        f"## Key Findings", f"",
        f"- RAG better on {rag_wins}/{n} questions",
        f"- No-RAG better on {norag_wins}/{n} questions",
        f"- Tied on {n-rag_wins-norag_wins}/{n} questions",
        f"- Correctness improvement from RAG: {(rm['avg_correctness']-nm['avg_correctness'])*100:+.1f}%",
        f"- Hallucination reduction from RAG: {(nm['hallucination_rate']-rm['hallucination_rate'])*100:+.1f}pp",
    ]

    path = os.path.join(EVAL_DIR, f"rag_vs_norag_report_{model_slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report saved -> {path}")


def run(model, top_k):
    print(f"\n{'='*60}")
    print(f"  RAG vs No-RAG | Model: {model} | Top-K: {top_k}")
    print(f"{'='*60}")

    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        questions = json.load(f)
    print(f"Loaded {len(questions)} questions")

    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        col = client.get_collection("shopbot_kb")
        print(f"ChromaDB: {col.count()} chunks")
    except Exception as e:
        print(f"ChromaDB error: {e}\nRun: python evaluation/rebuild_kb_and_evaluate.py first")
        sys.exit(1)

    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        avail = [m["name"] for m in r.json().get("models",[])]
        if not any(model in m for m in avail):
            print(f"Model '{model}' not in Ollama. Available: {avail}")
            print(f"Run: ollama pull {model}")
            sys.exit(1)
        print(f"Ollama OK — {model} available")
    except Exception as e:
        print(f"Ollama error: {e}"); sys.exit(1)

    all_results = []
    for i, q in enumerate(questions):
        print(f"\n[{i+1:02d}/{len(questions)}] {q['id']}: {q['question'][:50]}...")
        rag_r   = eval_rag(q, model, col, top_k)
        norag_r = eval_norag(q, model)
        print(f"  RAG:   C={rag_r['correctness']} R={rag_r['relevance']} H={'Y' if rag_r['hallucinated'] else 'N'} {rag_r['latency_ms']}ms {rag_r['chunks_retrieved']}chunks")
        print(f"  NoRAG: C={norag_r['correctness']} R={norag_r['relevance']} H={'Y' if norag_r['hallucinated'] else 'N'} {norag_r['latency_ms']}ms")
        all_results.append({"id":q["id"],"category":q["category"],"question":q["question"],
                             "ground_truth":q["ground_truth"],"requires_rag":q["requires_rag"],
                             "hallucination_trap":q["hallucination_trap"],"rag":rag_r,"no_rag":norag_r})

    def avg(lst): return round(sum(lst)/len(lst),4) if lst else 0.0
    n = len(all_results)

    rm = {"avg_correctness":avg([r["rag"]["correctness"] for r in all_results]),
          "avg_relevance":avg([r["rag"]["relevance"] for r in all_results]),
          "avg_latency_ms":avg([r["rag"]["latency_ms"] for r in all_results]),
          "avg_tokens":avg([r["rag"]["tokens_used"] for r in all_results]),
          "hallucination_rate":round(sum(1 for r in all_results if r["rag"]["hallucinated"])/n,4),
          "correct_count":sum(1 for r in all_results if r["rag"]["correctness"]==1.0),
          "partial_count":sum(1 for r in all_results if r["rag"]["correctness"]==0.5)}
    nm = {"avg_correctness":avg([r["no_rag"]["correctness"] for r in all_results]),
          "avg_relevance":avg([r["no_rag"]["relevance"] for r in all_results]),
          "avg_latency_ms":avg([r["no_rag"]["latency_ms"] for r in all_results]),
          "avg_tokens":avg([r["no_rag"]["tokens_used"] for r in all_results]),
          "hallucination_rate":round(sum(1 for r in all_results if r["no_rag"]["hallucinated"])/n,4),
          "correct_count":sum(1 for r in all_results if r["no_rag"]["correctness"]==1.0),
          "partial_count":sum(1 for r in all_results if r["no_rag"]["correctness"]==0.5)}

    output = {"model":model,"top_k":top_k,"total_questions":n,
              "evaluated_at":time.strftime("%Y-%m-%dT%H:%M:%S"),
              "rag_summary":rm,"no_rag_summary":nm,"per_question":all_results}

    model_slug = model.replace(":","_").replace("/","_")
    json_path  = os.path.join(RESULTS_DIR, f"rag_vs_norag_{model_slug}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nJSON saved -> {json_path}")

    save_report(output, model_slug)

    print(f"\n{'='*60}")
    print(f"  FINAL SUMMARY — {model}")
    print(f"{'='*60}")
    print(f"  {'Metric':<25} {'RAG':>8} {'No-RAG':>8}")
    print(f"  {'-'*45}")
    print(f"  {'Avg Correctness':<25} {rm['avg_correctness']:>8.3f} {nm['avg_correctness']:>8.3f}")
    print(f"  {'Avg Relevance':<25} {rm['avg_relevance']:>8.3f} {nm['avg_relevance']:>8.3f}")
    print(f"  {'Hallucination Rate':<25} {rm['hallucination_rate']*100:>7.1f}% {nm['hallucination_rate']*100:>7.1f}%")
    print(f"  {'Correct Answers':<25} {rm['correct_count']:>8} {nm['correct_count']:>8}")
    print(f"  {'Avg Latency (ms)':<25} {rm['avg_latency_ms']:>8.0f} {nm['avg_latency_ms']:>8.0f}")
    print(f"  RAG correctness gain: {(rm['avg_correctness']-nm['avg_correctness'])*100:+.1f}%")
    print(f"  Saved: {json_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",  default="deepseek-coder")
    parser.add_argument("--top-k",  type=int, default=3)
    args = parser.parse_args()
    run(args.model, args.top_k)
