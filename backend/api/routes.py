from fastapi import APIRouter

from backend.schemas.tasks import (
    DailyBasicsRunRequest,
    HealthResponse,
    MarketSentimentRunRequest,
    TaskListResponse,
    TaskRunResponse,
)
from backend.services.task_registry import list_task_metadata
from backend.services.task_runner import run_daily_basics_task, run_market_sentiment_task


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


@router.post("/tasks/market-sentiment/run", response_model=TaskRunResponse, tags=["tasks"])
def run_market_sentiment(request: MarketSentimentRunRequest):
    return run_market_sentiment_task(request)
