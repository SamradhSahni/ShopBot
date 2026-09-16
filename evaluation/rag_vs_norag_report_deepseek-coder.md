# ShopBot RAG vs No-RAG Evaluation Report

> **Model:** `deepseek-coder` | **Questions:** 25 | **Top-K:** 3 | **Date:** 2026-09-16T22:00:33

---

## Summary Comparison

| Metric | RAG | No-RAG | Delta | Winner |
|---|---|---|---|---|
| Avg Correctness | 0.440 | 0.040 | +0.400 | RAG |
| Avg Relevance | 0.684 | 0.445 | +0.240 | RAG |
| Hallucination Rate | 8.0% | 0.0% | -0.080 | No-RAG |
| Correct Answers | 7/25 | 0/25 | +7 | RAG |
| Avg Latency | 4584ms | 2616ms | +1968ms | No-RAG |
| Avg Tokens | 66 | 78 | -12 | — |

---

## Per-Question Results

| ID | Question | RAG | No-RAG | RAG Hallu | NoRAG Hallu |
|---|---|---|---|---|---|
| Q01 | What are the specifications of the Del… | Full | Partial | No | No |
| Q02 | How much does the Sony WH-1000XM5 head… | Miss | Miss | No | No |
| Q03 | Which laptops are currently in stock a… | Miss | Miss | No | No |
| Q04 | What is the warranty on the Samsung 65… | Partial | Miss | No | No |
| Q05 | What is the customer rating of the Son… | Miss | Miss | No | No |
| Q06 | Can I return a laptop I have already o… | Miss | Miss | No | No |
| Q07 | How many days do I have to return a pr… | Partial | Miss | No | No |
| Q08 | Are digital downloads and software lic… | Full | Miss | No | No |
| Q09 | How long does it take to receive a ref… | Full | Miss | No | No |
| Q10 | What condition must a product be in fo… | Full | Miss | No | No |
| Q11 | How much does express shipping cost? | Full | Miss | No | No |
| Q12 | What is the minimum order value for fr… | Miss | Miss | No | No |
| Q13 | How long does standard shipping take? | Miss | Miss | No | No |
| Q14 | Does TechMart ship internationally? | Partial | Miss | No | No |
| Q15 | What is the fastest shipping option an… | Partial | Miss | No | No |
| Q16 | What is the total cost of buying the D… | Full | Miss | No | No |
| Q17 | If I order the Sony WH-1000XM5 headpho… | Miss | Miss | No | No |
| Q18 | Can I return the Samsung TV if I opene… | Partial | Miss | No | No |
| Q19 | What payment methods are accepted for … | Full | Miss | No | No |
| Q20 | Which product has the best value consi… | Miss | Miss | No | No |
| Q21 | What is the price of the iPhone 15 Pro… | Miss | Miss | No | No |
| Q22 | Do you offer same-day delivery? | Partial | Miss | Yes | No |
| Q23 | What is TechMart's data privacy policy… | Partial | Partial | No | No |
| Q24 | Can I get a bulk discount if I buy 5 l… | Miss | Miss | Yes | No |
| Q25 | What happened to my order number 12345… | Partial | Miss | No | No |

---

## Detailed Responses

### Q01: What are the specifications of the Dell XPS 15 laptop?
**Ground Truth:** Intel Core i7-13700H, 16GB DDR5 RAM, 512GB NVMe SSD, NVIDIA RTX 4060 8GB, 15.6 inch OLED 3.5K display

**RAG** (C:1.0 R:0.9 H:No 49271ms 3chunks)
> The Dell XPS 15 Laptop has the following specifications:

- Processor: Intel Core i7-13700H
- RAM: 16GB DDR5 RAM
- Storage: 512GB NVMe SSD
- GPU: NVIDIA RTX 4060 8GB
- Display: 15.6" OLED 3.5K display
- Warranty: 2 years manufacturer warranty with on-site support
- Availability: In Stock
- Customer Rating: 4.7/5

