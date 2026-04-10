"""
sentiment.py — Sentiment analysis using TF-IDF + Naive Bayes
Trained on REAL IMDB movie review dataset (50,000 reviews).

HOW TO GET THE DATASET:
  1. Go to: https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews
  2. Download and save as 'reviews_dataset.csv' in your project folder
  3. Delete models/sentiment_model.pkl if it exists
  4. Run the app — model will auto-train on real data

Dataset columns required: 'review' (text), 'sentiment' (positive/negative)
"""

import re
import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

MODEL_PATH   = "models/sentiment_model.pkl"
DATASET_PATH = "reviews_dataset.csv"


# ── Text cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Normalize review text for vectorization."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── Real dataset loader ───────────────────────────────────────────────────────

def _load_real_dataset(n_per_class: int = 1500):
    """
    Load real IMDB reviews from CSV dataset.

    Expected CSV columns:
        review    — raw review text
        sentiment — 'positive' or 'negative'

    Download from:
        https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews
    Save as: reviews_dataset.csv in your project folder.
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
            "  4. Delete models/sentiment_model.pkl if it exists\n"
            "  5. Run the app again\n"
            "=" * 60
        )

    print(f"[Sentiment] Loading real dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)

    if "review" not in df.columns or "sentiment" not in df.columns:
        raise ValueError(
            f"CSV must have 'review' and 'sentiment' columns.\n"
            f"Found columns: {df.columns.tolist()}"
        )

    df = df[df["sentiment"].isin(["positive", "negative"])].dropna(subset=["review"])
    print(f"[Sentiment] Dataset loaded: {len(df)} total reviews")

    pos_reviews = df[df["sentiment"] == "positive"]["review"].tolist()
    neg_reviews = df[df["sentiment"] == "negative"]["review"].tolist()

    print(f"[Sentiment] Positive: {len(pos_reviews)} | Negative: {len(neg_reviews)}")

    sample_pos = random.sample(pos_reviews, min(n_per_class, len(pos_reviews)))
    sample_neg = random.sample(neg_reviews, min(n_per_class, len(neg_reviews)))

    X, y = [], []
    for r in sample_pos:
        X.append(clean_text(r))
        y.append(1)
    for r in sample_neg:
        X.append(clean_text(r))
        y.append(0)

    return X, y


# ── Training & persistence ────────────────────────────────────────────────────

def train_model(save: bool = True) -> Pipeline:
    print("[Sentiment] Training TF-IDF + Naive Bayes on REAL dataset...")
    X, y = _load_real_dataset(n_per_class=1500)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=8000,
            ngram_range=(1, 2),
            min_df=2,
            strip_accents="unicode",
            sublinear_tf=True,
        )),
        ("clf", MultinomialNB(alpha=0.1)),
    ])

    pipe.fit(X_train, y_train)

    report = classification_report(
        y_test, pipe.predict(X_test),
        target_names=["Negative", "Positive"]
    )
    print("[Sentiment] Eval on REAL data:\n", report)

    if save:
        os.makedirs("models", exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(pipe, f)
        print(f"[Sentiment] Model saved -> {MODEL_PATH}")

    return pipe


def load_model() -> Pipeline:
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    return train_model()


# ── Public API ────────────────────────────────────────────────────────────────

_model: Pipeline | None = None


def _get_model() -> Pipeline:
    global _model
    if _model is None:
        _model = load_model()
    return _model


def predict_sentiment(text: str) -> float:
    """Return sentiment score 0.0 (negative) to 1.0 (positive)."""
    cleaned = clean_text(text)
    if not cleaned:
        return 0.5
    proba = _get_model().predict_proba([cleaned])[0]
    return round(float(proba[1]), 3)


def analyze_reviews(reviews: list[str]) -> dict:
    """Analyze a batch of reviews and return aggregate sentiment stats."""
    if not reviews:
        return {
            "avg_sentiment":   0.5,
            "positive_count":  0,
            "negative_count":  0,
            "scores":          [],
            "sentiment_label": "No reviews",
        }

    scores   = [predict_sentiment(r) for r in reviews]
    positive = sum(1 for s in scores if s >= 0.5)
    avg      = float(np.mean(scores))

    return {
        "avg_sentiment":   round(avg, 3),
        "positive_count":  positive,
        "negative_count":  len(scores) - positive,
        "scores":          scores,
        "sentiment_label": _label(avg),
    }


def _label(score: float) -> str:
    if score >= 0.75: return "Very Positive"
    if score >= 0.55: return "Positive"
    if score >= 0.40: return "Neutral"
    if score >= 0.25: return "Negative"
    return "Very Negative"


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    _get_model()
    tests = [
        "Works perfectly, great sound quality, very happy with the purchase",
        "Broke after one week. Terrible quality. Never buying again.",
        "Decent product for the price, nothing special but does the job.",
        "BEST PRODUCT EVER!!! AMAZING!!!",
        "Stopped working after 2 days, very disappointed.",
    ]
    for t in tests:
        s = predict_sentiment(t)
        print(f"[{_label(s):15s} {s:.2f}] {t[:70]}")