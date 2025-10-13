"""策略层公共工具。

只放多个策略真正共用的小函数，避免变成大杂烩。
"""
from __future__ import annotations

import pandas as pd


def filter_limit_up(limit_df) -> pd.DataFrame:
    """取出涨停（U）记录，并把 limit_times 转成数值列。"""
    if limit_df is None or limit_df.empty:
        return pd.DataFrame(columns=["ts_code", "name", "limit", "limit_times"])

    limit_up = limit_df[limit_df["limit"] == "U"].copy()
    limit_up["limit_times"] = pd.to_numeric(limit_up.get("limit_times"), errors="coerce").fillna(0)
    return limit_up


def coerce_numeric(df, columns) -> pd.DataFrame:
    """把指定列统一转为数值，非法值转 NaN。"""
    frame = df.copy()
    for column in columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame
