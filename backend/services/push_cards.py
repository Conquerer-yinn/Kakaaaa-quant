from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from backend.schemas.frontend import PushCardActionResponse, PushCardItemResponse, PushCardListResponse
from common.config import FEISHU_BOT_WEBHOOK
from common.notifier import FeishuNotifier
from data_engine.tushare_api import TushareDataEngine
from market.push_views import build_auction_card, build_intraday_card, build_post_close_card, enrich_post_close_snapshot
from market.services import (
    build_auction_snapshot_from_raw,
    build_intraday_snapshot_from_raw,
    build_post_close_snapshot_from_raw,
)


CARD_META = {
    "post-close": {"title": "盘后复盘", "status": "stable", "status_label": "已稳定可用"},
    "auction": {"title": "竞价观察", "status": "v1", "status_label": "第一版可用"},
    "intraday": {"title": "盘中节奏", "status": "experimental", "status_label": "实验性 / 受实时权限影响"},
}



def list_push_cards() -> PushCardListResponse:
    """推送页首屏一次性拿到三类卡片，前端可以直接渲染。"""
    cards = [
        build_push_card_preview("post-close"),
        build_push_card_preview("auction"),
        build_push_card_preview("intraday"),
    ]
    return PushCardListResponse(success=any(card.success for card in cards), cards=cards, error_message=None)



def build_push_card_preview(card_type: str, trade_date: str | None = None) -> PushCardItemResponse:
    meta = CARD_META[card_type]
    try:
        snapshot, card_payload = _build_snapshot_and_card(card_type, trade_date)
        return PushCardItemResponse(
            success=True,
            card_type=card_type,
            title=meta["title"],
            status=meta["status"],
            status_label=meta["status_label"],
            date=snapshot.get("date"),
            snapshot=snapshot,
            card_payload=card_payload,
            error_message=None,
        )
    except Exception as exc:
        return PushCardItemResponse(
            success=False,
            card_type=card_type,
            title=meta["title"],
            status=meta["status"],
            status_label=meta["status_label"],
            date=trade_date,
            snapshot={},
            card_payload=None,
            error_message=str(exc),
        )



def _build_snapshot_and_card(card_type: str, trade_date: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """统一封装三类卡片，避免路由层分别处理数据链和发送链。"""
    if card_type == "post-close":
        resolved_date = trade_date or _resolve_latest_trade_date()
        snapshot = build_post_close_snapshot_from_raw(resolved_date)
        snapshot = enrich_post_close_snapshot(snapshot)
        return snapshot, build_post_close_card(snapshot)

    if card_type == "auction":
        resolved_date = trade_date or _resolve_latest_trade_date()
        snapshot = build_auction_snapshot_from_raw(resolved_date)
        return snapshot, build_auction_card(snapshot)

    if card_type == "intraday":
        resolved_date = trade_date or datetime.now().strftime("%Y%m%d")
        snapshot = build_intraday_snapshot_from_raw(trade_date=resolved_date)
        return snapshot, build_intraday_card(snapshot)

    raise ValueError(f"Unsupported card type: {card_type}")



def _resolve_latest_trade_date() -> str:
    """盘后与竞价页面默认读最近一个交易日，而不是简单拿自然日。"""
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=20)).strftime("%Y%m%d")
    engine = TushareDataEngine()
    trade_dates = engine.get_trade_calendar(start_date, end_date)
    if not trade_dates:
        raise ValueError("Unable to resolve latest trade date from trade calendar.")
    return trade_dates[-1]
