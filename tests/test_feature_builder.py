import math
from datetime import datetime, timedelta

from backend.tools.feature_builder import compute_features_from_data


def _gen_series(n=60, start_price=100.0, daily_ret=0.002):
    series = []
    price = start_price
    for i in range(n):
        open_p = price
        high = open_p * (1 + 0.01)
        low = open_p * (1 - 0.01)
        close = open_p * (1 + daily_ret)
        series.append({
            "date": f"2025-01-{(i%30)+1:02d}",
            "open": round(open_p, 4),
            "high": round(high, 4),
            "low": round(low, 4),
            "close": round(close, 4),
            "adjusted_close": round(close, 4),
            "volume": 1_000_000 + i * 1000,
        })
        price = close
    return series


def test_compute_features_basic():
    now = datetime.utcnow()
    def ts(d):
        return (now - timedelta(days=d)).strftime("%Y%m%dT%H%M%S")

    series = _gen_series(60)
    news = {
        "articles": [
            {
                "title": "Strong earnings",
                "time_published": ts(3),
                "overall_sentiment_score": 0.3,
                "overall_sentiment_label": "positive",
            },
            {
                "title": "Some risk",
                "time_published": ts(20),
                "overall_sentiment_score": -0.1,
                "overall_sentiment_label": "negative",
            },
        ]
    }
    insiders = {
        "transactions": [
            {"type": "Buy"},
            {"type": "Sell"},
            {"transactionType": "Buy"},
        ]
    }
    breadth = {"gainers": list(range(12)), "losers": list(range(8))}

    result = compute_features_from_data(
        ticker="AAA",
        time_series_daily={"series": series},
        news=news,
        insiders=insiders,
        fundamentals_income=None,
        fundamentals_balance=None,
        fundamentals_cash=None,
        gainers_losers=breadth,
        lookback_days=90,
    )

    feats = result.get("features", {})
    assert isinstance(feats, dict)
    # Check key features are present
    for key in [
        "ret_1d", "ret_5d", "ret_20d", "sma_5", "sma_20", "px_above_sma20",
        "atr14", "atr14_pct", "bbands20_width", "vol_5_over_20",
        "news_count_7", "news_count_30", "news_sent_mean_7", "news_sent_mean_30", "news_neg_count_7",
        "insider_buy_count", "insider_sell_count", "insider_net_count", "breadth_g_minus_l",
    ]:
        assert key in feats, f"missing feature: {key}"

    # Sanity checks
    assert feats["px_above_sma20"] in (0, 1)
    assert feats["insider_net_count"] == feats["insider_buy_count"] - feats["insider_sell_count"]
    assert feats["breadth_g_minus_l"] == 12 - 8


