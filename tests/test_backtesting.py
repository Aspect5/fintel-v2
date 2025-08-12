from backend.tools.backtesting import walk_forward_backtest_from_series


def _gen_series(n=220, start_price=100.0, step=0.5):
    series = []
    price = start_price
    for i in range(n):
        open_p = price
        high = open_p * 1.01
        low = open_p * 0.99
        close = open_p + step  # slow drift up
        series.append({
            "date": f"2024-10-{(i%28)+1:02d}",
            "open": round(open_p, 4),
            "high": round(high, 4),
            "low": round(low, 4),
            "close": round(close, 4),
            "adjusted_close": round(close, 4),
            "volume": 500_000 + i * 100
        })
        price = close
    return series


def test_backtest_baseline_runs_and_returns_metrics():
    series = _gen_series()
    out = walk_forward_backtest_from_series(
        ticker='AAA',
        series=series,
        horizon_days=5,
        min_train_size=50,
        step=10,
    )
    assert 'metrics' in out
    m = out['metrics']
    assert 'accuracy' in m and 'auc' in m and 'brier' in m
    assert 'predictions' in out or 'feature_list' in out


