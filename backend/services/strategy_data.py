from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

import pandas as pd

from backend.schemas.frontend import StrategyItemResponse, StrategyListResponse
from backend.schemas.strategies import StrategyStudyResponse, StrategyStudyRunRequest
from strategies.chinext_limit_up_workbook import (
    STRATEGY_RESULTS_DIR,
    find_latest_event_study_workbook,
)
from strategies.registry import load_registry
from strategies.run_chinext_limit_up_event_study import run_chinext_limit_up_event_study


STRATEGY_KEY = "chinext_limit_up_event_study"
STRATEGY_TITLE = "创业板涨停后 5 日事件研究"
STRATEGY_DESCRIPTION = (
    "观察创业板涨停事件后第 1、3、5 个交易日的收盘表现。"
    "结果用于历史研究与人工复盘，不代表已验证的交易收益。"
)
RUN_INFO_KEYS = {
    "研究开始日期": "research_start_date",
    "研究结束日期": "research_end_date",
    "候选事件数": "candidate_event_count",
    "完整样本数": "complete_sample_count",
    "未来窗口不足跳过数": "skipped_incomplete_count",
    "行情缺失跳过数": "skipped_missing_quote_count",
    "生成时间": "generated_at",
}



def build_strategy_list() -> StrategyListResponse:
    """把策略注册表原样暴露给前端，前端不需要理解 yaml。"""
    try:
        entries = load_registry()
    except Exception as exc:
        return StrategyListResponse(success=False, strategies=[], error_message=str(exc))

    items = [
        StrategyItemResponse(
            name=entry.name,
            script=entry.script,
            enabled=entry.enabled,
            push=entry.push,
            notes=entry.notes,
        )
        for entry in entries
    ]
    return StrategyListResponse(success=True, strategies=items, error_message=None)

def build_chinext_limit_up_study(
    limit: int = 100,
    base_dir: str = STRATEGY_RESULTS_DIR,
) -> StrategyStudyResponse:
    latest = find_latest_event_study_workbook(base_dir=base_dir)
    if latest is None:
        return _error_response("尚未生成创业板涨停事件研究结果，请先运行一次研究任务。")

    try:
        summary_df = pd.read_excel(latest.file_path, sheet_name="研究摘要")
        details_df = pd.read_excel(latest.file_path, sheet_name="事件明细")
        run_info_df = pd.read_excel(latest.file_path, sheet_name="运行信息")
    except (OSError, ValueError) as exc:
        return _error_response(f"读取策略研究工作簿失败: {exc}")

    details_df = _normalize_date_columns(details_df)
    recent_details = details_df.tail(max(int(limit), 0)).iloc[::-1].reset_index(drop=True)
    summary = _dataframe_records(summary_df)
    details = _dataframe_records(recent_details)
    metadata = _build_metadata(run_info_df, summary, details_df)
    return StrategyStudyResponse(
        success=True,
        strategy_key=STRATEGY_KEY,
        title=STRATEGY_TITLE,
        description=STRATEGY_DESCRIPTION,
        file_name=latest.file_name,
        updated_at=datetime.fromtimestamp(os.path.getmtime(latest.file_path)).strftime("%Y-%m-%d %H:%M:%S"),
        summary=summary,
        metadata=metadata,
        detail_columns=[str(column) for column in recent_details.columns],
        details=details,
        error_message=None,
    )


def _dataframe_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records = []
    for raw_record in frame.astype(object).where(frame.notna(), None).to_dict(orient="records"):
        records.append({str(key): _json_value(value) for key, value in raw_record.items()})
    return records


def _json_value(value: Any) -> Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _date_text(value: Any) -> str:
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.strftime("%Y%m%d")
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def _error_response(message: str) -> StrategyStudyResponse:
    return StrategyStudyResponse(
        success=False,
        strategy_key=STRATEGY_KEY,
        title=STRATEGY_TITLE,
        description=STRATEGY_DESCRIPTION,
        file_name=None,
        updated_at=None,
        summary=[],
        metadata={},
        detail_columns=[],
        details=[],
        error_message=message,
    )
