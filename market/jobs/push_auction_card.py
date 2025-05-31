import argparse
import json
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.config import FEISHU_BOT_WEBHOOK
from common.notifier import FeishuNotifier
from market.push_views import build_auction_card
from market.services import build_auction_snapshot_from_raw


def default_trade_date() -> str:
    return datetime.today().strftime("%Y%m%d")


def parse_args():
    parser = argparse.ArgumentParser(description="Build and send the auction Feishu card.")
    parser.add_argument("--trade-date", default=default_trade_date(), help="交易日，格式 YYYYMMDD。")
    parser.add_argument("--dry-run", action="store_true", help="只打印卡片 JSON，不实际发送。")
    return parser.parse_args()


def run_auction_card(trade_date: str, dry_run: bool = False):
    # 竞价卡片直接基于原始竞价结果构造，不依赖 Excel。
    snapshot = build_auction_snapshot_from_raw(trade_date)
    card = build_auction_card(snapshot)

    if dry_run:
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return {"success": True, "mode": "dry-run", "date": snapshot.get("date")}

    if not FEISHU_BOT_WEBHOOK:
        raise ValueError("Missing Feishu webhook. Set FEISHU_BOT_WEBHOOK first.")

    notifier = FeishuNotifier(FEISHU_BOT_WEBHOOK)
    response = notifier.send_interactive_card(card)
    print(f"Sent auction card for {snapshot.get('date')}.")
    return {"success": True, "mode": "send", "date": snapshot.get("date"), "response": response}


if __name__ == "__main__":
    args = parse_args()
    run_auction_card(trade_date=args.trade_date, dry_run=args.dry_run)
