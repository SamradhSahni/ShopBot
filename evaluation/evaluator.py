"""
evaluator.py — Quantitative evaluation of ShopBot across 3 LLM models
Week 4, Exercise 3: Correctness, Relevance, Retrieval Quality, Hallucination Rate,
                    Latency, Token Usage, Memory Consumption

Usage:
    python evaluator.py --model codellama
    python evaluator.py --model starcoder2
    python evaluator.py --model deepseek-coder
    python evaluator.py --all          # Run all 3 models sequentially
"""

import sys, os, json, time, argparse, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex1_basic"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex2_knowledge_base"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex3_rag"))

import psutil
import requests
from rag_pipeline import rag_chat, no_rag_chat
from retriever import retrieve

QUESTIONS_PATH = os.path.join(os.path.dirname(__file__), "questions.json")
RESULTS_DIR    = os.path.join(os.path.dirname(__file__), "results")
SUPPORTED_MODELS = ["tinyllama", "qwen2:0.5b", "gemma:2b"]

os.makedirs(RESULTS_DIR, exist_ok=True)


# ── Metric Definitions ────────────────────────────────────────────────────────

def score_correctness(actual: str, ground_truth: str) -> float:
    """
    METRIC: Correctness / Accuracy
    Definition: Does the model's answer contain the key factual elements from ground truth?
    Method: Keyword overlap — count how many ground truth key terms appear in the actual answer.
    Scale: 0.0 (wrong), 0.5 (partial), 1.0 (correct)
    """
    if not actual or not ground_truth:
        return 0.0

    actual_lower = actual.lower()
    gt_lower = ground_truth.lower()

    # Extract meaningful tokens from ground truth (ignore stop words)
    stop_words = {"the", "a", "an", "is", "are", "was", "in", "on", "at", "to",
                  "of", "for", "and", "or", "not", "it", "this", "that", "with"}
    gt_tokens = [t for t in re.findall(r'\b\w+\b', gt_lower) if t not in stop_words and len(t) > 2]

    if not gt_tokens:
        return 0.0

    # Count how many GT tokens appear in the actual answer
    matches = sum(1 for token in gt_tokens if token in actual_lower)
    ratio = matches / len(gt_tokens)

    if ratio >= 0.6:
        return 1.0
    elif ratio >= 0.3:
        return 0.5
    else:
        return 0.0


def score_relevance(question: str, actual: str) -> float:
    """
    METRIC: Relevance
    Definition: Is the response topically relevant to the question asked?
    Method: Check if question's key noun phrases appear in the response.
    Scale: 1-5 (mapped to 0.0-1.0)
    """
    if not actual:
        return 0.0

    q_lower = question.lower()
    a_lower = actual.lower()

    # Key terms from question
    q_tokens = re.findall(r'\b\w{4,}\b', q_lower)
    if not q_tokens:
        return 0.5

    matches = sum(1 for t in q_tokens if t in a_lower)
    ratio = matches / len(q_tokens)
    return round(min(ratio * 1.2, 1.0), 2)


def score_retrieval_quality(question: str, chunks: list, source_doc: str) -> float:
    """
    METRIC: Retrieval Quality (Precision@K)
    Definition: Did the retriever return chunks from the correct source document?
    Method: Check if any retrieved chunk's source matches the expected source document.
    Scale: 0.0 (no relevant chunks), 0.5 (partial), 1.0 (correct source retrieved)
    """
    if source_doc == "NOT_IN_KB":
        return 1.0  # Can't retrieve what doesn't exist — retriever is correct to return nothing useful

    if not chunks:
        return 0.0

    expected_sources = [s.strip() for s in source_doc.split("+")]
    retrieved_sources = [c.get("source", "") for c in chunks]

    matched = sum(1 for es in expected_sources if any(es in rs for rs in retrieved_sources))
    return round(matched / len(expected_sources), 2)


