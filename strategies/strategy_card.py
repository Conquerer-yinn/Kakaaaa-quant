"""策略运行结果的飞书摘要卡片。

一天的全部策略运行结果汇总成一张卡片，而不是每个策略各发一条。
"""
from __future__ import annotations

import os
import sys
from typing import Any

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.config import FEISHU_BOT_WEBHOOK
from common.notifier import FeishuNotifier


def build_strategy_summary_card(trade_date: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    """results: [{"name", "success", "output", "error"}, ...]"""
    ok_count = sum(1 for item in results if item.get("success"))
    lines = []
    for item in results:
        if item.get("success"):
            output = item.get("output") or "无新增样本"
            lines.append(f"✅ **{item['name']}**：{output}")
        else:
            lines.append(f"❌ **{item['name']}**：{item.get('error') or '未知错误'}")

    return {
        "config": {"wide_screen_mode": True, "enable_forward": True},
        "header": {
            "template": "purple",
            "title": {"tag": "plain_text", "content": f"{trade_date} 策略运行摘要"},
        },
        "elements": [
            {"tag": "markdown", "content": f"**运行结果：{ok_count}/{len(results)} 成功**"},
            {"tag": "markdown", "content": "\n".join(lines) or "今日没有启用的策略。"},
        ],
    }


def send_strategy_summary(trade_date: str, results: list[dict[str, Any]], webhook: str | None = None) -> dict:
    resolved_webhook = webhook or FEISHU_BOT_WEBHOOK
    if not resolved_webhook:
        raise ValueError("Missing Feishu webhook. Set FEISHU_BOT_WEBHOOK before sending strategy summary.")

    card = build_strategy_summary_card(trade_date, results)
    notifier = FeishuNotifier(resolved_webhook)
    return notifier.send_interactive_card(card)
