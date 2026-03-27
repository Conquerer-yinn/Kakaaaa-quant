import unittest

import pandas as pd

from strategies import chinext_limit_up_event_study as event_study_module
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
    def test_filters_st_and_recent_listings_and_reports_quality(self):
        codes = ["300001.SZ", "300002.SZ", "301003.SZ", "301004.SZ"]
        daily_by_date = {
            trade_date: daily_frame(
                **{ts_code: 10.0 + index for ts_code in codes}
            )
            for index, trade_date in enumerate(TRADE_DATES)
        }
        stock_basic_df = pd.DataFrame(
            [
                {"ts_code": "300001.SZ", "name": "正常样本", "list_date": "20200101"},
                {"ts_code": "300002.SZ", "name": "*ST风险", "list_date": "20200101"},
                {"ts_code": "301003.SZ", "name": "次新样本", "list_date": "20251220"},
            ]
        )

        result = build_event_study(
            trade_dates=TRADE_DATES,
            event_start_date="20260105",
            event_end_date="20260105",
            daily_by_date=daily_by_date,
            limit_by_date={
                "20260105": limit_frame(
                    {"ts_code": "300001.SZ", "name": "正常样本", "limit": "U", "limit_times": 1},
                    {"ts_code": "300002.SZ", "name": "*ST风险", "limit": "U", "limit_times": 1},
                    {"ts_code": "301003.SZ", "name": "次新样本", "limit": "U", "limit_times": 1},
                    {"ts_code": "301004.SZ", "name": "信息缺失", "limit": "U", "limit_times": 1},
                )
            },
            stock_basic_df=stock_basic_df,
        )

        self.assertEqual(result.candidate_event_count, 4)
        self.assertEqual(result.complete_sample_count, 2)
        self.assertEqual(result.excluded_st_count, 1)
        self.assertEqual(result.excluded_recent_listing_count, 1)
        self.assertEqual(result.missing_stock_basic_count, 1)
        self.assertEqual(
            set(result.details["股票代码"]),
            {"300001.SZ", "301004.SZ"},
        )
        quality = dict(zip(result.quality_summary["质量项目"], result.quality_summary["数量"]))
        self.assertEqual(quality["排除ST"], 1)
        self.assertEqual(quality["排除上市未满60天"], 1)
        self.assertEqual(quality["股票基础信息缺失"], 1)
        self.assertEqual(quality["完整样本"], 2)

    def test_assigns_board_stage_and_builds_group_summary(self):
        daily_by_date = {
            trade_date: daily_frame(**{"300001.SZ": 10.0 + index, "301002.SZ": 20.0 + index})
            for index, trade_date in enumerate(TRADE_DATES)
        }

        result = build_event_study(
            trade_dates=TRADE_DATES,
            event_start_date="20260105",
            event_end_date="20260105",
            daily_by_date=daily_by_date,
            limit_by_date={
                "20260105": limit_frame(
                    {"ts_code": "300001.SZ", "name": "首板样本", "limit": "U", "limit_times": 1},
                    {"ts_code": "301002.SZ", "name": "连板样本", "limit": "U", "limit_times": 2},
                )
            },
            market_regime_by_date={"20260105": "强"},
        )

        stages = dict(zip(result.details["股票代码"], result.details["连板阶段"]))
        self.assertEqual(stages, {"300001.SZ": "首板", "301002.SZ": "连板"})
        self.assertEqual(set(result.details["市场环境"]), {"强"})
        five_day_groups = result.group_summary.loc[result.group_summary["观察周期"] == "5日"]
        stage_counts = dict(
            zip(
                five_day_groups.loc[five_day_groups["分组维度"] == "连板阶段", "分组"],
                five_day_groups.loc[five_day_groups["分组维度"] == "连板阶段", "样本数"],
            )
        )
        regime_row = five_day_groups.loc[
            (five_day_groups["分组维度"] == "市场环境")
            & (five_day_groups["分组"] == "强")
        ].iloc[0]
        self.assertEqual(stage_counts, {"首板": 1, "连板": 1})
        self.assertEqual(regime_row["样本数"], 2)

    def test_market_regime_thresholds_are_explicit(self):
        self.assertEqual(event_study_module.classify_market_regime(0), "弱")
        self.assertEqual(event_study_module.classify_market_regime(30), "弱")
        self.assertEqual(event_study_module.classify_market_regime(31), "中")
        self.assertEqual(event_study_module.classify_market_regime(60), "中")
        self.assertEqual(event_study_module.classify_market_regime(61), "强")

    def test_calculates_benchmark_and_excess_returns(self):
        daily_by_date = {
            "20260105": daily_frame(**{"300001.SZ": 10.0}),
            "20260106": daily_frame(**{"300001.SZ": 11.0}),
            "20260107": daily_frame(**{"300001.SZ": 9.0}),
            "20260108": daily_frame(**{"300001.SZ": 12.0}),
            "20260109": daily_frame(**{"300001.SZ": 8.0}),
            "20260112": daily_frame(**{"300001.SZ": 11.0}),
        }
        benchmark_close_by_date = {
            "20260105": 100.0,
            "20260106": 101.0,
            "20260107": 102.0,
            "20260108": 103.0,
            "20260109": 104.0,
            "20260112": 105.0,
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
            benchmark_close_by_date=benchmark_close_by_date,
        )

        row = result.details.iloc[0]
        self.assertEqual(row["1日基准收益率(%)"], 1.0)
        self.assertEqual(row["1日超额收益率(%)"], 9.0)
        self.assertEqual(row["3日基准收益率(%)"], 3.0)
        self.assertEqual(row["3日超额收益率(%)"], 17.0)
        self.assertEqual(row["5日基准收益率(%)"], 5.0)
        self.assertEqual(row["5日超额收益率(%)"], 5.0)
        five_day = result.summary.loc[result.summary["观察周期"] == "5日"].iloc[0]
        self.assertEqual(five_day["基准平均收益率(%)"], 5.0)
        self.assertEqual(five_day["平均超额收益率(%)"], 5.0)
        self.assertEqual(five_day["超额正收益比例(%)"], 100.0)
        self.assertEqual(result.missing_benchmark_count, 0)

    def test_keeps_raw_returns_when_benchmark_is_missing(self):
        daily_by_date = {
            trade_date: daily_frame(**{"300001.SZ": 10.0 + index})
            for index, trade_date in enumerate(TRADE_DATES)
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
            benchmark_close_by_date={},
        )

        row = result.details.iloc[0]
        self.assertEqual(row["5日收益率(%)"], 50.0)
        self.assertTrue(pd.isna(row["5日基准收益率(%)"]))
        self.assertTrue(pd.isna(row["5日超额收益率(%)"]))
        self.assertEqual(result.missing_benchmark_count, 1)

    def test_calculates_available_horizons_when_later_benchmark_is_missing(self):
        daily_by_date = {
            trade_date: daily_frame(**{"300001.SZ": 10.0 + index})
            for index, trade_date in enumerate(TRADE_DATES)
        }
        benchmark_close_by_date = {
            "20260105": 100.0,
            "20260106": 101.0,
            "20260107": 102.0,
            "20260108": 103.0,
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
            benchmark_close_by_date=benchmark_close_by_date,
        )

        row = result.details.iloc[0]
        self.assertEqual(row["1日基准收益率(%)"], 1.0)
        self.assertEqual(row["1日超额收益率(%)"], 9.0)
        self.assertEqual(row["3日基准收益率(%)"], 3.0)
        self.assertEqual(row["3日超额收益率(%)"], 27.0)
        self.assertTrue(pd.isna(row["5日基准收益率(%)"]))
        self.assertTrue(pd.isna(row["5日超额收益率(%)"]))
        self.assertEqual(result.missing_benchmark_count, 1)

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

    def test_empty_result_preserves_detail_and_summary_columns(self):
        result = build_event_study(
            trade_dates=TRADE_DATES,
            event_start_date="20260105",
            event_end_date="20260105",
            daily_by_date={},
            limit_by_date={},
        )

        self.assertEqual(result.details.columns.tolist(), DETAIL_COLUMNS)
        self.assertEqual(result.summary.columns.tolist(), SUMMARY_COLUMNS)
        self.assertEqual(result.summary["观察周期"].tolist(), ["1日", "3日", "5日"])
        self.assertEqual(result.summary["样本数"].tolist(), [0, 0, 0])


if __name__ == "__main__":
    unittest.main()
