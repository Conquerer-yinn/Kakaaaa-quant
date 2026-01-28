import tempfile
import unittest
from pathlib import Path

import pandas as pd

from strategies.run_chinext_limit_up_event_study import (
    build_fetch_end,
    normalize_ymd,
    resolve_study_range,
    run_chinext_limit_up_event_study,
)


TRADE_DATES = [
    "20260105",
    "20260106",
    "20260107",
    "20260108",
    "20260109",
    "20260112",
]


class FakeEngine:
    def __init__(self):
        self.calendar_requests: list[tuple[str, str]] = []
        self.daily_calls: list[str] = []
        self.limit_calls: list[str] = []

    def get_trade_calendar(self, start_date, end_date):
        self.calendar_requests.append((start_date, end_date))
        return TRADE_DATES

    def get_daily_quotes(self, trade_date):
        self.daily_calls.append(trade_date)
        day_index = TRADE_DATES.index(trade_date)
        return pd.DataFrame(
            [{"ts_code": "300001.SZ", "close": 10.0 + day_index}]
        )

    def get_limit_list(self, trade_date):
        self.limit_calls.append(trade_date)
        if trade_date != "20260105":
            return pd.DataFrame()
        return pd.DataFrame(
            [
                {
                    "ts_code": "300001.SZ",
                    "name": "样本一",
                    "limit": "U",
                    "limit_times": 1,
                }
            ]
        )
