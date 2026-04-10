"""
intent.py — Query intent detection
Rule-based (fast, no GPU) + optional DistilBERT zero-shot (more accurate).
"""

import re
from functools import lru_cache

INTENT_MAP = {
    "budget":     ["cheap","affordable","budget","low price","under","best price",
                   "value for money","inexpensive","cost effective","below"],
    "premium":    ["best","premium","top","high end","professional","flagship",
                   "luxury","advanced","superior","pro"],
    "comparison": ["vs","versus","compare","better","difference","which is",
                   "alternative","or","between"],
    "feature":    ["wireless","waterproof","noise cancelling","long battery",
                   "fast charging","lightweight","foldable","compact","tws",
                   "anc","bluetooth","usb c"],
    "brand":      ["sony","boat","jbl","samsung","apple","oneplus","realme",
                   "bose","sennheiser","anker","mi","xiaomi","boult","ptron",
                   "zebronics","noise","infinity","skullcandy"],
    "general":    [],
}


def classify_intent_rules(query: str) -> dict:
    q = query.lower().strip()
    intents = {}

    for intent, keywords in INTENT_MAP.items():
        if intent == "general":
            continue
        hits = sum(1 for kw in keywords if kw in q)
        if hits:
            intents[intent] = hits / max(len(keywords), 1)

    if not intents:
        intents["general"] = 1.0

    total   = sum(intents.values())
    intents = {k: round(v / total, 3) for k, v in intents.items()}
    return {
        "primary_intent": max(intents, key=intents.get),
        "intents":        intents,
        "query":          query,
        "model":          "rules",
    }


# ── DistilBERT (optional, lazy-loaded) ───────────────────────────────────────

_pipe = None

def _load_distilbert():
    global _pipe
    if _pipe is not None:
        return _pipe
    try:
        from transformers import pipeline
        print("[Intent] Loading DistilBERT zero-shot model (~30s first time)...")
        _pipe = pipeline(
            "zero-shot-classification",
            model="cross-encoder/nli-distilroberta-base",
            device=-1,
        )
        print("[Intent] DistilBERT ready.")
    except Exception as e:
        print(f"[Intent] DistilBERT failed ({e}). Using rule-based fallback.")
        _pipe = None
    return _pipe


def classify_intent_distilbert(query: str) -> dict:
    pipe = _load_distilbert()
    if pipe is None:
        return classify_intent_rules(query)
    try:
        labels  = [k for k in INTENT_MAP if k != "general"]
        result  = pipe(query, labels, multi_label=True)
        intents = {l: round(s, 3)
                   for l, s in zip(result["labels"], result["scores"])
                   if s > 0.1}
        if not intents:
            intents = {"general": 1.0}
        return {
            "primary_intent": result["labels"][0],
            "intents":        intents,
            "query":          query,
            "model":          "distilbert",
        }
    except Exception as e:
        print(f"[Intent] Inference failed ({e}). Falling back to rules.")
        return classify_intent_rules(query)


# ── Public API ────────────────────────────────────────────────────────────────

@lru_cache(maxsize=512)
def analyze_intent(query: str, use_distilbert: bool = False) -> dict:
    """Main entry point. Results cached with lru_cache."""
    if use_distilbert:
        return classify_intent_distilbert(query)
    return classify_intent_rules(query)


def apply_intent_boost(products: list[dict], intent_result: dict) -> list[dict]:
    """Add a small score boost to products that match the detected intent."""
    primary = intent_result.get("primary_intent", "general")
    query   = intent_result.get("query", "").lower()

    for p in products:
        boost = 0.0
        price_str = re.sub(r"[^\d]", "", p.get("price", "0"))
        price     = int(price_str) if price_str else 0
        name      = p.get("name", "").lower()

        if primary == "budget" and 0 < price < 2000:
            boost = 0.06
        elif primary == "premium" and price > 5000:
            boost = 0.06
        elif primary == "brand":
            for brand in INTENT_MAP["brand"]:
                if brand in name and brand in query:
                    boost = 0.08
                    break
        elif primary == "feature":
            for feat in INTENT_MAP["feature"]:
                if feat in name:
                    boost = 0.04
                    break

        p["intent_boost"] = round(boost, 3)

    return products


def intent_summary(intent_result: dict) -> str:
    primary = intent_result.get("primary_intent", "general")
    summaries = {
        "budget":     "Looking for affordable options",
        "premium":    "Looking for top-quality products",
        "comparison": "Comparing options",
        "feature":    "Looking for specific features",
        "brand":      "Looking for a specific brand",
        "general":    "General search",
    }
    return summaries.get(primary, "General search")


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    queries = [
        "cheap wireless headphones under 1000",
        "best premium noise cancelling earbuds",
        "sony vs boat earphones which is better",
        "waterproof bluetooth speaker",
        "boAt Rockerz 450",
    ]
    for q in queries:
        r = classify_intent_rules(q)
        print(f"  {q!r:50s} → {r['primary_intent']} {r['intents']}")
