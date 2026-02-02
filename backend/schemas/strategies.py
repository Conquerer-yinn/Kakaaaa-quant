from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StrategyStudyRunRequest(BaseModel):
    start_date: str | None = Field(default=None, description="可选，事件研究开始日期 YYYYMMDD。")
    end_date: str | None = Field(default=None, description="可选，事件研究结束日期 YYYYMMDD。")


class StrategyStudyResponse(BaseModel):
    success: bool
    strategy_key: str
    title: str
    description: str
    file_name: str | None = None
    updated_at: str | None = None
    summary: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    detail_columns: list[str] = Field(default_factory=list)
    details: list[dict[str, Any]] = Field(default_factory=list)
    error_message: str | None = None
