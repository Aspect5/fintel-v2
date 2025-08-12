"""
Walk-forward backtesting utilities (Phase 3 complement)

Given a daily time series, construct features and labels for a chosen horizon
and perform a simple walk-forward evaluation with periodic retraining.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from backend.tools.feature_builder import compute_features_from_data
from backend.tools.model_inference import _create_pipeline, vectorize_features, FEATURE_LIST


@dataclass
class BacktestPoint:
    index: int
    date: str
    label: int
    prob_up: float
    predicted_class: int
    fwd_return: float


def _future_return(series: List[Dict[str, Any]], idx: int, horizon_days: int) -> float:
    """Compute forward return over horizon as (close_{t+h} / close_t - 1). Assumes series sorted by date asc."""
    if idx + horizon_days >= len(series):
        return 0.0
    c0 = float(series[idx].get("adjusted_close", series[idx].get("close", 0.0)) or 0.0)
    c1 = float(series[idx + horizon_days].get("adjusted_close", series[idx + horizon_days].get("close", 0.0)) or 0.0)
    if c0 == 0.0:
        return 0.0
    return (c1 / c0) - 1.0


def _direction_label(ret: float) -> int:
    return 1 if ret > 0.0 else 0


def walk_forward_backtest_from_series(
    *,
    ticker: str,
    series: List[Dict[str, Any]],
    horizon_days: int = 10,
    min_train_size: int = 150,
    step: int = 5,
    calibrate: bool = False,
) -> Dict[str, Any]:
    """Perform a simple walk-forward backtest using only price/volume features.

    - series: list of daily bars (ascending), entries include date, open/high/low/close/adjusted_close/volume
    - Returns metrics and the per-point predictions.
    """
    # Local import to avoid hard dependency in environments without numpy during linting
    import numpy as np

    if not series or len(series) < (min_train_size + horizon_days + 2):
        return {"error": "insufficient_series_length", "length": len(series)}

    # Ensure ascending by date
    try:
        series = sorted(series, key=lambda x: x.get("date", ""))
    except Exception:
        pass

    preds: List[BacktestPoint] = []
    X_train: List[np.ndarray] = []
    y_train: List[int] = []

    model = None
    for i in range(min_train_size, len(series) - horizon_days):
        # Periodic retraining
        if (i - min_train_size) % step == 0 or model is None:
            # Build training window up to i (exclusive)
            X_train.clear()
            y_train.clear()
            start_idx = 20  # need at least 20 days for some features
            for j in range(start_idx, i):
                # Features from truncated series up to j
                ts_daily = {"series": series[: j + 1]}
                feats_obj = compute_features_from_data(
                    ticker=ticker,
                    time_series_daily=ts_daily,
                    news=None,
                    insiders=None,
                    fundamentals_income=None,
                    fundamentals_balance=None,
                    fundamentals_cash=None,
                    gainers_losers=None,
                    lookback_days=180,
                )
                feats = feats_obj.get("features", {})
                fwd_ret = _future_return(series, j, horizon_days)
                label = _direction_label(fwd_ret)
                X_train.append(vectorize_features(feats))
                y_train.append(label)

            if not X_train:
                return {"error": "no_training_records"}

            Xtr = np.vstack(X_train)
            ytr = np.asarray(y_train)
            model = _create_pipeline()
            model.fit(Xtr, ytr)

        # Predict for point i using model trained on data < i
        ts_daily_i = {"series": series[: i + 1]}
        feats_obj_i = compute_features_from_data(
            ticker=ticker,
            time_series_daily=ts_daily_i,
            news=None,
            insiders=None,
            fundamentals_income=None,
            fundamentals_balance=None,
            fundamentals_cash=None,
            gainers_losers=None,
            lookback_days=180,
        )
        feats_i = feats_obj_i.get("features", {})
        xi = vectorize_features(feats_i).reshape(1, -1)
        try:
            proba_up = float(model.predict_proba(xi)[0, 1])
        except Exception:
            score = float(model.decision_function(xi)[0])
            proba_up = 1.0 / (1.0 + np.exp(-score))
        pred_cls = 1 if proba_up >= 0.5 else 0
        fwd_ret_i = _future_return(series, i, horizon_days)
        preds.append(
            BacktestPoint(
                index=i,
                date=str(series[i].get("date")),
                label=_direction_label(fwd_ret_i),
                prob_up=proba_up,
                predicted_class=pred_cls,
                fwd_return=fwd_ret_i,
            )
        )

    if not preds:
        return {"error": "no_predictions"}

    y_true = np.array([p.label for p in preds], dtype=int)
    p_up = np.array([p.prob_up for p in preds], dtype=float)
    y_pred = (p_up >= 0.5).astype(int)
    fwd_returns = np.array([p.fwd_return for p in preds], dtype=float)

    # Metrics
    accuracy = float((y_pred == y_true).mean()) if len(y_true) else 0.0
    try:
        # AUC may fail if labels are constant
        from sklearn.metrics import roc_auc_score, brier_score_loss

        auc = float(roc_auc_score(y_true, p_up)) if len(np.unique(y_true)) > 1 else float("nan")
        brier = float(brier_score_loss(y_true, p_up))
    except Exception:
        auc = float("nan")
        brier = float("nan")

    # Average forward return by predicted class
    ret_up = float(fwd_returns[y_pred == 1].mean()) if (y_pred == 1).any() else 0.0
    ret_down = float(fwd_returns[y_pred == 0].mean()) if (y_pred == 0).any() else 0.0
    mean_ret = float(fwd_returns.mean()) if fwd_returns.size else 0.0
    std_ret = float(fwd_returns.std(ddof=1)) if fwd_returns.size > 1 else 0.0
    sharpe_like = (mean_ret / std_ret) if std_ret else 0.0

    # Compact prediction trail
    trail = [
        {
            "date": p.date,
            "prob_up": p.prob_up,
            "pred": p.predicted_class,
            "label": p.label,
            "fwd_ret": p.fwd_return,
        }
        for p in preds
    ]

    return {
        "ticker": ticker.upper(),
        "horizon_days": horizon_days,
        "min_train_size": min_train_size,
        "step": step,
        "metrics": {
            "accuracy": accuracy,
            "auc": auc,
            "brier": brier,
            "mean_forward_return": mean_ret,
            "sharpe_like": sharpe_like,
            "ret_when_pred_up": ret_up,
            "ret_when_pred_down": ret_down,
            "n_predictions": int(len(preds)),
        },
        "predictions": trail,
        "feature_list": FEATURE_LIST,
    }


