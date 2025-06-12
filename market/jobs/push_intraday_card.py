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
from market.push_views import build_intraday_card
from market.services import build_intraday_snapshot_from_raw


def default_trade_date() -> str:
    return datetime.today().strftime("%Y%m%d")


def parse_args():
    parser = argparse.ArgumentParser(description="Build and send the intraday Feishu card.")
    parser.add_argument("--trade-date", default=default_trade_date(), help="交易日，格式 YYYYMMDD。当前只支持当日。")
    parser.add_argument("--webhook", default=None, help="飞书机器人 webhook，不传时读取 FEISHU_BOT_WEBHOOK。")
    parser.add_argument("--dry-run", action="store_true", help="只打印卡片 JSON，不实际发送。")
    return parser.parse_args()


def run_intraday_card(trade_date: str, webhook: str | None = None, dry_run: bool = False):
    # 盘中卡片直接走实时原始数据层，不依赖 Excel。
    snapshot = build_intraday_snapshot_from_raw(trade_date=trade_date)
    card = build_intraday_card(snapshot)

    if dry_run:
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return {"success": True, "mode": "dry-run", "date": snapshot.get("date")}

    resolved_webhook = webhook or FEISHU_BOT_WEBHOOK
    if not resolved_webhook:
        raise ValueError("Missing Feishu webhook. Pass --webhook or set FEISHU_BOT_WEBHOOK.")

    notifier = FeishuNotifier(resolved_webhook)
    response = notifier.send_interactive_card(card)
    print(f"Sent intraday card for {snapshot.get('date')} {snapshot.get('time_point')}.")
    return {"success": True, "mode": "send", "date": snapshot.get("date"), "response": response}


if __name__ == "__main__":
    args = parse_args()
    run_intraday_card(trade_date=args.trade_date, webhook=args.webhook, dry_run=args.dry_run)
