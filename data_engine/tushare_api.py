import time

import requests
import tushare as ts

from common.config import TUSHARE_HTTP_URL, TUSHARE_REQUEST_DELAY, TUSHARE_TOKEN


class TushareDataEngine:
    """Tushare 数据访问封装。"""

    def __init__(self, token=None, http_url=None, request_delay=None, max_retries=3):
        resolved_token = token or TUSHARE_TOKEN
        if not resolved_token:
            raise ValueError("TUSHARE_TOKEN is not configured.")

        self.request_delay = (
            TUSHARE_REQUEST_DELAY if request_delay is None else request_delay
        )
        self.max_retries = max_retries
        self.pro = ts.pro_api(resolved_token)

        # 兼容需要自定义 Tushare 网关的环境。
        if http_url or TUSHARE_HTTP_URL:
            self.pro._DataApi__token = resolved_token
            self.pro._DataApi__http_url = http_url or TUSHARE_HTTP_URL

    def get_trade_calendar(self, start_date, end_date, exchange="SSE"):
        # 交易日历是所有增量任务的时间基准。
        df = self._call_with_retry(
            self.pro.trade_cal,
            exchange=exchange,
            start_date=start_date,
            end_date=end_date,
            is_open=1,
        )
        if df.empty:
            return []
        return sorted(df["cal_date"].astype(str).tolist())

    def get_daily_quotes(self, trade_date):
        # 日线行情是大多数市场指标的基础表。
        return self._call_with_retry(self.pro.daily, trade_date=trade_date)

