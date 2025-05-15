from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from data_engine.tushare_api import TushareDataEngine
from market.indicators.sentiment_chinext import build_chinext_row
from market.indicators.sentiment_feedback import build_chinext_feedback_rows
from market.indicators.sentiment_height import build_height_observation_df
from market.indicators.sentiment_market import build_market_overview_row


DATE_COLUMN = "日期"
HEIGHT_LOOKBACK_TRADE_DAYS = 11
FEEDBACK_LOOKBACK_TRADE_DAYS = 2
CALENDAR_BUFFER_DAYS = 35


def build_post_close_snapshot_from_raw(trade_date: str) -> dict[str, Any]:
    """直接从原始数据层和指标计算层构造盘后卡片快照，不依赖 Excel 视图。"""
    engine = TushareDataEngine()
    calendar_start = _build_calendar_start(trade_date)
    trade_dates = engine.get_trade_calendar(calendar_start, trade_date)
    if not trade_dates or trade_date not in trade_dates:
        raise ValueError(f"Trade date {trade_date} is not available from trade calendar.")

    height_dates = trade_dates[-HEIGHT_LOOKBACK_TRADE_DAYS:]
    feedback_dates = trade_dates[-FEEDBACK_LOOKBACK_TRADE_DAYS:]
    # 盘后卡片不需要近 45 天全量抓数，只保留当前字段真正需要的最小日期集合。
    required_daily_dates = sorted(set(height_dates) | set(feedback_dates))
    required_full_dates = feedback_dates

    stock_basic_df = engine.get_stock_basic(fields="ts_code,name,list_date,market")

    daily_by_date = {}
    daily_basic_by_date = {}
    limit_by_date = {}
    stk_limit_by_date = {}
    market_rows = []
    all_daily_frames = []

    for current_date in required_daily_dates:
        daily_df = engine.get_daily_quotes(current_date)
        daily_by_date[current_date] = daily_df.copy()
        all_daily_frames.append(daily_df.copy())

        if current_date in required_full_dates:
            daily_basic_df = engine.get_daily_basic(current_date)
            limit_df = engine.get_limit_list(current_date)
            stk_limit_df = engine.get_stk_limit(current_date)

            daily_basic_by_date[current_date] = daily_basic_df.copy()
            limit_by_date[current_date] = limit_df.copy()
            stk_limit_by_date[current_date] = stk_limit_df.copy()
            market_rows.append(build_market_overview_row(current_date, daily_df, limit_df, stk_limit_df))

    market_df = pd.DataFrame(market_rows)
    if market_df.empty:
        raise ValueError(f"No market data collected for {trade_date}.")

    market_lookup = market_df.set_index(DATE_COLUMN)["总成交额(亿元)"].to_dict()
    chinext_rows = []
    chinext_samples = {}
    for current_date in feedback_dates:
        row, samples = build_chinext_row(
            trade_date=current_date,
            daily_df=daily_by_date.get(current_date),
            daily_basic_df=daily_basic_by_date.get(current_date),
            limit_df=limit_by_date.get(current_date),
            stk_limit_df=stk_limit_by_date.get(current_date),
            total_amount=market_lookup.get(current_date, 0),
        )
        chinext_rows.append(row)
        chinext_samples[current_date] = samples

    all_daily_df = pd.concat(all_daily_frames, ignore_index=True) if all_daily_frames else pd.DataFrame()
    height_df = build_height_observation_df(
        all_daily_df=all_daily_df,
        stock_basic_df=stock_basic_df,
        trade_dates=[trade_date],
        market_overview_df=market_df[market_df[DATE_COLUMN].astype(str) == str(trade_date)],
    )
    feedback_df = build_chinext_feedback_rows(feedback_dates, daily_by_date, chinext_samples)
    chinext_df = pd.DataFrame(chinext_rows).merge(feedback_df, on=DATE_COLUMN, how="left")

    latest_market = _pick_row(market_df, trade_date)
    latest_height = _pick_row(height_df, trade_date)
    latest_chinext = _pick_row(chinext_df, trade_date)

    snapshot = {
        "date": _to_text(latest_market.get("日期")),
        "all_height_stock": _to_text(latest_height.get("全市场高度个股")),
        "all_height_value": _to_number(latest_height.get("全市场近十日高度(%)")),
        "main_height_stock": _to_text(latest_height.get("主板高度个股")),
        "main_height_value": _to_number(latest_height.get("主板近十日高度(%)")),
        "chinext_height_stock": _to_text(latest_height.get("创业板高度个股")),
        "chinext_height_value": _to_number(latest_height.get("创业板近十日高度(%)")),
        "highest_streak": _to_number(latest_market.get("最高连板"), digits=0),
        "highest_streak_stock": _to_text(latest_market.get("最高连板个股")),
        "total_turnover": _to_number(latest_market.get("总成交额(亿元)")),
        "up_count": _to_number(latest_market.get("上涨家数"), digits=0),
        "down_count": _to_number(latest_market.get("下跌家数"), digits=0),
        "limit_up_count": _to_number(latest_market.get("涨停数"), digits=0),
        "limit_down_count": _to_number(latest_market.get("跌停数"), digits=0),
        "broken_limit_count": _to_number(latest_market.get("炸板数"), digits=0),
        "large_retrace_count": _to_number(latest_market.get("大回撤数"), digits=0),
        "chinext_turnover_ratio": _to_number(latest_chinext.get("创业板成交额占全市场比重(%)")),
        "chinext_limit_up_count": _to_number(latest_chinext.get("创业板涨停数"), digits=0),
        "chinext_broken_limit_count": _to_number(latest_chinext.get("创业板炸板数"), digits=0),
        "chinext_large_retrace_count": _to_number(latest_chinext.get("创业板大回撤数"), digits=0),
        "chinext_highest_streak": _to_number(latest_chinext.get("创业板连板高度"), digits=0),
        "chinext_highest_streak_stock": _to_text(latest_chinext.get("创业板最高板个股")),
        "prev_core_stock": _to_text(latest_chinext.get("昨日创业板核心股")),
        "prev_core_next_close_pct": _to_number(latest_chinext.get("昨日创业板核心股次日收盘涨幅(%)")),
        "prev_limit_up_next_close_pct": _to_number(latest_chinext.get("昨日创业板涨停股次日收盘溢价(%)")),
    }
    return snapshot


def _build_calendar_start(trade_date: str) -> str:
    start_dt = datetime.strptime(trade_date, "%Y%m%d")
    return (start_dt - timedelta(days=CALENDAR_BUFFER_DAYS)).strftime("%Y%m%d")


def _pick_row(df: pd.DataFrame, trade_date: str) -> pd.Series:
    if df is None or df.empty or DATE_COLUMN not in df.columns:
        raise ValueError(f"Missing data for {trade_date}.")
    row_df = df[df[DATE_COLUMN].astype(str) == str(trade_date)]
    if row_df.empty:
        raise ValueError(f"Trade date {trade_date} not found in computed snapshot.")
    return row_df.iloc[-1]


def _to_text(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def _to_number(value: Any, digits: int = 2) -> float | int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if digits == 0:
        return int(round(number))
    return round(number, digits)