The Dell XPS 15 Laptop is a high-end laptop with a sleek design and powerful performance. It has a 13-inch OLED 3.5K display, 16GB of RAM, and NVIDIA RTX 4060 8GB GPU. It also comes with a 2-year warranty and is in stock.

**No-RAG** (C:0.5 R:0.9 H:No 3449ms)
> I'm sorry, but as an AI developed by TechMart, I don't have real-time access to specific product specifications or reviews. I can only provide information based on the data I was trained on. 

However, I can tell you that Dell XPS 15 is a mid-range laptop that is known for its performance and features. It has a 15.6" touchscreen display, a 15.6-inch touchscreen with a resolution of 3840x2160 pixels. It has a Core i5 processor, 8GB of RAM, and a 512GB SSD. It also has Windows 10 Home edition.

For more accurate specifications, I recommend checking Dell's official website or contacting their cus

---

### Q02: How much does the Sony WH-1000XM5 headphones cost?
**Ground Truth:** $349.99 USD

**RAG** (C:0.0 R:0.8 H:No 2838ms 3chunks)
> I'm sorry, but as an AI, I don't have access to real-time data or the ability to fetch product information from a file or database. Therefore, I can't provide the cost of the Sony WH-1000XM5 headphones. I recommend checking the product on Amazon or another shopping platform for the most accurate price.

**No-RAG** (C:0.0 R:0.2 H:No 2623ms)
> I'm sorry for any confusion, but as an AI, I don't have real-time access to current product prices or inventory data. I'm designed to provide information and answer questions based on pre-existing knowledge and data. I recommend checking the latest prices on the Sony's official website or in the app store.

---

### Q03: Which laptops are currently in stock at TechMart?
**Ground Truth:** Dell XPS 15, Apple MacBook Pro 14 inch, and Lenovo ThinkPad E15 are all in stock

**RAG** (C:0.0 R:0.48 H:No 2761ms 3chunks)
> I'm sorry, but as an AI, I don't have real-time access to external databases or the ability to browse the internet. Therefore, I can't provide the current inventory of laptops at TechMart. I recommend checking TechMart's official website or contacting their customer service for the most accurate and up-to-date information.

**No-RAG** (C:0.0 R:0.48 H:No 2774ms)
> I'm sorry for any confusion, but as an AI, I don't have real-time access to databases or the ability to browse the internet in real-time. I can only provide information based on the data I was trained on. I can't provide current stock information or any other real-time data. I recommend checking TechMart's official website or contacting them directly for the most accurate and up-to-date information.

---

### Q04: What is the warranty on the Samsung 65 inch QLED TV?
**Ground Truth:** 1 year manufacturer warranty

**RAG** (C:0.5 R:0.72 H:No 2777ms 3chunks)
> I'm sorry, but as an AI, I don't have access to real-time data or the ability to browse the internet. Therefore, I can't provide the warranty details for the Samsung 65" QLED 4K TV. I recommend contacting TechMart directly or visiting their website to get the most accurate and up-to-date information.

**No-RAG** (C:0.0 R:0.48 H:No 2484ms)
> I'm sorry, but as an AI, I don't have the ability to provide real-time information or updates about specific products such as Samsung's QLED TV. I recommend checking the latest product reviews or contacting Samsung directly for the most accurate information.

---

### Q05: What is the customer rating of the Sony WH-1000XM5 headphones?
**Ground Truth:** 4.9 out of 5

**RAG** (C:0.0 R:1.0 H:No 2741ms 3chunks)
> I'm sorry, but as an AI, I don't have real-time access to customer reviews or ratings. However, based on the information provided in the products.json file, the customer rating of the Sony WH-1000XM5 headphones is 4.9/5.

**No-RAG** (C:0.0 R:0.2 H:No 2800ms)
> I'm sorry for any misunderstanding, but as an AI, I don't have access to real-time databases or the ability to browse the internet in real-time to provide current product ratings. My main function is to provide information and answer questions to the best of my knowledge and abilities. I recommend checking the latest reviews or ratings on trusted online platforms like Amazon or the product's official website.

