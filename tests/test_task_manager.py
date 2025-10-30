"""后台任务管理：生命周期、并发防抖、取消。"""
import threading
import time

import backend.services.task_manager as task_manager_module
from backend.schemas.tasks import MarketSentimentRunRequest
from backend.services.task_manager import MarketSentimentTaskManager
from market.jobs.run_market_sentiment import TaskCancelledError


def _wait_terminal(manager, task_id, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = manager.get_task(task_id).status
        if status in {"succeeded", "failed", "cancelled"}:
            return status
        time.sleep(0.05)
    raise AssertionError("task did not reach a terminal status in time")


def test_lifecycle_success(monkeypatch):
    monkeypatch.setattr(task_manager_module, "run_market_sentiment", lambda **kwargs: "输出.xlsx")
    monkeypatch.setattr(task_manager_module, "resolve_market_sentiment_target", lambda request: "目标.xlsx")

    manager = MarketSentimentTaskManager(max_workers=1)
    started = manager.start_task(MarketSentimentRunRequest())

    assert started.created is True
    assert _wait_terminal(manager, started.task_id) == "succeeded"

    final = manager.get_task(started.task_id)
    assert final.result is not None
    assert final.result.success is True
    assert final.result.output_path == "输出.xlsx"


def test_failure_is_captured(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("抓数失败")

    monkeypatch.setattr(task_manager_module, "run_market_sentiment", boom)
    monkeypatch.setattr(task_manager_module, "resolve_market_sentiment_target", lambda request: "目标.xlsx")

    manager = MarketSentimentTaskManager(max_workers=1)
    started = manager.start_task(MarketSentimentRunRequest())

    assert _wait_terminal(manager, started.task_id) == "failed"
    final = manager.get_task(started.task_id)
    assert "抓数失败" in (final.error_message or "")


def test_dedupe_and_cancel(monkeypatch):
    release = threading.Event()

    def blocking(**kwargs):
        should_cancel = kwargs.get("should_cancel")
        release.wait(8)
        if should_cancel and should_cancel():
            raise TaskCancelledError("任务已取消")
        return "p.xlsx"

    monkeypatch.setattr(task_manager_module, "run_market_sentiment", blocking)
    monkeypatch.setattr(task_manager_module, "resolve_market_sentiment_target", lambda request: "目标.xlsx")

    manager = MarketSentimentTaskManager(max_workers=1)
    first = manager.start_task(MarketSentimentRunRequest())
    second = manager.start_task(MarketSentimentRunRequest())

    # 同名任务运行中：不重复创建，直接返回当前任务
    assert second.created is False
    assert second.task_id == first.task_id

    cancelled = manager.cancel_task(first.task_id)
    assert cancelled.cancel_requested is True

    release.set()
    assert _wait_terminal(manager, first.task_id) == "cancelled"
