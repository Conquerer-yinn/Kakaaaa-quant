from typing import Any, Literal

from pydantic import BaseModel, Field


class AcceptedParam(BaseModel):
    name: str = Field(..., description="参数名")
    required: bool = Field(..., description="是否必填")
    description: str = Field(..., description="参数说明")


class TaskMetadata(BaseModel):
    # 任务元数据主要给 /tasks 和前端展示使用。
    task_name: str = Field(..., description="任务唯一名称")
    task_type: str = Field(..., description="任务类型：独立标准任务或综合研究任务")
    description: str = Field(..., description="任务简介")
    accepted_params: list[AcceptedParam] = Field(default_factory=list, description="任务支持的参数。")
    output_target: str = Field(..., description="默认输出目标")


class HealthResponse(BaseModel):
    status: str
    service: str
    available_task_count: int


class TaskListResponse(BaseModel):
    tasks: list[TaskMetadata]


class DailyBasicsRunRequest(BaseModel):
    start_date: str | None = Field(default=None, description="YYYYMMDD. 不传时走增量更新。")
    end_date: str | None = Field(default=None, description="YYYYMMDD. 不传时默认到今天。")
    output_file: str | None = Field(default=None, description="可选，手动指定输出文件名。")


class MarketSentimentRunRequest(BaseModel):
    start_date: str | None = Field(default=None, description="YYYYMMDD. 不传时走增量更新或 bootstrap。")
    end_date: str | None = Field(default=None, description="YYYYMMDD. 不传时默认到今天。")
    output_file: str | None = Field(default=None, description="可选，手动指定输出文件名。")
    history: bool = Field(default=True, description="默认为 true，更新历史主表；为 false 时生成测试数据工作簿。")


class TaskRunResponse(BaseModel):
    task_name: str
    task_type: str
    description: str
    params: dict[str, Any]
    success: bool
    output_target: str
    output_path: str | None = None
    error_message: str | None = None


TaskExecutionStatus = Literal["pending", "running", "cancelling", "cancelled", "succeeded", "failed"]


