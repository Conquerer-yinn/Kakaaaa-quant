"""示例策略：涨停放量样本筛选。

核心逻辑保持纯函数：输入行情 DataFrame，输出样本 DataFrame。
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

RESULT_COLUMNS = ["日期", "ts_code", "名称", "连板数", "成交额(亿元)"]


@dataclass(frozen=True)
class ExampleStrategyParams:
    min_amount_yi: float = 5.0
    min_limit_times: int = 1


def screen_limit_up_samples(trade_date, daily_df, limit_df, params=None) -> pd.DataFrame:
    """筛选当日涨停且成交额达标的样本。"""
    params = params or ExampleStrategyParams()
    if daily_df is None or daily_df.empty or limit_df is None or limit_df.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    limit_up = limit_df[limit_df["limit"] == "U"].copy()
    if limit_up.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    limit_up["limit_times"] = pd.to_numeric(limit_up.get("limit_times"), errors="coerce").fillna(0)
    limit_up = limit_up[limit_up["limit_times"] >= params.min_limit_times]

    merged = limit_up.merge(daily_df[["ts_code", "amount"]], on="ts_code", how="left")
    merged["成交额(亿元)"] = pd.to_numeric(merged["amount"], errors="coerce").fillna(0) / 1e5
    merged = merged[merged["成交额(亿元)"] >= params.min_amount_yi]
    if merged.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    result = pd.DataFrame(
        {
            "日期": str(trade_date),
            "ts_code": merged["ts_code"].astype(str),
            "名称": merged.get("name"),
            "连板数": merged["limit_times"].astype(int),
            "成交额(亿元)": merged["成交额(亿元)"].round(2),
        }
    )
    return result[RESULT_COLUMNS].sort_values("成交额(亿元)", ascending=False).reset_index(drop=True)
