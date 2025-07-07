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