---

### Q06: Can I return a laptop I have already opened?
**Ground Truth:** Yes, if returned within 30 days and in resalable condition with all original accessories

**RAG** (C:0.0 R:0.48 H:No 3029ms 3chunks)
> I'm sorry, but as an AI, I don't have the ability to return items to the store. I can only provide assistance based on the information provided in the FAQs and policies. 

For returning items, you should contact the store directly or use the online return feature available in the store. Please note that the return process can vary depending on the store's policies and the specific product.

**No-RAG** (C:0.0 R:0.72 H:No 2493ms)
> I'm sorry for any confusion, but as an AI, I don't have the ability to return a laptop. I'm designed to provide assistance with technical questions and problems. I recommend contacting TechMart's customer service or directly contacting the laptop manufacturer for assistance.

---

### Q07: How many days do I have to return a product?
**Ground Truth:** 30 days from the delivery date

**RAG** (C:0.5 R:0.72 H:No 2828ms 3chunks)
> As an AI, I don't have physical access to the store or the ability to return items. However, based on the information provided in the store policies and FAQs, you can return an item within 30 days if it's in a resizable condition and if it was not defective. If the item is defective or damaged, you should contact us within 7 days of delivery.

**No-RAG** (C:0.0 R:0.96 H:No 2751ms)
> I'm sorry, but as an AI, I don't have access to personal data about individuals unless it has been shared with me in the course of our conversation. I am designed to respect user privacy and confidentiality. Therefore, I can't provide the number of days you have to return a product. My primary function is to provide information and answer questions to the best of my knowledge and abilities. If you have any questions about ShopBot or any other topic, feel free to ask!

---

### Q08: Are digital downloads and software licenses refundable?
**Ground Truth:** No, opened software licenses and digital download codes are non-refundable

**RAG** (C:1.0 R:1.0 H:No 2629ms 3chunks)
> Yes, digital downloads and software licenses are refundable. However, it's important to note that the return policy can vary depending on the product and the store. For the most accurate information, please refer to the store's policies or contact their customer service.

**No-RAG** (C:0.0 R:0.0 H:No 2617ms)
> I'm sorry, but as an AI, I don't have access to real-time databases or the ability to provide current information about specific products or services. I'm designed to provide information based on pre-existing knowledge and data. I recommend checking the latest terms and conditions of the product you're referring to for the most accurate information.

---

### Q09: How long does it take to receive a refund after returning a product?
**Ground Truth:** Refunds are processed within 5 to 7 business days after receiving the return, with an additional 3 to 5 business days for credit card refunds

**RAG** (C:1.0 R:0.45 H:No 2468ms 3chunks)
> Refunds are processed within 5–7 business days after we receive the returned item. Credit card refunds appear within an additional 3–5 business days depending on your bank.

**No-RAG** (C:0.0 R:0.0 H:No 2609ms)
> I'm sorry, but as an AI, I don't have access to personal data about individuals unless it has been shared with me in the course of our conversation. I am designed to respect user privacy and confidentiality. Therefore, I can't provide the information you're looking for.

---

### Q10: What condition must a product be in for a return to be accepted?
**Ground Truth:** Original unused condition with all accessories, manuals, and original packaging included

**RAG** (C:1.0 R:0.4 H:No 2432ms 3chunks)
> Yes, as long as the product is in its original, unused condition and in its original packaging with all accessories, manuals, and documentation included.

**No-RAG** (C:0.0 R:0.0 H:No 0ms)
> ERROR:HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=300)

---

### Q11: How much does express shipping cost?
**Ground Truth:** $9.99 USD for 2 to 3 business day delivery

**RAG** (C:1.0 R:0.72 H:No 2451ms 3chunks)
> Express Shipping: Delivery in 2-3 business days. Cost: $9.99 USD.

