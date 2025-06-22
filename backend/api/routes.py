from fastapi import APIRouter

from backend.schemas.tasks import (
    HealthResponse,
    TaskListResponse,
)
from backend.services.task_registry import list_task_metadata


router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health_check():
    tasks = list_task_metadata()
    return HealthResponse(
        status="ok",
        service="Kaka_Quant API",
        available_task_count=len(tasks),
    )


@router.get("/tasks", response_model=TaskListResponse, tags=["tasks"])
def get_tasks():
    return TaskListResponse(tasks=list_task_metadata())
