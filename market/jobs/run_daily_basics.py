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

