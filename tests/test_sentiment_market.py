"""总市场情绪口径：涨跌停、炸板、大回撤。"""
import pandas as pd

from market.indicators.sentiment_market import (
    MARKET_OVERVIEW_COLUMNS,
    build_market_overview_row,
    count_broken_limit,
    count_large_retrace,
)


def _daily():
    return pd.DataFrame(
        {
            "ts_code": ["A", "B", "C"],
            "pct_chg": [10.0, -5.0, 2.0],
            "amount": [1e5, 1e5, 1e5],
            "high": [11.0, 100.0, 50.0],
            "close": [11.0, 92.0, 49.9],
        }
    )


def _limit():
    return pd.DataFrame(
        {
            "ts_code": ["A", "D", "E"],
            "name": ["龙头", "跌停股", "炸板股"],
            "limit": ["U", "D", "Z"],
            "limit_times": [2, 1, 1],
        }
    )


def _stk_limit():
    return pd.DataFrame({"ts_code": ["A", "B", "C"], "up_limit": [11.0, 105.0, 55.0], "down_limit": [9.0, 85.0, 45.0]})


def test_market_overview_row():
    row = build_market_overview_row("20260102", _daily(), _limit(), _stk_limit())

    assert list(row.keys()) == MARKET_OVERVIEW_COLUMNS
    assert row["上涨家数"] == 2
    assert row["下跌家数"] == 1
    assert row["总成交额(亿元)"] == 3.0
    assert row["涨停数"] == 1
    assert row["跌停数"] == 1
    assert row["炸板数"] == 1  # 优先采用 Tushare 炸板口径（Z 记录）
    assert row["大回撤数"] == 1  # B: (100-92)/100 = 8% >= 7%
    assert row["最高连板"] == 2
    assert row["最高连板个股"] == "龙头"


def test_broken_limit_price_fallback():
    daily = pd.DataFrame({"ts_code": ["X"], "high": [11.0], "close": [10.5]})
    stk_limit = pd.DataFrame({"ts_code": ["X"], "up_limit": [11.0], "down_limit": [9.0]})

    assert count_broken_limit(daily, stk_limit, None) == 1
    assert count_broken_limit(daily.iloc[0:0], stk_limit, None) == 0


def test_large_retrace_threshold():
    daily = pd.DataFrame({"high": [100.0, 100.0], "close": [93.1, 92.9]})
    # 6.9% 不算，7.1% 算
    assert count_large_retrace(daily) == 1
