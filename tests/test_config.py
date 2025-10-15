"""配置模块：环境变量优先，缺省值兜底。"""
import importlib

import common.config as config


def test_defaults(monkeypatch):
    monkeypatch.delenv("TUSHARE_REQUEST_DELAY", raising=False)
    monkeypatch.delenv("DAILY_BASICS_FILE", raising=False)
    monkeypatch.delenv("MARKET_SENTIMENT_HISTORY_PREFIX", raising=False)
    reloaded = importlib.reload(config)

    assert reloaded.TUSHARE_REQUEST_DELAY == 0.5
    assert reloaded.DAILY_BASICS_FILE == "每日基础数据.xlsx"
    assert reloaded.MARKET_SENTIMENT_HISTORY_PREFIX == "历史数据"
    assert reloaded.MASTER_DATA_DIR.endswith("data_master")
    assert reloaded.BACKUP_DIR.endswith("backups")


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("TUSHARE_REQUEST_DELAY", "1.5")
    monkeypatch.setenv("DAILY_BASICS_FILE", "自定义.xlsx")
    reloaded = importlib.reload(config)

    assert reloaded.TUSHARE_REQUEST_DELAY == 1.5
    assert reloaded.DAILY_BASICS_FILE == "自定义.xlsx"

    monkeypatch.undo()
    importlib.reload(config)
