"""统一的 HTTP 客户端封装。

设计原则：测试用例只与 ApiClient 交互，不直接调用 requests。
好处是 base_url、超时、默认 Header、鉴权注入、重试策略全部收口在一处，
接口规范变化时只需改这一个文件。
"""

from __future__ import annotations

from typing import Any

import requests

from config.settings import BASE_URL, DEFAULT_TIMEOUT


class ApiClient:
    """极简接口客户端。"""

    def __init__(
        self,
        base_url: str = BASE_URL,
        token: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )
        if token:
            self.set_token(token)

    def set_token(self, token: str) -> None:
        """注入 Bearer Token，供后续请求复用。"""
        self.session.headers["Authorization"] = f"Bearer {token}"

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method, url, **kwargs)

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", path, **kwargs)

    def close(self) -> None:
        self.session.close()
