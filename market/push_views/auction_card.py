from __future__ import annotations

from typing import Any


def build_auction_card(snapshot: dict[str, Any]) -> dict[str, Any]:
    """构造竞价观察飞书卡片。"""
    title = f"{snapshot.get('date') or '-'} 竞价观察卡片"
    return {
        "config": {"wide_screen_mode": True, "enable_forward": True},
        "header": {
            "template": "orange",
            "title": {"tag": "plain_text", "content": title},
        },
        "elements": [
            _section_header("竞价指数"),
            _fields([
                ("推送时点", snapshot.get("time_point") or "-"),
                ("上证开盘涨幅", _fmt(snapshot.get("sse_index_pct"), suffix="%")),
                ("深成开盘涨幅", _fmt(snapshot.get("szse_index_pct"), suffix="%")),
                ("创业板开盘涨幅", _fmt(snapshot.get("chinext_index_pct"), suffix="%")),
            ]),
            _section_header("竞价全貌"),
            _fields([
                ("竞价成交额", _fmt(snapshot.get("auction_turnover_yi"), suffix=" 亿元")),
                ("上涨 / 下跌", f"{_fmt(snapshot.get('up_count'), digits=0)} / {_fmt(snapshot.get('down_count'), digits=0)}"),
                ("竞价涨停数", _fmt(snapshot.get("limit_up_count"), digits=0)),
                ("竞价跌停数", _fmt(snapshot.get("limit_down_count"), digits=0)),
            ]),
            _section_header("前排观察"),
            _markdown_block(f"**竞价成交额前排**\n{snapshot.get('top_turnover_list') or '-'}"),
            _markdown_block(f"**竞价涨停前排**\n{snapshot.get('limit_up_list') or '-'}"),
            _markdown_block(f"**竞价跌停前排**\n{snapshot.get('limit_down_list') or '-'}"),
            _section_header("结论"),
            _markdown_block(f"**竞价结论**\n{snapshot.get('summary_text') or '-'}"),
            _markdown_block(f"**当前说明**\n{snapshot.get('availability_note') or '-'}"),
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


def _fmt(value: Any, digits: int = 2, suffix: str = "") -> str:
    if value is None:
        return "-"
    if isinstance(value, int):
        return f"{value}{suffix}"
    if isinstance(value, float):
        return f"{value:.{digits}f}{suffix}"
    return f"{value}{suffix}"
