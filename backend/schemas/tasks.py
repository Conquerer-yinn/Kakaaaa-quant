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


TaskExecutionStatus = Literal["pending", "running", "cancelling", "cancelled", "succeeded", "failed"]


