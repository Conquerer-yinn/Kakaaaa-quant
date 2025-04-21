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


def resolve_date_range(start_date, end_date, output_file, sheet_name=DAILY_BASICS_SHEET):
    resolved_end = normalize_ymd(end_date) or default_end_date()
    resolved_start = normalize_ymd(start_date)

    # 传了 start_date 就按手动区间跑，适合首次建表或历史补数。
    if resolved_start:
        return resolved_start, resolved_end, "manual", None

    # 不传 start_date 就默认做增量更新，从已有最后日期的下一天继续。
    last_date = get_existing_last_date(output_file, sheet_name=sheet_name)
    if last_date is None:
        raise ValueError(
            "No existing daily basics file was found. Use --start-date and --end-date for the first initialization run."
        )

    next_date = (datetime.strptime(last_date, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    return next_date, resolved_end, "incremental", last_date


def collect_daily_basics(start_date, end_date):
    engine = TushareDataEngine()
    trade_dates = engine.get_trade_calendar(start_date, end_date)

    if not trade_dates:
        print(f"No open trade days found between {start_date} and {end_date}.")
        return pd.DataFrame(columns=DAILY_BASICS_COLUMNS)

    rows = []
    for trade_date in trade_dates:
        print(f"Processing {trade_date} ...")
        try:
            daily_df = engine.get_daily_quotes(trade_date)
            limit_df = engine.get_limit_list(trade_date)
            rows.append(build_daily_basics_row(trade_date, daily_df, limit_df))
        except Exception as exc:
            # 单日失败不影响整段任务继续跑完。
            print(f"Failed on {trade_date}: {exc}")

    if not rows:
        return pd.DataFrame(columns=DAILY_BASICS_COLUMNS)

    return pd.DataFrame(rows, columns=DAILY_BASICS_COLUMNS)


def run_daily_basics(start_date=None, end_date=None, output_file=DAILY_BASICS_FILE):
    # 先判断本次是手动补数，还是自动续更。
    resolved_start, resolved_end, run_mode, existing_last_date = resolve_date_range(
        start_date=start_date,
        end_date=end_date,
        output_file=output_file,
        sheet_name=DAILY_BASICS_SHEET,
    )

    if resolved_start > resolved_end:
        print(f"No update needed. Existing data already covers up to {existing_last_date}.")
        return None

    if run_mode == "incremental":
        print(
            "Running in incremental mode: "
            f"existing data ends at {existing_last_date}, updating {resolved_start} -> {resolved_end}."
        )
    else:
        print(f"Running in manual range mode: {resolved_start} -> {resolved_end}.")

    df = collect_daily_basics(resolved_start, resolved_end)
    if df.empty:
        print("No daily basics data collected.")
        return None

    output_path = ExcelHelper.append_rows(
        df=df,
        file_name=output_file,
        sheet_name=DAILY_BASICS_SHEET,
        dedupe_subset=[DATE_COLUMN],
    )
    print(f"Wrote {len(df)} rows to {output_path}")
    return output_path


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

