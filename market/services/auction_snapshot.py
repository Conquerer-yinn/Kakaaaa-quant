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



def build_auction_summary_text(snapshot: dict[str, Any]) -> str:
    """生成竞价卡片的一句话总结。"""
    up_count = snapshot.get("up_count") or 0
    down_count = snapshot.get("down_count") or 0
    limit_up_count = snapshot.get("limit_up_count") or 0
    limit_down_count = snapshot.get("limit_down_count") or 0
    chinext_index_pct = snapshot.get("chinext_index_pct")

    parts = []
    if up_count > down_count * 1.2:
        parts.append("竞价整体偏强")
    elif down_count > up_count * 1.2:
        parts.append("竞价整体偏弱")
    else:
        parts.append("竞价整体中性")

    if limit_up_count >= 15:
        parts.append("涨停前排活跃")
    elif limit_up_count <= 3:
        parts.append("竞价封板偏少")

    if limit_down_count >= 5:
        parts.append("跌停端有压力")

    if chinext_index_pct is not None:
        if chinext_index_pct >= 1:
            parts.append("创业板竞价偏强")
        elif chinext_index_pct <= -1:
            parts.append("创业板竞价承压")

    return "，".join(parts)



def _build_auction_market_df(
    auction_df: pd.DataFrame,
    previous_daily_df: pd.DataFrame,
    stk_limit_df: pd.DataFrame,
    stock_basic_df: pd.DataFrame,
) -> pd.DataFrame:
    if auction_df is None or auction_df.empty:
        # 竞价结果有时会为空，这里仍然返回带标准列的空表，避免上层继续取列时报 KeyError。
        return pd.DataFrame(
            columns=[
                "ts_code",
                "close",
                "amount",
                "prev_close",
                "name",
                "up_limit",
                "down_limit",
                "auction_pct",
                "is_limit_up",
                "is_limit_down",
            ]
        )

    merged_df = auction_df.copy()
    previous_daily_df = previous_daily_df[["ts_code", "close"]].rename(columns={"close": "prev_close"})
    merged_df = merged_df.merge(previous_daily_df, on="ts_code", how="left")
    merged_df = merged_df.merge(stock_basic_df[["ts_code", "name"]], on="ts_code", how="left")

    if stk_limit_df is not None and not stk_limit_df.empty:
        merged_df = merged_df.merge(
            stk_limit_df[["ts_code", "up_limit", "down_limit"]],
            on="ts_code",
            how="left",
        )
    else:
        merged_df["up_limit"] = None
        merged_df["down_limit"] = None

    merged_df["auction_pct"] = ((merged_df["close"] / merged_df["prev_close"]) - 1) * 100
    merged_df["is_limit_up"] = (merged_df["up_limit"].notna()) & (merged_df["close"] >= merged_df["up_limit"] - 1e-6)
    merged_df["is_limit_down"] = (merged_df["down_limit"].notna()) & (merged_df["close"] <= merged_df["down_limit"] + 1e-6)
    return merged_df



def _build_index_open_snapshot(engine: TushareDataEngine, trade_date: str) -> dict[str, float | None]:
    snapshot = {}
    for key, ts_code in INDEX_CODES.items():
        daily_df = engine.get_index_daily(ts_code=ts_code, trade_date=trade_date)
        if daily_df is None or daily_df.empty:
            snapshot[f"{key}_index_pct"] = None
            continue
        row = daily_df.iloc[0]
        pre_close = row.get("pre_close")
        open_price = row.get("open")
        if pre_close in (None, 0) or open_price is None:
            snapshot[f"{key}_index_pct"] = None
            continue
        snapshot[f"{key}_index_pct"] = _to_number((float(open_price) / float(pre_close) - 1) * 100)
    return snapshot



def _format_rank_list(df: pd.DataFrame, sort_column: str, percent_column: str | None = None, top_n: int = 5) -> str:
    if df is None or df.empty or sort_column not in df.columns:
        return "-"

    top_df = df.sort_values(sort_column, ascending=False).head(top_n)
    items = []
    for _, row in top_df.iterrows():
        name = row.get("name") or row.get("ts_code") or "-"
        amount = _to_number((row.get(sort_column) or 0) / 1e8)
        if percent_column and pd.notna(row.get(percent_column)):
            pct = _to_number(row.get(percent_column))
            items.append(f"{name} {amount:.2f}亿 {pct:+.2f}%")
        else:
            items.append(f"{name} {amount:.2f}亿")
    return "；".join(items) if items else "-"