**No-RAG** (C:0.0 R:0.48 H:No 2604ms)
> I'm sorry for any confusion, but as an AI, I don't have access to real-time databases or the ability to provide current shipping costs or rates. I'm designed to provide information and answer questions based on pre-existing knowledge. I recommend checking the latest shipping rates on a shipping calculator or a shipping company's website.

---

### Q12: What is the minimum order value for free shipping?
**Ground Truth:** $50 USD. Orders over $50 receive free standard shipping

**RAG** (C:0.0 R:1.0 H:No 2752ms 3chunks)
> I'm sorry, but as an AI, I don't have access to specific store information or shipping zones. I can only provide information based on the information provided in the context. However, I can tell you that the minimum order value for free shipping is usually $10.

**No-RAG** (C:0.0 R:0.8 H:No 2701ms)
> I'm sorry, but as an AI, I don't have access to real-time data or the ability to provide current shipping rates or minimum order values. I'm designed to assist with technical and programming-related questions. I recommend checking with the shipping company or the website of the product you're interested in to get the most accurate information.

---

### Q13: How long does standard shipping take?
**Ground Truth:** 5 to 7 business days

**RAG** (C:0.0 R:0.24 H:No 2845ms 3chunks)
> I'm sorry, but as an AI, I don't have access to the data you've provided. I can't provide you with a specific answer based on the shipping zones and policies you've mentioned. However, I can suggest you to refer to the shipping zones and policies in the JSON file you provided. They should give you a clear understanding of the shipping options and costs.

**No-RAG** (C:0.0 R:0.24 H:No 2742ms)
> I'm sorry, but as an AI, I don't have real-time access to current shipping rates or delivery times. I'm designed to provide information based on pre-existing knowledge and data. I recommend checking the latest shipping rates on the official website of TechMart or contact their customer service for the most accurate information.

---

### Q14: Does TechMart ship internationally?
**Ground Truth:** Yes, TechMart ships to 40+ countries worldwide including Europe, Asia Pacific, Canada, Mexico, and rest of world

**RAG** (C:0.5 R:1.0 H:No 2596ms 3chunks)
> Yes, TechMart does ship internationally. However, it's important to note that not all products are available in all countries due to regional restrictions. Some products may not be available in certain countries due to specific laws or regulations.

**No-RAG** (C:0.0 R:0.3 H:No 2894ms)
> I'm sorry, but as an AI, I don't have real-time access to current information or data about specific companies or their operations. I'm designed to provide information and answer questions based on pre-existing knowledge and data. I can't provide real-time updates or information about specific companies or their operations. I recommend checking TechMart's official website or contacting them directly for the most accurate and up-to-date information.

---

### Q15: What is the fastest shipping option and how much does it cost?
**Ground Truth:** Overnight shipping at $24.99, delivers next business day for orders placed before 12PM EST

**RAG** (C:0.5 R:0.69 H:No 2517ms 3chunks)
> The fastest shipping option in the United States is Standard Shipping. It takes about 5-7 business days to deliver and costs $4.99.

**No-RAG** (C:0.0 R:0.34 H:No 2540ms)
> I'm sorry, but as an AI, I don't have access to real-time data or the ability to provide current shipping rates or costs. I recommend checking the latest shipping rates on a shipping calculator or a shipping company's website.

---

### Q16: What is the total cost of buying the Dell XPS 15 laptop with overnight shipping?
**Ground Truth:** $1524.98 USD ($1499.99 + $24.99 overnight shipping)

**RAG** (C:1.0 R:1.0 H:No 2398ms 3chunks)
> The total cost of buying the Dell XPS 15 laptop with overnight shipping is $1499.99 USD.

**No-RAG** (C:0.0 R:0.4 H:No 2582ms)
> I'm sorry for any confusion, but as an AI, I don't have access to real-time data or the ability to calculate costs. I'm designed to provide information and answer questions based on pre-existing knowledge and data. If you have any specifics about the Dell XPS 15 laptop, I'd be happy to help calculate the cost.

