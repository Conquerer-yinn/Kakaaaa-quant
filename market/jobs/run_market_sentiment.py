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



def merge_with_existing(output_file, sheet_name, df):
    existing_df = ExcelHelper.read_sheet(output_file, sheet_name)
    if existing_df is None or existing_df.empty:
        return df.reset_index(drop=True)

    merged = pd.concat([existing_df, df], ignore_index=True)
    merged = merged.drop_duplicates(subset=[DATE_COLUMN], keep="last")
    return merged.sort_values(DATE_COLUMN).reset_index(drop=True)



def collect_market_snapshots(fetch_start, output_end, should_cancel=None):
    # 这一层只负责把原始表按交易日拉下来，不做展示逻辑。
    engine = TushareDataEngine()
    stock_basic_df = engine.get_stock_basic(fields="ts_code,name,list_date,market")
    trade_dates = engine.get_trade_calendar(fetch_start, output_end)
    if not trade_dates:
        return trade_dates, stock_basic_df, {}, {}, {}, {}, pd.DataFrame(), pd.DataFrame()

    daily_by_date = {}
    daily_basic_by_date = {}
    limit_by_date = {}
    stk_limit_by_date = {}
    market_rows = []
    all_daily_frames = []

    for trade_date in trade_dates:
        _check_cancel(should_cancel)
        print(f"Processing {trade_date} ...")
        try:
            daily_df = engine.get_daily_quotes(trade_date)
            daily_basic_df = engine.get_daily_basic(trade_date)
            limit_df = engine.get_limit_list(trade_date)
            stk_limit_df = engine.get_stk_limit(trade_date)
        except Exception as exc:
            # 单日取数失败时继续往后跑，避免整段任务因为一天异常全部中断。
            print(f"Failed to fetch {trade_date}: {exc}")
            continue

        daily_by_date[trade_date] = daily_df.copy()
        daily_basic_by_date[trade_date] = daily_basic_df.copy()
        limit_by_date[trade_date] = limit_df.copy()
        stk_limit_by_date[trade_date] = stk_limit_df.copy()
        market_rows.append(build_market_overview_row(trade_date, daily_df, limit_df, stk_limit_df))
        all_daily_frames.append(daily_df.copy())
        _check_cancel(should_cancel)

    all_daily_df = pd.concat(all_daily_frames, ignore_index=True) if all_daily_frames else pd.DataFrame()
    market_df = pd.DataFrame(market_rows)
    return trade_dates, stock_basic_df, daily_by_date, daily_basic_by_date, limit_by_date, stk_limit_by_date, all_daily_df, market_df



def build_sentiment_tables(daily_by_date, daily_basic_by_date, limit_by_date, stk_limit_by_date, all_daily_df, market_df, stock_basic_df, should_cancel=None):
    chinext_rows = []
    chinext_samples = {}
    market_lookup = market_df.set_index(DATE_COLUMN)[MARKET_AMOUNT_COLUMN].to_dict() if not market_df.empty else {}

    for trade_date in market_df[DATE_COLUMN].tolist():
        _check_cancel(should_cancel)
        row, samples = build_chinext_row(
            trade_date=trade_date,
            daily_df=daily_by_date.get(trade_date),
            daily_basic_df=daily_basic_by_date.get(trade_date),
            limit_df=limit_by_date.get(trade_date),
            stk_limit_df=stk_limit_by_date.get(trade_date),
            total_amount=market_lookup.get(trade_date, 0),
        )
        chinext_rows.append(row)
        chinext_samples[trade_date] = samples

    trade_date_list = market_df[DATE_COLUMN].tolist()
    _check_cancel(should_cancel)
    height_df = build_height_observation_df(all_daily_df, stock_basic_df, trade_date_list, market_df)
    _check_cancel(should_cancel)
    feedback_df = build_chinext_feedback_rows(trade_date_list, daily_by_date, chinext_samples)
    chinext_df = pd.DataFrame(chinext_rows).merge(feedback_df, on=DATE_COLUMN, how="left")
    return height_df, chinext_df



