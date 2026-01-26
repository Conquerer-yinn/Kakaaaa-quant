from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta

import pandas as pd


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data_engine.tushare_api import TushareDataEngine
from strategies.chinext_limit_up_event_study import build_event_study
from strategies.chinext_limit_up_workbook import (
    STRATEGY_RESULTS_DIR,
    write_event_study_workbook,
)


DEFAULT_LOOKBACK_DAYS = 120
FUTURE_CALENDAR_BUFFER_DAYS = 14


def normalize_ymd(value: object) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")

    text = str(value).strip()
    if text.isdigit() and len(text) == 8:
        return text
    try:
        return pd.to_datetime(text, errors="raise").strftime("%Y%m%d")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"无法识别日期: {value}") from exc


if __name__ == "__main__":
    args = parse_args()
    run_chinext_limit_up_event_study(
        start_date=args.start_date,
        end_date=args.end_date,
        base_dir=args.output_dir,
    )
