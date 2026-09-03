"""
rag_analysis.py — Records and analyses RAG pipeline traces (W4-E5)
For 10 selected questions: captures QUESTION → RETRIEVED CONTEXT → LLM RESPONSE
and classifies retrieval quality and response quality.

Usage: python rag_analysis.py
Produces: rag_analysis_report.md
"""

import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex1_basic"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex2_knowledge_base"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex3_rag"))

from rag_pipeline import rag_chat
from retriever import retrieve

REPORT_PATH = os.path.join(os.path.dirname(__file__), "rag_analysis_report.md")

# 10 selected questions representing different RAG outcome cases
ANALYSIS_QUESTIONS = [
    {
        "id": "A01",
        "case": "Perfect Retrieval → Correct Answer",
        "question": "What is the return window for products at TechMart?",
        "ground_truth": "30 days from delivery date",
        "expected_source": "policies.md",
        "expected_case_type": "✅ Relevant retrieved → ✅ Correct answer"
    },
    {
        "id": "A02",
        "case": "Perfect Retrieval → Correct Answer",
        "question": "How much does express shipping cost?",
        "ground_truth": "$9.99 USD, 2-3 business days",
        "expected_source": "shipping_zones.json",
        "expected_case_type": "✅ Relevant retrieved → ✅ Correct answer"
    },
    {
        "id": "A03",
        "case": "Irrelevant Chunk Retrieved → LLM Still Correct",
        "question": "What is the total cost of the Dell XPS 15 with express shipping?",
        "ground_truth": "$1509.98 ($1499.99 + $9.99)",
        "expected_source": "products.json + shipping_zones.json",
        "expected_case_type": "⚠️ Mixed retrieval → ✅ LLM synthesises correctly"
    },
    {
        "id": "A04",
        "case": "Good Retrieval → LLM Correct Answer",
        "question": "Can I return a defective item even after 30 days?",
        "ground_truth": "Defective items must be reported within 7 days of delivery for free return",
        "expected_source": "policies.md",
        "expected_case_type": "✅ Relevant retrieved → ✅ Correct answer"
    },
    {
        "id": "A05",
        "case": "No Relevant Context → LLM Should Admit Uncertainty",
        "question": "What is the price of the iPhone 15 Pro?",
        "ground_truth": "Not in knowledge base — model should say it doesn't have this info",
        "expected_source": "NOT_IN_KB",
        "expected_case_type": "🚫 Not in KB → ✅ Model correctly uncertain OR ❌ Hallucinated"
    },
    {
        "id": "A06",
        "case": "Partial Retrieval → Partial Answer",
        "question": "Which product has the longest warranty at TechMart?",
        "ground_truth": "ASUS ROG Monitor, Dell UltraSharp, WD Passport SSD all have 3-year warranty",
        "expected_source": "products.json",
        "expected_case_type": "⚠️ Partial retrieval → ⚠️ Partial answer (depends on which products retrieved)"
    },
    {
        "id": "A07",
        "case": "Good Context → LLM Hallucinates Despite Context",
        "question": "Do you offer same-day delivery?",
        "ground_truth": "No, fastest is Overnight (next business day, $24.99)",
        "expected_source": "shipping_zones.json",
        "expected_case_type": "✅ Relevant retrieved → ❌ Possible hallucination check"
    },
    {
        "id": "A08",
        "case": "Multi-source Retrieval → Complex Correct Answer",
        "question": "What payment methods are accepted and is there a financing option?",
        "ground_truth": "Visa, Mastercard, Amex, PayPal, Apple/Google Pay, Gift Cards, Affirm (0% APR 6 months on $200+)",
        "expected_source": "policies.md",
        "expected_case_type": "✅ Relevant retrieved → ✅ Correct multi-fact answer"
    },
    {
        "id": "A09",
        "case": "Retrieval Miss → Missing Important Info",
        "question": "Can I ship to a P.O. Box with express shipping?",
        "ground_truth": "No, P.O. Boxes only allowed for standard shipping, not express or overnight",
        "expected_source": "shipping_zones.json",
        "expected_case_type": "⚠️ Context may include/miss PO Box detail → varies"
    },
    {
        "id": "A10",
        "case": "Live Data Required → Model Should Defer",
        "question": "What is the current status of my order number 98765?",
        "ground_truth": "Cannot access live order data — should direct to My Orders or support",
        "expected_source": "NOT_IN_KB",
        "expected_case_type": "🚫 Requires live data → ✅ Model correctly defers OR ❌ Hallucinated status"
    },
]