def add_position_metrics(market_df, height_df, chinext_df):
    # 位置度量继续保留在 Excel 里，方便你后续做人工判断；前端不再展示这些列。
    market_df = append_position_columns(
        market_df,
        [MARKET_AMOUNT_COLUMN, MARKET_LIMIT_UP_COLUMN, MARKET_BROKEN_COLUMN, MARKET_RETRACE_COLUMN, MARKET_STREAK_COLUMN],
    )
    height_df = append_position_columns(
        height_df,
        [HEIGHT_ALL_VALUE_COLUMN, HEIGHT_MAIN_VALUE_COLUMN, HEIGHT_CHINEXT_VALUE_COLUMN, MARKET_STREAK_COLUMN],
    )
    chinext_df = append_position_columns(
        chinext_df,
        [CHINEXT_SHARE_COLUMN, CHINEXT_LIMIT_UP_COLUMN, CHINEXT_BROKEN_COLUMN, CHINEXT_RETRACE_COLUMN, CHINEXT_PREMIUM_COLUMN],
    )
    return market_df, height_df, chinext_df



def build_overview_rows(market_df, height_df, chinext_df, run_mode):
    latest_market = market_df.iloc[-1] if not market_df.empty else pd.Series(dtype=object)
    latest_height = height_df.iloc[-1] if not height_df.empty else pd.Series(dtype=object)
    latest_chinext = chinext_df.iloc[-1] if not chinext_df.empty else pd.Series(dtype=object)

    summary_rows = []
    summary_rows.extend(build_latest_position_summary("总市场", market_df, [MARKET_AMOUNT_COLUMN, MARKET_LIMIT_UP_COLUMN, MARKET_BROKEN_COLUMN, MARKET_RETRACE_COLUMN, MARKET_STREAK_COLUMN]))
    summary_rows.extend(build_latest_position_summary("高度观察", height_df, [HEIGHT_ALL_VALUE_COLUMN, HEIGHT_MAIN_VALUE_COLUMN, HEIGHT_CHINEXT_VALUE_COLUMN]))
    summary_rows.extend(build_latest_position_summary("创业板", chinext_df, [CHINEXT_SHARE_COLUMN, CHINEXT_LIMIT_UP_COLUMN, CHINEXT_BROKEN_COLUMN, CHINEXT_RETRACE_COLUMN, CHINEXT_PREMIUM_COLUMN]))

    rows = [
        ["近期市场情绪总览"],
        ["最新日期", latest_market.get(DATE_COLUMN), None, "运行模式", run_mode],
        [None],
        ["最新十日高度", None, None, None, "最新连板高度", None, None, "创业板核心反馈"],
        ["全市场", latest_height.get(HEIGHT_ALL_STOCK_COLUMN), latest_height.get(HEIGHT_ALL_VALUE_COLUMN), None, "最高连板", latest_market.get(MARKET_STREAK_COLUMN), None, "昨日核心股", latest_chinext.get(CHINEXT_CORE_STOCK_COLUMN)],
        ["主板", latest_height.get(HEIGHT_MAIN_STOCK_COLUMN), latest_height.get(HEIGHT_MAIN_VALUE_COLUMN), None, "最高连板个股", latest_market.get(MARKET_STREAK_STOCK_COLUMN), None, "次日收盘涨幅", latest_chinext.get(CHINEXT_CORE_CLOSE_COLUMN)],
        ["创业板", latest_height.get(HEIGHT_CHINEXT_STOCK_COLUMN), latest_height.get(HEIGHT_CHINEXT_VALUE_COLUMN), None, "创业板连板高度", latest_chinext.get(CHINEXT_STREAK_COLUMN), None, "昨日涨停次日收盘", latest_chinext.get(CHINEXT_PREMIUM_COLUMN)],
        [None],
        ["模块", "指标", "最新值", "近期低点", "近期高点", "区间位置", "相对中枢"],
    ]

    for item in summary_rows:
        rows.append([
            item.get("模块"),
            item.get("指标"),
            item.get("最新值"),
            item.get("近期低点"),
            item.get("近期高点"),
            item.get("区间位置"),
            item.get("相对中枢"),
        ])
    return rows



def save_data_workbook(file_name, market_df, height_df, chinext_df, run_mode, base_dir=None):
    output_path = ExcelHelper.upsert_data_workbook(
        file_name=file_name,
        sheets={
            MARKET_SENTIMENT_MARKET_SHEET: market_df,
            MARKET_SENTIMENT_HEIGHT_SHEET: height_df,
            MARKET_SENTIMENT_CHINEXT_SHEET: chinext_df,
        },
        table_names=SHEET_TABLE_NAMES,
        base_dir=base_dir or MASTER_DATA_DIR,
    )
    overview_rows = build_overview_rows(market_df, height_df, chinext_df, run_mode)
    ExcelHelper.update_overview_sheet(
        file_name,
        MARKET_SENTIMENT_OVERVIEW_SHEET,
        overview_rows,
        base_dir=base_dir or MASTER_DATA_DIR,
    )
    return output_path



