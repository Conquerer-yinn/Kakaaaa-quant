"""十日高度观察：板块过滤与 ST / 次新剔除。"""
import pandas as pd

from market.indicators.sentiment_height import HEIGHT_OBSERVATION_COLUMNS, build_height_observation_df

DATES = [f"202601{day:02d}" for day in range(5, 16)]  # 11 个交易日


def _daily_rows(ts_code, closes):
    return [{"ts_code": ts_code, "trade_date": date, "close": close} for date, close in zip(DATES, closes)]


def _all_daily():
    rows = []
    rows += _daily_rows("600001.SH", [10] * 10 + [15])   # 十日涨幅 50%
    rows += _daily_rows("300500.SZ", [10] * 10 + [11])   # 十日涨幅 10%
    rows += _daily_rows("000003.SZ", [10] * 10 + [30])   # ST，应被剔除
    return pd.DataFrame(rows)


def _stock_basic():
    return pd.DataFrame(
        {
            "ts_code": ["600001.SH", "300500.SZ", "000003.SZ"],
            "name": ["主板龙", "创业龙", "ST雷股"],
            "list_date": ["20200101", "20200101", "20200101"],
        }
    )


def test_height_observation():
    market_overview = pd.DataFrame({"日期": [DATES[-1]], "最高连板": [4]})
    result = build_height_observation_df(_all_daily(), _stock_basic(), [DATES[-1]], market_overview)

    assert list(result.columns) == HEIGHT_OBSERVATION_COLUMNS
    assert len(result) == 1
    row = result.iloc[0]
    assert row["全市场高度个股"] == "主板龙"  # ST 剔除后 50% 最高
    assert row["全市场近十日高度(%)"] == 50.0
    assert row["主板高度个股"] == "主板龙"
    assert row["创业板高度个股"] == "创业龙"
    assert row["创业板近十日高度(%)"] == 10.0
    assert row["最高连板"] == 4


def test_empty_daily_returns_empty_frame():
    result = build_height_observation_df(pd.DataFrame(), _stock_basic(), [DATES[-1]], None)
    assert result.empty
    assert list(result.columns) == HEIGHT_OBSERVATION_COLUMNS
