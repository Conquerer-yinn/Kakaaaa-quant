"""任务注册表与同步执行器。"""
import backend.services.task_runner as task_runner
from backend.schemas.tasks import DailyBasicsRunRequest
from backend.services.task_registry import get_task_metadata, list_task_metadata


def test_registry_contains_two_tasks():
    tasks = list_task_metadata()
    assert len(tasks) == 2
    assert get_task_metadata("daily-basics").task_type == "独立标准任务"
    assert get_task_metadata("market-sentiment").task_type == "综合研究任务"


def test_daily_basics_success(monkeypatch):
    monkeypatch.setattr(task_runner, "run_daily_basics", lambda **kwargs: "out.xlsx")
    response = task_runner.run_daily_basics_task(DailyBasicsRunRequest())

    assert response.success is True
    assert response.output_path == "out.xlsx"
    assert response.error_message is None


def test_daily_basics_no_new_data(monkeypatch):
    monkeypatch.setattr(task_runner, "run_daily_basics", lambda **kwargs: None)
    response = task_runner.run_daily_basics_task(DailyBasicsRunRequest())

    assert response.success is False
    assert "未产生新数据" in (response.error_message or "")


def test_daily_basics_exception_is_captured(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("接口失败")

    monkeypatch.setattr(task_runner, "run_daily_basics", boom)
    response = task_runner.run_daily_basics_task(DailyBasicsRunRequest())

    assert response.success is False
    assert "接口失败" in (response.error_message or "")


def test_output_target_prefers_request_file(monkeypatch):
    monkeypatch.setattr(task_runner, "run_daily_basics", lambda **kwargs: "out.xlsx")
    response = task_runner.run_daily_basics_task(DailyBasicsRunRequest(output_file="自定义.xlsx"))
    assert response.output_target == "自定义.xlsx"
