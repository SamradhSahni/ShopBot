"""
output_tests.py — AI Output Testing Suite
==========================================
25 test cases that systematically check whether ShopBot's LLM output
satisfies defined pass/fail conditions BEFORE it is accepted by the app.

Test Categories:
  A. Relevance        (5 tests) — Is the answer relevant to the question?
  B. Groundedness     (5 tests) — Is the answer supported by context?
  C. Format           (5 tests) — Does output follow the expected format?
  D. Correct Refusal  (5 tests) — Does it refuse when info is unavailable?
  E. Correct Answer   (5 tests) — Does it answer when info IS available?

Each test has:
  - question, context, expected_behavior
  - pass/fail criteria functions
  - PASS / PARTIAL / FAIL verdict

Run from shopbot/ root:
    python evaluation/output_tests.py
"""

import sys, os, re, json, time, requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ex4_services", "app_service"))
from guardrails import GuardrailEngine

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("TEST_MODEL", "deepseek-coder")
engine = GuardrailEngine()

RAG_PROMPT = """You are ShopBot, TechMart's customer support assistant.
The following is TechMart's live store data. Answer using ONLY this data. Be direct.
Do NOT say "I don't have access to". Do NOT start with "I'm sorry".

TechMart Store Data:
{context}

Customer: {question}
ShopBot:"""

NO_RAG_PROMPT = """You are ShopBot, TechMart's customer support assistant.
Answer the customer's question helpfully. Do not invent specific prices or policies.

Customer: {question}
ShopBot:"""


def call_llm(question: str, context: str = "", max_tokens: int = 300) -> tuple:
    """Call Ollama, return (response_text, latency_ms)."""
    prompt = RAG_PROMPT.format(context=context, question=question) if context else NO_RAG_PROMPT.format(question=question)
    t0 = time.time()
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.1, "num_predict": max_tokens, "num_ctx": 2048}
        }, timeout=120)
        resp = r.json().get("response", "").strip()
        return resp, int((time.time()-t0)*1000)
    except Exception as e:
        return f"ERROR:{e}", 0


# ── Test Criteria Functions ───────────────────────────────────────────────────

def contains_keywords(response: str, keywords: list, min_count: int = 2) -> bool:
    rl = response.lower()
    return sum(1 for k in keywords if k.lower() in rl) >= min_count

def not_contains(response: str, bad_phrases: list) -> bool:
    rl = response.lower()
    return not any(p.lower() in rl for p in bad_phrases)

def is_grounded(response: str, context: str, min_overlap: int = 2) -> bool:
    """Check if response terms appear in context (basic groundedness)."""
    stop = {"the","a","an","is","are","in","on","at","to","of","and","or","it","be","for","with","this","that"}
    r_tokens = set(t for t in re.findall(r'\b\w{4,}\b', response.lower()) if t not in stop)
    c_tokens = set(t for t in re.findall(r'\b\w{4,}\b', context.lower()) if t not in stop)
    overlap = len(r_tokens & c_tokens)
    return overlap >= min_overlap

def is_refusal(response: str) -> bool:
    refusal_phrases = ["don't have","do not have","contact techmart","contact support",
                       "not have that information","unable to find","not in my knowledge",
                       "reach out to","not available","not listed","please contact"]
    rl = response.lower()
    return any(p in rl for p in refusal_phrases)

def no_markdown_headers(response: str) -> bool:
    return not bool(re.search(r'^#{1,4}\s', response, re.MULTILINE))

def min_length(response: str, chars: int = 30) -> bool:
    return len(response.strip()) >= chars

def max_length(response: str, chars: int = 800) -> bool:
    return len(response.strip()) <= chars

def no_apology_prefix(response: str) -> bool:
    rl = response.strip().lower()
    bad = ["i'm sorry", "i am sorry", "as an ai", "i don't have access", "i cannot access"]
    return not any(rl.startswith(p) for p in bad)


# ── Knowledge Base Snippets for Context ──────────────────────────────────────

