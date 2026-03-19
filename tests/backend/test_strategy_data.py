import tempfile
import unittest

import pandas as pd

from backend.schemas.strategies import StrategyStudyRunRequest
from backend.services.strategy_data import (
    build_chinext_limit_up_study,
    run_chinext_limit_up_study,
)
from strategies.chinext_limit_up_event_study import EventStudyResult
from strategies.chinext_limit_up_workbook import write_event_study_workbook


def result_fixture() -> EventStudyResult:
    details = pd.DataFrame(
        [
            {
                "事件日期": "20260105",
                "股票代码": "300001.SZ",
                "股票名称": "样本一",
                "1日收益率(%)": 5.0,
                "3日收益率(%)": 8.0,
                "5日收益率(%)": 10.0,
            },
            {
                "事件日期": "20260106",
                "股票代码": "301002.SZ",
                "股票名称": "样本二",
                "1日收益率(%)": -2.0,
                "3日收益率(%)": 1.0,
                "5日收益率(%)": 4.0,
            },
        ]
    )
    summary = pd.DataFrame(
        [
            {"观察周期": "1日", "样本数": 2, "平均收益率(%)": 1.5, "正收益比例(%)": 50.0},
            {"观察周期": "3日", "样本数": 2, "平均收益率(%)": 4.5, "正收益比例(%)": 100.0},
            {"观察周期": "5日", "样本数": 2, "平均收益率(%)": 7.0, "正收益比例(%)": 100.0},
        ]
    )
    return EventStudyResult(
        details=details,
        summary=summary,
        candidate_event_count=3,
        complete_sample_count=2,
        skipped_incomplete_count=1,
        skipped_missing_quote_count=0,
        missing_benchmark_count=1,
        excluded_st_count=1,
        excluded_recent_listing_count=2,
        missing_stock_basic_count=1,
        group_summary=pd.DataFrame(
            [
                {
                    "分组维度": "连板阶段",
                    "分组": "首板",
                    "观察周期": "5日",
                    "样本数": 2,
                    "平均收益率(%)": 7.0,
                    "平均超额收益率(%)": 3.0,
                }
            ]
        ),
        quality_summary=pd.DataFrame(
            [
                {"质量项目": "候选事件", "数量": 3, "说明": "创业板且涨停"},
                {"质量项目": "排除ST", "数量": 1, "说明": "名称包含ST"},
                {"质量项目": "完整样本", "数量": 2, "说明": "进入统计"},
            ]
        ),
    )


class StrategyDataServiceTest(unittest.TestCase):
    def test_returns_clear_empty_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            response = build_chinext_limit_up_study(base_dir=temp_dir)

        self.assertFalse(response.success)
        self.assertEqual(response.strategy_key, "chinext_limit_up_event_study")
        self.assertIn("尚未生成", response.error_message)
        self.assertEqual(response.details, [])

    def test_reads_latest_workbook_and_limits_recent_details(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_event_study_workbook(
                result_fixture(),
                start_date="20260101",
                end_date="20260331",
                base_dir=temp_dir,
            )

            response = build_chinext_limit_up_study(limit=1, base_dir=temp_dir)

        self.assertTrue(response.success)
        self.assertEqual(response.file_name, "创业板涨停事件研究_20260101_20260331.xlsx")
        self.assertEqual(len(response.summary), 3)
        self.assertEqual(len(response.details), 1)
        self.assertEqual(response.details[0]["事件日期"], "20260106")
        self.assertEqual(response.metadata["candidate_event_count"], 3)
        self.assertEqual(response.metadata["complete_sample_count"], 2)
        self.assertEqual(response.metadata["latest_event_date"], "20260106")
        self.assertEqual(response.metadata["five_day_average_return"], 7.0)
        self.assertEqual(response.metadata["five_day_positive_rate"], 100.0)
        self.assertEqual(response.metadata["missing_benchmark_count"], 1)
        self.assertEqual(response.metadata["excluded_st_count"], 1)
        self.assertEqual(response.metadata["excluded_recent_listing_count"], 2)
        self.assertEqual(response.metadata["missing_stock_basic_count"], 1)
        self.assertEqual(len(response.group_summary), 1)
        self.assertEqual(response.group_summary[0]["分组"], "首板")
        self.assertEqual(len(response.quality_summary), 3)
        self.assertEqual(response.quality_summary[1]["质量项目"], "排除ST")

    def test_run_service_uses_injected_runner_then_returns_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            calls = []

            def fake_runner(start_date, end_date, base_dir):
                calls.append((start_date, end_date, base_dir))
                return write_event_study_workbook(
                    result_fixture(),
                    start_date="20260101",
                    end_date="20260331",
                    base_dir=base_dir,
                )

            response = run_chinext_limit_up_study(
                StrategyStudyRunRequest(start_date="20260101", end_date="20260331"),
                base_dir=temp_dir,
                runner=fake_runner,
            )

        self.assertTrue(response.success)
        self.assertEqual(calls, [("20260101", "20260331", temp_dir)])

    def test_run_service_reads_the_workbook_returned_by_runner(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_event_study_workbook(
                result_fixture(),
                start_date="20261201",
                end_date="20261231",
                base_dir=temp_dir,
            )

            def older_runner(start_date, end_date, base_dir):
                return write_event_study_workbook(
                    result_fixture(),
                    start_date="20260101",
                    end_date="20260131",
                    base_dir=base_dir,
                )

            response = run_chinext_limit_up_study(
                StrategyStudyRunRequest(start_date="20260101", end_date="20260131"),
                base_dir=temp_dir,
                runner=older_runner,
            )

        self.assertTrue(response.success)
        self.assertEqual(response.file_name, "创业板涨停事件研究_20260101_20260131.xlsx")

    def test_run_service_returns_domain_error(self):
        def failing_runner(start_date, end_date, base_dir):
            raise ValueError("TUSHARE_TOKEN is not configured.")

        response = run_chinext_limit_up_study(
            StrategyStudyRunRequest(),
            runner=failing_runner,
        )

        self.assertFalse(response.success)
        self.assertIn("TUSHARE_TOKEN", response.error_message)


if __name__ == "__main__":
    unittest.main()
