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


