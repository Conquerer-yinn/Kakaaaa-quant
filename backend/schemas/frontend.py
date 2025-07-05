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


