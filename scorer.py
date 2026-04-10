"""
scorer.py — Composite trust scoring engine
Combines sentiment, fake-review ratio, star rating, and intent boost
into a single score (0.0–1.0) per product, then ranks them.
"""

import re
import numpy as np
from dataclasses import dataclass, field


@dataclass
class ProductScore:
    name:              str
    price:             str
    rating:            str
    url:               str
    reviews:           list
    sentiment_score:   float = 0.5
    fake_ratio:        float = 0.0
    avg_fake_score:    float = 0.0
    intent_boost:      float = 0.0
    composite_score:   float = 0.0
    sentiment_label:   str   = "Neutral"
    review_quality:    str   = "Unknown"
    price_numeric:     int   = 0
    positive_reviews:  list  = field(default_factory=list)
    negative_reviews:  list  = field(default_factory=list)


# ── Weights — must sum to 1.0 ─────────────────────────────────────────────────
WEIGHTS = {
    "sentiment":    0.35,
    "authenticity": 0.30,
    "rating":       0.25,
    "intent":       0.10,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_price(s: str) -> int:
    cleaned = re.sub(r"[^\d]", "", s)
    return int(cleaned) if cleaned else 0


def parse_rating(s: str) -> float:
    m = re.search(r"[\d.]+", s)
    if m:
        return min(float(m.group()) / 5.0, 1.0)
    return 0.5


def _quality_label(fake_ratio: float) -> str:
    if fake_ratio < 0.10: return "High quality"
    if fake_ratio < 0.30: return "Mostly genuine"
    if fake_ratio < 0.50: return "Mixed"
    return "Low quality"


def _sentiment_label(score: float) -> str:
    if score >= 0.75: return "Very Positive"
    if score >= 0.55: return "Positive"
    if score >= 0.40: return "Neutral"
    if score >= 0.25: return "Negative"
    return "Very Negative"


# ── Core formula ──────────────────────────────────────────────────────────────

def compute_composite(
    sentiment_score: float,
    fake_ratio:      float,
    rating_str:      str,
    intent_boost:    float = 0.0,
) -> float:
    """
    Trust score formula:
        score = sentiment  × 0.35
              + (1–fake)   × 0.30
              + rating/5   × 0.25
              + boost      × 0.10
    """
    raw = (
        sentiment_score       * WEIGHTS["sentiment"]    +
        (1.0 - fake_ratio)    * WEIGHTS["authenticity"] +
        parse_rating(rating_str) * WEIGHTS["rating"]    +
        intent_boost          * WEIGHTS["intent"]
    )
    return round(min(max(raw, 0.0), 1.0), 3)


# ── Full pipeline ─────────────────────────────────────────────────────────────

def score_products(
    products:       list[dict],
    intent_result:  dict,
    sentiment_fn,
    fake_review_fn,
) -> list[ProductScore]:
    """
    Score every product and return them sorted by composite_score (desc).

    Args:
        products       — list of dicts from scraper.py
        intent_result  — dict from intent.py
        sentiment_fn   — analyze_reviews() from sentiment.py
        fake_review_fn — analyze_reviews() from fake_review.py
    """
    scored = []

    for p in products:
        reviews = [r for r in p.get("reviews", []) if r and r.strip()]

        # ML models
        sent_result = sentiment_fn(reviews)
        fake_result = fake_review_fn(reviews)

        sentiment_score = sent_result.get("avg_sentiment", 0.5)
        fake_ratio      = fake_result.get("fake_ratio", 0.0)
        sent_scores     = sent_result.get("scores", [0.5] * len(reviews))
        fake_scores     = fake_result.get("scores", [0.0] * len(reviews))

        # Separate genuine positive / negative reviews for display
        pos_reviews, neg_reviews = [], []
        for r, fs, ss in zip(reviews, fake_scores, sent_scores):
            if fs < 0.5:                   # genuine
                (pos_reviews if ss >= 0.5 else neg_reviews).append(r)

        intent_boost = p.get("intent_boost", 0.0)
        score        = compute_composite(
            sentiment_score, fake_ratio, p.get("rating", "N/A"), intent_boost
        )

        scored.append(ProductScore(
            name            = p.get("name", "Unknown"),
            price           = p.get("price", "N/A"),
            rating          = p.get("rating", "N/A"),
            url             = p.get("url", ""),
            reviews         = reviews,
            sentiment_score = sentiment_score,
            fake_ratio      = fake_ratio,
            avg_fake_score  = fake_result.get("avg_fake_score", 0.0),
            intent_boost    = intent_boost,
            composite_score = score,
            sentiment_label = _sentiment_label(sentiment_score),
            review_quality  = _quality_label(fake_ratio),
            price_numeric   = parse_price(p.get("price", "0")),
            positive_reviews= pos_reviews[:3],
            negative_reviews= neg_reviews[:2],
        ))

    scored.sort(key=lambda x: x.composite_score, reverse=True)
    return scored


def score_summary(scored: list[ProductScore]) -> dict:
    if not scored:
        return {}
    scores = [p.composite_score for p in scored]
    return {
        "total_products":  len(scored),
        "avg_score":       round(float(np.mean(scores)), 3),
        "top_score":       round(max(scores), 3),
        "high_fake_count": sum(1 for p in scored if p.fake_ratio > 0.5),
        "best_product":    scored[0].name,
    }


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(compute_composite(0.78, 0.15, "4.2", 0.05))   # good product
    print(compute_composite(0.30, 0.70, "2.5", 0.00))   # bad product
