import json
from urllib import request
from urllib.error import HTTPError, URLError


class FeishuNotifier:
    """飞书机器人推送封装。"""

    def __init__(self, webhook: str, timeout: int = 15):
        if not webhook:
            raise ValueError("Feishu webhook is required.")
        self.webhook = webhook
        self.timeout = timeout

