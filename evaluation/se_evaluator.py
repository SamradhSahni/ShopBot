"""
se_evaluator.py - Software Engineering Category-Wise Evaluation
===============================================================
Evaluates 3 LLM models (starcoder, codellama, deepseek-coder) on 35 questions
across 7 software-engineering categories using the ShopBot codebase as context.

Categories:
  1. Explanation              (5 questions)
  2. Code Retrieval           (5 questions)
  3. Dependency Understanding (5 questions)
  4. Bug Analysis             (5 questions)
  5. Code Generation          (5 questions)
  6. Refactoring              (5 questions)
  7. RAG-based Question       (5 questions)

Metrics per category:
  - Correctness (keyword overlap with ground truth, 0/0.5/1.0)
  - Relevance   (question term overlap in response, 0.0-1.0)
  - Retrieval Quality (correct source in retrieved chunks)
  - Hallucination Rate (%)
  - Code Test-Pass Rate (for Code Generation only)
  - Response Latency (ms)
  - Tokens Used

Usage (from shopbot/ root):
  python evaluation/se_evaluator.py --model codellama
  python evaluation/se_evaluator.py --model deepseek-coder
  python evaluation/se_evaluator.py --model starcoder
  python evaluation/se_evaluator.py --all
"""

import os, sys, json, time, re, argparse, requests, subprocess, tempfile

EVAL_DIR       = os.path.dirname(os.path.abspath(__file__))
SHOPBOT_ROOT   = os.path.join(EVAL_DIR, "..")
QUESTIONS_PATH = os.path.join(EVAL_DIR, "se_questions.json")
RESULTS_DIR    = os.path.join(EVAL_DIR, "results")
CHROMA_PATH    = os.path.join(SHOPBOT_ROOT, "ex2_knowledge_base", "chroma_db")
CODEBASE_CHROMA= os.path.join(SHOPBOT_ROOT, "ex6_codebase", "codebase_chroma_db")
OLLAMA_URL     = os.getenv("OLLAMA_URL", "http://localhost:11434")
os.makedirs(RESULTS_DIR, exist_ok=True)

CATEGORIES = [
    "Explanation",
    "Code Retrieval",
    "Dependency Understanding",
    "Bug Analysis",
    "Code Generation",
    "Refactoring",
    "RAG-based Question",
]

SYSTEM_PROMPT = """You are an expert software engineer and code analyst.
Answer questions about the ShopBot AI codebase clearly and precisely.
Reference actual function names, file names, and line-level details when you can.
For code generation questions, write clean, working Python code only - no explanations unless asked."""

RAG_PROMPT = """You are a software engineering expert analyzing the ShopBot AI codebase.
Use the following source code context to answer the question accurately.
Reference specific function names and file names from the context.

CODEBASE CONTEXT:
{context}

QUESTION:
{question}

Answer:"""

NORAG_PROMPT = """You are a software engineering expert.
Answer the following question about software engineering, Python code, or system architecture.

QUESTION:
{question}

Answer:"""


# ── Metrics ───────────────────────────────────────────────────────────────────

def score_correctness(actual, ground_truth):
    if not actual or not ground_truth: return 0.0
    stop = {"the","a","an","is","are","was","in","on","at","to","of","for","and","or",
            "not","it","this","that","with","as","by","from","be","if","do","we","its"}
    gt_tokens = [t for t in re.findall(r'\b\w+\b', ground_truth.lower())
                 if t not in stop and len(t) > 2]
    if not gt_tokens: return 0.0
    a_lower = actual.lower()
    matches = sum(1 for t in gt_tokens if t in a_lower)
    ratio = matches / len(gt_tokens)
    return 1.0 if ratio >= 0.6 else (0.5 if ratio >= 0.3 else 0.0)


