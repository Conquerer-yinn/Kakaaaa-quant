from __future__ import annotations

from typing import Any

import pandas as pd

def build_post_close_card(snapshot: dict[str, Any]) -> dict[str, Any]:
    """构造飞书 interactive card。"""
    title = f"{snapshot.get('date') or '-'} 盘后复盘卡片"
    return {
        "config": {"wide_screen_mode": True, "enable_forward": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": title},
        },
        "elements": [
            _section_header("总市场"),
            _fields([
                ("总成交额", _fmt(snapshot.get("total_turnover"), suffix=" 亿元")),
                ("上涨 / 下跌", f"{_fmt(snapshot.get('up_count'), digits=0)} / {_fmt(snapshot.get('down_count'), digits=0)}"),
                ("涨停 / 跌停", f"{_fmt(snapshot.get('limit_up_count'), digits=0)} / {_fmt(snapshot.get('limit_down_count'), digits=0)}"),
                ("炸板数", _fmt(snapshot.get("broken_limit_count"), digits=0)),
                ("大回撤数", _fmt(snapshot.get("large_retrace_count"), digits=0)),
                ("最高连板", f"{_fmt(snapshot.get('highest_streak'), digits=0)} | {snapshot.get('highest_streak_stock') or '-'}"),
            ]),
            _section_header("高度"),
            _fields([
                ("全市场十日高度", _stock_value(snapshot.get("all_height_stock"), snapshot.get("all_height_value"))),
                ("主板十日高度", _stock_value(snapshot.get("main_height_stock"), snapshot.get("main_height_value"))),
                ("创业板十日高度", _stock_value(snapshot.get("chinext_height_stock"), snapshot.get("chinext_height_value"))),
                ("创业板连板高度", f"{_fmt(snapshot.get('chinext_highest_streak'), digits=0)} | {snapshot.get('chinext_highest_streak_stock') or '-'}"),
            ]),
            _section_header("创业板"),
            _fields([
                ("成交额占比", _fmt(snapshot.get("chinext_turnover_ratio"), suffix="%")),
                ("涨停数", _fmt(snapshot.get("chinext_limit_up_count"), digits=0)),
                ("炸板数", _fmt(snapshot.get("chinext_broken_limit_count"), digits=0)),
                ("大回撤数", _fmt(snapshot.get("chinext_large_retrace_count"), digits=0)),
                ("昨日核心股反馈", _stock_value(snapshot.get("prev_core_stock"), snapshot.get("prev_core_next_close_pct"), suffix="%")),
                ("昨日涨停次日收盘", _fmt(snapshot.get("prev_limit_up_next_close_pct"), suffix="%")),
            ]),
            _section_header("结论与风险"),
            _markdown_block(f"**情绪结论**\n{snapshot.get('summary_text') or '-'}"),
            _markdown_block(f"**风险提示**\n{snapshot.get('risk_text') or '-'}"),
        ],
    }


def _section_header(title: str) -> dict[str, Any]:
    return {"tag": "markdown", "content": f"**{title}**"}


def _markdown_block(text: str) -> dict[str, Any]:
    return {"tag": "markdown", "content": text}


def _fields(items: list[tuple[str, str]]) -> dict[str, Any]:
    return {
        "tag": "div",
        "fields": [
            {
                "is_short": True,
                "text": {"tag": "lark_md", "content": f"**{label}**\n{value}"},
            }
            for label, value in items
        ],
    }
