import json
import re
from rank_bm25 import BM25Okapi


def load_docs():
    """Load both JSON files into one list."""
    docs = []
    for path in ["darglobal.json", "wasalt.json"]:
        with open(path, encoding="utf-8") as f:
            docs.extend(json.load(f))
    return docs


def doc_to_text(d):
    """Turn one document into a readable block of facts: used for searching AND for the prompt."""
    if d["source"] == "DarGlobal":
        return (f"DarGlobal project: {d['name']}\nLocation: {d['location']}\n"
                f"Summary: {d['description']}\n{d['text'][:2000]}\nLink: {d['url']}")
    price = f"{d['price_sar']:,.0f} SAR" if d["price_sar"] else "not listed"
    if d["purpose"] == "rent" and d["rent_frequency"]:
        price += f" per {d['rent_frequency']}"
    return (f"Wasalt listing: {d['title']}\nFor: {d['purpose']}\nType: {d['property_type']}\n"
            f"Location: {d['address']}\nPrice: {price}\nBedrooms: {int(d['bedrooms']) if d['bedrooms'] else 'not listed'}\n"
            f"Built-up area: {d['built_up_area_sqm']} sqm\nDescription: {d['description'][:800]}\n"
            f"Link: {d['url']}")


def tokenize(text):
    """Lowercase, split into words, and strip plural 's' so 'villas' matches 'villa'."""
    words = re.findall(r"\w+", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
            for w in words]


DOCS = load_docs()
TEXTS = [doc_to_text(d) for d in DOCS]
BM25 = BM25Okapi([tokenize(t) for t in TEXTS])


CITIES = {"riyadh": {"riyadh", "الرياض"}, "jeddah": {"jeddah", "جدة", "جده"}}
RENT_WORDS = {"rent", "rental", "lease", "للإيجار", "للايجار", "إيجار", "ايجار"}
SALE_WORDS = {"sale", "buy", "buying", "purchase", "للبيع"}


def search(question, k=5):
    """Filter by the question's hard requirements, then rank the rest with BM25."""
    words = set(tokenize(question))

    wanted = "rent" if words & RENT_WORDS else "sale" if words & SALE_WORDS else None
    city = next((c for c, names in CITIES.items() if words & names), None)
    m = re.search(r"(\d+)\s*-?\s*(?:bed|br\b|bhk)", question.lower())   # "2 bedroom", "2-bed", "2br"
    bedrooms = int(m.group(1)) if m else None

    def matches(d):
        if wanted and d.get("purpose", "sale") != wanted:
            return False
        if city and city not in (d.get("city") or d.get("location") or "").lower():
            return False
        if bedrooms and d.get("bedrooms") and int(d["bedrooms"]) != bedrooms:
            return False
        return True

    scores = BM25.get_scores(tokenize(question))
    candidates = [i for i, d in enumerate(DOCS) if matches(d)]
    best = sorted(candidates, key=lambda i: scores[i], reverse=True)[:k]
    return [TEXTS[i] for i in best if scores[i] > 0]


if __name__ == "__main__":
    for q in ["Trump Tower Jeddah", "villa for sale in Riyadh", "apartment for rent Al Naeem",
              "DarGlobal projects in Oman"]:
        print(f"\n=== {q} ===")
        for text in search(q, k=3):
            print("-", text.splitlines()[0])