def score_relevance(question, actual):
    if not actual: return 0.0
    q_tokens = re.findall(r'\b\w{4,}\b', question.lower())
    if not q_tokens: return 0.5
    a_lower = actual.lower()
    matches = sum(1 for t in q_tokens if t in a_lower)
    return round(min(matches / len(q_tokens) * 1.2, 1.0), 2)


def score_retrieval_quality(chunks, source_doc):
    if not source_doc: return 1.0  # Code Generation / Refactoring - no expected source
    if not chunks: return 0.0
    expected = [s.strip() for s in source_doc.split("+")]
    retrieved = [c.get("source","") for c in chunks]
    matched = sum(1 for e in expected if any(e in r for r in retrieved))
    return round(matched / len(expected), 2)


def test_code_pass(response, question_id):
    """
    Code Test-Pass Rate: extract code from response and run it.
    Returns (passed: bool, notes: str)
    """
    # Extract code block from response
    code_match = re.search(r'```(?:python)?\n?(.*?)```', response, re.DOTALL)
    if not code_match:
        # Try to find function definition directly
        func_match = re.search(r'(def \w+\(.*?)(?=\n\n|\Z)', response, re.DOTALL)
        if not func_match:
            return False, "No code block found in response"
        code = func_match.group(1)
    else:
        code = code_match.group(1)

    # Basic syntax check
    try:
        compile(code, "<string>", "exec")
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"

    # Category-specific test cases
    test_cases = {
        "CG01": """
import chromadb, os
get_top_chunk
c = chromadb.Client()
col = c.get_or_create_collection("test")
col.add(ids=["1"], documents=["hello world"], embeddings=[[0.1]*384])
# just check the function is callable
assert callable(get_top_chunk), "get_top_chunk must be a function"
print("PASS")
""",
        "CG02": """
count_chunks_by_source
assert callable(count_chunks_by_source)
print("PASS")
""",
        "CG03": """
ping
result = ping()
assert isinstance(result, dict), "ping must return a dict"
assert "status" in result, "response must have status"
assert result["status"] == "ok"
print("PASS")
""",
        "CG04": """
chunk_by_size
result = chunk_by_size("abcdefghij", 3)
assert result == ["abc", "def", "ghi", "j"], f"got {result}"
assert chunk_by_size("", 5) == []
print("PASS")
""",
        "CG05": """
score_keyword_overlap
assert score_keyword_overlap("the price is 349 dollars", "price 349 dollars") == 1.0
assert score_keyword_overlap("hello world", "completely different answer here") == 0.0
print("PASS")
""",
    }

    test_code = test_cases.get(question_id, "")
    if not test_code:
        # Just syntax check passed
        return True, "Syntax valid (no runtime test for this question)"

    full_code = code + "\n" + test_code
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            tmp_path = f.name
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True, timeout=10
        )
        os.unlink(tmp_path)
        if result.returncode == 0 and "PASS" in result.stdout:
            return True, "Tests passed"
        else:
            return False, f"Runtime error: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, "Timeout (>10s)"
    except Exception as e:
        return False, str(e)


def detect_hallucination(actual, is_trap=False, trap_type=""):
    al = actual.lower()
    deny = ["don't have","do not have","not available","unable to","cannot access",
            "no information","i don't know","contact support","not listed","not offered","i'm not sure"]
    if is_trap:
        admitted = any(p in al for p in deny)
        return not admitted, "Should admit uncertainty" if not admitted else "Correctly uncertain"
    return False, "Non-trap question"


# ── Ollama Calls ──────────────────────────────────────────────────────────────

def embed_text(text):
    for endpoint, pk, rk in [("/api/embed","input","embeddings"), ("/api/embeddings","prompt","embedding")]:
        try:
            r = requests.post(f"{OLLAMA_URL}{endpoint}",
                              json={"model":"nomic-embed-text", pk: text}, timeout=60)
            if r.status_code == 404: continue
            r.raise_for_status()
            d = r.json()
            return d[rk][0] if rk == "embeddings" else d[rk]
        except: continue
    raise RuntimeError("Embedding failed")


