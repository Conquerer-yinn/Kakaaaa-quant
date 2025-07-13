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


class PushCardRequest(BaseModel):
    trade_date: str | None = Field(default=None, description="可选，手动指定 YYYYMMDD。")


class PushCardSendRequest(PushCardRequest):
    webhook: str | None = Field(default=None, description="可选，手动覆盖默认 webhook。")


class PushCardItemResponse(BaseModel):
    success: bool
    card_type: str
    title: str
    status: str
    status_label: str
    date: str | None = None
    snapshot: dict[str, Any] = Field(default_factory=dict)
    card_payload: dict[str, Any] | None = None
    error_message: str | None = None


class PushCardListResponse(BaseModel):
    success: bool
    cards: list[PushCardItemResponse] = Field(default_factory=list)
    error_message: str | None = None


class PushCardActionResponse(BaseModel):
    success: bool
    action: str
    card_type: str
    title: str
    status: str
    status_label: str
    date: str | None = None
    snapshot: dict[str, Any] = Field(default_factory=dict)
    card_payload: dict[str, Any] | None = None
    send_response: dict[str, Any] | None = None
    error_message: str | None = None
