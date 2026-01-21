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


