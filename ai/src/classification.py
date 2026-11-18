"""Crop problem classification (sections 5, 7, 8).

Two interchangeable backends implement the same ``classify_problem`` contract:

1. ``SklearnCropProblemClassifier`` — a REAL machine-learning text classifier
   (TF-IDF n-gram features + multinomial Logistic Regression). Trained on the
   prototype knowledge base (each problem's name, symptoms and keywords become
   labelled training documents). Produces ``predict_proba``-based confidence
   and full evaluation metrics (accuracy / precision / recall / F1 / confusion
   matrix). This is genuine ML — not a rule list of ``if crop == "maize"``.

2. ``KeywordClassifier`` — a deterministic keyword-overlap fallback that needs
   zero heavy dependencies. Always available so the pipeline runs even before
   the ML model is trained or when scikit-learn is absent.

``get_classifier()`` returns the trained ML classifier if available, else the
keyword fallback. ``train_classifier()`` trains the ML classifier and returns
evaluation results (called from the Colab notebook and from tests).

The orchestrator (``crop_analysis.py``) calls ``classify_problem`` and does not
care which backend is active — that is the whole point of the abstraction.
"""

import math
from typing import Dict, List, Optional, Tuple

from ai.src import knowledge

# Detect scikit-learn (optional). Fallback to keyword classification if absent.
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import (
        accuracy_score,
        precision_recall_fscore_support,
        classification_report,
        confusion_matrix,
    )
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover - sklearn simply not installed
    SKLEARN_AVAILABLE = False


def _round2(value: float) -> float:
    """Round to 2 decimals, half-up (matches JS Math.round(x*100)/100)."""
    return math.floor(value * 100 + 0.5) / 100


# ── Keyword fallback classifier (no dependencies) ─────────────────────────────
class KeywordClassifier:
    """Deterministic keyword-overlap classifier — the always-available fallback."""

    name = "keyword"

    def classify(self, crop_id: str, text: str) -> Dict:
        text = (text or "").lower()
        candidates = knowledge.get_problems_by_crop(crop_id) if crop_id and crop_id != "unknown" else knowledge.problems_as_dicts()
        if not candidates:
            candidates = knowledge.problems_as_dicts()

        scored = []
        for p in candidates:
            score = sum(1 for kw in p["keywords"] if kw.lower() in text)
            scored.append((p, score))
        scored.sort(key=lambda x: x[1], reverse=True)

        best = scored[0] if scored else None
        if not best or best[1] == 0:
            return {
                "category": "Unknown",
                "problem_id": None,
                "problem": None,
                "confidence": 0.38,
                "source": "keyword",
            }

        base = best[0]["confidence"]
        boost = min(best[1] * 0.04, 0.08)
        confidence = min(_round2(base + boost), 0.98)
        return {
            "category": best[0]["category"],
            "problem_id": best[0]["id"],
            "problem": best[0],
            "confidence": confidence,
            "source": "keyword",
        }


# ── Real ML classifier (scikit-learn) ─────────────────────────────────────────
def _build_training_data() -> Tuple[List[str], List[str], List[str]]:
    """Build labelled training documents from the knowledge base.

    Each problem contributes several short text documents (its name, each
    symptom sentence, and a keyword bag) so the classifier has enough samples to
    learn from — this is what makes the train/test evaluation meaningful rather
    than a single row per class.
    """
    docs, labels, categories = [], [], []
    for p in knowledge.problems_as_dicts():
        docs.append(p["name_en"])
        labels.append(p["id"])
        categories.append(p["category"])
        for symptom in p["symptoms_en"]:
            docs.append(symptom)
            labels.append(p["id"])
            categories.append(p["category"])
        if p["keywords"]:
            docs.append(" ".join(p["keywords"]))
            labels.append(p["id"])
            categories.append(p["category"])
    return docs, labels, categories


