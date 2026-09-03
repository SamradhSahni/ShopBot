"""
chunker.py — Document chunking strategies for ShopBot knowledge base
Exercise 2: Converts raw documents into chunks suitable for embedding
"""

import sys, io
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
import re
from pathlib import Path
from typing import List, Dict


def chunk_products(products_path: str) -> List[Dict]:
    """Each product becomes one self-contained chunk."""
    with open(products_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    chunks = []
    for p in products:
        text = (
            f"Product: {p['name']}. "
            f"Category: {p['category']}. "
            f"Price: ${p['price']} USD. "
            f"SKU: {p['sku']}. "
            f"Specifications: {p['specs']}. "
            f"Warranty: {p['warranty']}. "
            f"Availability: {p['stock']}. "
            f"Customer Rating: {p['rating']}/5."
        )
        chunks.append({
            "id": f"product_{p['id']}",
            "text": text,
            "metadata": {
                "source": "products.json",
                "type": "product",
                "product_id": p["id"],
                "product_name": p["name"],
                "category": p["category"],
                "price": p["price"],
            }
        })
    return chunks


def chunk_markdown(filepath: str, source_name: str, chunk_size: int = 400, overlap: int = 50) -> List[Dict]:
    """
    Split markdown into overlapping paragraph-level chunks.
    Preserves section headers for context.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Split into sections by ## headers
    sections = re.split(r"\n(?=## )", text)
    chunks = []
    chunk_index = 0

    for section in sections:
        if not section.strip():
            continue

        # Extract section header
        header_match = re.match(r"^(#+\s+.+)\n", section)
        header = header_match.group(1).strip() if header_match else ""

        # Split section into paragraphs
        paragraphs = [p.strip() for p in re.split(r"\n\n+", section) if p.strip()]

        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunks.append({
                        "id": f"{source_name}_chunk_{chunk_index}",
                        "text": current_chunk.strip(),
                        "metadata": {
                            "source": source_name,
                            "type": "policy" if "polic" in source_name else "faq",
                            "section": header,
                        }
                    })
                    chunk_index += 1
                # Start new chunk with overlap
                current_chunk = current_chunk[-overlap:] + "\n\n" + para if current_chunk else para

        if current_chunk.strip():
            chunks.append({
                "id": f"{source_name}_chunk_{chunk_index}",
                "text": current_chunk.strip(),
                "metadata": {
                    "source": source_name,
                    "type": "policy" if "polic" in source_name else "faq",
                    "section": header,
                }
            })
            chunk_index += 1

    return chunks


def chunk_faq(filepath: str) -> List[Dict]:
    """Each Q&A pair becomes one atomic chunk."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = []
    # Match Q: ... A: ... pattern
    pairs = re.findall(r"\*\*Q:\s*(.+?)\*\*\s*\nA:\s*(.+?)(?=\n\n\*\*Q:|\Z)", text, re.DOTALL)

    for i, (question, answer) in enumerate(pairs):
        chunk_text = f"Question: {question.strip()}\nAnswer: {answer.strip()}"
        chunks.append({
            "id": f"faq_chunk_{i}",
            "text": chunk_text,
            "metadata": {
                "source": "faqs.md",
                "type": "faq",
                "question": question.strip()[:100],
            }
        })

    return chunks


def chunk_shipping(filepath: str) -> List[Dict]:
    """Flatten shipping JSON into readable text chunks."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = []

    # Domestic options
    for method, info in data["domestic"].items():
        text = (
            f"Domestic Shipping — {info['name']}: "
            f"Delivery in {info['estimated_days']}. "
            f"Cost: ${info['cost_usd']} USD. "
            f"{'Free on orders over $' + str(info['free_threshold_usd']) + '.' if info.get('free_threshold_usd') else ''} "
            f"P.O. Box allowed: {'Yes' if info.get('po_box_allowed') else 'No'}. "
            f"Cut-off time: {info.get('cutoff_time', 'N/A')}. "
            f"{info.get('notes', '')}"
        ).strip()
        chunks.append({
            "id": f"shipping_domestic_{method}",
            "text": text,
            "metadata": {"source": "shipping_zones.json", "type": "shipping", "zone": f"domestic_{method}"}
        })

    # International options
    for region, info in data["international"].items():
        text = (
            f"International Shipping — {info['name']}: "
            f"Delivery in {info['estimated_days']}. "
            f"Cost: ${info['cost_usd']} USD. "
            f"Carrier: {info.get('carrier', 'N/A')}. "
            f"Note: {info.get('customs_note', '')}"
        ).strip()
        chunks.append({
            "id": f"shipping_intl_{region}",
            "text": text,
            "metadata": {"source": "shipping_zones.json", "type": "shipping", "zone": f"international_{region}"}
        })

    # Restrictions and tracking
    restrictions = data.get("restrictions", {})
    tracking = data.get("tracking", {})
    text = (
        f"Shipping restrictions: Signature required on orders over ${restrictions.get('signature_required_above_usd', 500)}. "
        f"Domestic carriers: {', '.join(restrictions.get('carriers_used_domestic', []))}. "
        f"Order tracking is available for {tracking.get('available_for', 'all orders')} "
        f"via email and SMS notification."
    )
    chunks.append({
        "id": "shipping_general_info",
        "text": text,
        "metadata": {"source": "shipping_zones.json", "type": "shipping", "zone": "general"}
    })

    return chunks


def load_all_chunks(kb_dir: str) -> List[Dict]:
    """Load and chunk all knowledge base documents."""
    kb = Path(kb_dir)
    all_chunks = []

    print("📦 Chunking products.json...")
    all_chunks.extend(chunk_products(str(kb / "products.json")))

    print("📄 Chunking policies.md...")
    all_chunks.extend(chunk_markdown(str(kb / "policies.md"), "policies.md"))

    print("❓ Chunking faqs.md...")
    all_chunks.extend(chunk_faq(str(kb / "faqs.md")))

    print("🚚 Chunking shipping_zones.json...")
    all_chunks.extend(chunk_shipping(str(kb / "shipping_zones.json")))

    print(f"✅ Total chunks created: {len(all_chunks)}")
    return all_chunks
