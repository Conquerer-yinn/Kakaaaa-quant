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

    def send_interactive_card(self, card: dict) -> dict:
        payload = {
            "msg_type": "interactive",
            "card": card,
        }
        return self._post_json(payload)

    def _post_json(self, payload: dict) -> dict:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            self.webhook,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                content = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Feishu webhook HTTP error: {exc.code} {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Feishu webhook network error: {exc}") from exc

        try:
            data = json.loads(content) if content else {}
        except json.JSONDecodeError:
            return {"raw": content}

        if data.get("StatusCode") not in (None, 0):
            raise RuntimeError(f"Feishu webhook failed: {data}")
        if data.get("code") not in (None, 0):
            raise RuntimeError(f"Feishu webhook failed: {data}")
        return data
