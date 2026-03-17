import tempfile
import unittest
from pathlib import Path

import pandas as pd

from strategies.run_chinext_limit_up_event_study import (
    build_fetch_end,
    load_trade_calendar_with_horizon,
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
        self.stock_basic_calls = 0
        self.index_calls: list[tuple[str, str, str]] = []

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

    def get_stock_basic(self, fields=None):
        self.stock_basic_calls += 1
        return pd.DataFrame(
            [{"ts_code": "300001.SZ", "name": "样本一", "list_date": "20200101"}]
        )

    def get_index_daily(self, ts_code, start_date=None, end_date=None, trade_date=None):
        self.index_calls.append((ts_code, start_date, end_date))
        return pd.DataFrame(
            [
                {"trade_date": value, "close": 100.0 + index}
                for index, value in enumerate(TRADE_DATES)
            ]
        )


class LongHolidayEngine:
    def __init__(self):
        self.calendar_requests: list[tuple[str, str]] = []

    def get_trade_calendar(self, start_date, end_date):
        self.calendar_requests.append((start_date, end_date))
        if len(self.calendar_requests) == 1:
            return ["20260120", "20260121", "20260122", "20260123"]
        return [
            "20260120",
            "20260121",
            "20260122",
            "20260123",
            "20260204",
            "20260205",
        ]

class RunChinextLimitUpEventStudyTest(unittest.TestCase):
    def test_normalizes_dates_and_rejects_reversed_range(self):
        self.assertEqual(normalize_ymd("2026-01-05"), "20260105")
        self.assertEqual(normalize_ymd("20260105"), "20260105")
        self.assertEqual(resolve_study_range("20260105", "20260112"), ("20260105", "20260112"))

        with self.assertRaisesRegex(ValueError, "开始日期不能晚于结束日期"):
            resolve_study_range("20260112", "20260105")

        for invalid_date in ("20260231", "20261301"):
            with self.subTest(invalid_date=invalid_date):
                with self.assertRaisesRegex(ValueError, "无法识别日期"):
                    normalize_ymd(invalid_date)

        with self.assertRaisesRegex(ValueError, "无法识别日期"):
            resolve_study_range("20260101", "20260231")

    def test_defaults_to_previous_120_calendar_days(self):
        self.assertEqual(resolve_study_range(None, "20260501"), ("20260101", "20260501"))

    def test_builds_fourteen_day_future_calendar_buffer(self):
        self.assertEqual(build_fetch_end("20260105"), "20260119")

    def test_expands_calendar_window_until_five_future_sessions_exist(self):
        engine = LongHolidayEngine()

        trade_dates = load_trade_calendar_with_horizon(
            engine=engine,
            start_date="20260120",
            end_date="20260120",
        )

        self.assertEqual(len([value for value in trade_dates if value > "20260120"]), 5)
        self.assertEqual(
            engine.calendar_requests,
            [("20260120", "20260203"), ("20260120", "20260217")],
        )

    def test_runner_uses_injected_engine_and_writes_workbook(self):
        engine = FakeEngine()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = run_chinext_limit_up_event_study(
                start_date="20260105",
                end_date="20260105",
                base_dir=temp_dir,
                engine=engine,
            )

            self.assertTrue(Path(output_path).exists())
            self.assertEqual(engine.calendar_requests, [("20260105", "20260119")])
            self.assertEqual(engine.daily_calls, TRADE_DATES)
            self.assertEqual(engine.limit_calls, ["20260105"])
            self.assertEqual(engine.stock_basic_calls, 1)
            self.assertEqual(engine.index_calls, [("399006.SZ", "20260105", "20260112")])
            details = pd.read_excel(output_path, sheet_name="事件明细")
            self.assertEqual(len(details), 1)
            self.assertEqual(details.iloc[0]["股票代码"], "300001.SZ")
            self.assertEqual(details.iloc[0]["市场环境"], "弱")
            self.assertEqual(details.iloc[0]["5日基准收益率(%)"], 5.0)
            self.assertEqual(details.iloc[0]["5日超额收益率(%)"], 45.0)


if __name__ == "__main__":
    unittest.main()
