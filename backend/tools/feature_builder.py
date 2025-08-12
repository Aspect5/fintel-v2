"""
Feature Builder utilities (Phase 2)

Pure-Python feature engineering helpers that compose existing data sources
into a normalized feature vector suitable for downstream modeling.

No external numeric libs required; keep minimal and robust to missing data.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: List[float]) -> float:
    n = len(values)
    if n <= 1:
        return 0.0
    mu = _mean(values)
    var = sum((v - mu) ** 2 for v in values) / (n - 1)
    return var ** 0.5


def _sma(values: List[float], window: int) -> float:
    if not values or len(values) < window:
        return 0.0
    return _mean(values[-window:])


def _bbands_width(values: List[float], window: int = 20) -> float:
    if len(values) < window:
        return 0.0
    window_vals = values[-window:]
    mu = _mean(window_vals)
    s = _std(window_vals)
    if mu == 0:
        return 0.0
    upper = mu + 2 * s
    lower = mu - 2 * s
    return (upper - lower) / mu


def _atr14(daily_series: List[Dict[str, Any]]) -> float:
    # daily_series sorted ascending by date
    if len(daily_series) < 15:
        return 0.0
    trs: List[float] = []
    for i in range(1, 15):
        today = daily_series[-i]
        prev = daily_series[-i - 1]
        high = _safe_float(today.get("high"))
        low = _safe_float(today.get("low"))
        prev_close = _safe_float(prev.get("close"))
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    return _mean(trs) if trs else 0.0


def _last_n_closes(daily_series: List[Dict[str, Any]], n: int) -> List[float]:
    closes = [_safe_float(x.get("adjusted_close", x.get("close"))) for x in daily_series]
    return closes[-n:] if len(closes) >= n else closes


def _return_ratio(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return (a / b) - 1.0


def _parse_time_published(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    # alpha vantage often uses YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMM
    try:
        if len(ts) >= 15:  # e.g., 20240115T143000
            return datetime.strptime(ts[:15], "%Y%m%dT%H%M%S")
        if len(ts) >= 13:  # e.g., 20240115T1430
            return datetime.strptime(ts[:13], "%Y%m%dT%H%M")
        # date only fallback
        if len(ts) >= 8:
            return datetime.strptime(ts[:8], "%Y%m%d")
    except Exception:
        return None
    return None


def safe_parse_yyyymmddTHHMM(ts: Optional[str]) -> Optional[datetime]:
    return _parse_time_published(ts)


def compute_features_from_data(
    *,
    ticker: str,
    time_series_daily: Dict[str, Any],
    news: Optional[Dict[str, Any]] = None,
    insiders: Optional[Dict[str, Any]] = None,
    fundamentals_income: Optional[Dict[str, Any]] = None,
    fundamentals_balance: Optional[Dict[str, Any]] = None,
    fundamentals_cash: Optional[Dict[str, Any]] = None,
    gainers_losers: Optional[Dict[str, Any]] = None,
    lookback_days: int = 90,
) -> Dict[str, Any]:
    """Compose engineered features from raw tool responses.

    Returns a dict with simple numeric features. Missing data is handled gracefully.
    """
    features: Dict[str, Any] = {}
    # --- Price/volume based features ---
    series = time_series_daily.get("series", []) or []
    # Ensure ascending order by date key if present
    try:
        series = sorted(series, key=lambda x: x.get("date", ""))
    except Exception:
        pass

    closes = [_safe_float(x.get("adjusted_close", x.get("close"))) for x in series]
    highs = [_safe_float(x.get("high")) for x in series]
    lows = [_safe_float(x.get("low")) for x in series]
    vols = [float(x.get("volume", 0) or 0) for x in series]

    last_close = closes[-1] if closes else 0.0
    features["price_last"] = last_close
    # Returns
    if len(closes) >= 2:
        features["ret_1d"] = _return_ratio(closes[-1], closes[-2])
    if len(closes) >= 6:
        features["ret_5d"] = _return_ratio(closes[-1], closes[-6])
    if len(closes) >= 21:
        features["ret_20d"] = _return_ratio(closes[-1], closes[-21])

    # SMAs and crossovers
    features["sma_5"] = _sma(closes, 5)
    features["sma_20"] = _sma(closes, 20)
    features["sma_50"] = _sma(closes, 50)
    if last_close and features["sma_20"]:
        features["px_above_sma20"] = 1 if last_close > features["sma_20"] else 0
    if features["sma_20"] and features["sma_50"]:
        features["sma20_above_sma50"] = 1 if features["sma_20"] > features["sma_50"] else 0

    # Volatility: ATR14 as percent of price
    atr = _atr14(series)
    features["atr14"] = atr
    features["atr14_pct"] = (atr / last_close) if last_close else 0.0

    # BBANDS width
    features["bbands20_width"] = _bbands_width(closes, 20)

    # Volume ratio 5/20
    sma_vol_5 = _sma(vols, 5)
    sma_vol_20 = _sma(vols, 20)
    features["vol_5_over_20"] = (sma_vol_5 / sma_vol_20) if sma_vol_20 else 0.0

    # --- News Sentiment features ---
    if news and isinstance(news.get("articles"), list):
        articles: List[Dict[str, Any]] = news["articles"]
        now = datetime.utcnow()
        cutoff_7 = now - timedelta(days=7)
        cutoff_30 = now - timedelta(days=30)
        sentiments_7: List[float] = []
        sentiments_30: List[float] = []
        neg_7 = 0
        count_7 = 0
        count_30 = 0
        for a in articles:
            ts = safe_parse_yyyymmddTHHMM(a.get("time_published"))
            if not ts:
                continue
            score = _safe_float(a.get("overall_sentiment_score"), 0.0)
            label = (a.get("overall_sentiment_label") or "").lower()
            if ts >= cutoff_30:
                count_30 += 1
                sentiments_30.append(score)
                if ts >= cutoff_7:
                    count_7 += 1
                    sentiments_7.append(score)
                    if label in ("negative", "bearish"):
                        neg_7 += 1
        features["news_count_7"] = count_7
        features["news_count_30"] = count_30
        features["news_sent_mean_7"] = _mean(sentiments_7)
        features["news_sent_mean_30"] = _mean(sentiments_30)
        features["news_neg_count_7"] = neg_7

    # --- Insider transactions ---
    if insiders and isinstance(insiders.get("transactions"), list):
        txs: List[Dict[str, Any]] = insiders["transactions"]
        buy_cnt = 0
        sell_cnt = 0
        for t in txs:
            ttype = (t.get("type") or t.get("transactionType") or "").lower()
            if "buy" in ttype:
                buy_cnt += 1
            elif "sell" in ttype:
                sell_cnt += 1
        features["insider_buy_count"] = buy_cnt
        features["insider_sell_count"] = sell_cnt
        features["insider_net_count"] = buy_cnt - sell_cnt

    # --- Fundamentals (Income Statement) ---
    if fundamentals_income and isinstance(fundamentals_income.get("annualReports"), list):
        annual = fundamentals_income["annualReports"]
        if len(annual) >= 2:
            # Most recent first? Alpha Vantage usually returns most recent first
            latest = annual[0]
            prev = annual[1]
            rev_latest = _safe_float(latest.get("totalRevenue") or latest.get("revenue"))
            rev_prev = _safe_float(prev.get("totalRevenue") or prev.get("revenue"))
            op_inc_latest = _safe_float(latest.get("operatingIncome") or latest.get("operatingIncomeLoss"))
            features["rev_yoy"] = _return_ratio(rev_latest, rev_prev) if rev_prev else 0.0
            features["op_margin"] = (op_inc_latest / rev_latest) if rev_latest else 0.0

    # --- Market breadth ---
    if gainers_losers:
        gainers = gainers_losers.get("gainers") or []
        losers = gainers_losers.get("losers") or []
        features["breadth_g_minus_l"] = (len(gainers) - len(losers))

    return {
        "ticker": ticker.upper(),
        "features": features,
        "generated_at": datetime.utcnow().isoformat(),
        "lookback_days": lookback_days,
    }


