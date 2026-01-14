from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


HORIZONS = (1, 3, 5)
DETAIL_COLUMNS = [
    "事件日期",
    "股票代码",
    "股票名称",
    "连板次数",
    "事件日收盘价",
    "1日后日期",
    "1日后收盘价",
    "1日收益率(%)",
    "3日后日期",
    "3日后收盘价",
    "3日收益率(%)",
    "5日后日期",
    "5日后收盘价",
    "5日收益率(%)",
    "5日内最高收盘收益率(%)",
    "5日内最低收盘收益率(%)",
]
SUMMARY_COLUMNS = [
    "观察周期",
    "样本数",
    "平均收益率(%)",
    "中位数收益率(%)",
    "正收益比例(%)",
    "最大收益率(%)",
    "最小收益率(%)",
]


@dataclass(frozen=True)
class EventStudyResult:
    details: pd.DataFrame
    summary: pd.DataFrame
    candidate_event_count: int
    complete_sample_count: int
    skipped_incomplete_count: int
    skipped_missing_quote_count: int


