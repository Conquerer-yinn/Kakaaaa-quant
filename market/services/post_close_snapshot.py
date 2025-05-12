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

    daily_df = engine.get_daily_quotes(trade_date)
    limit_df = engine.get_limit_list(trade_date)
    stk_limit_df = engine.get_stk_limit(trade_date)
    market_row = build_market_overview_row(trade_date, daily_df, limit_df, stk_limit_df)

    snapshot = {
        "date": str(market_row.get("日期")),
        "total_turnover": market_row.get("总成交额(亿元)"),
        "up_count": market_row.get("上涨家数"),
        "down_count": market_row.get("下跌家数"),
        "limit_up_count": market_row.get("涨停数"),
        "limit_down_count": market_row.get("跌停数"),
        "broken_limit_count": market_row.get("炸板数"),
        "large_retrace_count": market_row.get("大回撤数"),
        "highest_streak": market_row.get("最高连板"),
        "highest_streak_stock": market_row.get("最高连板个股"),
    }
    return snapshot


def _build_calendar_start(trade_date: str) -> str:
    start_dt = datetime.strptime(trade_date, "%Y%m%d")
    return (start_dt - timedelta(days=CALENDAR_BUFFER_DAYS)).strftime("%Y%m%d")


