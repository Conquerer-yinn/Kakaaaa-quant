from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


HORIZONS = (1, 3, 5)
RECENT_LISTING_DAYS = 60
DETAIL_COLUMNS = [
    "事件日期",
    "股票代码",
    "股票名称",
    "连板次数",
    "连板阶段",
    "市场环境",
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
GROUP_SUMMARY_COLUMNS = [
    "分组维度",
    "分组",
    "观察周期",
    "样本数",
    "平均收益率(%)",
    "平均超额收益率(%)",
    "正收益比例(%)",
    "超额正收益比例(%)",
]
QUALITY_SUMMARY_COLUMNS = ["质量项目", "数量", "说明"]


@dataclass(frozen=True)
class EventStudyResult:
    details: pd.DataFrame
    summary: pd.DataFrame
    candidate_event_count: int
    complete_sample_count: int
    skipped_incomplete_count: int
    skipped_missing_quote_count: int
    missing_benchmark_count: int = 0
    excluded_st_count: int = 0
    excluded_recent_listing_count: int = 0
    missing_stock_basic_count: int = 0
    group_summary: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame(columns=GROUP_SUMMARY_COLUMNS)
    )
    quality_summary: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame(columns=QUALITY_SUMMARY_COLUMNS)
    )


def build_event_study(
    trade_dates: list[str],
    event_start_date: str,
    event_end_date: str,
    daily_by_date: dict[str, pd.DataFrame],
    limit_by_date: dict[str, pd.DataFrame],
    benchmark_close_by_date: dict[str, float] | None = None,
    stock_basic_df: pd.DataFrame | None = None,
    market_regime_by_date: dict[str, str] | None = None,
) -> EventStudyResult:
    """计算创业板涨停事件后 1、3、5 个交易日的收盘表现。"""
    ordered_dates = sorted({str(value) for value in trade_dates})
    date_index = {trade_date: index for index, trade_date in enumerate(ordered_dates)}
    detail_rows: list[dict[str, object]] = []
    candidate_event_count = 0
    skipped_incomplete_count = 0
    skipped_missing_quote_count = 0
    missing_benchmark_count = 0
    excluded_st_count = 0
    excluded_recent_listing_count = 0
    missing_stock_basic_count = 0
    benchmark_closes = benchmark_close_by_date or {}
    stock_info = _stock_info_by_code(stock_basic_df)
    market_regimes = market_regime_by_date or {}

    for event_date in ordered_dates:
        if not event_start_date <= event_date <= event_end_date:
            continue

        events = _extract_chinext_limit_up_events(limit_by_date.get(event_date))
        candidate_event_count += len(events)
        if events.empty:
            continue

        eligible_rows = []
        for _, event in events.iterrows():
            ts_code = str(event["ts_code"])
            info = stock_info.get(ts_code)
            event_name = _optional_text(event.get("name"))
            stock_name = _optional_text(info.get("name")) if info is not None else None
            if _is_st_name(event_name) or _is_st_name(stock_name):
                excluded_st_count += 1
                continue

            list_date = _normalized_date(info.get("list_date")) if info is not None else None
            if info is None or list_date is None:
                missing_stock_basic_count += 1
            elif _listing_age_days(event_date, list_date) < RECENT_LISTING_DAYS:
                excluded_recent_listing_count += 1
                continue
            eligible_rows.append(event)

        if not eligible_rows:
            continue
        eligible_events = pd.DataFrame(eligible_rows, columns=events.columns)

        event_index = date_index[event_date]
        if event_index + max(HORIZONS) >= len(ordered_dates):
            skipped_incomplete_count += len(eligible_events)
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

        for _, event in eligible_events.iterrows():
            ts_code = str(event["ts_code"])
            event_close = event_quotes.get(ts_code)
            closes = [future_quotes[trade_date].get(ts_code) for trade_date in window_dates]
            if not _valid_close(event_close) or any(not _valid_close(value) for value in closes):
                skipped_missing_quote_count += 1
                continue

            window_returns = [_return_percent(value, event_close) for value in closes]
            benchmark_event_close = benchmark_closes.get(event_date)
            benchmark_future_closes = [
                benchmark_closes.get(trade_date) for trade_date in window_dates
            ]
            has_complete_benchmark = _valid_close(benchmark_event_close) and all(
                _valid_close(value) for value in benchmark_future_closes
            )
            if has_complete_benchmark:
                benchmark_returns = [
                    _return_percent(value, benchmark_event_close)
                    for value in benchmark_future_closes
                ]
                excess_returns = [
                    round(stock_return - benchmark_return, 2)
                    for stock_return, benchmark_return in zip(window_returns, benchmark_returns)
                ]
            else:
                missing_benchmark_count += 1
                benchmark_returns = [None] * len(window_dates)
                excess_returns = [None] * len(window_dates)
            detail_rows.append(
                {
                    "事件日期": event_date,
                    "股票代码": ts_code,
                    "股票名称": _optional_text(event.get("name")),
                    "连板次数": _optional_int(event.get("limit_times")),
                    "连板阶段": _board_stage(event.get("limit_times")),
                    "市场环境": market_regimes.get(event_date, "未知"),
                    "事件日收盘价": _round_number(event_close),
                    "事件日基准收盘价": (
                        _round_number(benchmark_event_close)
                        if _valid_close(benchmark_event_close)
                        else None
                    ),
                    "1日后日期": future_dates[1],
                    "1日后收盘价": _round_number(closes[0]),
                    "1日收益率(%)": window_returns[0],
                    "1日基准收益率(%)": benchmark_returns[0],
                    "1日超额收益率(%)": excess_returns[0],
                    "3日后日期": future_dates[3],
                    "3日后收盘价": _round_number(closes[2]),
                    "3日收益率(%)": window_returns[2],
                    "3日基准收益率(%)": benchmark_returns[2],
                    "3日超额收益率(%)": excess_returns[2],
                    "5日后日期": future_dates[5],
                    "5日后收盘价": _round_number(closes[4]),
                    "5日收益率(%)": window_returns[4],
                    "5日基准收益率(%)": benchmark_returns[4],
                    "5日超额收益率(%)": excess_returns[4],
                    "5日内最高收盘收益率(%)": max(window_returns),
                    "5日内最低收盘收益率(%)": min(window_returns),
                }
            )

    details = pd.DataFrame(detail_rows, columns=DETAIL_COLUMNS)
    summary = _build_summary(details)
    group_summary = _build_group_summary(details)
    quality_summary = _build_quality_summary(
        candidate_event_count=candidate_event_count,
        excluded_st_count=excluded_st_count,
        excluded_recent_listing_count=excluded_recent_listing_count,
        missing_stock_basic_count=missing_stock_basic_count,
        skipped_incomplete_count=skipped_incomplete_count,
        skipped_missing_quote_count=skipped_missing_quote_count,
        missing_benchmark_count=missing_benchmark_count,
        complete_sample_count=len(details),
    )
    return EventStudyResult(
        details=details,
        summary=summary,
        candidate_event_count=candidate_event_count,
        complete_sample_count=len(details),
        skipped_incomplete_count=skipped_incomplete_count,
        skipped_missing_quote_count=skipped_missing_quote_count,
        missing_benchmark_count=missing_benchmark_count,
        excluded_st_count=excluded_st_count,
        excluded_recent_listing_count=excluded_recent_listing_count,
        missing_stock_basic_count=missing_stock_basic_count,
        group_summary=group_summary,
        quality_summary=quality_summary,
    )


def classify_market_regime(limit_up_count: int) -> str:
    if limit_up_count <= 30:
        return "弱"
    if limit_up_count <= 60:
        return "中"
    return "强"


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
        benchmark_values = pd.to_numeric(
            details[f"{horizon}日基准收益率(%)"], errors="coerce"
        ).dropna()
        excess_values = pd.to_numeric(
            details[f"{horizon}日超额收益率(%)"], errors="coerce"
        ).dropna()
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
                    "基准平均收益率(%)": None,
                    "平均超额收益率(%)": None,
                    "超额正收益比例(%)": None,
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
                "基准平均收益率(%)": _mean_or_none(benchmark_values),
                "平均超额收益率(%)": _mean_or_none(excess_values),
                "超额正收益比例(%)": _positive_rate_or_none(excess_values),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def _return_percent(close: float, event_close: float) -> float:
    return round((float(close) / float(event_close) - 1) * 100, 2)


def _mean_or_none(values: pd.Series) -> float | None:
    if values.empty:
        return None
    return round(float(values.mean()), 2)


def _positive_rate_or_none(values: pd.Series) -> float | None:
    if values.empty:
        return None
    return round(float((values > 0).mean() * 100), 2)


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
