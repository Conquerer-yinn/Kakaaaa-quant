"""每日基础数据指标行。"""
import pandas as pd

from market.indicators.daily_basics import DAILY_BASICS_COLUMNS, build_daily_basics_row


def test_basic_row():
    daily = pd.DataFrame({"pct_chg": [5.0, -2.0, 1.0], "amount": [1e5, 2e5, 3e5]})
    limit = pd.DataFrame(
        {
            "limit": ["U", "U", "D"],
            "limit_times": [3, 1, 1],
            "name": ["龙一", "龙二", "跌停股"],
        }
    )

    row = build_daily_basics_row("20260102", daily, limit)

    assert list(row.keys()) == DAILY_BASICS_COLUMNS
    assert row["上涨家数"] == 2
    assert row["下跌家数"] == 1
    assert row["总成交额(亿元)"] == 6.0
    assert row["涨停数"] == 2
    assert row["跌停数"] == 1
    assert row["最高连板"] == 3
    assert row["最高连板个股"] == "龙一"


def test_empty_inputs_still_return_full_row():
    row = build_daily_basics_row("20260102", None, None)

    assert row["日期"] == "20260102"
    assert row["上涨家数"] == 0
    assert row["总成交额(亿元)"] == 0.0
    assert row["涨停数"] == 0
    assert row["最高连板"] == 0
    assert row["最高连板个股"] is None
