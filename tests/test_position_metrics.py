"""位置度量与相对中枢分类。"""
import pandas as pd

from market.indicators.position_metrics import (
    append_position_columns,
    build_latest_position_summary,
    build_position_frame,
)


def test_position_frame_high_position():
    series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    frame = build_position_frame(series)

    last = frame.iloc[-1]
    assert last["近期低点"] == 1
    assert last["近期高点"] == 10
    assert last["位置"] == "偏高"
    assert last["相对中枢"] == "强于中枢"


def test_position_frame_flat_series_is_neutral():
    frame = build_position_frame(pd.Series([5, 5, 5]))
    last = frame.iloc[-1]
    assert last["位置"] == "中位"
    assert last["相对中枢"] == "接近中枢"


def test_append_position_columns():
    df = pd.DataFrame({"日期": ["d1", "d2"], "涨停数": [10, 80]})
    result = append_position_columns(df, ["涨停数", "不存在的列"])

    assert "涨停数位置" in result.columns
    assert "涨停数相对中枢" in result.columns
    assert "不存在的列位置" not in result.columns
    assert result.loc[1, "涨停数位置"] == "偏高"


def test_latest_position_summary():
    df = pd.DataFrame({"涨停数": [10, 40, 80]})
    rows = build_latest_position_summary("总市场", df, ["涨停数"])

    assert len(rows) == 1
    summary = rows[0]
    assert summary["模块"] == "总市场"
    assert summary["指标"] == "涨停数"
    assert summary["最新值"] == 80
    assert summary["近期低点"] == 10
    assert summary["近期高点"] == 80
