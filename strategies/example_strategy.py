"""示例策略：涨停放量样本筛选（骨架版）。

先定义参数与输入输出约定，筛选逻辑下一步补。
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
    """筛选当日涨停样本。骨架版先返回空结果，保证接口稳定。"""
    return pd.DataFrame(columns=RESULT_COLUMNS)
