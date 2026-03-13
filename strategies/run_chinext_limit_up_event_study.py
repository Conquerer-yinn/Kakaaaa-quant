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
from strategies.chinext_limit_up_event_study import build_event_study, classify_market_regime
from strategies.chinext_limit_up_workbook import (
    STRATEGY_RESULTS_DIR,
    write_event_study_workbook,
)


DEFAULT_LOOKBACK_DAYS = 120
FUTURE_CALENDAR_BUFFER_DAYS = 14
MAX_FUTURE_CALENDAR_BUFFER_DAYS = 56
REQUIRED_FUTURE_TRADING_DAYS = 5
BENCHMARK_CODE = "399006.SZ"


def normalize_ymd(value: object) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")

    text = str(value).strip()
    if text.isdigit() and len(text) == 8:
        try:
            datetime.strptime(text, "%Y%m%d")
        except ValueError as exc:
            raise ValueError(f"无法识别日期: {value}") from exc
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


def build_fetch_end(
    end_date: str,
    buffer_days: int = FUTURE_CALENDAR_BUFFER_DAYS,
) -> str:
    return (
        datetime.strptime(end_date, "%Y%m%d")
        + timedelta(days=buffer_days)
    ).strftime("%Y%m%d")


def load_trade_calendar_with_horizon(
    engine: TushareDataEngine,
    start_date: str,
    end_date: str,
) -> list[str]:
    buffer_days = FUTURE_CALENDAR_BUFFER_DAYS
    while buffer_days <= MAX_FUTURE_CALENDAR_BUFFER_DAYS:
        fetch_end = build_fetch_end(end_date, buffer_days=buffer_days)
        trade_dates = sorted(set(engine.get_trade_calendar(start_date, fetch_end)))
        future_dates = [value for value in trade_dates if value > end_date]
        if len(future_dates) >= REQUIRED_FUTURE_TRADING_DAYS:
            return trade_dates
        buffer_days *= 2

    raise ValueError(
        f"无法在 {MAX_FUTURE_CALENDAR_BUFFER_DAYS} 个自然日内取得"
        f"事件结束日后的 {REQUIRED_FUTURE_TRADING_DAYS} 个交易日。"
    )


def run_chinext_limit_up_event_study(
    start_date: object = None,
    end_date: object = None,
    base_dir: str = STRATEGY_RESULTS_DIR,
    engine: TushareDataEngine | None = None,
) -> str:
    resolved_start, resolved_end = resolve_study_range(start_date, end_date)
    data_engine = engine or TushareDataEngine()
    trade_dates = load_trade_calendar_with_horizon(
        engine=data_engine,
        start_date=resolved_start,
        end_date=resolved_end,
    )
    if not trade_dates:
        raise ValueError(f"{resolved_start} 至 {resolved_end} 没有可用交易日。")

    stock_basic_df = data_engine.get_stock_basic(
        fields="ts_code,name,list_date,market"
    )
    benchmark_df = data_engine.get_index_daily(
        BENCHMARK_CODE,
        start_date=resolved_start,
        end_date=trade_dates[-1],
    )
    benchmark_close_by_date = _benchmark_close_by_date(benchmark_df)
    daily_by_date = {}
    limit_by_date = {}
    market_regime_by_date = {}
    for trade_date in trade_dates:
        print(f"加载事件研究行情 {trade_date} ...")
        daily_by_date[trade_date] = data_engine.get_daily_quotes(trade_date)
        if resolved_start <= trade_date <= resolved_end:
            limit_df = data_engine.get_limit_list(trade_date)
            limit_by_date[trade_date] = limit_df
            market_regime_by_date[trade_date] = _market_regime_from_limit_frame(limit_df)

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


def parse_args():
    parser = argparse.ArgumentParser(description="研究创业板涨停事件后 1、3、5 日表现。")
    parser.add_argument("--start-date", default=None, help="YYYYMMDD，默认回看 120 个自然日。")
    parser.add_argument("--end-date", default=None, help="YYYYMMDD，默认今天。")
    parser.add_argument("--output-dir", default=STRATEGY_RESULTS_DIR, help="研究工作簿输出目录。")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_chinext_limit_up_event_study(
        start_date=args.start_date,
        end_date=args.end_date,
        base_dir=args.output_dir,
    )