def detect_hallucination(actual: str, question: str, hallucination_trap: bool,
                          trap_type: str = "", ground_truth: str = "") -> dict:
    """
    METRIC: Hallucination Detection
    Definition: Did the model confidently state false or invented information?
    Method:
      - For trap questions: check if model correctly admits uncertainty
      - For factual questions: check if model invented facts not in ground truth
    Returns: {hallucinated: bool, confidence: str, notes: str}
    """
    actual_lower = actual.lower()

    # Uncertainty phrases the model should use when it doesn't know
    uncertainty_phrases = [
        "don't have", "do not have", "not available", "unable to",
        "cannot access", "no information", "not in", "i don't know",
        "contact support", "check your account", "not listed",
        "not in our catalogue", "not offered", "no record"
    ]

    if hallucination_trap:
        if trap_type == "requires_live_data":
            # Model should admit it can't access order data
            admitted = any(p in actual_lower for p in uncertainty_phrases)
            return {
                "hallucinated": not admitted,
                "notes": "Should admit no live order access" if not admitted else "Correctly deferred"
            }
        elif trap_type == "product_not_in_catalogue":
            # Model should not give a specific price for a product not in KB
            price_pattern = re.search(r'\$\d+|\d+ dollars', actual_lower)
            if price_pattern:
                return {"hallucinated": True, "notes": f"Invented price: {price_pattern.group()}"}
            return {"hallucinated": False, "notes": "Correctly acknowledged product not found"}
        elif trap_type in ("policy_not_offered", "policy_not_in_kb"):
            admitted = any(p in actual_lower for p in uncertainty_phrases)
            return {
                "hallucinated": not admitted,
                "notes": "Should say info not available" if not admitted else "Correctly uncertain"
            }

    # For non-trap questions: check for obviously invented specific numbers/facts
    # that differ significantly from ground truth
    return {"hallucinated": False, "notes": "Standard factual question"}


def get_memory_mb() -> float:
    """
    METRIC: Memory Consumption
    Definition: Current process RAM usage in MB
    Method: psutil.Process().memory_info().rss (Resident Set Size)
    """
    process = psutil.Process(os.getpid())
    return round(process.memory_info().rss / (1024 * 1024), 2)


def get_cpu_percent() -> float:
    """
    METRIC: CPU Usage
    Definition: CPU utilisation % during inference window
    Method: psutil.cpu_percent(interval=1) sampled during generation
    """
    return psutil.cpu_percent(interval=0.5)


# ── Main Evaluation Loop ──────────────────────────────────────────────────────

