"""数据引擎：token 校验、日历排序、限流重试。"""
import pandas as pd
import pytest

import data_engine.tushare_api as tushare_api
from data_engine.tushare_api import TushareDataEngine


class FakePro:
    def trade_cal(self, **kwargs):
        return pd.DataFrame({"cal_date": ["20260102", "20260101"]})


@pytest.fixture
def engine(monkeypatch):
    monkeypatch.setattr(tushare_api.ts, "pro_api", lambda token: FakePro())
    monkeypatch.setattr(tushare_api.time, "sleep", lambda seconds: None)
    return TushareDataEngine(token="dummy-token", request_delay=0)


def test_requires_token(monkeypatch):
    monkeypatch.setattr(tushare_api, "TUSHARE_TOKEN", None)
    with pytest.raises(ValueError):
        TushareDataEngine(token=None)


def test_trade_calendar_sorted(engine):
    assert engine.get_trade_calendar("20260101", "20260102") == ["20260101", "20260102"]


def test_retry_on_rate_limit(engine):
    attempts = {"n": 0}

    def flaky(**kwargs):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("抱歉，您每分钟最多访问该接口2次")
        return pd.DataFrame({"ok": [1]})

    result = engine._call_with_retry(flaky)
    assert attempts["n"] == 3
    assert not result.empty


def test_no_retry_on_business_error(engine):
    attempts = {"n": 0}

    def broken(**kwargs):
        attempts["n"] += 1
        raise ValueError("参数错误")

    with pytest.raises(ValueError):
        engine._call_with_retry(broken)
    assert attempts["n"] == 1


def test_should_retry_keywords(engine):
    assert engine._should_retry(RuntimeError("请求超时")) is True
    assert engine._should_retry(RuntimeError("普通业务异常")) is False
