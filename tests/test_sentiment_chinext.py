"""创业板专区与次日反馈口径。"""
import pandas as pd

from market.indicators.sentiment_chinext import CHINEXT_COLUMNS, build_chinext_row, filter_chinext
from market.indicators.sentiment_feedback import CHINEXT_FEEDBACK_COLUMNS, build_chinext_feedback_rows


def _chinext_inputs():
    daily = pd.DataFrame(
        {
            "ts_code": ["300001.SZ", "300002.SZ", "600001.SH"],
            "amount": [1e5, 2e5, 5e5],
            "high": [11.0, 22.0, 30.0],
            "close": [11.0, 22.0, 30.0],
        }
    )
    daily_basic = pd.DataFrame({"ts_code": ["300001.SZ", "300002.SZ"], "turnover_rate": [5.0, 15.0]})
    limit = pd.DataFrame(
        {
            "ts_code": ["300001.SZ", "300002.SZ", "600001.SH"],
            "name": ["创一", "创二", "主板股"],
            "limit": ["U", "U", "U"],
            "limit_times": [3, 1, 5],
        }
    )
    stk_limit = pd.DataFrame({"ts_code": ["300001.SZ", "300002.SZ"], "up_limit": [11.0, 22.0]})
    return daily, daily_basic, limit, stk_limit


def test_filter_chinext_only_keeps_30x():
    daily, *_ = _chinext_inputs()
    filtered = filter_chinext(daily)
    assert filtered["ts_code"].tolist() == ["300001.SZ", "300002.SZ"]


def test_build_chinext_row_and_samples():
    daily, daily_basic, limit, stk_limit = _chinext_inputs()
    row, samples = build_chinext_row("20260105", daily, daily_basic, limit, stk_limit, total_amount=10.0)

    assert list(row.keys()) == CHINEXT_COLUMNS
    assert row["创业板成交额(亿元)"] == 3.0
    assert row["创业板成交额占全市场比重(%)"] == 30.0
    assert row["创业板涨停数"] == 2  # 主板涨停不计入
    assert row["创业板连板高度"] == 3
    assert row["创业板最高板个股"] == "创一"
    assert row["创业板最大成交涨停股"] == "创二"  # 成交额 2e5 更大
    assert samples["core_code"] == "300002.SZ"
    assert set(samples["limit_up_codes"]) == {"300001.SZ", "300002.SZ"}


def test_feedback_rows_next_day_premium():
    next_daily = pd.DataFrame(
        {
            "ts_code": ["300001.SZ"],
            "open": [11.0],
            "close": [12.0],
            "high": [12.5],
            "pre_close": [10.0],
        }
    )
    daily_by_date = {"20260106": next_daily}
    samples_by_date = {
        "20260105": {
            "limit_up_codes": ["300001.SZ"],
            "broken_codes": [],
            "core_code": "300001.SZ",
            "core_name": "创一",
        }
    }

    result = build_chinext_feedback_rows(["20260105", "20260106"], daily_by_date, samples_by_date)

    assert list(result.columns) == CHINEXT_FEEDBACK_COLUMNS
    day2 = result.iloc[1]
    assert day2["昨日创业板涨停样本数"] == 1
    assert day2["昨日创业板涨停股次日开盘溢价(%)"] == 10.0
    assert day2["昨日创业板涨停股次日收盘溢价(%)"] == 20.0
    assert day2["昨日创业板核心股"] == "创一"
    assert day2["昨日创业板核心股次日盘中最高涨幅(%)"] == 25.0