PRODUCT_CONTEXT = """Dell XPS 15 — Price: $1,299
Display: 15.6" OLED 3.5K touch
Processor: Intel Core i7-13700H
RAM: 16GB DDR5
Storage: 512GB NVMe SSD
GPU: NVIDIA RTX 4060 8GB
Warranty: 2-year manufacturer
In Stock: Yes
Rating: 4.7/5"""

POLICY_CONTEXT = """TechMart Return Policy:
- 30-day return window from purchase date
- Items must be in original packaging with receipt
- Opened software and digital downloads are non-refundable
- Final Sale items cannot be returned
- Refunds processed within 5-7 business days"""

SHIPPING_CONTEXT = """TechMart Shipping Options:
- Standard Shipping: Free on orders over $50, 5-7 business days
- Express Shipping: $15.99, 2-3 business days
- Same-Day Delivery: $29.99, select cities only
- International Shipping: Available in 30+ countries"""

PAYMENT_CONTEXT = """TechMart Accepted Payment Methods:
- Credit Cards: Visa, MasterCard, American Express
- Debit Cards: Visa Debit, MasterCard Debit
- PayPal and PayPal Credit
- TechMart Gift Cards
- Buy Now Pay Later: Affirm, Klarna (min. $100 purchase)"""


# ── Test Cases ────────────────────────────────────────────────────────────────

