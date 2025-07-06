from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SummaryLink(BaseModel):
    label: str = Field(..., description="首页入口文案。")
    path: str = Field(..., description="前端页面路径。")
    description: str = Field(..., description="入口对应说明。")


class SummaryCapability(BaseModel):
    title: str = Field(..., description="能力标题。")
    description: str = Field(..., description="能力说明。")
    status: str = Field(..., description="状态，如 stable / v1 / planning。")


class DashboardSummaryResponse(BaseModel):
    success: bool
    project_name: str
    project_positioning: str
    main_lines: list[dict[str, str]]
    capability_summary: list[SummaryCapability]
    quick_links: list[SummaryLink]


class HistorySectionResponse(BaseModel):
    key: str = Field(..., description="前端内部使用的分区键。")
    title: str = Field(..., description="展示标题。")
    columns: list[str] = Field(default_factory=list, description="表格列名。")
    rows: list[dict[str, Any]] = Field(default_factory=list, description="数据行。")


class HistoryDatasetResponse(BaseModel):
    success: bool
    dataset: str
    file_name: str | None = None
    updated_at: str | None = None
    sections: list[HistorySectionResponse] = Field(default_factory=list)
    error_message: str | None = None


