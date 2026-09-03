"""
fix_products_json.py - Fix the merged products.json with two arrays joined as ][
Also fixes unescaped double-quotes inside string values (e.g. 55" TV names)
"""
import json, re

filepath = r'e:\projects\AIDevops\shopbot\knowledge_base\products.json'

with open(filepath, 'r', encoding='utf-8') as f:
    raw = f.read()

print(f"File size: {len(raw)} bytes")

# Step 1: Merge the two arrays - replace ][ with a comma
fixed = re.sub(r'\]\s*\n?\s*\[', ',\n', raw, count=1)

# Step 2: Fix unescaped inch/quote marks inside JSON string values
# Pattern: a digit followed by unescaped " followed by a space, comma, or end of value
# e.g. 55" QLED  or  27"  inside a name/spec field
# We replace  digit"  with  digit\"  but only inside string contexts
# Strategy: find all occurrences of  [0-9]"  that are NOT already escaped
fixed = re.sub(r'(\d)"(?!,|\n|}|\\)', r'\1\\"', fixed)


# Parse
try:
    data = json.loads(fixed)
    print(f"JSON valid! Total products: {len(data)}")
    print(f"First: {data[0]['id']} - {data[0]['name']}")
    print(f"Last:  {data[-1]['id']} - {data[-1]['name']}")

    # Check duplicate IDs
    ids = [p["id"] for p in data]
    dupes = list(set(x for x in ids if ids.count(x) > 1))
    if dupes:
        print(f"Duplicate IDs ({len(dupes)}): {dupes[:10]}")
    else:
        print("No duplicate IDs")

    # Check required fields
    required = ["id","name","category","price","specs","warranty","stock","rating","sku"]
    missing_fields = []
    for p in data:
        for field in required:
            if field not in p:
                missing_fields.append(f"{p.get('id','?')} missing '{field}'")
    if missing_fields:
        print(f"Missing fields: {missing_fields[:5]}")
    else:
        print("All required fields present in all products")

    # Category breakdown
    from collections import Counter
    cats = Counter(p["category"] for p in data)
    print("\nCategory breakdown:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    # Write fixed file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nFile written: {filepath}")

except json.JSONDecodeError as e:
    print(f"JSON ERROR at pos {e.pos}: {e.msg}")
    print(f"Context: {repr(fixed[max(0, e.pos-100):e.pos+100])}")
