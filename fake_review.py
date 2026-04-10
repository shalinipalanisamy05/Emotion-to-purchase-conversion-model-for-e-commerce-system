"""
fake_review.py — Fake review detector using Random Forest
Uses 12 linguistic features extracted from review text.
Trained on REAL IMDB dataset — fake reviews are detected using
real linguistic signals (caps ratio, exclamation marks, repetition, length etc.)

HOW TO GET THE DATASET:
  1. Go to: https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews
  2. Download and save as 'reviews_dataset.csv' in your project folder
  3. Delete models/fake_review_model.pkl if it exists
  4. Run the app — model will auto-train on real data
"""

import re
import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

MODEL_PATH   = "models/fake_review_model.pkl"
DATASET_PATH = "reviews_dataset.csv"


# ── Feature extraction ────────────────────────────────────────────────────────

def extract_features(review: str) -> list[float]:
    """
    12 linguistic features that distinguish real vs fake reviews.

    Fake reviews typically have:
      - High caps ratio (shouting)
      - Many exclamation marks
      - Repetitive words
      - Very short or very generic text
      - Superlative overuse (best! amazing! worst! terrible!)
      - No specific details (no numbers, no dates, no specifics)

    Genuine reviews typically have:
      - Mixed case normal writing
      - Specific details (numbers, timeframes)
      - Longer, varied vocabulary
      - Measured language
    """
    if not review or not review.strip():
        return [0.0] * 12

    text  = review.strip()
    words = text.split()
    wc    = max(len(words), 1)
    cc    = max(len(text), 1)

    length            = len(text)
    exclamation_ratio = text.count("!") / cc
    caps_ratio        = sum(1 for c in text if c.isupper()) / cc
    unique_word_ratio = len(set(w.lower() for w in words)) / wc
    avg_word_len      = sum(len(w) for w in words) / wc

    superlatives = {
        "best", "worst", "greatest", "amazing", "terrible", "perfect",
        "excellent", "horrible", "outstanding", "awful", "incredible",
        "fantastic", "dreadful", "superb", "pathetic", "unbelievable",
        "magnificent", "atrocious", "phenomenal", "dreadful",
    }
    superlative_ratio = sum(1 for w in words if w.lower() in superlatives) / wc

    starts_with_i  = 1.0 if text.lower().startswith("i ") else 0.0
    has_numbers    = 1.0 if re.search(r"\d+", text) else 0.0
    repeated_punct = float(len(re.findall(r"[!?]{2,}", text)))
    sentence_count = max(len(re.split(r"[.!?]+", text)), 1)
    avg_sent_len   = wc / sentence_count
    has_url        = 1.0 if re.search(r"http|www\.|@", text, re.IGNORECASE) else 0.0

    return [
        length, exclamation_ratio, caps_ratio, unique_word_ratio,
        avg_word_len, superlative_ratio, starts_with_i, has_numbers,
        repeated_punct, sentence_count, avg_sent_len, has_url,
    ]


# ── Real dataset loader ───────────────────────────────────────────────────────

