# ShopBot AI — RAG vs No-RAG Comparison Report

> **Generated:** 2026-09-02 21:36:55  
> **Model Evaluated:** `codellama`  
> **Questions Tested:** 5  

---

## Summary Takeaways
- **Grounded Truth:** With RAG, answers reference exact catalog prices, warranty durations, and policy conditions.
- **Hallucination Prevention:** Without RAG, the model produces generic or factually inaccurate answers.
- **Latency Trade-off:** RAG introduces vector retrieval overhead, but provides high factual reliability.

---

## Side-by-Side Comparison

### 1. What is the warranty on the Dell XPS 15 laptop?

| Metric | Without RAG (Base Model) | With RAG (ShopBot Knowledge Base) |
| :--- | :--- | :--- |
| **Response** | The Dell XPS 15 laptop has a one-year limited warranty on the laptop itself, which covers defects in materials and workmanship. Additionally, Dell offers a one-year extended warranty on the laptop's battery and hard drive. The warranty information can be found on the Dell website or by contacting Dell customer support. | The Dell XPS 15 laptop has a 2-year manufacturer warranty with on-site support. |
| **Latency** | `7572 ms` | `7402 ms` (Retrieval: `2384 ms`) |
| **Tokens Used** | `80` | `27` |
| **Sources** | *None* | `products.json, products.json, products.json` |
| **Top Similarity** | *N/A* | `0.79` |

<details><summary><b>View Retrieved Context Chunks</b></summary>

- **[products.json | product | score: 0.79]:** Product: Dell XPS 15 Laptop. Category: Laptops. Price: $1499.99 USD. SKU: DELL-XPS15-13700H. Specifications: Intel Core i7-13700H, 16GB DDR5 RAM, 512GB NVMe SSD, NVIDIA RTX 4060 8G...
- **[products.json | product | score: 0.692]:** Product: Dell G16 7630 - 16GB/1TB. Category: Laptops. Price: $1437.29 USD. SKU: DELL-G16-7630-16GB-1TB. Specifications: Intel Core i7-class processor, 16GB DDR5 and 1TB PCIe NVMe S...
- **[products.json | product | score: 0.69]:** Product: Dell Latitude 5450 - 16GB/512GB. Category: Laptops. Price: $893.17 USD. SKU: DELL-LATITUDE-5450-16GB-512GB. Specifications: Intel Core Ultra-class processor, 16GB DDR5 mem...
</details>

---

### 2. How much does express shipping cost?

| Metric | Without RAG (Base Model) | With RAG (ShopBot Knowledge Base) |
| :--- | :--- | :--- |
| **Response** | Express shipping is available for orders over $50. The cost of express shipping is $10.99 for domestic orders and $15.99 for international orders. Please note that these prices are subject to change and may vary depending on the shipping carrier and location. Additionally, if you have any questions about express shipping or would like to know more about our shipping options, please don't hesitate to ask. | Express shipping costs $9.99 USD. |
| **Latency** | `8388 ms` | `5574 ms` (Retrieval: `2090 ms`) |
| **Tokens Used** | `94` | `13` |
| **Sources** | *None* | `shipping_zones.json, shipping_zones.json, shipping_zones.json` |
| **Top Similarity** | *N/A* | `0.783` |

<details><summary><b>View Retrieved Context Chunks</b></summary>

- **[shipping_zones.json | shipping | score: 0.783]:** Domestic Shipping — Express Shipping: Delivery in 2-3 business days. Cost: $9.99 USD.  P.O. Box allowed: No. Cut-off time: 2:00 PM EST. Physical address required. Not available for...
- **[shipping_zones.json | shipping | score: 0.737]:** International Shipping — Rest of World: Delivery in 14-21 business days. Cost: $39.99 USD. Carrier: DHL Express. Note: Customer responsible for all import duties and taxes....
- **[shipping_zones.json | shipping | score: 0.732]:** International Shipping — Asia Pacific: Delivery in 10-18 business days. Cost: $34.99 USD. Carrier: FedEx International. Note: Customer responsible for all import duties and taxes....
</details>

---

### 3. Can I return an opened laptop within 30 days?

