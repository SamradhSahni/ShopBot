# ShopBot AI — RAG Pipeline Analysis Report (W4-E5)

> Model: `codellama` | Questions analysed: 10

> **Objective:** Understand how retrieval quality affects LLM response quality.

> The pipeline is: `QUESTION → EMBED → RETRIEVE → CONTEXT → LLM → RESPONSE`


## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ RELEVANT | Correct source documents retrieved |
| ⚠️ PARTIAL | Some but not all expected sources retrieved |
| 🚫 MISSED | Expected source not retrieved |
| ❌ HALLUCINATED | Model stated false/invented facts |
| 🎯 CORRECT | Response matches ground truth |
| 💬 PARTIAL | Response partially matches ground truth |
| ❓ UNCERTAIN | Model correctly admitted lack of knowledge |

---

## Traced Examples

### [A01] Perfect Retrieval → Correct Answer

**Expected outcome:** ✅ Relevant retrieved → ✅ Correct answer

**Actual outcome:** ✅ RELEVANT retrieval → 🎯 CORRECT response

**QUESTION:**
> What is the return window for products at TechMart?

**GROUND TRUTH:**
> 30 days from delivery date

**RETRIEVED CONTEXT:**

> **Chunk 1** | Source: `policies.md` | Type: `policy` | Similarity: `0.754`
> - Photos of damage may be required for processing.

### Return Process
1. Log into your TechMart account and go to "My Orders".
2. Select the order and click "Initiate Return".
3. Choose the item(s) a...

> **Chunk 2** | Source: `policies.md` | Type: `policy` | Similarity: `0.740`
> # TechMart Store Policies...

> **Chunk 3** | Source: `policies.md` | Type: `policy` | Similarity: `0.702`
> ## Return & Refund Policy

### Standard Return Window
- Customers may return eligible items within **30 days** of the delivery date.
- Items must be in their **original, unused condition** and in **or...

**LLM RESPONSE:**
> The return window for products at TechMart is 30 days from the delivery date. Items must be in their original, unused condition and in original packaging with all accessories, manuals, and documentation included. A valid proof of purchase (order number or receipt) is required for all returns.

If you have any further questions or concerns, please don't hesitate to reach out to our customer support team. They will be happy to assist you with your inquiry.

If you have any other questions or concerns, please don't hesitate to reach out to our customer support team. They will be happy to assist you with your inquiry.

In addition, if you have any other questions or concerns, please don't hesitate to reach out to our customer support team. They will be happy to assist you with your inquiry.

If you have any other questions or concerns, please don't hesitate to reach out to our customer support team. They will be happy to assist you with your inquiry.

If you have any other questions or concerns, please don't hesitate to reach out to our customer support team. They will be happy to assist you with your inquiry.

If you have any other questions or concerns, please don't hesitate to reach out to our customer support team. They will be happy to assist you with your inquiry.

If you have any other questions or concerns, please don't hesitate to reach out to our customer support team. They will be happy to assist you with your inquiry.

If you have any other questions or concerns, please don't hesitate to reach out to our customer support team. They will be happy to assist you with your inquiry.

If you have any other questions or concerns, please don't hesitate to reach out to our customer support team. They will be happy to assist you with your inquiry.

If you have any other questions or concerns, please don't hesitate to reach out to our customer support team. They will be happy to assist you with your inquiry.

If you have any other questions or concerns, please don't hesitate to reach out to our customer support team. They will be happy to assist you with your inquiry.

If you have any other questions or concerns, please don't hesitate to reach out to our customer support team. They

**ANALYSIS:**

- Retrieval: ✅ `RELEVANT` — All expected sources retrieved: ['policies.md']
- Response: 🎯 `CORRECT` — Key facts matched (4/4 tokens)
- Latency: 45990ms | Tokens: 512 | Chunks: 3

---

### [A02] Perfect Retrieval → Correct Answer

**Expected outcome:** ✅ Relevant retrieved → ✅ Correct answer

**Actual outcome:** ✅ RELEVANT retrieval → ❌ INCORRECT_OR_HALLUCINATED response