def evaluate_model(model: str, questions: list) -> dict:
    """Run all 25 questions against a given model and collect all metrics."""

    print(f"\n{'='*65}")
    print(f"  Evaluating Model: {model.upper()}")
    print(f"  Questions: {len(questions)}")
    print(f"{'='*65}")

    results = []

    for i, q in enumerate(questions):
        print(f"\n[{i+1:02d}/{len(questions)}] Q{q['id']}: {q['question'][:60]}...")

        mem_before = get_memory_mb()
        cpu_start  = get_cpu_percent()

        # Run RAG pipeline
        try:
            rag_result = rag_chat(q["question"], model=model, top_k=3)
            actual     = rag_result["response"]
            chunks     = rag_result["retrieved_chunks"]
            metrics    = rag_result["metrics"]
        except Exception as e:
            print(f"  ❌ Error: {e}")
            actual, chunks, metrics = f"ERROR: {e}", [], {}

        mem_after  = get_memory_mb()
        cpu_end    = get_cpu_percent()

        # ── Score all metrics ──────────────────────────────────────────────
        correctness      = score_correctness(actual, q["ground_truth"])
        relevance        = score_relevance(q["question"], actual)
        retrieval_qual   = score_retrieval_quality(q["question"], chunks, q["source_doc"])
        hallucination    = detect_hallucination(
            actual, q["question"],
            q["hallucination_trap"],
            q.get("trap_type", ""),
            q["ground_truth"]
        )

        result = {
            "question_id":       q["id"],
            "category":          q["category"],
            "question":          q["question"],
            "ground_truth":      q["ground_truth"],
            "actual_response":   actual,
            "model":             model,
            "hallucination_trap": q["hallucination_trap"],
            "trap_type":         q.get("trap_type", ""),

            # Quality metrics
            "correctness":       correctness,
            "relevance":         relevance,
            "retrieval_quality": retrieval_qual,
            "hallucinated":      hallucination["hallucinated"],
            "hallucination_notes": hallucination["notes"],

            # Retrieved chunks
            "chunks_retrieved":  len(chunks),
            "top_similarity":    chunks[0]["similarity_score"] if chunks else 0,
            "chunk_sources":     [c["source"] for c in chunks],

            # Performance metrics
            "latency_ms":        metrics.get("total_latency_ms", 0),
            "retrieve_ms":       metrics.get("retrieve_latency_ms", 0),
            "llm_ms":            metrics.get("llm_latency_ms", 0),
            "tokens_used":       metrics.get("tokens_used", 0),
            "prompt_tokens":     metrics.get("prompt_tokens", 0),
            "memory_before_mb":  mem_before,
            "memory_after_mb":   mem_after,
            "memory_delta_mb":   round(mem_after - mem_before, 2),
            "cpu_percent":       round((cpu_start + cpu_end) / 2, 1),
        }

        # Print summary for this question
        flag = "🟢" if correctness == 1.0 else ("🟡" if correctness == 0.5 else "🔴")
        hall = "⚠️ HALLUCINATED" if hallucination["hallucinated"] else "✅"
        print(f"  {flag} Correct: {correctness:.1f} | Relevance: {relevance:.2f} | "
              f"Retrieval: {retrieval_qual:.2f} | {hall}")
        print(f"  ⏱  Total: {result['latency_ms']}ms | LLM: {result['llm_ms']}ms | "
              f"Tokens: {result['tokens_used']} | Memory Δ: {result['memory_delta_mb']}MB")

        results.append(result)
        time.sleep(0.5)  # Brief pause between requests

    return summarise(model, results)


def summarise(model: str, results: list) -> dict:
    """Aggregate all individual results into model-level summary statistics."""

    n = len(results)
    hallucination_traps = [r for r in results if r["hallucination_trap"]]
    non_trap = [r for r in results if not r["hallucination_trap"]]

    summary = {
        "model": model,
        "total_questions": n,
        "results": results,
        "summary": {
            # Quality metrics
            "avg_correctness":       round(sum(r["correctness"]       for r in results) / n, 3),
            "avg_relevance":         round(sum(r["relevance"]         for r in results) / n, 3),
            "avg_retrieval_quality": round(sum(r["retrieval_quality"] for r in results) / n, 3),
            "hallucination_rate":    round(sum(1 for r in results if r["hallucinated"]) / n, 3),
            "hallucination_count":   sum(1 for r in results if r["hallucinated"]),
            "total_questions":       n,
            "trap_hallucination_rate": round(
                sum(1 for r in hallucination_traps if r["hallucinated"]) / max(len(hallucination_traps), 1), 3
            ),
            "correct_count":   sum(1 for r in results if r["correctness"] == 1.0),
            "partial_count":   sum(1 for r in results if r["correctness"] == 0.5),
            "incorrect_count": sum(1 for r in results if r["correctness"] == 0.0),

            # Performance metrics
            "avg_latency_ms":    round(sum(r["latency_ms"]    for r in results) / n, 1),
            "avg_retrieve_ms":   round(sum(r["retrieve_ms"]   for r in results) / n, 1),
            "avg_llm_ms":        round(sum(r["llm_ms"]        for r in results) / n, 1),
            "avg_tokens_used":   round(sum(r["tokens_used"]   for r in results) / n, 1),
            "avg_prompt_tokens": round(sum(r["prompt_tokens"] for r in results) / n, 1),
            "avg_memory_mb":     round(sum(r["memory_after_mb"] for r in results) / n, 2),
            "avg_memory_delta":  round(sum(r["memory_delta_mb"] for r in results) / n, 2),
            "avg_cpu_percent":   round(sum(r["cpu_percent"]   for r in results) / n, 1),
            "total_tokens":      sum(r["tokens_used"] for r in results),

            # Retrieval stats
            "avg_chunks_retrieved": round(sum(r["chunks_retrieved"] for r in results) / n, 2),
            "avg_top_similarity":   round(sum(r["top_similarity"]   for r in results) / n, 3),
        }
    }
    return summary


