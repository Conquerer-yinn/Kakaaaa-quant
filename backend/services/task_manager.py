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

    def cancel_task(self, task_id: str) -> BackgroundTaskStatusResponse:
        with self._lock:
            task = self._get_task_locked(task_id)
            if task.status in {"succeeded", "failed", "cancelled"}:
                return self._serialize_task_locked(task)

            task.cancel_requested = True
            task.cancel_event.set()
            if task.status != "cancelled":
                task.status = "cancelling"
            task.progress_message = "已收到取消请求，等待当前步骤安全结束。"
            return self._serialize_task_locked(task)

    def _run_task(self, task_id: str, request: MarketSentimentRunRequest) -> None:
        with self._lock:
            task = self._get_task_locked(task_id)
            task.status = "running"
            task.started_at = _now_iso()
            task.progress_message = "market-sentiment 正在后台更新。"

        try:
            output_path = run_market_sentiment(
                start_date=request.start_date,
                end_date=request.end_date,
                output_file=resolve_market_sentiment_target(request),
                history_mode=request.history,
                should_cancel=task.cancel_event.is_set,
            )
            result = build_task_run_response(
                metadata=get_task_metadata("market-sentiment"),
                params=request.model_dump(),
                output_target=resolve_market_sentiment_target(request),
                output_path=output_path,
                error_message=None if output_path is not None else "任务未产生新数据或无需更新。",
            )
            with self._lock:
                task = self._get_task_locked(task_id)
                task.result = result
                task.status = "succeeded"
                task.error_message = result.error_message
                task.progress_message = "market-sentiment 已执行完成。" if result.success else (result.error_message or "market-sentiment 已执行完成。")
                task.finished_at = _now_iso()
        except TaskCancelledError as exc:
            with self._lock:
                task = self._get_task_locked(task_id)
                task.status = "cancelled"
                task.error_message = str(exc)
                task.progress_message = "market-sentiment 已取消。"
                task.finished_at = _now_iso()
                task.result = build_task_run_response(
                    metadata=get_task_metadata("market-sentiment"),
                    params=request.model_dump(),
                    output_target=resolve_market_sentiment_target(request),
                    output_path=None,
                    error_message=str(exc),
                )
        except Exception as exc:
            with self._lock:
                task = self._get_task_locked(task_id)
                task.status = "failed"
                task.error_message = str(exc)
                task.progress_message = "market-sentiment 执行失败。"
                task.finished_at = _now_iso()
                task.result = build_task_run_response(
                    metadata=get_task_metadata("market-sentiment"),
                    params=request.model_dump(),
                    output_target=resolve_market_sentiment_target(request),
                    output_path=None,
                    error_message=str(exc),
                )

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


