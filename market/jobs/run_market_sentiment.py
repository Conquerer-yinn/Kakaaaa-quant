import argparse
import os
import shutil
import sys
from datetime import datetime, timedelta

import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.config import (
    BACKUP_DIR,
    MARKET_SENTIMENT_CHINEXT_SHEET,
    MARKET_SENTIMENT_HEIGHT_SHEET,
    MARKET_SENTIMENT_MARKET_SHEET,
    MARKET_SENTIMENT_OVERVIEW_SHEET,
    MASTER_DATA_DIR,
)
from data_engine.tushare_api import TushareDataEngine
from market.indicators.sentiment_stat import (
    CHINEXT_COLUMNS,
    append_position_columns,
    build_chinext_feedback_rows,
    build_chinext_row,
    build_height_observation_df,
    build_latest_position_summary,
    build_market_overview_row,
    HEIGHT_OBSERVATION_COLUMNS,
    MARKET_OVERVIEW_COLUMNS,
)
from market.services.market_sentiment_workbook import (
    build_history_workbook_name,
    build_supplement_workbook_name,
    build_test_workbook_name,
    find_latest_history_workbook,
    parse_ranged_workbook_name,
)
from storage.excel_helper import ExcelHelper

DATE_COLUMN = MARKET_OVERVIEW_COLUMNS[0]
MARKET_AMOUNT_COLUMN = MARKET_OVERVIEW_COLUMNS[3]
MARKET_LIMIT_UP_COLUMN = MARKET_OVERVIEW_COLUMNS[4]
MARKET_BROKEN_COLUMN = MARKET_OVERVIEW_COLUMNS[6]
MARKET_RETRACE_COLUMN = MARKET_OVERVIEW_COLUMNS[7]
MARKET_STREAK_COLUMN = MARKET_OVERVIEW_COLUMNS[8]
MARKET_STREAK_STOCK_COLUMN = MARKET_OVERVIEW_COLUMNS[9]

HEIGHT_ALL_VALUE_COLUMN = HEIGHT_OBSERVATION_COLUMNS[1]
HEIGHT_ALL_STOCK_COLUMN = HEIGHT_OBSERVATION_COLUMNS[2]
HEIGHT_MAIN_VALUE_COLUMN = HEIGHT_OBSERVATION_COLUMNS[3]
HEIGHT_MAIN_STOCK_COLUMN = HEIGHT_OBSERVATION_COLUMNS[4]
HEIGHT_CHINEXT_VALUE_COLUMN = HEIGHT_OBSERVATION_COLUMNS[5]
HEIGHT_CHINEXT_STOCK_COLUMN = HEIGHT_OBSERVATION_COLUMNS[6]

CHINEXT_SHARE_COLUMN = CHINEXT_COLUMNS[2]
CHINEXT_LIMIT_UP_COLUMN = CHINEXT_COLUMNS[3]
CHINEXT_BROKEN_COLUMN = CHINEXT_COLUMNS[4]
CHINEXT_RETRACE_COLUMN = CHINEXT_COLUMNS[5]
CHINEXT_STREAK_COLUMN = CHINEXT_COLUMNS[6]
CHINEXT_PREMIUM_COLUMN = "昨日创业板涨停股次日收盘溢价(%)"
CHINEXT_CORE_STOCK_COLUMN = "昨日创业板核心股"
CHINEXT_CORE_CLOSE_COLUMN = "昨日创业板核心股次日收盘涨幅(%)"

HISTORY_BOOTSTRAP_CALENDAR_DAYS = 180
TEST_BOOTSTRAP_CALENDAR_DAYS = 45
FETCH_BUFFER_DAYS = 45
SHEET_TABLE_NAMES = {
    MARKET_SENTIMENT_MARKET_SHEET: "tbl_market_overview",
    MARKET_SENTIMENT_HEIGHT_SHEET: "tbl_height_observation",
    MARKET_SENTIMENT_CHINEXT_SHEET: "tbl_chinext_sentiment",
}


class TaskCancelledError(Exception):
    pass



def _check_cancel(should_cancel):
    if should_cancel and should_cancel():
        raise TaskCancelledError("任务已取消，未继续写入 market-sentiment 数据。")



def default_end_date():
    return datetime.today().strftime("%Y%m%d")