| Metric | Without RAG (Base Model) | With RAG (ShopBot Knowledge Base) |
| :--- | :--- | :--- |
| **Response** | Yes, you can return an opened laptop within 30 days of purchase. Please note that the return process may vary depending on the specific product and the retailer's return policy. It is best to check with the retailer's return policy and follow their instructions for returning an opened laptop within 30 days. Additionally, it is important to ensure that the laptop is in its original condition and packaged in its original packaging to facilitate a smooth return process. | Yes, you can return an opened laptop within 30 days of delivery. However, it's important to note that opened software and digital codes are not returnable. If the laptop is damaged or defective, you can contact our customer service team within 7 days of delivery to arrange a free return and receive a full refund or replacement at no extra cost. Photos of damage may be required for processing.<br><br>It's also important to check the return and refund policy to ensure that you are eligible for a return and to understand the process for initiating a return. You can find the return and refund policy on our website or by contacting our customer service team.<br><br>If you have any further questions or concerns, please don't hesitate to ask. We're here to help and want to make sure you have a positive shopping experience with us. |
| **Latency** | `8926 ms` | `17621 ms` (Retrieval: `2071 ms`) |
| **Tokens Used** | `101` | `187` |
| **Sources** | *None* | `faqs.md, policies.md, policies.md` |
| **Top Similarity** | *N/A* | `0.804` |

<details><summary><b>View Retrieved Context Chunks</b></summary>

- **[faqs.md | faq | score: 0.804]:** Question: Can I return an opened product? Answer: Yes, as long as it's within 30 days and the product is in resalable condition with all original accessories. Opened software and d...
- **[policies.md | policy | score: 0.741]:** ## Return & Refund Policy  ### Standard Return Window - Customers may return eligible items within **30 days** of the delivery date. - Items must be in their **original, unused con...
- **[policies.md | policy | score: 0.676]:** order systems cannot be returned unless defective.  ### Defective or Damaged Items - If an item arrives damaged or defective, contact us within **7 days** of delivery. - We will ar...
</details>

---

### 4. What is the price of the Sony WH-1000XM5 headphones?

| Metric | Without RAG (Base Model) | With RAG (ShopBot Knowledge Base) |
| :--- | :--- | :--- |
| **Response** | The price of the Sony WH-1000XM5 headphones is $349.99 USD. | The price of the Sony WH-1000XM5 headphones is $349.99 USD. |
| **Latency** | `5004 ms` | `6892 ms` (Retrieval: `2078 ms`) |
| **Tokens Used** | `29` | `29` |
| **Sources** | *None* | `products.json, products.json, products.json` |
| **Top Similarity** | *N/A* | `0.828` |

<details><summary><b>View Retrieved Context Chunks</b></summary>

- **[products.json | product | score: 0.828]:** Product: Sony WH-1000XM5 Headphones. Category: Audio. Price: $349.99 USD. SKU: SONY-WH1000XM5. Specifications: Industry-leading noise cancelling, 30hr battery, Bluetooth 5.2, LDAC,...
- **[products.json | product | score: 0.782]:** Product: Sony WF-1000XM5 - Black. Category: Audio. Price: $279.63 USD. SKU: SONY-WF-1000XM5-BLACK. Specifications: True wireless earbuds with active noise cancellation, Bluetooth m...
- **[products.json | product | score: 0.768]:** Product: Sony WF-1000XM5 - White. Category: Audio. Price: $291.47 USD. SKU: SONY-WF-1000XM5-WHITE. Specifications: True wireless ANC earbuds with Bluetooth multipoint, high-resolut...
</details>

---

### 5. Do you offer free shipping? What is the minimum order?

| Metric | Without RAG (Base Model) | With RAG (ShopBot Knowledge Base) |
| :--- | :--- | :--- |
| **Response** | Yes, we offer free shipping on all orders over $50. The minimum order is $50. If you have any questions about our shipping policies or would like to know more about our shipping options, please let me know. | Yes, we offer free shipping on all orders over $50 within the United States. The minimum order value is $50, but orders under $50 incur a $4.99 standard shipping fee. If you have any further questions or concerns about shipping, please don't hesitate to contact our customer support team. |
| **Latency** | `5778 ms` | `9935 ms` (Retrieval: `2122 ms`) |
| **Tokens Used** | `51` | `73` |
| **Sources** | *None* | `faqs.md, faqs.md, shipping_zones.json` |
| **Top Similarity** | *N/A* | `0.79` |

<details><summary><b>View Retrieved Context Chunks</b></summary>

- **[faqs.md | faq | score: 0.79]:** Question: Do you offer free shipping? Answer: Yes! Standard shipping is free on all orders over $50 within the United States....
- **[faqs.md | faq | score: 0.761]:** Question: Is there a minimum order value? Answer: No minimum order value. However, orders under $50 incur a $4.99 standard shipping fee....
- **[shipping_zones.json | shipping | score: 0.734]:** Domestic Shipping — Standard Shipping: Delivery in 5-7 business days. Cost: $4.99 USD. Free on orders over $50.0. P.O. Box allowed: Yes. Cut-off time: 2:00 PM EST. Free on orders o...
</details>

---