def _load_real_dataset(n: int = 3000):
    """
    Load REAL reviews from IMDB dataset CSV and label them as
    genuine (0) or fake (1) using linguistic signals.

    A review is considered FAKE if it shows these real-world fake signals:
      - Excessive capitals (caps_ratio > 0.35)
      - 3 or more exclamation marks
      - Very short text (under 10 words)
      - Very low unique word ratio (repetitive, under 0.45)
      - Very high superlative density (over 30% of words are superlatives)

    All other reviews are treated as GENUINE.

    Download dataset from:
        https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews
    Save as: reviews_dataset.csv
    """
    import pandas as pd
    import random
    random.seed(42)
    np.random.seed(42)

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            "\n\n"
            "=" * 60 + "\n"
            "REAL DATASET NOT FOUND!\n"
            "=" * 60 + "\n"
            "Please download the IMDB dataset:\n"
            "  1. Go to: https://www.kaggle.com/datasets/lakshmi25npathi"
            "/imdb-dataset-of-50k-movie-reviews\n"
            "  2. Download the CSV file\n"
            "  3. Save it as 'reviews_dataset.csv' in your project folder\n"
            "  4. Delete models/fake_review_model.pkl if it exists\n"
            "  5. Run the app again\n"
            "=" * 60
        )

    print(f"[FakeReview] Loading real dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH).dropna(subset=["review"])
    print(f"[FakeReview] Dataset loaded: {len(df)} reviews")

    reviews = df["review"].tolist()
    random.shuffle(reviews)

    def is_fake_by_linguistics(text: str) -> bool:
        """
        Label a review as fake using real linguistic signals.
        These are the same signals used in academic fake review research.
        """
        words      = text.split()
        wc         = max(len(words), 1)
        cc         = max(len(text), 1)
        caps_ratio = sum(1 for c in text if c.isupper()) / cc
        excl_count = text.count("!")

        unique_ratio = len(set(w.lower() for w in words)) / wc

        superlatives = {
            "best", "worst", "greatest", "amazing", "terrible", "perfect",
            "excellent", "horrible", "outstanding", "awful", "incredible",
            "fantastic", "dreadful", "superb", "pathetic",
        }
        superlative_ratio = sum(1 for w in words if w.lower() in superlatives) / wc

        return (
            caps_ratio > 0.35        or   # too many capitals = shouting
            excl_count >= 3          or   # too many exclamation marks
            wc < 10                  or   # too short to be genuine
            unique_ratio < 0.45      or   # too repetitive
            superlative_ratio > 0.30      # too many extreme words
        )

    X, y = [], []
    genuine_count = 0
    fake_count    = 0

    for r in reviews:
        label = 1 if is_fake_by_linguistics(r) else 0
        X.append(extract_features(r))
        y.append(label)
        if label == 0:
            genuine_count += 1
        else:
            fake_count += 1
        if len(X) >= n:
            break

    print(f"[FakeReview] Labeled: {genuine_count} genuine | {fake_count} fake "
          f"(from {len(X)} real reviews)")

    return np.array(X), np.array(y)


# ── Model training & persistence ──────────────────────────────────────────────

def train_model(save: bool = True) -> RandomForestClassifier:
    print("[FakeReview] Training Random Forest on REAL dataset...")
    X, y = _load_real_dataset(n=3000)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_tr, y_tr)

    report = classification_report(
        y_te, model.predict(X_te),
        target_names=["Genuine", "Fake"]
    )
    print("[FakeReview] Eval on REAL data:\n", report)

    if save:
        os.makedirs("models", exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        print(f"[FakeReview] Model saved -> {MODEL_PATH}")

    return model


def load_model() -> RandomForestClassifier:
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    return train_model()


# ── Public API ────────────────────────────────────────────────────────────────

_model: RandomForestClassifier | None = None


def _get_model() -> RandomForestClassifier:
    global _model
    if _model is None:
        _model = load_model()
    return _model


def predict_fake(review: str) -> float:
    """Return probability 0.0-1.0 that a review is fake."""
    m        = _get_model()
    features = np.array(extract_features(review)).reshape(1, -1)
    proba    = m.predict_proba(features)[0]
    idx      = list(m.classes_).index(1)
    return round(float(proba[idx]), 3)


def analyze_reviews(reviews: list[str]) -> dict:
    """Return aggregate fake-review stats for a list of reviews."""
    if not reviews:
        return {
            "fake_ratio":     0.0,
            "fake_count":     0,
            "total":          0,
            "scores":         [],
            "avg_fake_score": 0.0,
        }

    scores     = [predict_fake(r) for r in reviews]
    fake_count = sum(1 for s in scores if s > 0.5)

    return {
        "fake_ratio":     round(fake_count / len(reviews), 3),
        "fake_count":     fake_count,
        "total":          len(reviews),
        "scores":         scores,
        "avg_fake_score": round(float(np.mean(scores)), 3),
    }


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    _get_model()
    tests = [
        "I bought these headphones 2 months ago. Battery life is decent, about 18 hours.",
        "BEST PRODUCT EVER!!! AMAZING!!! BUY NOW!!!",
        "The sound quality is good but the ear cushions are a bit uncomfortable.",
        "WORST WORST WORST!!! AVOID AVOID AVOID!!!",
        "Used it for 3 weeks. Works fine for the price. Delivery was on time.",
    ]
    for r in tests:
        s = predict_fake(r)
        print(f"[{'FAKE   ' if s > 0.5 else 'Genuine'} {s:.2f}] {r[:70]}")