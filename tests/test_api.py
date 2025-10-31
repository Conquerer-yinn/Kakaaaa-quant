"""FastAPI 路由集成冒烟：TestClient 全链路。"""
from fastapi.testclient import TestClient

import backend.api.routes as routes
from backend.main import app
from backend.schemas.frontend import HistoryDatasetResponse, PushCardActionResponse
from backend.schemas.tasks import TaskRunResponse

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["available_task_count"] == 2


def test_tasks_list():
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()["tasks"]) == 2


def test_dashboard_summary():
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["project_name"] == "Kaka_Quant"
    assert len(body["quick_links"]) == 3


def test_market_sentiment_history(monkeypatch):
    fake = HistoryDatasetResponse(success=True, dataset="market-sentiment", sections=[])
    monkeypatch.setattr(routes, "build_market_sentiment_history", lambda limit: fake)

    response = client.get("/market/history/market-sentiment?limit=20")
    assert response.status_code == 200
    assert response.json()["dataset"] == "market-sentiment"


def test_history_limit_validation():
    response = client.get("/market/history/market-sentiment?limit=5")
    assert response.status_code == 422  # limit 下限为 10


def test_daily_basics_run(monkeypatch):
    fake = TaskRunResponse(
        task_name="daily-basics",
        task_type="独立标准任务",
        description="test",
        params={},
        success=True,
        output_target="t.xlsx",
        output_path="p.xlsx",
        error_message=None,
    )
    monkeypatch.setattr(routes, "run_daily_basics_task", lambda request: fake)

    response = client.post("/tasks/daily-basics/run", json={})
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_push_card_refresh(monkeypatch):
    fake = PushCardActionResponse(
        success=True,
        action="refresh",
        card_type="post-close",
        title="盘后复盘",
        status="stable",
        status_label="已稳定可用",
        date="20260102",
        snapshot={},
        card_payload=None,
        send_response=None,
        error_message=None,
    )
    monkeypatch.setattr(routes, "refresh_push_card", lambda **kwargs: fake)

    response = client.post("/market/push/post-close/refresh", json={})
    assert response.status_code == 200
    assert response.json()["card_type"] == "post-close"


def test_unknown_task_returns_404():
    response = client.get("/tasks/market-sentiment/does-not-exist")
    assert response.status_code == 404


def test_strategies_endpoint():
    response = client.get("/strategies")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["strategies"], list)
