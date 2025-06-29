from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from threading import Event, Lock
from typing import Any
from uuid import uuid4

from backend.schemas.tasks import BackgroundTaskStartResponse, BackgroundTaskStatusResponse, MarketSentimentRunRequest, TaskRunResponse
from backend.services.task_registry import get_task_metadata
from backend.services.task_runner import build_task_run_response, resolve_market_sentiment_target
from market.jobs.run_market_sentiment import TaskCancelledError, run_market_sentiment


ACTIVE_TASK_STATUSES = {"pending", "running", "cancelling"}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class ManagedTask:
    task_id: str
    task_name: str
    task_type: str
    description: str
    params: dict[str, Any]
    output_target: str
    status: str = "pending"
    progress_message: str | None = None
    error_message: str | None = None
    cancel_requested: bool = False
    created_at: str = field(default_factory=_now_iso)
    started_at: str | None = None
    finished_at: str | None = None
    result: TaskRunResponse | None = None
    cancel_event: Event = field(default_factory=Event, repr=False)
    future: Future | None = field(default=None, repr=False)


class MarketSentimentTaskManager:
    def __init__(self, max_workers: int = 2):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="market-sentiment")
        self._lock = Lock()
        self._tasks: dict[str, ManagedTask] = {}

    def start_task(self, request: MarketSentimentRunRequest) -> BackgroundTaskStartResponse:
        metadata = get_task_metadata("market-sentiment")
        with self._lock:
            existing = self._find_active_task_locked(metadata.task_name)
            if existing is not None:
                return BackgroundTaskStartResponse(created=False, **self._serialize_task_locked(existing).model_dump())

            task = ManagedTask(
                task_id=uuid4().hex,
                task_name=metadata.task_name,
                task_type=metadata.task_type,
                description=metadata.description,
                params=request.model_dump(),
                output_target=resolve_market_sentiment_target(request),
                progress_message="任务已创建，等待后台执行。",
            )
            self._tasks[task.task_id] = task
            task.future = self._executor.submit(self._run_task, task.task_id, request)
            return BackgroundTaskStartResponse(created=True, **self._serialize_task_locked(task).model_dump())

    def get_task(self, task_id: str) -> BackgroundTaskStatusResponse:
        with self._lock:
            task = self._get_task_locked(task_id)
            return self._serialize_task_locked(task)

    def _get_task_locked(self, task_id: str) -> ManagedTask:
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(task_id)
        return task

    def _serialize_task_locked(self, task: ManagedTask) -> BackgroundTaskStatusResponse:
        return BackgroundTaskStatusResponse(
            task_id=task.task_id,
            task_name=task.task_name,
            task_type=task.task_type,
            description=task.description,
            status=task.status,
            params=task.params,
            output_target=task.output_target,
            progress_message=task.progress_message,
            error_message=task.error_message,
            cancel_requested=task.cancel_requested,
            created_at=task.created_at,
            started_at=task.started_at,
            finished_at=task.finished_at,
            result=task.result,
        )


market_sentiment_task_manager = MarketSentimentTaskManager()


