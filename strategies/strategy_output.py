"""策略输出统一封装。

所有策略复盘表统一使用 `策略数据_策略名.xlsx` 命名并通过 storage 层落盘，
避免各策略自行发明文件规则。
"""
from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from storage.excel_helper import ExcelHelper

STRATEGY_OUTPUT_PREFIX = "策略数据"


def build_strategy_output_name(strategy_name: str) -> str:
    return f"{STRATEGY_OUTPUT_PREFIX}_{strategy_name}.xlsx"


def write_strategy_result(df, strategy_name: str, dedupe_subset=None, base_dir=None):
    """把策略结果追加进该策略的复盘主表，返回输出路径。"""
    if df is None or df.empty:
        return None

    kwargs = {
        "df": df,
        "file_name": build_strategy_output_name(strategy_name),
        "dedupe_subset": dedupe_subset or ["日期", "ts_code"],
    }
    if base_dir:
        kwargs["base_dir"] = base_dir
    return ExcelHelper.append_rows(**kwargs)
