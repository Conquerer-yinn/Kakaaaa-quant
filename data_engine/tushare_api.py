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

