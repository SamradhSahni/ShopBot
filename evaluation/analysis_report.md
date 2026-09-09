# ShopBot AI — Model Evaluation Analysis Report

> Generated: 2026-09-09 21:18  
> Application: E-Commerce Product & Policy Support Bot (TechMart)  
> Models evaluated: codellama, starcoder2, deepseek-coder

---

## 1. Evaluation Setup

| Parameter | Value |
|-----------|-------|
| Total Questions | 25 |
| Categories | Product Info (5), Return Policy (5), Shipping (5), Cross-domain (5), Hallucination Traps (5) |
| Models Compared | Code Llama 7B, StarCoder2 7B, DeepSeek-Coder 6.7B |
| Embedding Model | nomic-embed-text (same for all) |
| Knowledge Base | 18 products, policies, FAQs, shipping zones |
| RAG Enabled | Yes (top-k=3, cosine similarity) |
| Temperature | 0.2 (same for all) |

---

## 2. Metric Definitions

| Metric | Type | Definition | Measurement |
|--------|------|-----------|-------------|
| **Correctness** | Quality | Does the answer match ground truth key facts? | Keyword overlap ratio: ≥60% = 1.0, ≥30% = 0.5, <30% = 0.0 |
| **Relevance** | Quality | Is the response topically on-topic? | Question-keyword overlap in response, 0.0–1.0 |
| **Retrieval Quality** | Quality | Were the right source documents retrieved? | Source match: correct source in top-3 chunks |
| **Hallucination Rate** | Quality | Did model state false/invented facts? | Trap detection + false claim detection, % of answers |
| **Response Latency** | Performance | Total time from request to response | `time.time()` wall clock, milliseconds |
| **Token Usage** | Performance | Output tokens consumed per response | Ollama `eval_count` field |
| **Memory Usage** | Performance | Peak RAM used by process | `psutil.Process().memory_info().rss`, MB |
| **CPU Usage** | Performance | CPU load during inference | `psutil.cpu_percent(interval=0.5)`, % |

---

## 3. Quality Metrics Comparison

| Metric | Codellama | Starcoder2 | Deepseek-coder |
|--------|--------|--------|--------|
| Avg Correctness (0–1) | **0.600** ✅ | 0.020 | 0.480 |
| Avg Relevance (0–1) | **0.867** ✅ | 0.605 | 0.764 |
| Avg Retrieval Quality | **0.920** ✅ | 0.920 | 0.920 |
| Hallucination Rate | **8.0%** ✅ | 12.0% | 8.0% |
| Trap Hallucination Rate | **50.0%** ✅ | 75.0% | 50.0% |
| Correct Answers | **11** ✅ | 0 | 8 |
| Partial Answers | 8 | **1** ✅ | 8 |
| Incorrect Answers | **6** ✅ | 24 | 9 |

---

## 4. Performance Metrics Comparison

| Metric | Codellama | Starcoder2 | Deepseek-coder |
|--------|--------|--------|--------|
| Avg Total Latency (ms) | 11055 | 5895 | **5463** ✅ |
| Avg LLM Latency (ms) | 8877 | 3800 | **3359** ✅ |
| Avg Retrieve Latency (ms) | 2176 | **2095** ✅ | 2102 |
| Avg Output Tokens | 88 | **31** ✅ | 113 |
| Avg Prompt Tokens | 740 | **419** ✅ | 704 |
| Total Tokens (all 25 Q) | 2209 | **782** ✅ | 2829 |
| Avg Memory Usage (MB) | 103.6 | 64.4 | **46.6** ✅ |
| Avg Memory Delta (MB) | **-0.99** ✅ | -0.81 | 0.01 |
| Avg CPU Usage (%) | 20.5 | 17.7 | **16.0** ✅ |

---

## 5. Per-Category Analysis

### Product Information

| Metric | Codellama | Starcoder2 | Deepseek-coder |
|--------|--------|--------|--------|
| Correctness | 0.60 | 0.10 | 0.60 |
| Retrieval Quality | 1.00 | 1.00 | 1.00 |

### Return Policy

| Metric | Codellama | Starcoder2 | Deepseek-coder |
|--------|--------|--------|--------|
| Correctness | 1.00 | 0.00 | 0.60 |
| Retrieval Quality | 1.00 | 1.00 | 1.00 |

### Shipping