**QUESTION:**
> How much does express shipping cost?

**GROUND TRUTH:**
> $9.99 USD, 2-3 business days

**RETRIEVED CONTEXT:**

> **Chunk 1** | Source: `shipping_zones.json` | Type: `shipping` | Similarity: `0.783`
> Domestic Shipping — Express Shipping: Delivery in 2-3 business days. Cost: $9.99 USD.  P.O. Box allowed: No. Cut-off time: 2:00 PM EST. Physical address required. Not available for all products....

> **Chunk 2** | Source: `shipping_zones.json` | Type: `shipping` | Similarity: `0.737`
> International Shipping — Rest of World: Delivery in 14-21 business days. Cost: $39.99 USD. Carrier: DHL Express. Note: Customer responsible for all import duties and taxes....

> **Chunk 3** | Source: `shipping_zones.json` | Type: `shipping` | Similarity: `0.732`
> International Shipping — Asia Pacific: Delivery in 10-18 business days. Cost: $34.99 USD. Carrier: FedEx International. Note: Customer responsible for all import duties and taxes....

**LLM RESPONSE:**
> Express shipping costs $9.99 USD.

**ANALYSIS:**

- Retrieval: ✅ `RELEVANT` — All expected sources retrieved: ['shipping_zones.json']
- Response: ❌ `INCORRECT_OR_HALLUCINATED` — Low match (0/2 tokens)
- Latency: 6565ms | Tokens: 13 | Chunks: 3

---

### [A03] Irrelevant Chunk Retrieved → LLM Still Correct

**Expected outcome:** ⚠️ Mixed retrieval → ✅ LLM synthesises correctly

**Actual outcome:** ✅ RELEVANT retrieval → 🎯 CORRECT response

**QUESTION:**
> What is the total cost of the Dell XPS 15 with express shipping?

**GROUND TRUTH:**
> $1509.98 ($1499.99 + $9.99)

**RETRIEVED CONTEXT:**

> **Chunk 1** | Source: `products.json` | Type: `product` | Similarity: `0.737`
> Product: Dell XPS 15 Laptop. Category: Laptops. Price: $1499.99 USD. SKU: DELL-XPS15-13700H. Specifications: Intel Core i7-13700H, 16GB DDR5 RAM, 512GB NVMe SSD, NVIDIA RTX 4060 8GB, 15.6" OLED 3.5K d...

> **Chunk 2** | Source: `shipping_zones.json` | Type: `shipping` | Similarity: `0.693`
> Domestic Shipping — Express Shipping: Delivery in 2-3 business days. Cost: $9.99 USD.  P.O. Box allowed: No. Cut-off time: 2:00 PM EST. Physical address required. Not available for all products....

> **Chunk 3** | Source: `shipping_zones.json` | Type: `shipping` | Similarity: `0.680`
> International Shipping — Rest of World: Delivery in 14-21 business days. Cost: $39.99 USD. Carrier: DHL Express. Note: Customer responsible for all import duties and taxes....

**LLM RESPONSE:**
> The total cost of the Dell XPS 15 with express shipping is $1499.99 USD + $9.99 USD = $1509.99 USD.

**ANALYSIS:**

- Retrieval: ✅ `RELEVANT` — All expected sources retrieved: ['products.json', 'shipping_zones.json']
- Response: 🎯 `CORRECT` — Key facts matched (2/2 tokens)
- Latency: 8074ms | Tokens: 48 | Chunks: 3

---

### [A04] Good Retrieval → LLM Correct Answer

**Expected outcome:** ✅ Relevant retrieved → ✅ Correct answer

**Actual outcome:** ✅ RELEVANT retrieval → 🎯 CORRECT response

**QUESTION:**
> Can I return a defective item even after 30 days?

**GROUND TRUTH:**
> Defective items must be reported within 7 days of delivery for free return

**RETRIEVED CONTEXT:**

> **Chunk 1** | Source: `faqs.md` | Type: `faq` | Similarity: `0.777`
> Question: Can I return an opened product?
Answer: Yes, as long as it's within 30 days and the product is in resalable condition with all original accessories. Opened software and digital codes are not...