def classify_retrieval(chunks, expected_source):
    """Classify whether the retrieval was relevant, partial, or missed."""
    if expected_source == "NOT_IN_KB":
        return "NOT_APPLICABLE", "Expected source not in knowledge base"

    expected = [s.strip() for s in expected_source.split("+")]
    retrieved_sources = [c.get("source", "") for c in chunks]

    matched = [es for es in expected if any(es in rs for rs in retrieved_sources)]

    if len(matched) == len(expected):
        return "RELEVANT", f"All expected sources retrieved: {matched}"
    elif len(matched) > 0:
        return "PARTIAL", f"Partially retrieved: {matched}, missing: {[e for e in expected if e not in matched]}"
    else:
        return "MISSED", f"None of expected sources ({expected}) in retrieved: {retrieved_sources}"


def classify_response(actual, ground_truth, is_not_in_kb=False):
    """Classify the LLM response quality."""
    actual_lower = actual.lower()
    gt_lower = ground_truth.lower()

    uncertainty_phrases = ["don't have", "do not have", "not available", "unable to",
                           "cannot access", "no information", "not in", "i don't know",
                           "contact support", "check your account", "not listed"]

    if is_not_in_kb:
        admitted = any(p in actual_lower for p in uncertainty_phrases)
        if admitted:
            return "CORRECTLY_UNCERTAIN", "Model correctly admitted lack of information"
        else:
            return "HALLUCINATED", "Model gave a specific answer despite having no KB context"

    import re
    gt_tokens = re.findall(r'\b\w{4,}\b', gt_lower)
    if not gt_tokens:
        return "UNKNOWN", "Could not evaluate"

    matches = sum(1 for t in gt_tokens if t in actual_lower)
    ratio = matches / len(gt_tokens)

    if ratio >= 0.6:
        return "CORRECT", f"Key facts matched ({matches}/{len(gt_tokens)} tokens)"
    elif ratio >= 0.3:
        return "PARTIAL", f"Partially correct ({matches}/{len(gt_tokens)} tokens matched)"
    else:
        return "INCORRECT_OR_HALLUCINATED", f"Low match ({matches}/{len(gt_tokens)} tokens)"


def run_analysis(model="codellama"):
    print(f"\n{'='*65}")
    print(f"  ShopBot RAG Pipeline Analysis — Model: {model}")
    print(f"  Tracing {len(ANALYSIS_QUESTIONS)} questions")
    print(f"{'='*65}\n")

    traces = []
    for q in ANALYSIS_QUESTIONS:
        print(f"[{q['id']}] {q['question'][:60]}...")
        result = rag_chat(q["question"], model=model, top_k=3)

        chunks = result["retrieved_chunks"]
        retrieval_class, retrieval_notes = classify_retrieval(chunks, q["expected_source"])
        is_not_in_kb = q["expected_source"] == "NOT_IN_KB"
        response_class, response_notes = classify_response(
            result["response"], q["ground_truth"], is_not_in_kb
        )

        trace = {
            "id": q["id"],
            "case_description": q["case"],
            "expected_case_type": q["expected_case_type"],
            "question": q["question"],
            "ground_truth": q["ground_truth"],
            "response": result["response"],
            "retrieved_chunks": [
                {
                    "source": c["source"],
                    "type": c["type"],
                    "similarity": c["similarity_score"],
                    "preview": c["text"][:200]
                } for c in chunks
            ],
            "retrieval_classification": retrieval_class,
            "retrieval_notes": retrieval_notes,
            "response_classification": response_class,
            "response_notes": response_notes,
            "metrics": result["metrics"]
        }
        traces.append(trace)
        time.sleep(0.3)

    return traces


