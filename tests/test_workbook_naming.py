"""情绪工作簿命名规则解析与扫描。"""
from pathlib import Path

from market.services.market_sentiment_workbook import (
    build_history_workbook_name,
    build_supplement_workbook_name,
    build_test_workbook_name,
    find_latest_history_workbook,
    list_ranged_workbooks,
    parse_ranged_workbook_name,
)


def test_build_names():
    assert build_history_workbook_name("20250101", "20250601") == "历史数据_20250101_20250601.xlsx"
    assert build_supplement_workbook_name("20250601", "20250701") == "补充数据_20250601_20250701.xlsx"
    assert build_test_workbook_name("20250601", "20250701") == "测试数据_20250601_20250701.xlsx"


def test_parse_valid_and_invalid_names():
    parsed = parse_ranged_workbook_name("历史数据_20250101_20250601.xlsx")
    assert parsed is not None
    assert parsed.prefix == "历史数据"
    assert parsed.start_date == "20250101"
    assert parsed.end_date == "20250601"

    assert parse_ranged_workbook_name("随便什么_20250101_20250601.xlsx") is None
    assert parse_ranged_workbook_name("历史数据_2025_0601.xlsx") is None
    assert parse_ranged_workbook_name("历史数据.xlsx") is None


def test_list_and_find_latest(tmp_path):
    for name in [
        "历史数据_20250101_20250401.xlsx",
        "历史数据_20250101_20250601.xlsx",
        "补充数据_20250501_20250601.xlsx",
        "~$历史数据_20250101_20250601.xlsx",
    ]:
        Path(tmp_path / name).write_bytes(b"")

    history = list_ranged_workbooks("历史数据", base_dir=str(tmp_path))
    assert [item.end_date for item in history] == ["20250401", "20250601"]

    latest = find_latest_history_workbook(base_dir=str(tmp_path))
    assert latest is not None
    assert latest.file_name == "历史数据_20250101_20250601.xlsx"


def test_find_latest_returns_none_for_empty_dir(tmp_path):
    assert find_latest_history_workbook(base_dir=str(tmp_path)) is None
