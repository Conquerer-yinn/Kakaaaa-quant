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


def _extract_chinext_limit_up_events(limit_df: pd.DataFrame | None) -> pd.DataFrame:
    if limit_df is None or limit_df.empty:
        return pd.DataFrame(columns=["ts_code", "name", "limit", "limit_times"])
    if "ts_code" not in limit_df.columns or "limit" not in limit_df.columns:
        return pd.DataFrame(columns=["ts_code", "name", "limit", "limit_times"])

    frame = limit_df.copy()
    for column in ("name", "limit_times"):
        if column not in frame.columns:
            frame[column] = None
    code_mask = frame["ts_code"].astype(str).str.startswith(("300", "301"))
    limit_mask = frame["limit"].astype(str).str.upper().eq("U")
    return frame.loc[code_mask & limit_mask, ["ts_code", "name", "limit", "limit_times"]]


def _close_by_code(daily_df: pd.DataFrame | None) -> dict[str, float]:
    if daily_df is None or daily_df.empty:
        return {}
    if "ts_code" not in daily_df.columns or "close" not in daily_df.columns:
        return {}

    frame = daily_df[["ts_code", "close"]].copy()
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.dropna(subset=["ts_code", "close"])
    return {
        str(row["ts_code"]): float(row["close"])
        for _, row in frame.drop_duplicates("ts_code", keep="last").iterrows()
    }