def build_report(traces, model):
    lines = []
    lines.append("# ShopBot AI — RAG Pipeline Analysis Report (W4-E5)\n")
    lines.append(f"> Model: `{model}` | Questions analysed: {len(traces)}\n")
    lines.append("> **Objective:** Understand how retrieval quality affects LLM response quality.\n")
    lines.append("> The pipeline is: `QUESTION → EMBED → RETRIEVE → CONTEXT → LLM → RESPONSE`\n")

    # Legend
    lines.append("\n## Legend\n")
    lines.append("| Symbol | Meaning |")
    lines.append("|--------|---------|")
    lines.append("| ✅ RELEVANT | Correct source documents retrieved |")
    lines.append("| ⚠️ PARTIAL | Some but not all expected sources retrieved |")
    lines.append("| 🚫 MISSED | Expected source not retrieved |")
    lines.append("| ❌ HALLUCINATED | Model stated false/invented facts |")
    lines.append("| 🎯 CORRECT | Response matches ground truth |")
    lines.append("| 💬 PARTIAL | Response partially matches ground truth |")
    lines.append("| ❓ UNCERTAIN | Model correctly admitted lack of knowledge |")

    retrieval_emoji = {
        "RELEVANT": "✅",
        "PARTIAL": "⚠️",
        "MISSED": "🚫",
        "NOT_APPLICABLE": "—"
    }
    response_emoji = {
        "CORRECT": "🎯",
        "PARTIAL": "💬",
        "CORRECTLY_UNCERTAIN": "❓",
        "HALLUCINATED": "❌",
        "INCORRECT_OR_HALLUCINATED": "❌",
        "UNKNOWN": "❔"
    }

    lines.append("\n---\n")
    lines.append("## Traced Examples\n")

    for t in traces:
        r_emoji = retrieval_emoji.get(t["retrieval_classification"], "?")
        resp_emoji = response_emoji.get(t["response_classification"], "?")

        lines.append(f"### [{t['id']}] {t['case_description']}\n")
        lines.append(f"**Expected outcome:** {t['expected_case_type']}\n")
        lines.append(f"**Actual outcome:** {r_emoji} {t['retrieval_classification']} retrieval → {resp_emoji} {t['response_classification']} response\n")

        lines.append(f"**QUESTION:**\n> {t['question']}\n")
        lines.append(f"**GROUND TRUTH:**\n> {t['ground_truth']}\n")

        lines.append("**RETRIEVED CONTEXT:**\n")
        if t["retrieved_chunks"]:
            for i, c in enumerate(t["retrieved_chunks"]):
                lines.append(f"> **Chunk {i+1}** | Source: `{c['source']}` | Type: `{c['type']}` | Similarity: `{c['similarity']:.3f}`")
                lines.append(f"> {c['preview']}...\n")
        else:
            lines.append("> *(No chunks retrieved)*\n")

        lines.append(f"**LLM RESPONSE:**\n> {t['response']}\n")

        lines.append(f"**ANALYSIS:**\n")
        lines.append(f"- Retrieval: {r_emoji} `{t['retrieval_classification']}` — {t['retrieval_notes']}")
        lines.append(f"- Response: {resp_emoji} `{t['response_classification']}` — {t['response_notes']}")
        lines.append(f"- Latency: {t['metrics']['total_latency_ms']}ms | Tokens: {t['metrics']['tokens_used']} | Chunks: {t['metrics']['chunks_retrieved']}\n")
        lines.append("---\n")

    # Summary table
    lines.append("## Summary Table\n")
    lines.append("| ID | Case | Retrieval | Response |")
    lines.append("|----|------|-----------|----------|")
    for t in traces:
        r = retrieval_emoji.get(t["retrieval_classification"], "?") + " " + t["retrieval_classification"]
        resp = response_emoji.get(t["response_classification"], "?") + " " + t["response_classification"]
        lines.append(f"| {t['id']} | {t['case_description'][:40]} | {r} | {resp} |")

    lines.append("\n---\n")
    lines.append("## Key Insights\n")

    correct_retrieval = sum(1 for t in traces if t["retrieval_classification"] == "RELEVANT")
    hallucinated = sum(1 for t in traces if t["response_classification"] in ["HALLUCINATED", "INCORRECT_OR_HALLUCINATED"])
    correct_resp = sum(1 for t in traces if t["response_classification"] == "CORRECT")

    lines.append(f"- **Retrieval Accuracy:** {correct_retrieval}/{len(traces)} questions retrieved relevant context")
    lines.append(f"- **Response Accuracy:** {correct_resp}/{len(traces)} responses matched ground truth")
    lines.append(f"- **Hallucinations:** {hallucinated}/{len(traces)} responses contained false information")
    lines.append(f"\n**Relationship: RETRIEVAL QUALITY → CONTEXT QUALITY → RESPONSE QUALITY**\n")
    lines.append("> When retrieval is accurate (RELEVANT), LLM responses tend to be correct.")
    lines.append("> When retrieval misses the right document, the LLM either hallucinates or gives a generic answer.")
    lines.append("> Even with good retrieval, LLMs can misinterpret context — RAG is not a guarantee of correctness.")
    lines.append("> For questions outside the knowledge base, the LLM must clearly admit uncertainty — failure to do so is a hallucination.\n")

    return "\n".join(lines)


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "codellama"
    traces = run_analysis(model)
    report = build_report(traces, model)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ RAG analysis report saved: {REPORT_PATH}")

    # Save raw traces
    trace_path = os.path.join(os.path.dirname(__file__), "results", f"rag_traces_{model}.json")
    os.makedirs(os.path.dirname(trace_path), exist_ok=True)
    with open(trace_path, "w") as f:
        json.dump(traces, f, indent=2)
    print(f"💾 Raw traces saved: {trace_path}")


if __name__ == "__main__":
    main()
