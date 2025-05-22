from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from data_engine.tushare_api import TushareDataEngine


INDEX_CODES = {
    "sse": "000001.SH",
    "szse": "399001.SZ",
    "chinext": "399006.SZ",
}
CALENDAR_BUFFER_DAYS = 20



def build_auction_snapshot_from_raw(trade_date: str) -> dict[str, Any]:
    """基于竞价结果和最小辅助表构造竞价卡片快照。"""
    engine = TushareDataEngine()
    trade_dates = engine.get_trade_calendar(_build_calendar_start(trade_date), trade_date)
    if trade_date not in trade_dates:
        raise ValueError(f"Trade date {trade_date} is not available from trade calendar.")
    if len(trade_dates) < 2:
        raise ValueError(f"Not enough trade dates to build auction snapshot for {trade_date}.")

    previous_trade_date = trade_dates[-2]
    auction_df = engine.get_stock_open_auction(trade_date)
    previous_daily_df = engine.get_daily_quotes(previous_trade_date)
    stk_limit_df = engine.get_stk_limit(trade_date)
    stock_basic_df = engine.get_stock_basic(fields="ts_code,name")

    merged_df = _build_auction_market_df(auction_df, previous_daily_df, stk_limit_df, stock_basic_df)
    index_snapshot = _build_index_open_snapshot(engine, trade_date)

    snapshot = {
        "date": trade_date,
        "time_point": "09:25",
        "sse_index_pct": index_snapshot.get("sse_index_pct"),
        "szse_index_pct": index_snapshot.get("szse_index_pct"),
        "chinext_index_pct": index_snapshot.get("chinext_index_pct"),
        "auction_turnover_yi": _to_number(merged_df["amount"].sum() / 1e8 if not merged_df.empty else 0),
        "up_count": int((merged_df["auction_pct"] > 0).sum()) if not merged_df.empty else 0,
        "down_count": int((merged_df["auction_pct"] < 0).sum()) if not merged_df.empty else 0,
        "limit_up_count": int(merged_df["is_limit_up"].sum()) if not merged_df.empty else 0,
        "limit_down_count": int(merged_df["is_limit_down"].sum()) if not merged_df.empty else 0,
        "top_turnover_list": _format_rank_list(merged_df, "amount", percent_column="auction_pct"),
        "limit_up_list": _format_rank_list(
            merged_df[merged_df["is_limit_up"]].copy(),
            "amount",
            percent_column="auction_pct",
        ),
        "limit_down_list": _format_rank_list(
            merged_df[merged_df["is_limit_down"]].copy(),
            "amount",
            percent_column="auction_pct",
        ),
        "summary_text": "",
        "availability_note": "当前先使用 Tushare 开盘集合竞价结果。预计量能、委买额前排等字段待后续补竞价明细源。",
    }
    snapshot["summary_text"] = build_auction_summary_text(snapshot)
    return snapshot



