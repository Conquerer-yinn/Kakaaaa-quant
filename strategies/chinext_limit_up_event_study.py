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
    "事件日基准收盘价",
    "1日后日期",
    "1日后收盘价",
    "1日收益率(%)",
    "1日基准收益率(%)",
    "1日超额收益率(%)",
    "3日后日期",
    "3日后收盘价",
    "3日收益率(%)",
    "3日基准收益率(%)",
    "3日超额收益率(%)",
    "5日后日期",
    "5日后收盘价",
    "5日收益率(%)",
    "5日基准收益率(%)",
    "5日超额收益率(%)",
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
    "基准平均收益率(%)",
    "平均超额收益率(%)",
    "超额正收益比例(%)",
]


@dataclass(frozen=True)
class EventStudyResult:
    details: pd.DataFrame
    summary: pd.DataFrame
    candidate_event_count: int
    complete_sample_count: int
    skipped_incomplete_count: int
    skipped_missing_quote_count: int


def build_event_study(
    trade_dates: list[str],
    event_start_date: str,
    event_end_date: str,
    daily_by_date: dict[str, pd.DataFrame],
    limit_by_date: dict[str, pd.DataFrame],
) -> EventStudyResult:
    """计算创业板涨停事件后 1、3、5 个交易日的收盘表现。"""
    ordered_dates = sorted({str(value) for value in trade_dates})
    date_index = {trade_date: index for index, trade_date in enumerate(ordered_dates)}
    detail_rows: list[dict[str, object]] = []
    candidate_event_count = 0
    skipped_incomplete_count = 0
    skipped_missing_quote_count = 0

    for event_date in ordered_dates:
        if not event_start_date <= event_date <= event_end_date:
            continue

        events = _extract_chinext_limit_up_events(limit_by_date.get(event_date))
        candidate_event_count += len(events)
        if events.empty:
            continue

        event_index = date_index[event_date]
        if event_index + max(HORIZONS) >= len(ordered_dates):
            skipped_incomplete_count += len(events)
            continue

        future_dates = {
            horizon: ordered_dates[event_index + horizon] for horizon in HORIZONS
        }
        window_dates = ordered_dates[event_index + 1 : event_index + max(HORIZONS) + 1]
        event_quotes = _close_by_code(daily_by_date.get(event_date))
        future_quotes = {
            trade_date: _close_by_code(daily_by_date.get(trade_date))
            for trade_date in window_dates
        }

        for _, event in events.iterrows():
            ts_code = str(event["ts_code"])
            event_close = event_quotes.get(ts_code)
            closes = [future_quotes[trade_date].get(ts_code) for trade_date in window_dates]
            if not _valid_close(event_close) or any(not _valid_close(value) for value in closes):
                skipped_missing_quote_count += 1
                continue

            window_returns = [_return_percent(value, event_close) for value in closes]
            detail_rows.append(
                {
                    "事件日期": event_date,
                    "股票代码": ts_code,
                    "股票名称": _optional_text(event.get("name")),
                    "连板次数": _optional_int(event.get("limit_times")),
                    "事件日收盘价": _round_number(event_close),
                    "1日后日期": future_dates[1],
                    "1日后收盘价": _round_number(closes[0]),
                    "1日收益率(%)": window_returns[0],
                    "3日后日期": future_dates[3],
                    "3日后收盘价": _round_number(closes[2]),
                    "3日收益率(%)": window_returns[2],
                    "5日后日期": future_dates[5],
                    "5日后收盘价": _round_number(closes[4]),
                    "5日收益率(%)": window_returns[4],
                    "5日内最高收盘收益率(%)": max(window_returns),
                    "5日内最低收盘收益率(%)": min(window_returns),
                }
            )

    details = pd.DataFrame(detail_rows, columns=DETAIL_COLUMNS)
    summary = _build_summary(details)
    return EventStudyResult(
        details=details,
        summary=summary,
        candidate_event_count=candidate_event_count,
        complete_sample_count=len(details),
        skipped_incomplete_count=skipped_incomplete_count,
        skipped_missing_quote_count=skipped_missing_quote_count,
    )


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


def _build_summary(details: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        column = f"{horizon}日收益率(%)"
        values = pd.to_numeric(details[column], errors="coerce").dropna()
        if values.empty:
            rows.append(
                {
                    "观察周期": f"{horizon}日",
                    "样本数": 0,
                    "平均收益率(%)": None,
                    "中位数收益率(%)": None,
                    "正收益比例(%)": None,
                    "最大收益率(%)": None,
                    "最小收益率(%)": None,
                }
            )
            continue

        rows.append(
            {
                "观察周期": f"{horizon}日",
                "样本数": int(len(values)),
                "平均收益率(%)": round(float(values.mean()), 2),
                "中位数收益率(%)": round(float(values.median()), 2),
                "正收益比例(%)": round(float((values > 0).mean() * 100), 2),
                "最大收益率(%)": round(float(values.max()), 2),
                "最小收益率(%)": round(float(values.min()), 2),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def _return_percent(close: float, event_close: float) -> float:
    return round((float(close) / float(event_close) - 1) * 100, 2)


def _valid_close(value: object) -> bool:
    return value is not None and pd.notna(value) and float(value) > 0


def _round_number(value: float) -> float:
    return round(float(value), 4)


def _optional_text(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(float(value))
