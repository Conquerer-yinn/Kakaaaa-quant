from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StrategyStudyRunRequest(BaseModel):
    start_date: str | None = Field(default=None, description="可选，事件研究开始日期 YYYYMMDD。")
    end_date: str | None = Field(default=None, description="可选，事件研究结束日期 YYYYMMDD。")