def call_llm(prompt, model):
    t0 = time.time()
    r = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": model, "prompt": prompt, "system": SYSTEM_PROMPT,
        "stream": False, "options": {"temperature": 0.1, "num_predict": -1, "num_ctx": 4096, "num_thread": 4}
    }, timeout=300)
    r.raise_for_status()
    d = r.json()
    return d.get("response","").strip(), int((time.time()-t0)*1000), d.get("eval_count",0)


def retrieve_context(question, source_doc, top_k=5):
    """Try codebase chromadb first, then KB chromadb."""
    chunks = []
    context = ""
    try:
        import chromadb as cdb
        # Try codebase index first
        for chroma_path, collection_name in [
            (CODEBASE_CHROMA, "shopbot_codebase"),
            (CHROMA_PATH,     "shopbot_kb"),
        ]:
            try:
                client = cdb.PersistentClient(path=chroma_path)
                col = client.get_collection(collection_name)
                if col.count() == 0: continue
                emb = embed_text(question)
                res = col.query(query_embeddings=[emb], n_results=min(top_k, col.count()),
                                include=["documents","metadatas","distances"])
                for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
                    chunks.append({
                        "text": doc[:600],
                        "source": meta.get("file", meta.get("source","unknown")),
                        "similarity": round(1-dist,3)
                    })
                if chunks:
                    context = "\n\n---\n\n".join(c["text"] for c in chunks)
                    break
            except Exception:
                continue
    except Exception:
        pass
    return context, chunks


# ── Per-question Evaluation ───────────────────────────────────────────────────

def evaluate_question(q, model):
    qid      = q["id"]
    category = q["category"]
    question = q["question"]
    gt       = q["ground_truth"]
    src      = q.get("source_doc","")
    is_cg    = (category == "Code Generation")

    # Retrieve context for RAG-dependent categories
    context, chunks = "", []
    if q.get("requires_rag", False):
        try:
            context, chunks = retrieve_context(question, src)
        except Exception as e:
            context = ""

    # Build prompt
    if context:
        prompt = RAG_PROMPT.format(context=context, question=question)
    else:
        prompt = NORAG_PROMPT.format(question=question)

    # Call LLM
    try:
        response, latency_ms, tokens = call_llm(prompt, model)
    except Exception as e:
        response, latency_ms, tokens = f"ERROR:{e}", 0, 0

    # Score metrics
    correctness = score_correctness(response, gt)
    relevance   = score_relevance(question, response)
    rq          = score_retrieval_quality(chunks, src)
    hal, hnotes = detect_hallucination(response)

    # Code test pass (Code Generation only)
    code_pass, code_notes = None, ""
    if is_cg:
        code_pass, code_notes = test_code_pass(response, qid)

    return {
        "id": qid,
        "category": category,
        "question": question,
        "ground_truth": gt,
        "response": response,
        "latency_ms": latency_ms,
        "tokens_used": tokens,
        "chunks_retrieved": len(chunks),
        "correctness": correctness,
        "relevance": relevance,
        "retrieval_quality": rq,
        "hallucinated": hal,
        "hallucination_notes": hnotes,
        "code_pass": code_pass,
        "code_notes": code_notes,
    }


# ── Main Evaluation ───────────────────────────────────────────────────────────

