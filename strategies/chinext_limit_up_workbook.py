from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from common.config import BASE_DIR
from storage.excel_helper import ExcelHelper
from strategies.chinext_limit_up_event_study import EventStudyResult


EVENT_STUDY_PREFIX = "创业板涨停事件研究"
STRATEGY_RESULTS_DIR = os.getenv(
    "STRATEGY_RESULTS_DIR",
    os.path.join(BASE_DIR, "storage", "strategy_results"),
)
FILE_PATTERN = re.compile(
    rf"^{re.escape(EVENT_STUDY_PREFIX)}_(?P<start>\d{{8}})_(?P<end>\d{{8}})\.xlsx$"
)


@dataclass(frozen=True)
class EventStudyWorkbook:
    file_name: str
    start_date: str
    end_date: str
    file_path: str


def build_event_study_file_name(start_date: str, end_date: str) -> str:
    return f"{EVENT_STUDY_PREFIX}_{start_date}_{end_date}.xlsx"


def write_event_study_workbook(
    result: EventStudyResult,
    start_date: str,
    end_date: str,
    base_dir: str = STRATEGY_RESULTS_DIR,
) -> str:
    file_name = build_event_study_file_name(start_date, end_date)
    run_info = pd.DataFrame(
        [
            {"字段": "研究开始日期", "值": start_date},
            {"字段": "研究结束日期", "值": end_date},
            {"字段": "候选事件数", "值": result.candidate_event_count},
            {"字段": "完整样本数", "值": result.complete_sample_count},
            {"字段": "未来窗口不足跳过数", "值": result.skipped_incomplete_count},
            {"字段": "行情缺失跳过数", "值": result.skipped_missing_quote_count},
            {"字段": "生成时间", "值": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        ]
    )
    return ExcelHelper.upsert_data_workbook(
        file_name=file_name,
        sheets={
            "研究摘要": result.summary,
            "事件明细": result.details,
            "运行信息": run_info,
        },
        table_names={
            "研究摘要": "ChinextEventSummary",
            "事件明细": "ChinextEventDetails",
            "运行信息": "ChinextEventRunInfo",
        },
        base_dir=base_dir,
    )


def find_latest_event_study_workbook(
    base_dir: str = STRATEGY_RESULTS_DIR,
) -> EventStudyWorkbook | None:
    if not os.path.isdir(base_dir):
        return None

    workbooks = []
    for file_name in os.listdir(base_dir):
        match = FILE_PATTERN.fullmatch(file_name)
        if match is None:
            continue
        workbooks.append(
            EventStudyWorkbook(
                file_name=file_name,
                start_date=match.group("start"),
                end_date=match.group("end"),
                file_path=os.path.join(base_dir, file_name),
            )
        )

    if not workbooks:
        return None
    return max(workbooks, key=lambda item: (item.end_date, item.start_date, item.file_name))
