from __future__ import annotations

from typing import Any


def build_intraday_card(snapshot: dict[str, Any]) -> dict[str, Any]:
    """构造盘中节奏飞书卡片。"""
    title = f"{snapshot.get('date') or '-'} 盘中节奏卡片"
    return {
        "config": {"wide_screen_mode": True, "enable_forward": True},
        "header": {
            "template": "turquoise",
            "title": {"tag": "plain_text", "content": title},
        },
        "elements": [
            _section_header("指数节奏"),
            _fields([
                ("推送时点", snapshot.get("time_point") or "-"),
                ("上证涨幅", _fmt(snapshot.get("sse_index_pct"), suffix="%")),
                ("深成涨幅", _fmt(snapshot.get("szse_index_pct"), suffix="%")),
                ("创业板涨幅", _fmt(snapshot.get("chinext_index_pct"), suffix="%")),
            ]),
            _section_header("市场宽度"),
            _fields([
                ("预计成交额", _fmt(snapshot.get("estimated_turnover_yi"), suffix=" 亿元")),
                ("上涨 / 下跌", f"{_fmt(snapshot.get('up_count'), digits=0)} / {_fmt(snapshot.get('down_count'), digits=0)}"),
                ("涨停 / 跌停", f"{_fmt(snapshot.get('limit_up_count'), digits=0)} / {_fmt(snapshot.get('limit_down_count'), digits=0)}"),
                ("炸板数", _fmt(snapshot.get("broken_limit_count"), digits=0)),
                ("最高连板", _fmt(snapshot.get("highest_streak"), digits=0)),
            ]),
            _section_header("节奏判断"),
            _markdown_block(f"**市场节奏**\n{snapshot.get('style_text') or '-'}"),
            _markdown_block(f"**风险提示**\n{snapshot.get('risk_text') or '-'}"),
            _markdown_block(f"**当前说明**\n{snapshot.get('availability_note') or '-'}"),
        ],
    }


