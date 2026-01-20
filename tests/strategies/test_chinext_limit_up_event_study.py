import unittest

import pandas as pd

from strategies.chinext_limit_up_event_study import (
    DETAIL_COLUMNS,
    SUMMARY_COLUMNS,
    build_event_study,
)


TRADE_DATES = [
    "20260105",
    "20260106",
    "20260107",
    "20260108",
    "20260109",
    "20260112",
]


def daily_frame(**closes: float) -> pd.DataFrame:
    return pd.DataFrame(
        [{"ts_code": ts_code, "close": close} for ts_code, close in closes.items()]
    )


def limit_frame(*rows: dict) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["ts_code", "name", "limit", "limit_times"])


class ChinextLimitUpEventStudyTest(unittest.TestCase):
    def test_builds_complete_event_returns_and_filters_non_events(self):
        daily_by_date = {
            "20260105": daily_frame(**{"300001.SZ": 10.0}),
            "20260106": daily_frame(**{"300001.SZ": 11.0}),
            "20260107": daily_frame(**{"300001.SZ": 9.0}),
            "20260108": daily_frame(**{"300001.SZ": 12.0}),
            "20260109": daily_frame(**{"300001.SZ": 8.0}),
            "20260112": daily_frame(**{"300001.SZ": 11.0}),
        }
        limit_by_date = {
            "20260105": limit_frame(
                {
                    "ts_code": "300001.SZ",
                    "name": "样本一",
                    "limit": "U",
                    "limit_times": 2,
                },
                {
                    "ts_code": "600001.SH",
                    "name": "非创业板",
                    "limit": "U",
                    "limit_times": 1,
                },
                {
                    "ts_code": "301002.SZ",
                    "name": "创业板炸板",
                    "limit": "Z",
                    "limit_times": 1,
                },
            )
        }

        result = build_event_study(
            trade_dates=TRADE_DATES,
            event_start_date="20260105",
            event_end_date="20260105",
            daily_by_date=daily_by_date,
            limit_by_date=limit_by_date,
        )

        self.assertEqual(result.candidate_event_count, 1)
        self.assertEqual(result.complete_sample_count, 1)
        self.assertEqual(result.skipped_incomplete_count, 0)
        self.assertEqual(result.skipped_missing_quote_count, 0)
        row = result.details.iloc[0]
        self.assertEqual(row["事件日期"], "20260105")
        self.assertEqual(row["股票代码"], "300001.SZ")
        self.assertEqual(row["连板次数"], 2)
        self.assertEqual(row["1日后日期"], "20260106")
        self.assertEqual(row["1日收益率(%)"], 10.0)
        self.assertEqual(row["3日收益率(%)"], 20.0)
        self.assertEqual(row["5日收益率(%)"], 10.0)
        self.assertEqual(row["5日内最高收盘收益率(%)"], 20.0)
        self.assertEqual(row["5日内最低收盘收益率(%)"], -20.0)

    def test_summary_reports_mean_median_and_positive_rate(self):
        daily_by_date = {
            "20260105": daily_frame(**{"300001.SZ": 10.0, "301002.SZ": 20.0}),
            "20260106": daily_frame(**{"300001.SZ": 11.0, "301002.SZ": 18.0}),
            "20260107": daily_frame(**{"300001.SZ": 9.0, "301002.SZ": 18.0}),
            "20260108": daily_frame(**{"300001.SZ": 12.0, "301002.SZ": 16.0}),
            "20260109": daily_frame(**{"300001.SZ": 8.0, "301002.SZ": 21.0}),
            "20260112": daily_frame(**{"300001.SZ": 11.0, "301002.SZ": 22.0}),
        }
        limit_by_date = {
            "20260105": limit_frame(
                {"ts_code": "300001.SZ", "name": "样本一", "limit": "U", "limit_times": 2},
                {"ts_code": "301002.SZ", "name": "样本二", "limit": "U", "limit_times": 1},
            )
        }

        result = build_event_study(
            trade_dates=TRADE_DATES,
            event_start_date="20260105",
            event_end_date="20260105",
            daily_by_date=daily_by_date,
            limit_by_date=limit_by_date,
        )

        one_day = result.summary.loc[result.summary["观察周期"] == "1日"].iloc[0]
        five_day = result.summary.loc[result.summary["观察周期"] == "5日"].iloc[0]
        self.assertEqual(one_day["样本数"], 2)
        self.assertEqual(one_day["平均收益率(%)"], 0.0)
        self.assertEqual(one_day["中位数收益率(%)"], 0.0)
        self.assertEqual(one_day["正收益比例(%)"], 50.0)
        self.assertEqual(five_day["平均收益率(%)"], 10.0)
        self.assertEqual(five_day["正收益比例(%)"], 100.0)

    def test_skips_event_without_full_five_day_window(self):
        result = build_event_study(
            trade_dates=TRADE_DATES,
            event_start_date="20260108",
            event_end_date="20260108",
            daily_by_date={"20260108": daily_frame(**{"300001.SZ": 10.0})},
            limit_by_date={
                "20260108": limit_frame(
                    {"ts_code": "300001.SZ", "name": "样本一", "limit": "U", "limit_times": 1}
                )
            },
        )

        self.assertEqual(result.candidate_event_count, 1)
        self.assertEqual(result.complete_sample_count, 0)
        self.assertEqual(result.skipped_incomplete_count, 1)
        self.assertEqual(result.skipped_missing_quote_count, 0)
        self.assertTrue(result.details.empty)

    def test_skips_event_when_event_day_quote_is_missing(self):
        daily_by_date = {
            trade_date: daily_frame(**{"301999.SZ": 10.0}) for trade_date in TRADE_DATES
        }
        result = build_event_study(
            trade_dates=TRADE_DATES,
            event_start_date="20260105",
            event_end_date="20260105",
            daily_by_date=daily_by_date,
            limit_by_date={
                "20260105": limit_frame(
                    {"ts_code": "300001.SZ", "name": "样本一", "limit": "U", "limit_times": 1}
                )
            },
        )

        self.assertEqual(result.candidate_event_count, 1)
        self.assertEqual(result.complete_sample_count, 0)
        self.assertEqual(result.skipped_missing_quote_count, 1)