def run_evaluation(model):
    print(f"\n{'='*65}")
    print(f"  ShopBot SE Category-Wise Evaluation")
    print(f"  Model: {model}  |  35 Questions x 7 Categories")
    print(f"{'='*65}")

    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        questions = json.load(f)

    # Verify Ollama
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        avail = [m["name"] for m in r.json().get("models",[])]
        if not any(model in m for m in avail):
            print(f"Model '{model}' not found. Available: {avail}")
            print(f"Run: ollama pull {model}")
            sys.exit(1)
        print(f"Ollama OK — {model} available")
    except Exception as e:
        print(f"Ollama error: {e}"); sys.exit(1)

    all_results = []
    for i, q in enumerate(questions):
        print(f"\n[{i+1:02d}/35] {q['id']} ({q['category']}): {q['question'][:50]}...")
        result = evaluate_question(q, model)
        cp = f"Code:{'PASS' if result['code_pass'] else ('FAIL' if result['code_pass'] is False else 'N/A')}"
        print(f"  C={result['correctness']} R={result['relevance']} RQ={result['retrieval_quality']} H={'Y' if result['hallucinated'] else 'N'} {result['latency_ms']}ms {cp}")
        all_results.append(result)

    # ── Category Aggregation ─────────────────────────────────────────────────
    def avg(lst): return round(sum(lst)/len(lst), 4) if lst else 0.0

    category_stats = {}
    for cat in CATEGORIES:
        cat_results = [r for r in all_results if r["category"] == cat]
        is_cg = (cat == "Code Generation")
        code_results = [r for r in cat_results if r["code_pass"] is not None]

        category_stats[cat] = {
            "count": len(cat_results),
            "avg_correctness":      avg([r["correctness"] for r in cat_results]),
            "avg_relevance":        avg([r["relevance"] for r in cat_results]),
            "avg_retrieval_quality":avg([r["retrieval_quality"] for r in cat_results]),
            "hallucination_rate":   round(sum(1 for r in cat_results if r["hallucinated"])/len(cat_results),4) if cat_results else 0,
            "avg_latency_ms":       avg([r["latency_ms"] for r in cat_results]),
            "avg_tokens":           avg([r["tokens_used"] for r in cat_results]),
            "correct_count":        sum(1 for r in cat_results if r["correctness"] == 1.0),
            "partial_count":        sum(1 for r in cat_results if r["correctness"] == 0.5),
            "code_test_pass_rate":  round(sum(1 for r in code_results if r["code_pass"])/len(code_results),4) if code_results else None,
        }

    overall = {
        "avg_correctness":      avg([r["correctness"] for r in all_results]),
        "avg_relevance":        avg([r["relevance"] for r in all_results]),
        "avg_retrieval_quality":avg([r["retrieval_quality"] for r in all_results]),
        "hallucination_rate":   round(sum(1 for r in all_results if r["hallucinated"])/len(all_results),4),
        "avg_latency_ms":       avg([r["latency_ms"] for r in all_results]),
        "avg_tokens":           avg([r["tokens_used"] for r in all_results]),
        "correct_count":        sum(1 for r in all_results if r["correctness"] == 1.0),
    }

    output = {
        "model": model,
        "total_questions": len(all_results),
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "overall": overall,
        "by_category": category_stats,
        "per_question": all_results,
    }

    model_slug = model.replace(":","_").replace("/","_")
    json_path = os.path.join(RESULTS_DIR, f"se_eval_{model_slug}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nJSON saved -> {json_path}")

    # ── Print Category Summary ───────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  CATEGORY-WISE RESULTS — Model: {model}")
    print(f"{'='*70}")
    print(f"  {'Category':<26} {'Correct':>7} {'Relev':>6} {'RQ':>5} {'Hallu':>6} {'CTP':>5} {'ms':>7}")
    print(f"  {'-'*65}")
    for cat, s in category_stats.items():
        ctp = f"{s['code_test_pass_rate']*100:.0f}%" if s['code_test_pass_rate'] is not None else "N/A"
        print(f"  {cat:<26} {s['avg_correctness']:>7.3f} {s['avg_relevance']:>6.3f} "
              f"{s['avg_retrieval_quality']:>5.2f} {s['hallucination_rate']*100:>5.1f}% "
              f"{ctp:>5} {s['avg_latency_ms']:>7.0f}")
    print(f"  {'-'*65}")
    print(f"  {'OVERALL':<26} {overall['avg_correctness']:>7.3f} {overall['avg_relevance']:>6.3f} "
          f"{overall['avg_retrieval_quality']:>5.2f} {overall['hallucination_rate']*100:>5.1f}%   N/A {overall['avg_latency_ms']:>7.0f}")

    return output


