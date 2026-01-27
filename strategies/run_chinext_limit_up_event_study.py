from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta

import pandas as pd


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data_engine.tushare_api import TushareDataEngine
from strategies.chinext_limit_up_event_study import build_event_study
from strategies.chinext_limit_up_workbook import (
    STRATEGY_RESULTS_DIR,
    write_event_study_workbook,
)


DEFAULT_LOOKBACK_DAYS = 120
FUTURE_CALENDAR_BUFFER_DAYS = 14


def normalize_ymd(value: object) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")

    text = str(value).strip()
    if text.isdigit() and len(text) == 8:
        return text
    try:
        return pd.to_datetime(text, errors="raise").strftime("%Y%m%d")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"无法识别日期: {value}") from exc


def resolve_study_range(
    start_date: object = None,
    end_date: object = None,
) -> tuple[str, str]:
    resolved_end = normalize_ymd(end_date) or datetime.today().strftime("%Y%m%d")
    resolved_start = normalize_ymd(start_date)
    if resolved_start is None:
        resolved_start = (
            datetime.strptime(resolved_end, "%Y%m%d")
            - timedelta(days=DEFAULT_LOOKBACK_DAYS)
        ).strftime("%Y%m%d")
    if resolved_start > resolved_end:
        raise ValueError("开始日期不能晚于结束日期。")
    return resolved_start, resolved_end


def build_fetch_end(end_date: str) -> str:
    return (
        datetime.strptime(end_date, "%Y%m%d")
        + timedelta(days=FUTURE_CALENDAR_BUFFER_DAYS)
    ).strftime("%Y%m%d")


def run_chinext_limit_up_event_study(
    start_date: object = None,
    end_date: object = None,
    base_dir: str = STRATEGY_RESULTS_DIR,
    engine: TushareDataEngine | None = None,
) -> str:
    resolved_start, resolved_end = resolve_study_range(start_date, end_date)
    fetch_end = build_fetch_end(resolved_end)
    data_engine = engine or TushareDataEngine()
    trade_dates = data_engine.get_trade_calendar(resolved_start, fetch_end)
    if not trade_dates:
        raise ValueError(f"{resolved_start} 至 {fetch_end} 没有可用交易日。")

    daily_by_date = {}
    limit_by_date = {}
    for trade_date in trade_dates:
        print(f"加载事件研究行情 {trade_date} ...")
        daily_by_date[trade_date] = data_engine.get_daily_quotes(trade_date)
        if resolved_start <= trade_date <= resolved_end:
            limit_by_date[trade_date] = data_engine.get_limit_list(trade_date)

    result = build_event_study(
        trade_dates=trade_dates,
        event_start_date=resolved_start,
        event_end_date=resolved_end,
        daily_by_date=daily_by_date,
        limit_by_date=limit_by_date,
    )
    output_path = write_event_study_workbook(
        result=result,
        start_date=resolved_start,
        end_date=resolved_end,
        base_dir=base_dir,
    )
    print(
        f"事件研究完成：候选 {result.candidate_event_count}，"
        f"完整样本 {result.complete_sample_count}，输出 {output_path}"
    )
    return output_path


if __name__ == "__main__":
    args = parse_args()
    run_chinext_limit_up_event_study(
        start_date=args.start_date,
        end_date=args.end_date,
        base_dir=args.output_dir,
    )