---

### Q17: If I order the Sony WH-1000XM5 headphones today with express shipping, when will they arrive?
**Ground Truth:** In 2 to 3 business days, assuming order placed before 2PM EST on a business day

**RAG** (C:0.0 R:0.1 H:No 2808ms 3chunks)
> I'm sorry, but as an AI, I don't have real-time capabilities to provide shipping information. I recommend checking the shipping zones file or contacting TechMart's customer service for the most accurate and up-to-date information.

**No-RAG** (C:0.0 R:0.1 H:No 2582ms)
> I'm sorry for any confusion, but as an AI, I don't have the ability to track the delivery of products. I can only provide information based on the data I was trained on. I recommend checking the Sony's official website or contacting them directly for the most accurate information.

---

### Q18: Can I return the Samsung TV if I opened it but it arrived defective?
**Ground Truth:** Yes, defective items can be returned within 7 days of delivery regardless of opened condition, with free return shipping arranged

**RAG** (C:0.5 R:0.96 H:No 3103ms 3chunks)
> Yes, you can return the Samsung TV if it arrived defective. However, please note that the return process may vary depending on the manufacturer and the specific product. 

For the Samsung TV, you should contact TechMart support within 7 days of receiving the product. They will arrange a free return and provide a full refund or replacement at no extra cost. Photos of the damage may be required for processing.

The order system or receipt number is required for all returns.

Please note that the return process may vary depending on the manufacturer and the specific product.

**No-RAG** (C:0.0 R:0.24 H:No 2672ms)
> I'm sorry, but as an AI, I don't have the ability to physically interact with devices or systems. I can only provide information and answer questions based on the data I've been trained on. I recommend contacting the manufacturer or the customer service of the Samsung TV for assistance.

---

### Q19: What payment methods are accepted for international orders?
**Ground Truth:** Visa, Mastercard, American Express, Discover, PayPal, Apple Pay, Google Pay, TechMart Gift Cards, and Affirm

**RAG** (C:1.0 R:0.0 H:No 2579ms 3chunks)
> We accept Visa, Mastercard, American Express, Discover, PayPal, Apple Pay, Google Pay, TechMart Gift Cards, and Affirm (Buy Now Pay Later).

**No-RAG** (C:0.0 R:1.0 H:No 2705ms)
> I'm sorry, but as an AI, I don't have access to real-time databases or the ability to process payments. I can only provide information based on the data I was trained on. Therefore, I can't provide the specifics about accepted payment methods for international orders. I recommend contacting your customer service or the relevant department for this information.

---

### Q20: Which product has the best value considering price and warranty length?
**Ground Truth:** The ASUS ROG Monitor and Dell UltraSharp Monitor both offer 3 years warranty. The Dell XPS 15 offers 2 years warranty. The WD Passport SSD offers 3 years warranty at $129.99.

**RAG** (C:0.0 R:0.9 H:No 2903ms 3chunks)
> Based on the provided store information, the Apple MacBook Pro with the M3 Pro chip, 18GB unified memory, 512GB SSD, 14" Liquid Retina XDR display, 18hr battery, and 1 year Apple limited warranty would have the best value considering price and warranty length.

**No-RAG** (C:0.0 R:0.45 H:No 2684ms)
> I'm sorry, but as an AI, I don't have the ability to browse the internet or access real-time databases to provide the best value products. My main function is to provide information and answer questions to the best of my knowledge and abilities. If you have any questions about specifics, feel free to ask!

---

### Q21: What is the price of the iPhone 15 Pro at TechMart?
**Ground Truth:** The model should state it does not have this information. Apple iPhone 15 Pro is NOT listed in TechMart catalogue (only Samsung Galaxy S24 Ultra and Google Pixel 8 are listed as smartphones).