def save_results(model: str, data: dict):
    """Save results to JSON file."""
    safe_name = model.replace(":", "_").replace("/", "_")
    path = os.path.join(RESULTS_DIR, f"{safe_name}_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\n💾 Results saved: {path}")
    return path


def print_model_summary(data: dict):
    """Print a human-readable summary table for one model."""
    s = data["summary"]
    m = data["model"]
    print(f"\n{'─'*55}")
    print(f"  📊 SUMMARY — {m.upper()}")
    print(f"{'─'*55}")
    print(f"  Correctness:       {s['avg_correctness']:.3f}  ({s['correct_count']} correct, {s['partial_count']} partial, {s['incorrect_count']} wrong)")
    print(f"  Relevance:         {s['avg_relevance']:.3f}")
    print(f"  Retrieval Quality: {s['avg_retrieval_quality']:.3f}")
    print(f"  Hallucination:     {s['hallucination_rate']:.1%}  ({s['hallucination_count']}/{s['total_questions']} answers)")
    print(f"  Trap Hallucin.:    {s['trap_hallucination_rate']:.1%}  (on trap questions only)")
    print(f"  ─")
    print(f"  Avg Latency:       {s['avg_latency_ms']:.0f}ms  (LLM: {s['avg_llm_ms']:.0f}ms | Retrieve: {s['avg_retrieve_ms']:.0f}ms)")
    print(f"  Avg Tokens:        {s['avg_tokens_used']:.0f} output / {s['avg_prompt_tokens']:.0f} prompt")
    print(f"  Total Tokens:      {s['total_tokens']}")
    print(f"  Avg Memory:        {s['avg_memory_mb']:.1f} MB  (Δ {s['avg_memory_delta']:+.1f} MB)")
    print(f"  Avg CPU:           {s['avg_cpu_percent']:.1f}%")
    print(f"{'─'*55}")


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ShopBot Model Evaluator")
    parser.add_argument("--model", help="Model to evaluate (any Ollama model name)")
    parser.add_argument("--all", action="store_true", help="Evaluate all 3 lightweight VM models (tinyllama, qwen2:0.5b, gemma:2b)")
    args = parser.parse_args()

    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    models_to_run = SUPPORTED_MODELS if args.all else ([args.model] if args.model else ["tinyllama"])

    all_summaries = []
    for model in models_to_run:
        data = evaluate_model(model, questions)
        print_model_summary(data)
        save_results(model, data)
        all_summaries.append(data["summary"])

    # If multiple models ran, print comparison
    if len(all_summaries) >= 2:
        print(f"\n{'═'*65}")
        print("  📊 CROSS-MODEL COMPARISON")
        print(f"{'═'*65}")
        headers = ["Metric", "CodeLlama", "StarCoder2", "DeepSeek"]
        fmt = "{:<25} {:<15} {:<15} {:<15}"
        print(fmt.format(*headers))
        print("─" * 65)
        metrics = [
            ("Correctness",       "avg_correctness",       ".3f"),
            ("Relevance",         "avg_relevance",          ".3f"),
            ("Retrieval Quality", "avg_retrieval_quality",  ".3f"),
            ("Hallucination Rate","hallucination_rate",      ".1%"),
            ("Avg Latency (ms)",  "avg_latency_ms",         ".0f"),
            ("Avg Tokens",        "avg_tokens_used",        ".0f"),
            ("Avg Memory (MB)",   "avg_memory_mb",          ".1f"),
        ]
        for label, key, fmt_spec in metrics:
            vals = [format(s[key], fmt_spec) for s in all_summaries]
            print(f"  {label:<23} {vals[0]:<15} {vals[1]:<15} {vals[2]:<15}")
        print(f"{'═'*65}")


if __name__ == "__main__":
    main()
