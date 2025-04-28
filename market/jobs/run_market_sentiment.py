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


