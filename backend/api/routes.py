from fastapi import APIRouter, HTTPException

from backend.schemas.tasks import (
    BackgroundTaskStartResponse,
    BackgroundTaskStatusResponse,
    DailyBasicsRunRequest,
    HealthResponse,
    MarketSentimentRunRequest,
    TaskListResponse,
    TaskRunResponse,
)
from backend.services.task_manager import market_sentiment_task_manager
from backend.services.task_registry import list_task_metadata
from backend.services.task_runner import run_daily_basics_task


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


@router.post("/tasks/daily-basics/run", response_model=TaskRunResponse, tags=["tasks"])
def run_daily_basics(request: DailyBasicsRunRequest):
    return run_daily_basics_task(request)


@router.post("/tasks/market-sentiment/run", response_model=BackgroundTaskStartResponse, tags=["tasks"])
def run_market_sentiment(request: MarketSentimentRunRequest):
    return market_sentiment_task_manager.start_task(request)


@router.get("/tasks/market-sentiment/{task_id}", response_model=BackgroundTaskStatusResponse, tags=["tasks"])
def get_market_sentiment_task(task_id: str):
    try:
        return market_sentiment_task_manager.get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"未找到任务 {task_id}") from exc


@router.post("/tasks/market-sentiment/{task_id}/cancel", response_model=BackgroundTaskStatusResponse, tags=["tasks"])
def cancel_market_sentiment_task(task_id: str):
    try:
        return market_sentiment_task_manager.cancel_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"未找到任务 {task_id}") from exc
