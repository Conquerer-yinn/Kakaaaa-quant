"""连板样本研究：跟踪连板梯队的隔日表现。

第一版先把样本池建出来：当日连板数达到门槛的涨停股。
核心逻辑保持纯函数，方便离线测试。
"""
from __future__ import annotations

import pandas as pd

SAMPLE_COLUMNS = ["日期", "ts_code", "名称", "连板数"]


def build_follow_samples(trade_date, limit_df, min_streak: int = 2) -> pd.DataFrame:
    """从涨停名单里取出连板数达到门槛的样本。"""
    if limit_df is None or limit_df.empty:
        return pd.DataFrame(columns=SAMPLE_COLUMNS)

    limit_up = limit_df[limit_df["limit"] == "U"].copy()
    if limit_up.empty:
        return pd.DataFrame(columns=SAMPLE_COLUMNS)

    limit_up["limit_times"] = pd.to_numeric(limit_up.get("limit_times"), errors="coerce").fillna(0)
    samples = limit_up[limit_up["limit_times"] >= min_streak]
    if samples.empty:
        return pd.DataFrame(columns=SAMPLE_COLUMNS)

    return pd.DataFrame(
        {
            "日期": str(trade_date),
            "ts_code": samples["ts_code"].astype(str),
            "名称": samples.get("name"),
            "连板数": samples["limit_times"].astype(int),
        }
    )[SAMPLE_COLUMNS].sort_values("连板数", ascending=False).reset_index(drop=True)
