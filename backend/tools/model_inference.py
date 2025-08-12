"""
Baseline modeling utilities (Phase 3)

Implements a simple classification model for directional prediction using
engineered features. Includes training, persistence, and inference.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, roc_auc_score, brier_score_loss
import joblib


# Default feature order used for vectorization
FEATURE_LIST: List[str] = [
    "ret_1d",
    "ret_5d",
    "ret_20d",
    "sma_5",
    "sma_20",
    "sma_50",
    "px_above_sma20",
    "sma20_above_sma50",
    "atr14_pct",
    "bbands20_width",
    "vol_5_over_20",
    "news_count_7",
    "news_count_30",
    "news_sent_mean_7",
    "news_sent_mean_30",
    "news_neg_count_7",
    "insider_buy_count",
    "insider_sell_count",
    "insider_net_count",
    "rev_yoy",
    "op_margin",
    "breadth_g_minus_l",
    "price_last",
]


def vectorize_features(features: Dict[str, Any], feature_list: Sequence[str] = FEATURE_LIST) -> np.ndarray:
    """Convert a feature dict into a fixed-order numpy vector, filling missing with 0.0.
    """
    row = []
    for name in feature_list:
        value = features.get(name, 0.0)
        try:
            row.append(float(value))
        except Exception:
            row.append(0.0)
    return np.asarray(row, dtype=float)


def get_model_path() -> Path:
    models_dir = Path(__file__).resolve().parents[1] / "models"
    models_dir.mkdir(exist_ok=True)
    return models_dir / "baseline_logreg.pkl"


def _create_pipeline() -> Pipeline:
    # Standard scaler + logistic regression is a strong baseline
    return Pipeline([
        ("scaler", StandardScaler(with_mean=True, with_std=True)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])


def load_model() -> Optional[Pipeline]:
    path = get_model_path()
    if path.exists():
        try:
            return joblib.load(path)
        except Exception:
            return None
    return None


def save_model(model: Pipeline) -> str:
    path = get_model_path()
    joblib.dump(model, path)
    return str(path)


def create_dummy_model() -> Pipeline:
    """
    Create a tiny placeholder model to ensure inference works out of the box.
    Trains on synthetic data with the default feature list.
    """
    rng = np.random.default_rng(42)
    n_samples = 200
    X = rng.normal(size=(n_samples, len(FEATURE_LIST)))
    # Create a synthetic label with weak linear relationship
    weights = rng.normal(size=(len(FEATURE_LIST),))
    logits = X @ weights
    y = (logits > 0).astype(int)
    pipe = _create_pipeline()
    pipe.fit(X, y)
    return pipe


@dataclass
class TrainMetrics:
    accuracy: float
    auc: float
    brier: float
    train_samples: int
    test_samples: int


def train_baseline_model(records: List[Dict[str, Any]], calibrate: bool = True) -> Dict[str, Any]:
    """
    Train a baseline classifier.

    records: List of {"features": {..}, "label": 0 or 1}
    """
    if not records:
        return {"error": "no_training_data"}

    X_list: List[np.ndarray] = []
    y_list: List[int] = []
    for rec in records:
        feats = rec.get("features") or {}
        label = rec.get("label")
        if label not in (0, 1):
            # Skip invalid labels
            continue
        X_list.append(vectorize_features(feats))
        y_list.append(int(label))

    if not X_list:
        return {"error": "no_valid_records"}

    X = np.vstack(X_list)
    y = np.asarray(y_list)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=17, stratify=y if len(set(y)) > 1 else None)

    base = _create_pipeline()
    base.fit(X_train, y_train)

    model: Pipeline
    if calibrate and len(X_train) >= 100 and len(set(y_train)) > 1:
        # Wrap with sigmoid calibration for better probability estimates
        model = CalibratedClassifierCV(base, method="sigmoid", cv=3)
        model.fit(X_train, y_train)
    else:
        model = base

    # Metrics
    proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else np.clip(model.decision_function(X_test), -8, 8)
    pred = (proba >= 0.5).astype(int)
    acc = accuracy_score(y_test, pred)
    try:
        auc = roc_auc_score(y_test, proba)
    except Exception:
        auc = float("nan")
    try:
        brier = brier_score_loss(y_test, proba)
    except Exception:
        brier = float("nan")

    path = save_model(model)  # persist

    return {
        "status": "trained",
        "model_path": path,
        "metrics": {
            "accuracy": acc,
            "auc": auc,
            "brier": brier,
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
        },
        "feature_list": FEATURE_LIST,
    }


def predict_proba_from_features(features: Dict[str, Any]) -> Dict[str, Any]:
    model = load_model()
    if model is None:
        model = create_dummy_model()

    x = vectorize_features(features)
    x = x.reshape(1, -1)

    try:
        proba = model.predict_proba(x)[0, 1]
    except Exception:
        # Fallback for models without predict_proba
        score = float(model.decision_function(x)[0])
        # Sigmoid approximation
        proba = 1.0 / (1.0 + np.exp(-score))

    predicted_class = int(proba >= 0.5)
    return {
        "prob_up": float(proba),
        "predicted_class": predicted_class,
        "confidence": float(abs(proba - 0.5) * 2.0),  # 0..1 measure
        "feature_list": FEATURE_LIST,
        "model_path": str(get_model_path()),
    }


