"""
compare_demo.py — Side-by-side RAG vs No-RAG comparison
Exercise 3: Demonstrates the value of retrieval-augmented generation
Saves results cleanly to both JSON and Markdown formats.
"""

import sys, os, io, json, time, argparse
from datetime import datetime

# UTF-8 stdout protection for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex1_basic"))
sys.path.insert(0, os.path.dirname(__file__))

from rag_pipeline import rag_chat, no_rag_chat

DEMO_QUESTIONS = [
    "What is the warranty on the Dell XPS 15 laptop?",
    "How much does express shipping cost?",
    "Can I return an opened laptop within 30 days?",
    "What is the price of the Sony WH-1000XM5 headphones?",
    "Do you offer free shipping? What is the minimum order?",
]

OUTPUT_DIR = os.path.dirname(__file__)
DEFAULT_JSON_PATH = os.path.join(OUTPUT_DIR, "comparison_results.json")
DEFAULT_MD_PATH   = os.path.join(OUTPUT_DIR, "comparison_results.md")


def print_separator(char="─", width=70):
    print(char * width)


def compare(question: str, model: str = "codellama") -> dict:
    print_separator("═")
    print(f"❓ QUESTION: {question}")
    print_separator()

    print("\n🚫 WITHOUT RAG (No context provided):")
    no_rag = no_rag_chat(question, model)
    print(f"   {no_rag['response'].strip()}")
    print(f"   ⏱  Latency: {no_rag['metrics']['llm_latency_ms']}ms | Tokens: {no_rag['metrics']['tokens_used']}")

    print("\n✅ WITH RAG (Retrieved context provided):")
    with_rag = rag_chat(question, model)
    print(f"   {with_rag['response'].strip()}")
    print(f"   ⏱  Latency: {with_rag['metrics']['total_latency_ms']}ms | Tokens: {with_rag['metrics']['tokens_used']}")
    print(f"   📄 Context from: {[c['source'] for c in with_rag['retrieved_chunks']]}")
    print(f"   🔍 Top similarity score: {with_rag['metrics']['top_similarity']:.3f}")
    print()

    return {
        "question": question,
        "without_rag": {
            "response": no_rag["response"].strip(),
            "latency_ms": no_rag["metrics"]["llm_latency_ms"],
            "tokens_used": no_rag["metrics"]["tokens_used"],
        },
        "with_rag": {
            "response": with_rag["response"].strip(),
            "latency_ms": with_rag["metrics"]["total_latency_ms"],
            "retrieve_latency_ms": with_rag["metrics"]["retrieve_latency_ms"],
            "llm_latency_ms": with_rag["metrics"]["llm_latency_ms"],
            "tokens_used": with_rag["metrics"]["tokens_used"],
            "sources": [c["source"] for c in with_rag["retrieved_chunks"]],
            "top_similarity": round(with_rag["metrics"]["top_similarity"], 3),
            "retrieved_chunks": [
                {
                    "source": c.get("source"),
                    "type": c.get("type"),
                    "similarity": round(c.get("similarity_score", 0), 3),
                    "preview": c.get("text", "")[:180].replace("\n", " ") + "...",
                }
                for c in with_rag["retrieved_chunks"]
            ],
        },
    }


def save_results(results: list, model: str, json_path: str, md_path: str):
    """Save structured comparison to JSON and clean human-readable Markdown."""
    payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": model,
        "total_questions": len(results),
        "comparisons": results,
    }

    # 1. Save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # 2. Save Markdown Report
    md_lines = [
        f"# ShopBot AI — RAG vs No-RAG Comparison Report",
        f"",
        f"> **Generated:** {payload['timestamp']}  ",
        f"> **Model Evaluated:** `{model}`  ",
        f"> **Questions Tested:** {len(results)}  ",
        f"",
        f"---",
        f"",
        f"## Summary Takeaways",
        f"- **Grounded Truth:** With RAG, answers reference exact catalog prices, warranty durations, and policy conditions.",
        f"- **Hallucination Prevention:** Without RAG, the model produces generic or factually inaccurate answers.",
        f"- **Latency Trade-off:** RAG introduces vector retrieval overhead, but provides high factual reliability.",
        f"",
        f"---",
        f"",
        f"## Side-by-Side Comparison",
        f"",
    ]

    for i, item in enumerate(results, 1):
        q = item["question"]
        no_rag = item["without_rag"]
        rag = item["with_rag"]

        md_lines.append(f"### {i}. {q}")
        md_lines.append(f"")
        md_lines.append(f"| Metric | Without RAG (Base Model) | With RAG (ShopBot Knowledge Base) |")
        md_lines.append(f"| :--- | :--- | :--- |")
        md_lines.append(f"| **Response** | {no_rag['response'].replace(chr(10), '<br>')} | {rag['response'].replace(chr(10), '<br>')} |")
        md_lines.append(f"| **Latency** | `{no_rag['latency_ms']} ms` | `{rag['latency_ms']} ms` (Retrieval: `{rag['retrieve_latency_ms']} ms`) |")
        md_lines.append(f"| **Tokens Used** | `{no_rag['tokens_used']}` | `{rag['tokens_used']}` |")
        md_lines.append(f"| **Sources** | *None* | `{', '.join(rag['sources'])}` |")
        md_lines.append(f"| **Top Similarity** | *N/A* | `{rag['top_similarity']}` |")
        md_lines.append(f"")
        md_lines.append(f"<details><summary><b>View Retrieved Context Chunks</b></summary>")
        md_lines.append(f"")
        for chunk in rag["retrieved_chunks"]:
            md_lines.append(f"- **[{chunk['source']} | {chunk['type']} | score: {chunk['similarity']}]:** {chunk['preview']}")
        md_lines.append(f"</details>")
        md_lines.append(f"")
        md_lines.append(f"---")
        md_lines.append(f"")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))


def main():
    parser = argparse.ArgumentParser(description="ShopBot RAG vs No-RAG Comparison Demo")
    parser.add_argument("--model", default="codellama", help="Ollama model to use (default: codellama)")
    parser.add_argument("--json-out", default=DEFAULT_JSON_PATH, help="Path for output JSON file")
    parser.add_argument("--md-out", default=DEFAULT_MD_PATH, help="Path for output Markdown report")
    args = parser.parse_args()

    print("\n" + "═" * 70)
    print("  ShopBot AI — Exercise 3: RAG vs No-RAG Comparison")
    print("═" * 70)
    print(f"  Model: {args.model}")
    print(f"  Comparing {len(DEMO_QUESTIONS)} questions\n")

    results = []
    for q in DEMO_QUESTIONS:
        res = compare(q, args.model)
        results.append(res)

    print_separator("═")
    print("  Summary:")
    print("  • With RAG: Answers grounded in actual store data")
    print("  • Without RAG: Generic/hallucinated responses")
    print("  • RAG adds retrieval latency but dramatically improves accuracy")
    print_separator("═")

    # Save to files
    save_results(results, args.model, args.json_out, args.md_out)
    print(f"\n💾 Results successfully saved to:")
    print(f"   • JSON:     {os.path.abspath(args.json_out)}")
    print(f"   • Markdown: {os.path.abspath(args.md_out)}\n")


if __name__ == "__main__":
    main()
