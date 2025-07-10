from __future__ import annotations

import os
from datetime import datetime

from backend.schemas.frontend import (
    DashboardSummaryResponse,
    HistoryDatasetResponse,
    HistorySectionResponse,
    SummaryCapability,
    SummaryLink,
)
from common.config import (
    MARKET_SENTIMENT_CHINEXT_SHEET,
    MARKET_SENTIMENT_HEIGHT_SHEET,
    MARKET_SENTIMENT_MARKET_SHEET,
)
from market.services.market_sentiment_workbook import find_latest_history_workbook
from storage.excel_helper import ExcelHelper


DEFAULT_HISTORY_LIMIT = 20



def build_dashboard_summary() -> DashboardSummaryResponse:
    """首页概览只保留当前阶段最值得展示的真实能力。"""
    return DashboardSummaryResponse(
        success=True,
        project_name="Kaka_Quant",
        project_positioning="面向 A 股研究工作流的轻量量化研究工作台，当前以 Excel 为主输出，并逐步补齐 API、消息推送与前端展示。",
        main_lines=[
            {
                "title": "market",
                "description": "围绕行情、情绪、盘中盘后观察，逐步沉淀可复用指标与卡片展示。",
            },
            {
                "title": "strategies",
                "description": "围绕策略研究、历史筛选、Excel 复盘与后续成熟策略日常运行。",
            },
        ],
        capability_summary=[
            SummaryCapability(
                title="市场情绪历史数据",
                description="前端当前重点展示历史主表里的总市场数据、高度观察、创业板专区三块真实结果。",
                status="stable",
            ),
            SummaryCapability(
                title="消息推送链路",
                description="盘后、竞价、盘中三类卡片统一通过后端接口预览、刷新与发送。",
                status="v1",
            ),
            SummaryCapability(
                title="前端展示壳",
                description="这一版先服务真实演示与 review，不往重后台方向扩张。",
                status="v1",
            ),
        ],
        quick_links=[
            SummaryLink(label="历史数据", path="/market/history", description="查看历史主表里最近 20 个交易日数据。"),
            SummaryLink(label="推送卡片", path="/market/push", description="预览三类卡片，执行刷新与发送。"),
            SummaryLink(label="策略占位", path="/strategies", description="查看策略方向说明与后续规划。"),
        ],
    )



def build_market_sentiment_history(limit: int = DEFAULT_HISTORY_LIMIT) -> HistoryDatasetResponse:
    """历史页只返回 market-sentiment 三个核心 sheet，并过滤前端不需要的冗余列。"""
    file_name = _resolve_market_sentiment_file()
    if not file_name:
        return HistoryDatasetResponse(
            success=False,
            dataset="market-sentiment",
            file_name="",
            updated_at=None,
            sections=[],
            error_message="当前未找到可展示的市场情绪历史主表，请先运行 market-sentiment 更新任务。",
        )

    sections: list[HistorySectionResponse] = []
    for key, title, sheet_name in (
        ("market_overview", "总市场数据", MARKET_SENTIMENT_MARKET_SHEET),
        ("height_observation", "高度观察", MARKET_SENTIMENT_HEIGHT_SHEET),
        ("chinext_sentiment", "创业板专区", MARKET_SENTIMENT_CHINEXT_SHEET),
    ):
        section = _build_history_section(
            key=key,
            title=title,
            file_name=file_name,
            sheet_name=sheet_name,
            limit=limit,
        )
        if section is not None:
            sections.append(section)

    if not sections:
        return HistoryDatasetResponse(
            success=False,
            dataset="market-sentiment",
            file_name=file_name,
            updated_at=_get_file_updated_at(file_name),
            sections=[],
            error_message="当前未找到可展示的市场情绪历史主表，请先运行 market-sentiment 更新任务。",
        )

    return HistoryDatasetResponse(
        success=True,
        dataset="market-sentiment",
        file_name=file_name,
        updated_at=_get_file_updated_at(file_name),
        sections=sections,
        error_message=None,
    )



def _build_history_section(
    key: str,
    title: str,
    file_name: str,
    sheet_name: str,
    limit: int,
) -> HistorySectionResponse | None:
    df = ExcelHelper.read_sheet(file_name, sheet_name)
    if df is None or df.empty:
        return None

    display_columns = _pick_display_columns(df.columns.tolist())
    preview_df = df[display_columns].tail(limit).copy().reset_index(drop=True)
    preview_df = preview_df.where(preview_df.notna(), None)
    return HistorySectionResponse(
        key=key,
        title=title,
        columns=[str(column) for column in preview_df.columns.tolist()],
        rows=preview_df.to_dict(orient="records"),
    )



def _pick_display_columns(columns: list[str]) -> list[str]:
    return [
        str(column)
        for column in columns
        if "位置" not in str(column) and "相对中枢" not in str(column)
    ]



def _resolve_market_sentiment_file() -> str:
    latest_history = find_latest_history_workbook()
    if latest_history is not None:
        return latest_history.file_name
    return ""



def _get_file_updated_at(file_name: str) -> str | None:
    if not file_name:
        return None
    file_path = ExcelHelper.build_master_path(file_name)
    if not os.path.exists(file_path):
        return None
    return datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")