| Metric | Codellama | Starcoder2 | Deepseek-coder |
|--------|--------|--------|--------|
| Correctness | 0.50 | 0.00 | 0.50 |
| Retrieval Quality | 0.80 | 0.80 | 0.80 |

### Cross-domain

| Metric | Codellama | Starcoder2 | Deepseek-coder |
|--------|--------|--------|--------|
| Correctness | 0.50 | 0.00 | 0.40 |
| Retrieval Quality | 0.80 | 0.80 | 0.80 |

### Hallucination Trap

| Metric | Codellama | Starcoder2 | Deepseek-coder |
|--------|--------|--------|--------|
| Correctness | 0.40 | 0.00 | 0.30 |
| Retrieval Quality | 1.00 | 1.00 | 1.00 |


---

## 6. Key Analysis Questions

**Q: Which model provides better accuracy?**  
→ `codellama` achieved the highest correctness score of 0.600.

**Q: Which model produces fewer hallucinations?**  
→ `codellama` had the lowest hallucination rate at 8.0%.

**Q: Which model provides better retrieval-based responses?**  
→ `codellama` achieved the best retrieval quality score of 0.920.

**Q: Which model has lower response latency?**  
→ `deepseek-coder` was the fastest at 5463ms average.

**Q: Which model requires fewer computational resources?**  
→ `deepseek-coder` used least memory (46.6 MB) and `starcoder2` used fewest tokens (31 avg).

**Q: Is the most accurate model also the most efficient?**  
→ No. The most accurate model (`codellama`) is NOT the fastest. This demonstrates a quality–latency trade-off between accuracy and speed.


---

## 7. Trade-off Analysis

> The goal is not simply to identify the 'best' model, but to understand the trade-offs between quality, latency, and resource usage.

### codellama

- **Correctness:** 0.600 | **Hallucination:** 8.0% | **Latency:** 11055ms | **Memory:** 103.6MB
- **Suitable for:** Production deployments where answer accuracy is the top priority and latency of ~11 seconds is acceptable. Best choice for customer support where a wrong answer is more costly than a slow one. Achieved 11 fully correct answers (vs 8 for deepseek-coder and 0 for starcoder2).

### starcoder2

- **Correctness:** 0.020 | **Hallucination:** 12.0% | **Latency:** 5895ms | **Memory:** 64.4MB
- **Suitable for:** NOT recommended for this use case. Despite being 2x faster than codellama and using the least tokens (31 avg), it answered correctly on only 0 of 25 questions. It is tuned for code generation, not natural language Q&A, making it a poor fit for a customer support bot.

### deepseek-coder

- **Correctness:** 0.480 | **Hallucination:** 8.0% | **Latency:** 5463ms | **Memory:** 46.6MB
- **Suitable for:** Latency-sensitive deployments where speed matters more than peak accuracy. Ties with codellama on hallucination rate (8%) but is 2x faster (5463ms vs 11055ms) and uses 55% less memory. A good balance model for real-time chat scenarios where ~0.5 correctness is acceptable.


---

## 8. Conclusion

**Code Llama** achieved the highest accuracy (0.600 correctness, 8.0% hallucination rate, 11 fully correct answers)
but required the longest latency at 11,055ms average and 103.6MB memory. It is the clear winner on **quality**.

**DeepSeek-Coder** provided the best **speed-quality balance**: correctness of 0.480, same 8.0% hallucination rate as
Code Llama, but 2x faster (5,463ms) and using 55% less memory (46.6MB). For real-time customer support chat,
this is the recommended trade-off model.

**StarCoder2** is unsuitable for this task despite being fast and token-efficient. With only 0/25 correct answers
and a 12% hallucination rate, it demonstrates that a model specialised for code generation does not transfer
well to natural language Q&A over structured business documents.

**Key Insight — Quality-Latency Trade-off:**
The most accurate model (Code Llama) is NOT the fastest. Choosing between accuracy and speed depends on use case:
- Customer support (tolerates delays): Code Llama (0.600 accuracy)
- Live chat / real-time (speed critical): DeepSeek-Coder (0.480 accuracy, 2x faster)
- Low-resource VM / edge devices: TinyLlama (used in this project's Docker deployment, ~600MB RAM)

**Retrieval Quality was identical (0.920) across all 3 models**, confirming that the RAG pipeline
(ChromaDB + sentence-transformers) is robust and model-independent. The difference in final answer quality
comes entirely from how well each LLM *reasons over* the retrieved context, not from retrieval failures.