from fastapi import APIRouter, HTTPException, Query

from backend.schemas.frontend import (
    DashboardSummaryResponse,
    HistoryDatasetResponse,
    PushCardActionResponse,
    PushCardListResponse,
    PushCardRequest,
    PushCardSendRequest,
    StrategyListResponse,
)
from backend.schemas.tasks import (
    BackgroundTaskStartResponse,
    BackgroundTaskStatusResponse,
    DailyBasicsRunRequest,
    HealthResponse,
    MarketSentimentRunRequest,
    TaskListResponse,
    TaskRunResponse,
)
from backend.schemas.strategies import StrategyStudyResponse, StrategyStudyRunRequest
from backend.services.frontend_data import build_dashboard_summary, build_market_sentiment_history
from backend.services.push_cards import list_push_cards, refresh_push_card, send_push_card
from backend.services.strategy_data import (
    build_chinext_limit_up_study,
    build_strategy_list,
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


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse, tags=["frontend"])
def get_dashboard_summary():
    # 首页目前只消费静态定位信息和已落地能力，不把后端做成复杂概览平台。
    return build_dashboard_summary()


@router.get("/market/history/market-sentiment", response_model=HistoryDatasetResponse, tags=["frontend"])
def get_market_sentiment_history(limit: int = Query(default=20, ge=10, le=120)):
    return build_market_sentiment_history(limit=limit)


@router.get(
    "/strategies/chinext-limit-up-event-study",
    response_model=StrategyStudyResponse,
    tags=["strategies"],
)
def get_chinext_limit_up_event_study(limit: int = Query(default=100, ge=10, le=500)):
    return build_chinext_limit_up_study(limit=limit)


@router.get("/market/push/cards", response_model=PushCardListResponse, tags=["frontend"])
def get_push_cards():
    return list_push_cards()


@router.get("/strategies", response_model=StrategyListResponse, tags=["frontend"])
def get_strategies():
    return build_strategy_list()


@router.post("/market/push/post-close/refresh", response_model=PushCardActionResponse, tags=["frontend"])
def refresh_post_close_card(request: PushCardRequest):
    return refresh_push_card(card_type="post-close", trade_date=request.trade_date)


@router.post("/market/push/post-close/send", response_model=PushCardActionResponse, tags=["frontend"])
def send_post_close_card(request: PushCardSendRequest):
    return send_push_card(card_type="post-close", trade_date=request.trade_date, webhook=request.webhook)


@router.post("/market/push/auction/refresh", response_model=PushCardActionResponse, tags=["frontend"])
def refresh_auction_card(request: PushCardRequest):
    return refresh_push_card(card_type="auction", trade_date=request.trade_date)


@router.post("/market/push/auction/send", response_model=PushCardActionResponse, tags=["frontend"])
def send_auction_card(request: PushCardSendRequest):
    return send_push_card(card_type="auction", trade_date=request.trade_date, webhook=request.webhook)


@router.post("/market/push/intraday/refresh", response_model=PushCardActionResponse, tags=["frontend"])
def refresh_intraday_card(request: PushCardRequest):
    return refresh_push_card(card_type="intraday", trade_date=request.trade_date)


@router.post("/market/push/intraday/send", response_model=PushCardActionResponse, tags=["frontend"])
def send_intraday_card(request: PushCardSendRequest):
    return send_push_card(card_type="intraday", trade_date=request.trade_date, webhook=request.webhook)


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
