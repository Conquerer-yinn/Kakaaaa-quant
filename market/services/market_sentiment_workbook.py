from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from common.config import (
    MARKET_SENTIMENT_HISTORY_FILE,
    MARKET_SENTIMENT_HISTORY_PREFIX,
    MARKET_SENTIMENT_SUPPLEMENT_PREFIX,
    MARKET_SENTIMENT_TEST_PREFIX,
    MASTER_DATA_DIR,
)

RANGED_WORKBOOK_PATTERN = re.compile(r"^(?P<prefix>.+)_(?P<start>\d{8})_(?P<end>\d{8})\.xlsx$")


@dataclass(frozen=True)
class RangedWorkbookName:
    prefix: str
    start_date: str
    end_date: str
    file_name: str


ALL_PREFIXES = {
    MARKET_SENTIMENT_HISTORY_PREFIX,
    MARKET_SENTIMENT_SUPPLEMENT_PREFIX,
    MARKET_SENTIMENT_TEST_PREFIX,
}


def parse_ranged_workbook_name(file_name: str) -> RangedWorkbookName | None:
    match = RANGED_WORKBOOK_PATTERN.match(file_name)
    if not match:
        return None

    prefix = match.group("prefix")
    if prefix not in ALL_PREFIXES:
        return None

    return RangedWorkbookName(
        prefix=prefix,
        start_date=match.group("start"),
        end_date=match.group("end"),
        file_name=file_name,
    )


def build_ranged_workbook_name(prefix: str, start_date: str, end_date: str) -> str:
    return f"{prefix}_{start_date}_{end_date}.xlsx"


def build_history_workbook_name(start_date: str, end_date: str) -> str:
    return build_ranged_workbook_name(MARKET_SENTIMENT_HISTORY_PREFIX, start_date, end_date)


def build_supplement_workbook_name(start_date: str, end_date: str) -> str:
    return build_ranged_workbook_name(MARKET_SENTIMENT_SUPPLEMENT_PREFIX, start_date, end_date)


def build_test_workbook_name(start_date: str, end_date: str) -> str:
    return build_ranged_workbook_name(MARKET_SENTIMENT_TEST_PREFIX, start_date, end_date)


def list_ranged_workbooks(prefix: str, base_dir: str = MASTER_DATA_DIR) -> list[RangedWorkbookName]:
    results: list[RangedWorkbookName] = []
    for path in Path(base_dir).glob("*.xlsx"):
        if path.name.startswith("~$"):
            continue
        parsed = parse_ranged_workbook_name(path.name)
        if parsed and parsed.prefix == prefix:
            results.append(parsed)
    return sorted(results, key=lambda item: (item.end_date, item.start_date, item.file_name))