def normalize_ymd(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")

    text = str(value).strip()
    if not text:
        return None
    if text.isdigit() and len(text) == 8:
        return text
    return pd.to_datetime(text).strftime("%Y%m%d")



def bootstrap_start_date(end_date, calendar_days):
    end_dt = datetime.strptime(end_date, "%Y%m%d")
    return (end_dt - timedelta(days=calendar_days)).strftime("%Y%m%d")



def build_fetch_start(output_start):
    start_dt = datetime.strptime(output_start, "%Y%m%d")
    return (start_dt - timedelta(days=FETCH_BUFFER_DAYS)).strftime("%Y%m%d")



def get_existing_last_date(file_name):
    existing_df = ExcelHelper.read_sheet(file_name, MARKET_SENTIMENT_MARKET_SHEET)
    if existing_df is None or existing_df.empty or DATE_COLUMN not in existing_df.columns:
        return None

    normalized_dates = existing_df[DATE_COLUMN].dropna().map(normalize_ymd).dropna()
    if normalized_dates.empty:
        return None
    return max(normalized_dates)



def get_existing_first_date(file_name):
    existing_df = ExcelHelper.read_sheet(file_name, MARKET_SENTIMENT_MARKET_SHEET)
    if existing_df is None or existing_df.empty or DATE_COLUMN not in existing_df.columns:
        return None

    normalized_dates = existing_df[DATE_COLUMN].dropna().map(normalize_ymd).dropna()
    if normalized_dates.empty:
        return None
    return min(normalized_dates)



def resolve_history_run_plan(start_date=None, end_date=None, output_file=None):
    resolved_end = normalize_ymd(end_date) or default_end_date()
    current_history = output_file or _resolve_current_history_workbook()
    parsed_name = parse_ranged_workbook_name(current_history) if current_history else None

    history_start = parsed_name.start_date if parsed_name else None
    existing_last_date = parsed_name.end_date if parsed_name else None

    if current_history and history_start is None:
        history_start = get_existing_first_date(current_history)
    if current_history and existing_last_date is None:
        existing_last_date = get_existing_last_date(current_history)

    resolved_start = normalize_ymd(start_date)
    if resolved_start:
        output_start = resolved_start
    elif existing_last_date:
        output_start = (datetime.strptime(existing_last_date, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    else:
        output_start = bootstrap_start_date(resolved_end, HISTORY_BOOTSTRAP_CALENDAR_DAYS)

    history_start = history_start or output_start
    fetch_start = build_fetch_start(output_start)
    target_history = build_history_workbook_name(history_start, resolved_end)
    supplement_file = build_supplement_workbook_name(output_start, resolved_end)

    return {
        "current_history": current_history,
        "history_start": history_start,
        "existing_last_date": existing_last_date,
        "output_start": output_start,
        "output_end": resolved_end,
        "fetch_start": fetch_start,
        "target_history": target_history,
        "supplement_file": supplement_file,
    }



def resolve_test_run_plan(start_date=None, end_date=None, output_file=None):
    resolved_end = normalize_ymd(end_date) or default_end_date()
    output_start = normalize_ymd(start_date) or bootstrap_start_date(resolved_end, TEST_BOOTSTRAP_CALENDAR_DAYS)
    parsed_name = parse_ranged_workbook_name(output_file) if output_file else None
    target_file = output_file if parsed_name and parsed_name.prefix == "测试数据" else build_test_workbook_name(output_start, resolved_end)
    return {
        "output_start": output_start,
        "output_end": resolved_end,
        "fetch_start": build_fetch_start(output_start),
        "target_file": target_file,
    }



def _resolve_current_history_workbook():
    latest_history = find_latest_history_workbook()
    if latest_history is not None:
        return latest_history.file_name
    return None



def parse_args():
    parser = argparse.ArgumentParser(description="Build and update market sentiment data workbooks.")
    parser.add_argument("--start-date", default=None, help="YYYYMMDD. 不传时走增量更新。")
    parser.add_argument("--end-date", default=default_end_date(), help="YYYYMMDD. 默认到今天。")
    parser.add_argument("--output-file", default=None, help="可选，手动指定目标文件。")
    parser.add_argument("--test-mode", action="store_true", help="生成测试数据工作簿，不更新历史主表。")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_market_sentiment(
        start_date=args.start_date,
        end_date=args.end_date,
        output_file=args.output_file,
        history_mode=not args.test_mode,
    )