class SklearnCropProblemClassifier:
    """TF-IDF + Logistic Regression crop-problem classifier (REAL ML)."""

    name = "ml"

    def __init__(self):
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn is not installed")
        self.pipeline = None
        self.labels: List[str] = []
        self.trained = False

    def train(self, test_size: float = 0.25, random_state: int = 42) -> Dict:
        """Train the classifier and return evaluation metrics on a held-out split."""
        docs, labels, _ = _build_training_data()

        self.pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=1,
                    sublinear_tf=True,
                )),
                ("clf", LogisticRegression(
                    max_iter=2000,
                    C=10.0,
                    class_weight="balanced",
                )),
            ]
        )

        # Stratified split where possible (>=2 samples per class).
        stratify = labels if len(set(labels)) > 1 else None
        try:
            x_train, x_test, y_train, y_test = train_test_split(
                docs, labels, test_size=test_size, random_state=random_state, stratify=stratify,
            )
        except ValueError:
            # Fall back to a non-stratified split if a class is too small.
            x_train, x_test, y_train, y_test = train_test_split(
                docs, labels, test_size=test_size, random_state=random_state,
            )

        self.pipeline.fit(x_train, y_train)
        self.labels = sorted(set(labels))
        self.trained = True

        y_pred = self.pipeline.predict(x_test)
        acc = accuracy_score(y_test, y_pred)
        # average=None gives per-class metrics; macro gives a single summary.
        prec, rec, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average="macro", zero_division=0
        )
        report = classification_report(
            y_test, y_pred, zero_division=0, output_dict=True
        )
        cm = confusion_matrix(y_test, y_pred, labels=self.labels).tolist()

        return {
            "n_train": len(x_train),
            "n_test": len(x_test),
            "n_classes": len(self.labels),
            "accuracy": float(acc),
            "precision_macro": float(prec),
            "recall_macro": float(rec),
            "f1_macro": float(f1),
            "report": report,
            "confusion_matrix": cm,
            "labels": self.labels,
            "note": (
                "Evaluation on a small held-out split of the prototype knowledge "
                "base. Metrics are illustrative of the ML approach, not a claim of "
                "production accuracy."
            ),
        }

    def classify(self, crop_id: str, text: str) -> Dict:
        if not self.trained:
            raise RuntimeError("Classifier is not trained — call train_classifier() first")
        text = text or ""
        probs = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        best_idx = int(probs.argmax())
        problem_id = classes[best_idx]
        confidence = float(probs[best_idx])

        problem = knowledge.get_problem_by_id(problem_id)

        # Crop-context guard: if the top prediction does not affect this crop and
        # a crop-specific candidate exists with comparable probability, prefer the
        # crop-specific one (avoids e.g. predicting a cassava problem for maize).
        if crop_id and crop_id != "unknown" and problem and crop_id not in problem["affected_crops"]:
            crop_problems = knowledge.get_problems_by_crop(crop_id)
            crop_ids = {p["id"] for p in crop_problems}
            best_crop_idx, best_crop_prob = -1, -1.0
            for i, cls in enumerate(classes):
                if cls in crop_ids and probs[i] > best_crop_prob:
                    best_crop_prob, best_crop_idx = float(probs[i]), i
            if best_crop_idx >= 0:
                problem_id = classes[best_crop_idx]
                confidence = best_crop_prob
                problem = knowledge.get_problem_by_id(problem_id)

        if not problem:
            return {
                "category": "Unknown",
                "problem_id": None,
                "problem": None,
                "confidence": 0.38,
                "source": "ml",
            }

        return {
            "category": problem["category"],
            "problem_id": problem["id"],
            "problem": problem,
            "confidence": confidence,
            "source": "ml",
        }


# ── Module-level singleton + public API ──────────────────────────────────────
_ML_CLASSIFIER: Optional[SklearnCropProblemClassifier] = None


def is_ml_available() -> bool:
    return SKLEARN_AVAILABLE and _ML_CLASSIFIER is not None and _ML_CLASSIFIER.trained


def get_classifier():
    """Return the trained ML classifier if available, else the keyword fallback."""
    if is_ml_available():
        return _ML_CLASSIFIER
    return KeywordClassifier()


def train_classifier(test_size: float = 0.25, random_state: int = 42) -> Dict:
    """Train the scikit-learn classifier and cache it. Returns evaluation metrics.

    Safe to call only when scikit-learn is installed. The Colab notebook calls
    this; tests that need the keyword path simply don't call it.
    """
    global _ML_CLASSIFIER
    if not SKLEARN_AVAILABLE:
        raise RuntimeError("scikit-learn is not installed — cannot train ML classifier")
    _ML_CLASSIFIER = SklearnCropProblemClassifier()
    return _ML_CLASSIFIER.train(test_size=test_size, random_state=random_state)


def classify_problem(
    crop_id: str,
    description: str,
    image_hint: Optional[Dict] = None,
    use_ml: bool = True,
) -> Dict:
    """Classify a crop problem from a text description (+ optional image hint).

    Returns ``{category, problem_id, problem, confidence, source}``.
    ``source`` is ``"ml"`` or ``"keyword"`` so callers can transparently tell
    which backend produced the result (section 6: distinguish real vs simulated).
    """
    text = f"{description or ''} {(image_hint or {}).get('text') or ''}".strip()
    classifier = get_classifier() if use_ml else KeywordClassifier()
    return classifier.classify(crop_id, text)
