"""登录 / 登出接口定义。

每个业务接口一个薄函数，只负责「拼路径 + 传参」，
断言与数据准备留给测试用例，职责清晰。
"""

from __future__ import annotations

import requests

from api.client import ApiClient


def login(client: ApiClient, username: str, password: str) -> requests.Response:
    """POST /auth/login"""
    return client.post("/auth/login", json={"username": username, "password": password})


def logout(client: ApiClient) -> requests.Response:
    """POST /auth/logout（需带 Token）"""
    return client.post("/auth/logout")
