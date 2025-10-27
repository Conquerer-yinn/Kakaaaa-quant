"""三类飞书卡片：快照 -> 卡片 JSON 结构与文案规则。"""
from market.push_views.auction_card import build_auction_card
from market.push_views.intraday_card import build_intraday_card
from market.push_views.post_close_card import (
    build_post_close_card,
    build_risk_text,
    build_summary_text,
    enrich_post_close_snapshot,
)


def _post_close_snapshot():
    return {
        "date": "20260102",
        "total_turnover": 18500.5,
        "up_count": 3200,
        "down_count": 1800,
        "limit_up_count": 85,
        "limit_down_count": 5,
        "broken_limit_count": 12,
        "large_retrace_count": 40,
        "highest_streak": 6,
        "highest_streak_stock": "龙头股",
        "all_height_stock": "高度股",
        "all_height_value": 120.5,
        "chinext_limit_up_count": 10,
        "chinext_broken_limit_count": 1,
        "prev_core_stock": "创核",
        "prev_core_next_close_pct": 5.2,
        "prev_limit_up_next_close_pct": 2.1,
    }


def test_enrich_adds_summary_and_risk():
    enriched = enrich_post_close_snapshot(_post_close_snapshot())
    assert "summary_text" in enriched and enriched["summary_text"]
    assert "risk_text" in enriched and enriched["risk_text"]


def test_summary_text_rules():
    text = build_summary_text(_post_close_snapshot())
    assert "连板高度仍在" in text
    assert "涨停家数较强" in text
    assert "创业板活跃" in text
    assert "昨日创业板核心反馈偏正" in text


def test_risk_text_default_when_no_risk():
    text = build_risk_text(_post_close_snapshot())
    assert "未出现特别突出的风险项" in text


def test_risk_text_flags_high_broken():
    snapshot = _post_close_snapshot()
    snapshot["broken_limit_count"] = 30
    snapshot["prev_limit_up_next_close_pct"] = -1.5
    text = build_risk_text(snapshot)
    assert "炸板数偏高" in text
    assert "创业板涨停次日反馈偏弱" in text


def test_post_close_card_structure():
    card = build_post_close_card(enrich_post_close_snapshot(_post_close_snapshot()))
    assert card["header"]["template"] == "blue"
    assert "20260102" in card["header"]["title"]["content"]
    assert card["elements"][0]["content"] == "**总市场**"
    assert len(card["elements"]) == 9


def test_auction_card_handles_missing_values():
    card = build_auction_card({"date": "20260102", "summary_text": "整体偏强"})
    assert "20260102" in card["header"]["title"]["content"]
    contents = str(card["elements"])
    assert "整体偏强" in contents
    assert "-" in contents  # 缺失数值统一展示为 -


def test_intraday_card_structure():
    card = build_intraday_card({"date": "20260102", "time_point": "10:30"})
    assert "20260102" in card["header"]["title"]["content"]
    assert card["elements"]