**RAG** (C:0.0 R:0.9 H:No 2857ms 3chunks)
> I'm sorry, but as an AI, I don't have real-time access to external databases or the internet to fetch current prices. Therefore, I can't provide the current price of the iPhone 15 Pro at TechMart. I recommend checking the website or contacting TechMart directly for the most accurate information.

**No-RAG** (C:0.0 R:0.6 H:No 2711ms)
> I'm sorry for any confusion, but as an AI, I don't have real-time access to current market prices or inventory data. I'm designed to provide information and answer questions based on pre-existing knowledge and data. I recommend checking TechMart's official website or contacting them directly for the most accurate and up-to-date information.

---

### Q22: Do you offer same-day delivery?
**Ground Truth:** The model should say no, TechMart does not offer same-day delivery. Fastest option is Overnight (next business day).

**RAG** (C:0.5 R:1.0 H:Yes 2529ms 3chunks)
> Yes, I do offer same-day delivery.

**No-RAG** (C:0.0 R:0.0 H:No 2781ms)
> I'm sorry for any confusion, but as an AI, I don't have the capability to provide real-time information or updates about specific products or services. I'm designed to provide assistance with information and answer questions based on pre-existing knowledge. I'm here to help with any questions you have about ShopBot, TechMart's products and services.

---

### Q23: What is TechMart's data privacy policy regarding selling customer data to advertisers?
**Ground Truth:** The model should state that customer data is never sold to third parties, based on the privacy section in policies.md

**RAG** (C:0.5 R:0.48 H:No 2811ms 3chunks)
> I'm sorry, but as an AI, I don't have access to any specific store information or policies. I can only provide information based on the data I was trained on. I can't provide a detailed answer about the privacy policy or data security practices of a specific store. I recommend reaching out to the store directly for accurate information.

**No-RAG** (C:0.5 R:0.72 H:No 3079ms)
> I'm sorry, but as an AI, I don't have access to real-time data or the ability to browse the internet in real-time. Therefore, I can't provide the current data privacy policy of TechMart. However, I can tell you that generally, data privacy is a crucial aspect of any business, and it's important to ensure that all customers' data is protected. This includes sensitive information like personal identifiers, shopping data, and more. For more detailed information, you should refer to the latest data privacy policies of your specific business.

---

### Q24: Can I get a bulk discount if I buy 5 laptops?
**Ground Truth:** The model should say it does not have information about bulk discounts in its knowledge base and suggest contacting support

**RAG** (C:0.0 R:1.0 H:Yes 2718ms 3chunks)
> Sure, you can get a bulk discount if you buy 5 laptops. However, you can only use one discount code per order. If you want to use a discount code, you should create a new order with the discount code.

**No-RAG** (C:0.0 R:1.0 H:No 2917ms)
> I'm sorry for any confusion, but as an AI, I don't have access to real-time data or the ability to process personal data unless it's shared with me in the course of our conversation. I am designed to respect user privacy and confidentiality. Therefore, I can't provide you with a bulk discount if you buy 5 laptops. I suggest you to check the specifics of the laptop you're purchasing or contact your local store directly for the best possible deal.

---

### Q25: What happened to my order number 12345? Can you check the status?
**Ground Truth:** The model should clarify it cannot access real-time order data and direct the user to My Orders in their account or customer support

**RAG** (C:0.5 R:0.17 H:No 2964ms 3chunks)
> I'm sorry, but as an AI, I don't have the ability to track orders or access customer accounts. I can only provide information based on the data I was trained on. If you have any questions about tracking an order, you should contact your customer service or the support team of the store.

**No-RAG** (C:0.0 R:0.51 H:No 2600ms)
> I'm sorry for any confusion, but as an AI, I don't have the ability to track or check the status of orders. I'm designed to provide assistance with questions related to tech support and programming. If you have any questions related to these topics, feel free to ask.

---

## Key Findings

- RAG better on 14/25 questions
- No-RAG better on 0/25 questions
- Tied on 11/25 questions
- Correctness improvement from RAG: +40.0%
- Hallucination reduction from RAG: -8.0pp