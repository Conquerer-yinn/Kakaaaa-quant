from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from data_engine.tushare_api import TushareDataEngine


INDEX_CODES = "000001.SH,399001.SZ,399006.SZ"
INDEX_CODE_MAP = {
    "000001.SH": "sse_index_pct",
    "399001.SZ": "szse_index_pct",
    "399006.SZ": "chinext_index_pct",
}
TODAY_ONLY_ERROR = "盘中节奏卡片当前只支持当日实时推送。"


def build_intraday_snapshot_from_raw(trade_date: str | None = None) -> dict[str, Any]:
    """基于实时接口构造盘中节奏卡片快照。"""
    today = datetime.now().strftime("%Y%m%d")
    target_date = trade_date or today
    if target_date != today:
        raise ValueError(TODAY_ONLY_ERROR)

    engine = TushareDataEngine()
    notes = []
    try:
        index_df = engine.get_realtime_index_quotes(INDEX_CODES)
        if index_df is None or index_df.empty:
            raise ValueError("Failed to fetch realtime index quotes.")
        index_snapshot = _build_index_snapshot(index_df)
    except Exception as exc:
        # 实时指数权限不足时，先回退到当日日线口径，保证卡片能发。
        index_snapshot = _build_index_fallback(engine, target_date)
        notes.append(f"Tushare 实时指数接口受限，已回退到当日日线口径：{exc}")

    snapshot = {
        "date": today,
        "time_point": index_snapshot.get("time_point"),
        "sse_index_pct": index_snapshot.get("sse_index_pct"),
        "szse_index_pct": index_snapshot.get("szse_index_pct"),
        "chinext_index_pct": index_snapshot.get("chinext_index_pct"),
        "estimated_turnover_yi": None,
        "up_count": None,
        "down_count": None,
        "limit_up_count": None,
        "limit_down_count": None,
        "broken_limit_count": None,
        "highest_streak": None,
        "style_text": "",
        "risk_text": "",
        "availability_note": "",
    }

    market_note = _try_fill_realtime_market_snapshot(engine, snapshot)
    if market_note:
        notes.append(market_note)
    snapshot["style_text"] = build_intraday_style_text(snapshot)
    snapshot["risk_text"] = build_intraday_risk_text(snapshot)
    snapshot["availability_note"] = "；".join(notes) if notes else "当前盘中卡片已接入实时指数与尽力版市场宽度。"
    return snapshot


def _build_index_snapshot(index_df: pd.DataFrame) -> dict[str, Any]:
    snapshot = {"time_point": None}
    for ts_code, field_name in INDEX_CODE_MAP.items():
        row_df = index_df[index_df["ts_code"] == ts_code]
        if row_df.empty:
            snapshot[field_name] = None
            continue
        row = row_df.iloc[0]
        pre_close = row.get("pre_close")
        close = row.get("close")
        if pre_close in (None, 0) or close is None:
            snapshot[field_name] = None
        else:
            snapshot[field_name] = round((float(close) / float(pre_close) - 1) * 100, 2)

        trade_time = row.get("trade_time")
        if trade_time:
            snapshot["time_point"] = str(trade_time)[11:16]
    return snapshot


def _build_index_fallback(engine: TushareDataEngine, trade_date: str) -> dict[str, Any]:
    snapshot = {"time_point": datetime.now().strftime("%H:%M")}
    for ts_code, field_name in INDEX_CODE_MAP.items():
        daily_df = engine.get_index_daily(ts_code=ts_code, trade_date=trade_date)
        if daily_df is None or daily_df.empty:
            snapshot[field_name] = None
            continue
        row = daily_df.iloc[0]
        pre_close = row.get("pre_close")
        close = row.get("close")
        if pre_close in (None, 0) or close is None:
            snapshot[field_name] = None
        else:
            snapshot[field_name] = round((float(close) / float(pre_close) - 1) * 100, 2)
    return snapshot


def _try_fill_realtime_market_snapshot(engine: TushareDataEngine, snapshot: dict[str, Any]) -> str:
    # 实时全市场快照权限波动较大，这里按“能取到就补，取不到就降级”的思路处理。
    try:
        rt_df = engine.get_realtime_stock_quotes()
    except Exception as exc:
        return f"当前盘中卡片先用指数口径构造；全市场实时宽度未接入，原因：{exc}"

    if rt_df is None or rt_df.empty:
        return "当前盘中卡片先用指数口径构造；全市场实时宽度返回为空。"

    required_columns = {"ts_code", "close", "pre_close", "amount", "high"}
    if not required_columns.issubset(set(rt_df.columns)):
        return "当前盘中卡片先用指数口径构造；实时股票快照字段不足，未展开宽度统计。"

    today = snapshot["date"]
    stk_limit_df = engine.get_stk_limit(today)

    market_df = rt_df.copy()
    market_df["pct_chg"] = ((market_df["close"] / market_df["pre_close"]) - 1) * 100
    snapshot["up_count"] = int((market_df["pct_chg"] > 0).sum())
    snapshot["down_count"] = int((market_df["pct_chg"] < 0).sum())
    snapshot["estimated_turnover_yi"] = _estimate_full_day_turnover(market_df["amount"].sum())

    if stk_limit_df is not None and not stk_limit_df.empty:
        market_df = market_df.merge(
            stk_limit_df[["ts_code", "up_limit", "down_limit"]],
            on="ts_code",
            how="left",
        )
        market_df["is_limit_up"] = (market_df["up_limit"].notna()) & (market_df["close"] >= market_df["up_limit"] - 1e-6)
        market_df["is_limit_down"] = (market_df["down_limit"].notna()) & (market_df["close"] <= market_df["down_limit"] + 1e-6)
        market_df["is_broken_limit"] = (
            market_df["up_limit"].notna()
            & (market_df["high"] >= market_df["up_limit"] - 1e-6)
            & (market_df["close"] < market_df["up_limit"] - 1e-6)
        )
        snapshot["limit_up_count"] = int(market_df["is_limit_up"].sum())
        snapshot["limit_down_count"] = int(market_df["is_limit_down"].sum())
        snapshot["broken_limit_count"] = int(market_df["is_broken_limit"].sum())

    return "当前盘中卡片已接入实时指数；全市场实时宽度为尽力统计，若权限受限会自动降级。"


def _estimate_full_day_turnover(total_amount_k: Any) -> float | None:
    if total_amount_k is None:
        return None
    try:
        total_amount_k = float(total_amount_k)
    except (TypeError, ValueError):
        return None

    now = datetime.now()
    elapsed_ratio = _session_elapsed_ratio(now.hour * 60 + now.minute)
    if elapsed_ratio <= 0:
        return None
    return round((total_amount_k / 1e5) / elapsed_ratio, 2)


def _session_elapsed_ratio(total_minutes: int) -> float:
    # A 股交易时段按 240 分钟估算，午休不计。
    morning_start = 9 * 60 + 30
    morning_end = 11 * 60 + 30
    afternoon_start = 13 * 60
    afternoon_end = 15 * 60

    if total_minutes <= morning_start:
        return 0
    if total_minutes <= morning_end:
        return (total_minutes - morning_start) / 240
    if total_minutes <= afternoon_start:
        return 120 / 240
    if total_minutes <= afternoon_end:
        return (120 + total_minutes - afternoon_start) / 240
    return 1
