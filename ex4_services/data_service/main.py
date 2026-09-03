"""
main.py — Data Service
Exercise 4: Serves raw knowledge base data via REST API
Port: 8003
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json, os
from pathlib import Path

app = FastAPI(title="ShopBot Data Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

KB_DIR = Path(os.getenv("KB_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base")))


def load_products():
    with open(KB_DIR / "products.json", "r") as f:
        return json.load(f)

def load_policies():
    with open(KB_DIR / "policies.md", "r") as f:
        return f.read()

def load_faqs():
    with open(KB_DIR / "faqs.md", "r") as f:
        return f.read()

def load_shipping():
    with open(KB_DIR / "shipping_zones.json", "r") as f:
        return json.load(f)


@app.get("/health")
def health():
    return {"service": "data-service", "status": "ok", "port": 8003}

@app.get("/products")
def get_all_products():
    return {"products": load_products(), "count": len(load_products())}

@app.get("/products/{product_id}")
def get_product(product_id: str):
    products = load_products()
    for p in products:
        if p["id"].upper() == product_id.upper():
            return p
    raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

@app.get("/products/search/{query}")
def search_products(query: str):
    products = load_products()
    query_lower = query.lower()
    matches = [p for p in products if
               query_lower in p["name"].lower() or
               query_lower in p["category"].lower() or
               query_lower in p["specs"].lower()]
    return {"results": matches, "count": len(matches)}

@app.get("/policies")
def get_policies():
    return {"content": load_policies(), "format": "markdown"}

@app.get("/faqs")
def get_faqs():
    return {"content": load_faqs(), "format": "markdown"}

@app.get("/shipping")
def get_shipping():
    return load_shipping()

@app.get("/categories")
def get_categories():
    products = load_products()
    cats = list(set(p["category"] for p in products))
    return {"categories": sorted(cats)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
