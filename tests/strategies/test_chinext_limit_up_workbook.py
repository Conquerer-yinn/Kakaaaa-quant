import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from strategies.chinext_limit_up_event_study import EventStudyResult
from strategies.chinext_limit_up_workbook import (
    build_event_study_file_name,
    find_latest_event_study_workbook,
    write_event_study_workbook,
)


def sample_result() -> EventStudyResult:
    return EventStudyResult(
        details=pd.DataFrame(
            [
                {
                    "事件日期": "20260105",
                    "股票代码": "300001.SZ",
                    "股票名称": "样本一",
                    "5日收益率(%)": 10.0,
                }
            ]
        ),
        summary=pd.DataFrame(
            [{"观察周期": "5日", "样本数": 1, "平均收益率(%)": 10.0}]
        ),
        candidate_event_count=2,
        complete_sample_count=1,
        skipped_incomplete_count=1,
        skipped_missing_quote_count=0,
    )


class ChinextLimitUpWorkbookTest(unittest.TestCase):
    def test_builds_stable_file_name(self):
        self.assertEqual(
            build_event_study_file_name("20260101", "20260331"),
            "创业板涨停事件研究_20260101_20260331.xlsx",
        )