def write_supplement_workbook(file_name, market_df, height_df, chinext_df):
    return save_data_workbook(
        file_name=file_name,
        market_df=market_df,
        height_df=height_df,
        chinext_df=chinext_df,
        run_mode="supplement",
        base_dir=BACKUP_DIR,
    )



def _prepare_history_target_file(current_history, target_history):
    current_path = ExcelHelper.build_master_path(current_history) if current_history else None
    target_path = ExcelHelper.build_master_path(target_history)

    if current_path and os.path.exists(current_path) and current_history != target_history:
        if os.path.exists(target_path):
            ExcelHelper.backup_file(target_path)
            os.remove(target_path)
        shutil.copy2(current_path, target_path)

    return current_path, target_path



def _finalize_history_target_file(current_history, target_history):
    if not current_history or current_history == target_history:
        return

    current_path = ExcelHelper.build_master_path(current_history)
    if os.path.exists(current_path):
        ExcelHelper.backup_file(current_path)
        os.remove(current_path)



def run_market_sentiment(start_date=None, end_date=None, output_file=None, history_mode=True, should_cancel=None):
    if history_mode:
        plan = resolve_history_run_plan(start_date=start_date, end_date=end_date, output_file=output_file)
        run_mode = "incremental_history"
        current_history = plan["current_history"]
        target_file = plan["target_history"]
    else:
        plan = resolve_test_run_plan(start_date=start_date, end_date=end_date, output_file=output_file)
        run_mode = "test_range"
        current_history = None
        target_file = plan["target_file"]

    output_start = plan["output_start"]
    output_end = plan["output_end"]
    fetch_start = plan["fetch_start"]

    if output_start > output_end:
        last_date = plan.get("existing_last_date")
        print(f"No update needed. Existing data already covers up to {last_date}.")
        return None

    if history_mode:
        print(f"Running in history incremental mode: supplementing {output_start} -> {output_end}.")
    else:
        print(f"Running in test mode: building {output_start} -> {output_end}.")

    _check_cancel(should_cancel)

    (
        trade_dates,
        stock_basic_df,
        daily_by_date,
        daily_basic_by_date,
        limit_by_date,
        stk_limit_by_date,
        all_daily_df,
        market_df,
    ) = collect_market_snapshots(fetch_start, output_end, should_cancel=should_cancel)

    if market_df.empty:
        print("No market data collected.")
        return None

    _check_cancel(should_cancel)
    height_df, chinext_df = build_sentiment_tables(
        daily_by_date=daily_by_date,
        daily_basic_by_date=daily_basic_by_date,
        limit_by_date=limit_by_date,
        stk_limit_by_date=stk_limit_by_date,
        all_daily_df=all_daily_df,
        market_df=market_df,
        stock_basic_df=stock_basic_df,
        should_cancel=should_cancel,
    )

    _check_cancel(should_cancel)
    market_df = market_df[(market_df[DATE_COLUMN] >= output_start) & (market_df[DATE_COLUMN] <= output_end)]
    height_df = height_df[(height_df[DATE_COLUMN] >= output_start) & (height_df[DATE_COLUMN] <= output_end)]
    chinext_df = chinext_df[(chinext_df[DATE_COLUMN] >= output_start) & (chinext_df[DATE_COLUMN] <= output_end)]

    if market_df.empty:
        print("No new market sentiment rows remained after date filtering.")
        return None

    if history_mode:
        _check_cancel(should_cancel)
        supplement_path = write_supplement_workbook(plan["supplement_file"], market_df, height_df, chinext_df)
        print(f"Wrote supplement workbook to {supplement_path}")

    if history_mode:
        _check_cancel(should_cancel)
        if current_history:
            market_df = merge_with_existing(current_history, MARKET_SENTIMENT_MARKET_SHEET, market_df)
            height_df = merge_with_existing(current_history, MARKET_SENTIMENT_HEIGHT_SHEET, height_df)
            chinext_df = merge_with_existing(current_history, MARKET_SENTIMENT_CHINEXT_SHEET, chinext_df)

        _check_cancel(should_cancel)
        _prepare_history_target_file(current_history, target_file)

    _check_cancel(should_cancel)
    market_df, height_df, chinext_df = add_position_metrics(market_df, height_df, chinext_df)
    _check_cancel(should_cancel)
    output_path = save_data_workbook(target_file, market_df, height_df, chinext_df, run_mode)

    if history_mode:
        _finalize_history_target_file(current_history, target_file)

    print(f"Wrote market sentiment data workbook to {output_path}")
    return output_path



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