# ── Comparison Report ─────────────────────────────────────────────────────────

def generate_comparison_report(models=None):
    """Load results for all 3 models and generate category-wise comparison."""
    if models is None:
        models = ["codellama", "starcoder", "deepseek-coder"]

    all_data = {}
    for m in models:
        slug = m.replace(":","_").replace("/","_")
        path = os.path.join(RESULTS_DIR, f"se_eval_{slug}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                all_data[m] = json.load(f)

    if len(all_data) < 2:
        print(f"Need at least 2 model results. Found: {list(all_data.keys())}")
        return

    model_names = list(all_data.keys())
    lines = [
        "# ShopBot SE Category-Wise Model Comparison Report",
        "",
        f"> **Models:** {' | '.join(f'`{m}`' for m in model_names)}",
        f"> **Categories:** {len(CATEGORIES)} | **Questions:** 35 (5 per category)",
        f"> **Date:** {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
        "## Executive Summary — Category Winners",
        "",
        "| Category | Best Model (Correctness) | Best Model (Latency) | Best Code-Test-Pass |",
        "|---|---|---|---|",
    ]

    for cat in CATEGORIES:
        cat_data = {m: d["by_category"].get(cat,{}) for m,d in all_data.items()}
        best_c = max(cat_data, key=lambda m: cat_data[m].get("avg_correctness",0))
        best_l = min(cat_data, key=lambda m: cat_data[m].get("avg_latency_ms",9999999))
        ctp_vals = {m: cat_data[m].get("code_test_pass_rate") for m in model_names}
        ctp_vals = {m:v for m,v in ctp_vals.items() if v is not None}
        best_ctp = max(ctp_vals, key=ctp_vals.get) if ctp_vals else "N/A"
        lines.append(f"| **{cat}** | `{best_c}` ({cat_data[best_c].get('avg_correctness',0):.3f}) | `{best_l}` ({cat_data[best_l].get('avg_latency_ms',0):.0f}ms) | {best_ctp} |")

    lines += ["", "---", "", "## Per-Category Detailed Comparison", ""]

    for cat in CATEGORIES:
        lines += [f"### {cat}", ""]
        # Correctness table
        lines += [
            f"| Metric | {' | '.join(model_names)} |",
            f"|---|{'---|'*len(model_names)}",
        ]
        for metric, label, fmt in [
            ("avg_correctness",       "Avg Correctness",       ".3f"),
            ("avg_relevance",         "Avg Relevance",         ".3f"),
            ("avg_retrieval_quality", "Retrieval Quality",     ".3f"),
            ("hallucination_rate",    "Hallucination Rate",    ".1%"),
            ("correct_count",         "Correct Answers",       "d"),
            ("partial_count",         "Partial Answers",       "d"),
            ("avg_latency_ms",        "Avg Latency (ms)",      ".0f"),
            ("avg_tokens",            "Avg Tokens",            ".0f"),
            ("code_test_pass_rate",   "Code Test-Pass Rate",   ".1%"),
        ]:
            vals = []
            best_val = None
            for m in model_names:
                v = all_data[m]["by_category"].get(cat,{}).get(metric)
                if v is not None: best_val = v if best_val is None else best_val
            row_vals = []
            for m in model_names:
                v = all_data[m]["by_category"].get(cat,{}).get(metric)
                if v is None:
                    row_vals.append("N/A")
                else:
                    row_vals.append(format(v, fmt))
            lines.append(f"| **{label}** | {' | '.join(row_vals)} |")

        # Per-question detail for this category
        lines += ["", f"**Per-question responses:**", ""]
        q_ids = [q["id"] for q in json.load(open(QUESTIONS_PATH, encoding="utf-8")) if q["category"]==cat]
        for qid in q_ids:
            # Get question text
            q_text = next((q["question"] for q in json.load(open(QUESTIONS_PATH,encoding="utf-8")) if q["id"]==qid),"")
            lines += [f"**{qid}:** {q_text[:80]}{'...' if len(q_text)>80 else ''}", ""]
            for m in model_names:
                qr = next((r for r in all_data[m]["per_question"] if r["id"]==qid), None)
                if qr:
                    cp = f" | Code: {'PASS' if qr.get('code_pass') else ('FAIL' if qr.get('code_pass') is False else 'N/A')}" if qr.get('code_pass') is not None or qr.get('code_notes') else ""
                    lines.append(f"- **`{m}`** (C:{qr['correctness']} R:{qr['relevance']} {qr['latency_ms']}ms{cp}): {qr['response'][:200].replace(chr(10),' ')}...")
            lines.append("")
        lines += ["---", ""]

    # Overall comparison
    lines += [
        "## Overall Performance Comparison",
        "",
        f"| Metric | {' | '.join(model_names)} |",
        f"|---|{'---|'*len(model_names)}",
    ]
    for metric, label, fmt in [
        ("avg_correctness","Avg Correctness",".3f"),
        ("avg_relevance","Avg Relevance",".3f"),
        ("avg_retrieval_quality","Retrieval Quality",".3f"),
        ("hallucination_rate","Hallucination Rate",".1%"),
        ("correct_count","Correct Answers","d"),
        ("avg_latency_ms","Avg Latency (ms)",".0f"),
        ("avg_tokens","Avg Tokens",".0f"),
    ]:
        row_vals = []
        all_vs = []
        for m in model_names:
            v = all_data[m]["overall"].get(metric)
            row_vals.append((m,v))
            if v is not None: all_vs.append(v)
        # Highlight best
        is_lower_better = metric in ("hallucination_rate","avg_latency_ms")
        best_v = min(all_vs) if is_lower_better else (max(all_vs) if all_vs else None)
        cells = []
        for m,v in row_vals:
            if v is None: cells.append("N/A")
            else:
                s = format(v, fmt)
                cells.append(f"**{s}** ✅" if v==best_v else s)
        lines.append(f"| {label} | {' | '.join(cells)} |")

    lines += [
        "",
        "---",
        "",
        "## Key Findings",
        "",
    ]
    for cat in CATEGORIES:
        cat_data = {m: all_data[m]["by_category"].get(cat,{}) for m in model_names if m in all_data}
        if not cat_data: continue
        best = max(cat_data, key=lambda m: cat_data[m].get("avg_correctness",0))
        worst = min(cat_data, key=lambda m: cat_data[m].get("avg_correctness",0))
        lines.append(f"- **{cat}**: `{best}` performs best (correctness {cat_data[best].get('avg_correctness',0):.3f}). "
                     f"`{worst}` performs worst ({cat_data[worst].get('avg_correctness',0):.3f}).")
    lines.append("")

    report_path = os.path.join(EVAL_DIR, "se_category_comparison_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nComparison report saved -> {report_path}")
    return report_path


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="Single model to evaluate")
    parser.add_argument("--all",   action="store_true", help="Run all 3 models")
    parser.add_argument("--report",action="store_true", help="Generate comparison report from existing results")
    args = parser.parse_args()

    MODELS = ["codellama", "starcoder", "deepseek-coder"]

    if args.report:
        generate_comparison_report(MODELS)
    elif args.all:
        for m in MODELS:
            run_evaluation(m)
        generate_comparison_report(MODELS)
    elif args.model:
        run_evaluation(args.model)
        # If all 3 results exist, auto-generate report
        all_exist = all(os.path.exists(os.path.join(RESULTS_DIR, f"se_eval_{m.replace(':','_')}.json")) for m in MODELS)
        if all_exist:
            generate_comparison_report(MODELS)
    else:
        parser.print_help()