TEST_CASES = [

    # ── A. RELEVANCE (5) ──────────────────────────────────────────────────────
    {
        "id": "A01", "category": "Relevance",
        "question": "What is the price of the Dell XPS 15?",
        "context": PRODUCT_CONTEXT,
        "expected": "answer contains price ($1,299) and product name",
        "criteria": [
            ("Contains price",    lambda r,c: contains_keywords(r, ["1,299","1299","price"], 1)),
            ("Contains product",  lambda r,c: contains_keywords(r, ["dell","xps"], 1)),
            ("No apology prefix", lambda r,c: no_apology_prefix(r)),
            ("Min length",        lambda r,c: min_length(r, 20)),
        ],
        "pass_threshold": 3,
    },
    {
        "id": "A02", "category": "Relevance",
        "question": "How long is the return window at TechMart?",
        "context": POLICY_CONTEXT,
        "expected": "answer mentions 30 days",
        "criteria": [
            ("Contains 30",       lambda r,c: contains_keywords(r, ["30","thirty"], 1)),
            ("Contains days/return",lambda r,c: contains_keywords(r, ["day","return","window"], 1)),
            ("No apology prefix", lambda r,c: no_apology_prefix(r)),
            ("Min length",        lambda r,c: min_length(r, 20)),
        ],
        "pass_threshold": 3,
    },
    {
        "id": "A03", "category": "Relevance",
        "question": "How much does express shipping cost?",
        "context": SHIPPING_CONTEXT,
        "expected": "answer mentions $15.99",
        "criteria": [
            ("Contains price",    lambda r,c: contains_keywords(r, ["15.99","15","express"], 1)),
            ("Contains shipping", lambda r,c: contains_keywords(r, ["ship","express","deliver"], 1)),
            ("No apology prefix", lambda r,c: no_apology_prefix(r)),
            ("Min length",        lambda r,c: min_length(r, 15)),
        ],
        "pass_threshold": 3,
    },
    {
        "id": "A04", "category": "Relevance",
        "question": "Do you accept PayPal?",
        "context": PAYMENT_CONTEXT,
        "expected": "confirms PayPal is accepted",
        "criteria": [
            ("Mentions PayPal",   lambda r,c: "paypal" in r.lower()),
            ("Positive answer",   lambda r,c: any(w in r.lower() for w in ["yes","accept","available","can","do"])),
            ("No apology prefix", lambda r,c: no_apology_prefix(r)),
            ("Min length",        lambda r,c: min_length(r, 10)),
        ],
        "pass_threshold": 3,
    },
    {
        "id": "A05", "category": "Relevance",
        "question": "What GPU does the Dell XPS 15 have?",
        "context": PRODUCT_CONTEXT,
        "expected": "mentions RTX 4060",
        "criteria": [
            ("Mentions RTX",      lambda r,c: any(t in r.lower() for t in ["rtx","4060","nvidia"])),
            ("Relevant response", lambda r,c: contains_keywords(r, ["gpu","graphics","nvidia","rtx"], 1)),
            ("No apology prefix", lambda r,c: no_apology_prefix(r)),
            ("Min length",        lambda r,c: min_length(r, 10)),
        ],
        "pass_threshold": 3,
    },

    # ── B. GROUNDEDNESS (5) ────────────────────────────────────────────────────
    {
        "id": "B01", "category": "Groundedness",
        "question": "Tell me about the Dell XPS 15.",
        "context": PRODUCT_CONTEXT,
        "expected": "response grounded in provided specs",
        "criteria": [
            ("Grounded in context", lambda r,c: is_grounded(r, c, 4)),
            ("Mentions actual specs",lambda r,c: contains_keywords(r, ["1,299","oled","i7","16gb","512"], 2)),
            ("No apology prefix",  lambda r,c: no_apology_prefix(r)),
            ("Max length",         lambda r,c: max_length(r, 600)),
        ],
        "pass_threshold": 3,
    },
    {
        "id": "B02", "category": "Groundedness",
        "question": "What items cannot be returned?",
        "context": POLICY_CONTEXT,
        "expected": "mentions software and final sale items from context",
        "criteria": [
            ("Grounded in context", lambda r,c: is_grounded(r, c, 3)),
            ("Mentions non-returnable", lambda r,c: contains_keywords(r, ["software","digital","final","sale","open"], 1)),
            ("No apology prefix",  lambda r,c: no_apology_prefix(r)),
            ("Min length",         lambda r,c: min_length(r, 20)),
        ],
        "pass_threshold": 3,
    },
    {
        "id": "B03", "category": "Groundedness",
        "question": "Is same-day delivery available and how much does it cost?",
        "context": SHIPPING_CONTEXT,
        "expected": "mentions $29.99 and select cities",
        "criteria": [
            ("Grounded in context", lambda r,c: is_grounded(r, c, 3)),
            ("Mentions price",     lambda r,c: "29.99" in r or "29" in r),
            ("Mentions availability caveat", lambda r,c: any(t in r.lower() for t in ["select","certain","cities","available"])),
            ("No apology prefix",  lambda r,c: no_apology_prefix(r)),
        ],
        "pass_threshold": 3,
    },
    {
        "id": "B04", "category": "Groundedness",
        "question": "What is the RAM in the Dell XPS 15?",
        "context": PRODUCT_CONTEXT,
        "expected": "states 16GB DDR5 from context",
        "criteria": [
            ("Grounded in context", lambda r,c: is_grounded(r, c, 2)),
            ("Correct RAM value",  lambda r,c: "16" in r and any(t in r.lower() for t in ["gb","ram","ddr5","memory"])),
            ("No invented specs",  lambda r,c: not contains_keywords(r, ["32gb","64gb","8gb"], 1)),
            ("No apology prefix",  lambda r,c: no_apology_prefix(r)),
        ],
        "pass_threshold": 3,
    },
    {
        "id": "B05", "category": "Groundedness",
        "question": "How many business days does a refund take?",
        "context": POLICY_CONTEXT,
        "expected": "states 5-7 business days from context",
        "criteria": [
            ("Grounded in context", lambda r,c: is_grounded(r, c, 2)),
            ("Correct timeframe",  lambda r,c: any(t in r for t in ["5-7","5 to 7","five","5","7"])),
            ("Mentions business days", lambda r,c: "business" in r.lower() or "day" in r.lower()),
            ("No apology prefix",  lambda r,c: no_apology_prefix(r)),
        ],
        "pass_threshold": 3,
    },

    # ── C. FORMAT (5) ──────────────────────────────────────────────────────────
    {
        "id": "C01", "category": "Format",
        "question": "What payment methods do you accept?",
        "context": PAYMENT_CONTEXT,
        "expected": "plain English, no markdown headers, reasonable length",
        "criteria": [
            ("No markdown headers", lambda r,c: no_markdown_headers(r)),
            ("No apology prefix",   lambda r,c: no_apology_prefix(r)),
            ("Min length",          lambda r,c: min_length(r, 20)),
            ("Max length",          lambda r,c: max_length(r, 600)),
        ],
        "pass_threshold": 4,
    },
    {
        "id": "C02", "category": "Format",
        "question": "What is TechMart's return policy?",
        "context": POLICY_CONTEXT,
        "expected": "does not use ### markdown headers",
        "criteria": [
            ("No markdown headers", lambda r,c: no_markdown_headers(r)),
            ("No 'STORE INFORMATION'", lambda r,c: "store information" not in r.lower()),
            ("No apology prefix",   lambda r,c: no_apology_prefix(r)),
            ("Min length",          lambda r,c: min_length(r, 30)),
        ],
        "pass_threshold": 4,
    },
    {
        "id": "C03", "category": "Format",
        "question": "Tell me about shipping options.",
        "context": SHIPPING_CONTEXT,
        "expected": "friendly tone, no error strings, readable",
        "criteria": [
            ("No error strings",    lambda r,c: not_contains(r, ["error:","exception:","traceback","500"])),
            ("No apology prefix",   lambda r,c: no_apology_prefix(r)),
            ("Min length",          lambda r,c: min_length(r, 30)),
            ("Max length",          lambda r,c: max_length(r, 700)),
        ],
        "pass_threshold": 4,
    },
    {
        "id": "C04", "category": "Format",
        "question": "What is the warranty on the Dell XPS 15?",
        "context": PRODUCT_CONTEXT,
        "expected": "mentions 2-year warranty without source labels",
        "criteria": [
            ("No source labels",    lambda r,c: "[source:" not in r.lower()),
            ("No apology prefix",   lambda r,c: no_apology_prefix(r)),
            ("Min length",          lambda r,c: min_length(r, 10)),
            ("Mentions warranty",   lambda r,c: "warranty" in r.lower() or "year" in r.lower()),
        ],
        "pass_threshold": 4,
    },
    {
        "id": "C05", "category": "Format",
        "question": "How do I track my order?",
        "context": "",
        "expected": "helpful response, no blank output, no error message",
        "criteria": [
            ("No error strings",    lambda r,c: not_contains(r, ["error:","exception:","traceback"])),
            ("No apology prefix",   lambda r,c: no_apology_prefix(r)),
            ("Min length",          lambda r,c: min_length(r, 20)),
            ("Not blank",           lambda r,c: bool(r.strip())),
        ],
        "pass_threshold": 4,
    },

    # ── D. CORRECT REFUSAL (5) ────────────────────────────────────────────────
    {
        "id": "D01", "category": "Correct Refusal",
        "question": "What is the price of the TechMart Xbox Series X bundle from 2021?",
        "context": "",
        "expected": "should refuse or redirect — no made-up prices",
        "criteria": [
            ("No invented price",   lambda r,c: not bool(re.search(r'\$\d{3,4}', r))),
            ("No apology prefix",   lambda r,c: no_apology_prefix(r)),
            ("Min length",          lambda r,c: min_length(r, 10)),
        ],
        "pass_threshold": 2,
    },
    {
        "id": "D02", "category": "Correct Refusal",
        "question": "What is TechMart's lunar new year 2027 discount policy?",
        "context": "",
        "expected": "should say information is not available",
        "criteria": [
            ("Appropriate refusal or redirect", lambda r,c: is_refusal(r) or "contact" in r.lower() or "don't have" in r.lower() or "not have" in r.lower()),
            ("No invented policy",  lambda r,c: not bool(re.search(r'\d+\s*%\s*(off|discount)', r))),
            ("Min length",          lambda r,c: min_length(r, 10)),
        ],
        "pass_threshold": 2,
    },
    {
        "id": "D03", "category": "Correct Refusal",
        "question": "Can you give me the personal email of TechMart's CEO?",
        "context": "",
        "expected": "should refuse — personal data not available",
        "criteria": [
            ("No email address",    lambda r,c: not bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', r))),
            ("Refusal or redirect", lambda r,c: is_refusal(r) or "private" in r.lower() or "not available" in r.lower() or "cannot" in r.lower()),
            ("Min length",          lambda r,c: min_length(r, 10)),
        ],
        "pass_threshold": 2,
    },
    {
        "id": "D04", "category": "Correct Refusal",
        "question": "What was TechMart's Q3 revenue for 2025?",
        "context": "",
        "expected": "should refuse — financial data not in KB",
        "criteria": [
            ("No invented revenue", lambda r,c: not bool(re.search(r'\$\d+\s*(million|billion|M|B)', r))),
            ("Min length",          lambda r,c: min_length(r, 10)),
        ],
        "pass_threshold": 2,
    },
    {
        "id": "D05", "category": "Correct Refusal",
        "question": "What are the staff working hours at the Tokyo TechMart store?",
        "context": "",
        "expected": "should say it doesn't have that specific info",
        "criteria": [
            ("No invented hours",   lambda r,c: not bool(re.search(r'\d+\s*(am|pm|AM|PM|\:00)', r))),
            ("Redirect or refusal", lambda r,c: is_refusal(r) or "contact" in r.lower() or "specific" in r.lower()),
            ("Min length",          lambda r,c: min_length(r, 10)),
        ],
        "pass_threshold": 2,
    },

    # ── E. CORRECT ANSWER (5) ─────────────────────────────────────────────────
    {
        "id": "E01", "category": "Correct Answer",
        "question": "Is the Dell XPS 15 available in stock?",
        "context": PRODUCT_CONTEXT,
        "expected": "should confirm it's in stock (context says Yes)",
        "criteria": [
            ("Confirms availability", lambda r,c: any(t in r.lower() for t in ["in stock","available","yes","currently"])),
            ("No refusal",           lambda r,c: not is_refusal(r)),
            ("Min length",           lambda r,c: min_length(r, 10)),
        ],
        "pass_threshold": 2,
    },
    {
        "id": "E02", "category": "Correct Answer",
        "question": "What is the free shipping threshold at TechMart?",
        "context": SHIPPING_CONTEXT,
        "expected": "should state free shipping on orders over $50",
        "criteria": [
            ("Mentions $50",         lambda r,c: "50" in r),
            ("Mentions free",        lambda r,c: "free" in r.lower()),
            ("No refusal",           lambda r,c: not is_refusal(r)),
            ("Min length",           lambda r,c: min_length(r, 10)),
        ],
        "pass_threshold": 3,
    },
    {
        "id": "E03", "category": "Correct Answer",
        "question": "Does TechMart accept buy now pay later?",
        "context": PAYMENT_CONTEXT,
        "expected": "confirms BNPL via Affirm/Klarna",
        "criteria": [
            ("Confirms BNPL",        lambda r,c: any(t in r.lower() for t in ["yes","affirm","klarna","buy now","pay later"])),
            ("No refusal",           lambda r,c: not is_refusal(r)),
            ("Min length",           lambda r,c: min_length(r, 10)),
        ],
        "pass_threshold": 2,
    },
    {
        "id": "E04", "category": "Correct Answer",
        "question": "What is the display size of the Dell XPS 15?",
        "context": PRODUCT_CONTEXT,
        "expected": "states 15.6 inch",
        "criteria": [
            ("Correct size",         lambda r,c: any(t in r for t in ["15.6","15\"","15-inch"])),
            ("No refusal",           lambda r,c: not is_refusal(r)),
            ("Min length",           lambda r,c: min_length(r, 10)),
        ],
        "pass_threshold": 2,
    },
    {
        "id": "E05", "category": "Correct Answer",
        "question": "How do I return a product to TechMart?",
        "context": POLICY_CONTEXT,
        "expected": "gives return instructions from policy context",
        "criteria": [
            ("Mentions 30 days",     lambda r,c: "30" in r),
            ("Mentions receipt/packaging", lambda r,c: any(t in r.lower() for t in ["original","receipt","packaging"])),
            ("No refusal",           lambda r,c: not is_refusal(r)),
            ("Min length",           lambda r,c: min_length(r, 30)),
        ],
        "pass_threshold": 3,
    },
]


# ── Test Runner ───────────────────────────────────────────────────────────────

def run_tests():
    print(f"\n{'='*70}")
    print(f"  ShopBot AI Output Testing — 25 Test Cases")
    print(f"  Model: {MODEL}")
    print(f"{'='*70}")

    results = []
    category_counts = {}

    for test in TEST_CASES:
        tid = test["id"]
        cat = test["category"]
        q   = test["question"]
        ctx = test["context"]
        threshold = test["pass_threshold"]

        print(f"\n[{tid}] ({cat}): {q[:60]}{'...' if len(q)>60 else ''}")

        # Get LLM response
        response, latency = call_llm(q, ctx)
        print(f"  LLM ({latency}ms): {response[:120].replace(chr(10),' ')}{'...' if len(response)>120 else ''}")

        # Evaluate criteria
        passed_criteria = 0
        criteria_results = []
        for cname, cfn in test["criteria"]:
            try:
                passed = cfn(response, ctx)
            except Exception as e:
                passed = False
            criteria_results.append({"name": cname, "passed": passed})
            if passed:
                passed_criteria += 1

        # Verdict
        total = len(test["criteria"])
        if passed_criteria >= threshold:
            verdict = "PASS"
            icon = "✅"
        elif passed_criteria >= threshold - 1:
            verdict = "PARTIAL"
            icon = "⚠️ "
        else:
            verdict = "FAIL"
            icon = "❌"

        print(f"  {icon} {verdict} — {passed_criteria}/{total} criteria met (threshold={threshold})")
        for cr in criteria_results:
            status = "✓" if cr["passed"] else "✗"
            print(f"       [{status}] {cr['name']}")

        rec = {
            "id": tid, "category": cat, "question": q,
            "response": response, "latency_ms": latency,
            "criteria_passed": passed_criteria, "criteria_total": total,
            "threshold": threshold, "verdict": verdict,
            "criteria_results": criteria_results,
        }
        results.append(rec)

        if cat not in category_counts:
            category_counts[cat] = {"PASS":0,"PARTIAL":0,"FAIL":0}
        category_counts[cat][verdict] += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n\n{'='*70}")
    print(f"  TEST SUMMARY")
    print(f"{'='*70}")
    total_pass = sum(1 for r in results if r["verdict"]=="PASS")
    total_partial = sum(1 for r in results if r["verdict"]=="PARTIAL")
    total_fail = sum(1 for r in results if r["verdict"]=="FAIL")

    print(f"\n  {'Category':<25} {'PASS':>6} {'PARTIAL':>8} {'FAIL':>6}")
    print(f"  {'-'*50}")
    for cat, counts in category_counts.items():
        print(f"  {cat:<25} {counts['PASS']:>6} {counts['PARTIAL']:>8} {counts['FAIL']:>6}")
    print(f"  {'-'*50}")
    print(f"  {'TOTAL (25 tests)':<25} {total_pass:>6} {total_partial:>8} {total_fail:>6}")
    pass_rate = round((total_pass + 0.5*total_partial) / len(results) * 100, 1)
    print(f"\n  Effective Pass Rate: {pass_rate}%")
    print(f"  Full Pass: {total_pass}/25 | Partial: {total_partial}/25 | Fail: {total_fail}/25")

    # ── Save ─────────────────────────────────────────────────────────────────
    out = {
        "model": MODEL, "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "summary": {
            "total": len(results), "pass": total_pass,
            "partial": total_partial, "fail": total_fail,
            "pass_rate_pct": pass_rate
        },
        "by_category": category_counts,
        "results": results,
    }
    out_path = os.path.join(os.path.dirname(__file__), "results", f"output_tests_{MODEL.replace('-','_')}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved → {out_path}")
    return out


if __name__ == "__main__":
    run_tests()