> **Chunk 2** | Source: `policies.md` | Type: `policy` | Similarity: `0.773`
> ## Return & Refund Policy

### Standard Return Window
- Customers may return eligible items within **30 days** of the delivery date.
- Items must be in their **original, unused condition** and in **or...

> **Chunk 3** | Source: `policies.md` | Type: `policy` | Similarity: `0.762`
> order systems cannot be returned unless defective.

### Defective or Damaged Items
- If an item arrives damaged or defective, contact us within **7 days** of delivery.
- We will arrange a free return ...

**LLM RESPONSE:**
> Hi there! I'm happy to help you with your question.

According to the return and refund policy, items that arrive damaged or defective within 7 days of delivery can be returned for a full refund or replacement at no extra cost. However, if the item arrives after 30 days, it may not be eligible for a return.

It's important to note that the return window for defective or damaged items is 7 days, not 30 days. If you have any questions or concerns about the return process, I would recommend contacting TechMart support for further assistance.

If you have any other questions or concerns, feel free to ask!

**ANALYSIS:**

- Retrieval: ✅ `RELEVANT` — All expected sources retrieved: ['policies.md']
- Response: 🎯 `CORRECT` — Key facts matched (7/9 tokens)
- Latency: 14033ms | Tokens: 151 | Chunks: 3

---

### [A05] No Relevant Context → LLM Should Admit Uncertainty

**Expected outcome:** 🚫 Not in KB → ✅ Model correctly uncertain OR ❌ Hallucinated

**Actual outcome:** — NOT_APPLICABLE retrieval → ❌ HALLUCINATED response

**QUESTION:**
> What is the price of the iPhone 15 Pro?

**GROUND TRUTH:**
> Not in knowledge base — model should say it doesn't have this info

**RETRIEVED CONTEXT:**

> **Chunk 1** | Source: `products.json` | Type: `product` | Similarity: `0.783`
> Product: Apple iPhone 15 Pro. Category: Smartphones. Price: $999.99 USD. SKU: APPLE-IP15PRO-256. Specifications: A17 Pro chip, 8GB RAM, 256GB storage, 48MP ProRAW camera, 6.1" Super Retina XDR ProMoti...

> **Chunk 2** | Source: `products.json` | Type: `product` | Similarity: `0.771`
> Product: Apple iPhone 15 Pro Max - 512GB/12GB. Category: Smartphones. Price: $1397.74 USD. SKU: APPLE-IPHONE-15-PRO-MAX-512GB-12GB. Specifications: Apple A17 Pro with 512GB-class NVMe storage; 6.7-inc...

> **Chunk 3** | Source: `products.json` | Type: `product` | Similarity: `0.767`
> Product: Apple iPhone 15 Pro Max - 128GB/8GB. Category: Smartphones. Price: $1179.82 USD. SKU: APPLE-IPHONE-15-PRO-MAX-128GB-8GB. Specifications: Apple A17 Pro with fast NVMe storage; 6.7-inch ProMoti...

**LLM RESPONSE:**
> The price of the iPhone 15 Pro is $999.99 USD.

**ANALYSIS:**

- Retrieval: — `NOT_APPLICABLE` — Expected source not in knowledge base
- Response: ❌ `HALLUCINATED` — Model gave a specific answer despite having no KB context
- Latency: 6587ms | Tokens: 21 | Chunks: 3

---

### [A06] Partial Retrieval → Partial Answer

**Expected outcome:** ⚠️ Partial retrieval → ⚠️ Partial answer (depends on which products retrieved)

**Actual outcome:** 🚫 MISSED retrieval → 💬 PARTIAL response

**QUESTION:**
> Which product has the longest warranty at TechMart?

**GROUND TRUTH:**
> ASUS ROG Monitor, Dell UltraSharp, WD Passport SSD all have 3-year warranty

**RETRIEVED CONTEXT:**

> **Chunk 1** | Source: `policies.md` | Type: `policy` | Similarity: `0.790`
> ## Warranty Policy

