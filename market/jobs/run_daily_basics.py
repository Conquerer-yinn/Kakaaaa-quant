import argparse
import os
import sys
from datetime import datetime, timedelta

import pandas as pd

# Allow running the file directly with:
# `python market/jobs/run_daily_basics.py`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.config import DAILY_BASICS_FILE, DAILY_BASICS_SHEET
from data_engine.tushare_api import TushareDataEngine
from market.indicators.daily_basics import DAILY_BASICS_COLUMNS, build_daily_basics_row
from storage.excel_helper import ExcelHelper


DATE_COLUMN = DAILY_BASICS_COLUMNS[0]


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


def get_existing_last_date(output_file, sheet_name=DAILY_BASICS_SHEET):
    # 增量更新时，以 Excel 里最后一条实际数据作为准绳。
    file_path = ExcelHelper.build_master_path(output_file)
    if not os.path.exists(file_path):
        return None

    existing_df = pd.read_excel(file_path, sheet_name=sheet_name)
    if existing_df.empty or DATE_COLUMN not in existing_df.columns:
        return None

    date_series = existing_df[DATE_COLUMN].dropna()
    if date_series.empty:
        return None

    normalized_dates = date_series.map(normalize_ymd).dropna()
    if normalized_dates.empty:
        return None

    return max(normalized_dates)


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch and update daily basics data.")
    parser.add_argument(
        "--start-date",
        default=None,
        help=(
            "YYYYMMDD. If omitted, the script continues from the day after "
            "the last date already stored in Excel."
        ),
    )
    parser.add_argument(
        "--end-date",
        default=default_end_date(),
        help="YYYYMMDD. Defaults to today.",
    )
    parser.add_argument("--output-file", default=DAILY_BASICS_FILE)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_daily_basics(
        start_date=args.start_date,
        end_date=args.end_date,
        output_file=args.output_file,
    )

