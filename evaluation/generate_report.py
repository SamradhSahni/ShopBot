"""
generate_report.py — Reads results JSONs and generates a full analysis report (W4-E4)
Usage: python generate_report.py
Produces: analysis_report.md
"""

import json, os, sys
from pathlib import Path
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "analysis_report.md")
MODELS = ["codellama", "starcoder2", "deepseek-coder"]


def load_results(model: str) -> dict | None:
    safe = model.replace(":", "_").replace("/", "_")
    path = os.path.join(RESULTS_DIR, f"{safe}_results.json")
    if not os.path.exists(path):
        print(f"⚠ Results not found for {model}: {path}")
        return None
    with open(path) as f:
        return json.load(f)


def find_best(summaries: list, key: str, higher_is_better: bool = True) -> str:
    vals = [(s["model"], s["summary"][key]) for s in summaries]
    best = max(vals, key=lambda x: x[1]) if higher_is_better else min(vals, key=lambda x: x[1])
    return best[0]


def generate_report(all_data: list) -> str:
    summaries = [d["summary"] for d in all_data]
    models    = [d["model"]   for d in all_data]
    now       = datetime.now().strftime("%Y-%m-%d %H:%M")

    def fmt(val, spec):
        return format(val, spec)

    def row(label, key, spec, higher_is_better=True):
        vals = [fmt(s[key], spec) for s in summaries]
        best_model = find_best(all_data, key, higher_is_better)
        best_idx   = models.index(best_model)
        vals[best_idx] = f"**{vals[best_idx]}** ✅"
        return f"| {label} | {' | '.join(vals)} |"

    lines = []
    lines.append(f"# ShopBot AI — Model Evaluation Analysis Report")
    lines.append(f"\n> Generated: {now}  \n> Application: E-Commerce Product & Policy Support Bot (TechMart)  \n> Models evaluated: {', '.join(models)}")

    lines.append("\n---\n")
    lines.append("## 1. Evaluation Setup\n")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    lines.append(f"| Total Questions | 25 |")
    lines.append(f"| Categories | Product Info (5), Return Policy (5), Shipping (5), Cross-domain (5), Hallucination Traps (5) |")
    lines.append(f"| Models Compared | Code Llama 7B, StarCoder2 7B, DeepSeek-Coder 6.7B |")
    lines.append(f"| Embedding Model | nomic-embed-text (same for all) |")
    lines.append(f"| Knowledge Base | 18 products, policies, FAQs, shipping zones |")
    lines.append(f"| RAG Enabled | Yes (top-k=3, cosine similarity) |")
    lines.append(f"| Temperature | 0.2 (same for all) |")

    lines.append("\n---\n")
    lines.append("## 2. Metric Definitions\n")
    lines.append("| Metric | Type | Definition | Measurement |")
    lines.append("|--------|------|-----------|-------------|")
    lines.append("| **Correctness** | Quality | Does the answer match ground truth key facts? | Keyword overlap ratio: ≥60% = 1.0, ≥30% = 0.5, <30% = 0.0 |")
    lines.append("| **Relevance** | Quality | Is the response topically on-topic? | Question-keyword overlap in response, 0.0–1.0 |")
    lines.append("| **Retrieval Quality** | Quality | Were the right source documents retrieved? | Source match: correct source in top-3 chunks |")
    lines.append("| **Hallucination Rate** | Quality | Did model state false/invented facts? | Trap detection + false claim detection, % of answers |")
    lines.append("| **Response Latency** | Performance | Total time from request to response | `time.time()` wall clock, milliseconds |")
    lines.append("| **Token Usage** | Performance | Output tokens consumed per response | Ollama `eval_count` field |")
    lines.append("| **Memory Usage** | Performance | Peak RAM used by process | `psutil.Process().memory_info().rss`, MB |")
    lines.append("| **CPU Usage** | Performance | CPU load during inference | `psutil.cpu_percent(interval=0.5)`, % |")

    lines.append("\n---\n")
    lines.append("## 3. Quality Metrics Comparison\n")
    lines.append(f"| Metric | {' | '.join(m.capitalize() for m in models)} |")
    lines.append(f"|--------|{'|'.join(['--------'] * len(models))}|")
    lines.append(row("Avg Correctness (0–1)",    "avg_correctness",       ".3f", True))
    lines.append(row("Avg Relevance (0–1)",       "avg_relevance",         ".3f", True))
    lines.append(row("Avg Retrieval Quality",      "avg_retrieval_quality", ".3f", True))
    lines.append(row("Hallucination Rate",         "hallucination_rate",    ".1%", False))
    lines.append(row("Trap Hallucination Rate",    "trap_hallucination_rate",".1%",False))
    lines.append(row("Correct Answers",            "correct_count",         "d",   True))
    lines.append(row("Partial Answers",            "partial_count",         "d",   False))
    lines.append(row("Incorrect Answers",          "incorrect_count",       "d",   False))

    lines.append("\n---\n")
    lines.append("## 4. Performance Metrics Comparison\n")
    lines.append(f"| Metric | {' | '.join(m.capitalize() for m in models)} |")
    lines.append(f"|--------|{'|'.join(['--------'] * len(models))}|")
    lines.append(row("Avg Total Latency (ms)",  "avg_latency_ms",    ".0f", False))
    lines.append(row("Avg LLM Latency (ms)",    "avg_llm_ms",        ".0f", False))
    lines.append(row("Avg Retrieve Latency (ms)","avg_retrieve_ms",  ".0f", False))
    lines.append(row("Avg Output Tokens",        "avg_tokens_used",  ".0f", False))
    lines.append(row("Avg Prompt Tokens",        "avg_prompt_tokens",".0f", False))
    lines.append(row("Total Tokens (all 25 Q)",  "total_tokens",     "d",   False))
    lines.append(row("Avg Memory Usage (MB)",    "avg_memory_mb",    ".1f", False))
    lines.append(row("Avg Memory Delta (MB)",    "avg_memory_delta", ".2f", False))
    lines.append(row("Avg CPU Usage (%)",        "avg_cpu_percent",  ".1f", False))

    lines.append("\n---\n")
    lines.append("## 5. Per-Category Analysis\n")

    categories = ["Product Information", "Return Policy", "Shipping", "Cross-domain", "Hallucination Trap"]
    for cat in categories:
        lines.append(f"### {cat}\n")
        lines.append(f"| Metric | {' | '.join(m.capitalize() for m in models)} |")
        lines.append(f"|--------|{'|'.join(['--------'] * len(models))}|")
        for d in all_data:
            cat_results = [r for r in d["results"] if r["category"] == cat]
        for metric_label, metric_key in [("Correctness", "correctness"), ("Retrieval Quality", "retrieval_quality")]:
            row_vals = []
            for d in all_data:
                cat_r = [r for r in d["results"] if r["category"] == cat]
                if cat_r:
                    avg = sum(r[metric_key] for r in cat_r) / len(cat_r)
                    row_vals.append(f"{avg:.2f}")
                else:
                    row_vals.append("N/A")
            lines.append(f"| {metric_label} | {' | '.join(row_vals)} |")
        lines.append("")

    lines.append("\n---\n")
    lines.append("## 6. Key Analysis Questions\n")

    best_correct  = find_best(all_data, "avg_correctness",        True)
    best_latency  = find_best(all_data, "avg_latency_ms",         False)
    best_halluc   = find_best(all_data, "hallucination_rate",     False)
    best_retrieve = find_best(all_data, "avg_retrieval_quality",  True)
    best_memory   = find_best(all_data, "avg_memory_mb",          False)
    best_tokens   = find_best(all_data, "avg_tokens_used",        False)

    def get_val(model, key, spec):
        for d in all_data:
            if d["model"] == model:
                return format(d["summary"][key], spec)
        return "N/A"

    lines.append(f"**Q: Which model provides better accuracy?**  \n"
                 f"→ `{best_correct}` achieved the highest correctness score of "
                 f"{get_val(best_correct, 'avg_correctness', '.3f')}.\n")

    lines.append(f"**Q: Which model produces fewer hallucinations?**  \n"
                 f"→ `{best_halluc}` had the lowest hallucination rate at "
                 f"{get_val(best_halluc, 'hallucination_rate', '.1%')}.\n")

    lines.append(f"**Q: Which model provides better retrieval-based responses?**  \n"
                 f"→ `{best_retrieve}` achieved the best retrieval quality score of "
                 f"{get_val(best_retrieve, 'avg_retrieval_quality', '.3f')}.\n")

    lines.append(f"**Q: Which model has lower response latency?**  \n"
                 f"→ `{best_latency}` was the fastest at "
                 f"{get_val(best_latency, 'avg_latency_ms', '.0f')}ms average.\n")

    lines.append(f"**Q: Which model requires fewer computational resources?**  \n"
                 f"→ `{best_memory}` used least memory ({get_val(best_memory, 'avg_memory_mb', '.1f')} MB) "
                 f"and `{best_tokens}` used fewest tokens ({get_val(best_tokens, 'avg_tokens_used', '.0f')} avg).\n")

    is_best_also_fastest = best_correct == best_latency
    lines.append(f"**Q: Is the most accurate model also the most efficient?**  \n"
                 f"→ {'Yes' if is_best_also_fastest else 'No'}. "
                 f"The most accurate model (`{best_correct}`) "
                 f"{'is also' if is_best_also_fastest else 'is NOT'} the fastest. "
                 f"This {'confirms' if is_best_also_fastest else 'demonstrates'} a "
                 f"{'alignment' if is_best_also_fastest else 'quality–latency trade-off'} "
                 f"between accuracy and speed.\n")

    lines.append("\n---\n")
    lines.append("## 7. Trade-off Analysis\n")
    lines.append("> The goal is not simply to identify the 'best' model, but to understand "
                 "the trade-offs between quality, latency, and resource usage.\n")

    for d in all_data:
        s = d["summary"]
        m = d["model"]
        lines.append(f"### {m}\n")
        lines.append(f"- **Correctness:** {s['avg_correctness']:.3f} | "
                     f"**Hallucination:** {s['hallucination_rate']:.1%} | "
                     f"**Latency:** {s['avg_latency_ms']:.0f}ms | "
                     f"**Memory:** {s['avg_memory_mb']:.1f}MB")
        lines.append(f"- Suitable for: *[fill in after running evaluation]*\n")

    lines.append("\n---\n")
    lines.append("## 8. Conclusion\n")
    lines.append("> *[To be filled in after running all three models — compare the numbers "
                 "from Section 3 and 4, and use the trade-off analysis from Section 7 to "
                 "write a data-driven recommendation.]*\n")
    lines.append(f"\nExample structure:\n")
    lines.append("```\n"
                 "Model A achieved the highest accuracy (X.XXX) and lowest hallucination rate (X.X%),\n"
                 "but required Xms average latency and XMB memory.\n\n"
                 "Model B showed X% lower accuracy but was X% faster with X% less memory,\n"
                 "making it a better fit for latency-sensitive deployments.\n\n"
                 "Model C provided the best balance of [quality/speed/resource usage].\n"
                 "```")

    return "\n".join(lines)


def main():
    print("📊 Generating analysis report...")
    all_data = []
    for model in MODELS:
        data = load_results(model)
        if data:
            all_data.append(data)

    if not all_data:
        print("❌ No result files found. Run evaluator.py first.")
        sys.exit(1)

    report = generate_report(all_data)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ Report saved: {REPORT_PATH}")
    print(f"   Models included: {[d['model'] for d in all_data]}")


if __name__ == "__main__":
    main()