### Manufacturer Warranty
- All TechMart products are covered by the **manufacturer's warranty** as specified on each product page.
- Warranty periods vary by product (see product ...

> **Chunk 2** | Source: `faqs.md` | Type: `faq` | Similarity: `0.773`
> Question: Does TechMart offer its own extended warranty?
Answer: Yes, TechMart Care extended warranty plans are available at checkout. They extend coverage by 1–2 additional years and may include acci...

> **Chunk 3** | Source: `policies.md` | Type: `policy` | Similarity: `0.742`
> sical damage, water damage, or damage from misuse.

### Extended Warranty (TechMart Care)
- Extended warranty plans are available at checkout for most electronics.
- Plans extend coverage by 1 or 2 ad...

**LLM RESPONSE:**
> The longest warranty at TechMart is 3 years for most electronics. This is specified on each product page and is covered under the manufacturer's warranty. Additionally, TechMart Care extended warranty plans are available at checkout and extend coverage by 1 or 2 additional years beyond the manufacturer warranty, and may include accidental damage protection.

If you have any further questions or concerns, please don't hesitate to contact TechMart support.

**ANALYSIS:**

- Retrieval: 🚫 `MISSED` — None of expected sources (['products.json']) in retrieved: ['policies.md', 'faqs.md', 'policies.md']
- Response: 💬 `PARTIAL` — Partially correct (3/8 tokens matched)
- Latency: 11429ms | Tokens: 105 | Chunks: 3

---

### [A07] Good Context → LLM Hallucinates Despite Context

**Expected outcome:** ✅ Relevant retrieved → ❌ Possible hallucination check

**Actual outcome:** ✅ RELEVANT retrieval → ❌ INCORRECT_OR_HALLUCINATED response

**QUESTION:**
> Do you offer same-day delivery?

**GROUND TRUTH:**
> No, fastest is Overnight (next business day, $24.99)

**RETRIEVED CONTEXT:**

> **Chunk 1** | Source: `policies.md` | Type: `policy` | Similarity: `0.676`
> Overnight Shipping | Next business day | $24.99 |

- Orders placed before **2:00 PM EST** on business days ship same day.
- Orders placed after 2:00 PM or on weekends ship the next business day.
- Fre...

> **Chunk 2** | Source: `shipping_zones.json` | Type: `shipping` | Similarity: `0.640`
> Domestic Shipping — Overnight Shipping: Delivery in 1 business day. Cost: $24.99 USD.  P.O. Box allowed: No. Cut-off time: 12:00 PM EST. Must order before 12PM EST. Not available on Fridays for Saturd...

> **Chunk 3** | Source: `faqs.md` | Type: `faq` | Similarity: `0.624`
> Question: Can I use multiple discount codes on one order?
Answer: Only one discount code can be applied per order. Gift cards can be combined with a discount code.

---

## Shipping & Delivery...

**LLM RESPONSE:**
> Yes, we do offer same-day delivery for orders placed before 2:00 PM EST on business days. However, please note that this service is subject to availability and may not be available on weekends or holidays. Additionally, free standard shipping is automatically applied when the cart total exceeds $50. If you have any questions about our shipping policies or would like to request a quote for a specific order, please feel free to ask.

**ANALYSIS:**

- Retrieval: ✅ `RELEVANT` — All expected sources retrieved: ['shipping_zones.json']
- Response: ❌ `INCORRECT_OR_HALLUCINATED` — Low match (1/4 tokens)
- Latency: 11296ms | Tokens: 98 | Chunks: 3

---

### [A08] Multi-source Retrieval → Complex Correct Answer

**Expected outcome:** ✅ Relevant retrieved → ✅ Correct multi-fact answer

**Actual outcome:** ✅ RELEVANT retrieval → 🎯 CORRECT response

**QUESTION:**
> What payment methods are accepted and is there a financing option?

**GROUND TRUTH:**
> Visa, Mastercard, Amex, PayPal, Apple/Google Pay, Gift Cards, Affirm (0% APR 6 months on $200+)

**RETRIEVED CONTEXT:**

> **Chunk 1** | Source: `faqs.md` | Type: `faq` | Similarity: `0.737`
> Question: What payment methods do you accept?
Answer: We accept Visa, Mastercard, American Express, Discover, PayPal, Apple Pay, Google Pay, TechMart Gift Cards, and Affirm (Buy Now Pay Later)....

> **Chunk 2** | Source: `policies.md` | Type: `policy` | Similarity: `0.683`
> ## Payment Policy

### Accepted Payment Methods
- Visa, Mastercard, American Express, Discover
- PayPal and PayPal Credit
- Apple Pay and Google Pay
- TechMart Gift Cards and Store Credit
- Affirm (Bu...

> **Chunk 3** | Source: `faqs.md` | Type: `faq` | Similarity: `0.616`
> Question: Do you offer financing or instalment payments?
Answer: Yes, through Affirm. Eligible customers can get 0% APR for 6 months on orders over $200. Available at checkout....

**LLM RESPONSE:**
> We accept Visa, Mastercard, American Express, Discover, PayPal, Apple Pay, Google Pay, TechMart Gift Cards, and Affirm (Buy Now Pay Later). Yes, through Affirm, eligible customers can get 0% APR for 6 months on orders over $200. Available at checkout.

**ANALYSIS:**

- Retrieval: ✅ `RELEVANT` — All expected sources retrieved: ['policies.md']
- Response: 🎯 `CORRECT` — Key facts matched (9/10 tokens)
- Latency: 10056ms | Tokens: 76 | Chunks: 3

---

### [A09] Retrieval Miss → Missing Important Info

**Expected outcome:** ⚠️ Context may include/miss PO Box detail → varies

**Actual outcome:** ✅ RELEVANT retrieval → 💬 PARTIAL response

**QUESTION:**
> Can I ship to a P.O. Box with express shipping?

**GROUND TRUTH:**
> No, P.O. Boxes only allowed for standard shipping, not express or overnight

**RETRIEVED CONTEXT:**

> **Chunk 1** | Source: `faqs.md` | Type: `faq` | Similarity: `0.829`
> Question: Can I ship to a P.O. Box?
Answer: Standard shipping can deliver to P.O. Boxes. Express and Overnight shipping require a physical address....

> **Chunk 2** | Source: `shipping_zones.json` | Type: `shipping` | Similarity: `0.714`
> Domestic Shipping — Express Shipping: Delivery in 2-3 business days. Cost: $9.99 USD.  P.O. Box allowed: No. Cut-off time: 2:00 PM EST. Physical address required. Not available for all products....

> **Chunk 3** | Source: `shipping_zones.json` | Type: `shipping` | Similarity: `0.615`
> Shipping restrictions: Signature required on orders over $500. Domestic carriers: UPS, FedEx, USPS. Order tracking is available for All orders via email and SMS notification....

**LLM RESPONSE:**
> Hi there! I'm happy to help you with your question about shipping to a P.O. Box with express shipping.

According to the store information provided, standard shipping can deliver to P.O. Boxes. However, express shipping requires a physical address. Therefore, it is not possible to ship to a P.O. Box with express shipping.

If you have any other questions or concerns about shipping, I'd be happy to help. Additionally, if you have any issues with your order, please don't hesitate to contact our support team. They'll be able to assist you with any questions or concerns you may have.

Thank you for reaching out to us!

**ANALYSIS:**

- Retrieval: ✅ `RELEVANT` — All expected sources retrieved: ['shipping_zones.json']
- Response: 💬 `PARTIAL` — Partially correct (4/7 tokens matched)
- Latency: 14411ms | Tokens: 154 | Chunks: 3

---

### [A10] Live Data Required → Model Should Defer

**Expected outcome:** 🚫 Requires live data → ✅ Model correctly defers OR ❌ Hallucinated status

**Actual outcome:** — NOT_APPLICABLE retrieval → ❓ CORRECTLY_UNCERTAIN response

**QUESTION:**
> What is the current status of my order number 98765?

**GROUND TRUTH:**
> Cannot access live order data — should direct to My Orders or support

**RETRIEVED CONTEXT:**

> **Chunk 1** | Source: `policies.md` | Type: `policy` | Similarity: `0.655`
> pped internationally due to regional restrictions.

### Order Tracking
- A tracking number is emailed as soon as your order ships.
- Track your order at any time via "My Orders" in your account or dir...

> **Chunk 2** | Source: `faqs.md` | Type: `faq` | Similarity: `0.643`
> Question: How do I track my order?
Answer: Once your order ships, you'll receive a tracking number via email. You can also log into your account and go to "My Orders" to see real-time tracking....

> **Chunk 3** | Source: `faqs.md` | Type: `faq` | Similarity: `0.608`
> Question: How do I know if a product is in stock?
Answer: Product availability is shown on each product page. "In Stock" means ready to ship, "Low Stock" means limited units available, and "Out of Sto...

**LLM RESPONSE:**
> Hello! I'm happy to help you with your question about your order number 98765.

To check the status of your order, you can log into your account and go to "My Orders." If you don't have an account, you can also contact our customer support team and provide your order number to check the status.

If you have any further questions or concerns about your order, please don't hesitate to ask. We're here to help and want to make sure you have a positive shopping experience with us.

In the meantime, if you're looking for a way to track your order, you can also check the tracking number that was emailed to you as soon as your order shipped. You can also log into your account and go to "My Orders" to see real-time tracking updates for all domestic orders.

If you have any questions about product availability, you can also check the availability of the product on the product page. "In Stock" means the product is ready to ship, "Low Stock" means there are limited units available, and "Out of Stock" means the product is currently unavailable.

I hope this information helps you with your question. If you have any further questions, please don't hesitate to ask.

**ANALYSIS:**

- Retrieval: — `NOT_APPLICABLE` — Expected source not in knowledge base
- Response: ❓ `CORRECTLY_UNCERTAIN` — Model correctly admitted lack of information
- Latency: 22751ms | Tokens: 281 | Chunks: 3

---

## Summary Table

| ID | Case | Retrieval | Response |
|----|------|-----------|----------|
| A01 | Perfect Retrieval → Correct Answer | ✅ RELEVANT | 🎯 CORRECT |
| A02 | Perfect Retrieval → Correct Answer | ✅ RELEVANT | ❌ INCORRECT_OR_HALLUCINATED |
| A03 | Irrelevant Chunk Retrieved → LLM Still C | ✅ RELEVANT | 🎯 CORRECT |
| A04 | Good Retrieval → LLM Correct Answer | ✅ RELEVANT | 🎯 CORRECT |
| A05 | No Relevant Context → LLM Should Admit U | — NOT_APPLICABLE | ❌ HALLUCINATED |
| A06 | Partial Retrieval → Partial Answer | 🚫 MISSED | 💬 PARTIAL |
| A07 | Good Context → LLM Hallucinates Despite  | ✅ RELEVANT | ❌ INCORRECT_OR_HALLUCINATED |
| A08 | Multi-source Retrieval → Complex Correct | ✅ RELEVANT | 🎯 CORRECT |
| A09 | Retrieval Miss → Missing Important Info | ✅ RELEVANT | 💬 PARTIAL |
| A10 | Live Data Required → Model Should Defer | — NOT_APPLICABLE | ❓ CORRECTLY_UNCERTAIN |

---

## Key Insights

- **Retrieval Accuracy:** 7/10 questions retrieved relevant context
- **Response Accuracy:** 4/10 responses matched ground truth
- **Hallucinations:** 3/10 responses contained false information

**Relationship: RETRIEVAL QUALITY → CONTEXT QUALITY → RESPONSE QUALITY**

> When retrieval is accurate (RELEVANT), LLM responses tend to be correct.
> When retrieval misses the right document, the LLM either hallucinates or gives a generic answer.
> Even with good retrieval, LLMs can misinterpret context — RAG is not a guarantee of correctness.
> For questions outside the knowledge base, the LLM must clearly admit uncertainty — failure to do so is a hallucination.
