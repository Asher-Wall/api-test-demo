"""全局 fixture：Mock 服务、base_url、ApiClient、登录态、数据源。

三个设计要点：
1. 默认 mock 环境下在进程内启动内置 Mock API，用例开箱即跑、不依赖外部服务；
2. 登录态用 session 级 fixture，整轮测试只登录一次，避免重复登录拖慢用例；
3. 数据驱动用例的数据从 data/*.yaml 读取，改数据不需要改代码。
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from typing import Any

import pytest
import yaml

from api.client import ApiClient
from api.endpoints.auth import login
from config.settings import (
    BASE_URL,
    ENV,
    PROJECT_ROOT,
    TEST_PASSWORD,
    TEST_USER,
)
from mock_api.app import create_server

DATA_DIR = PROJECT_ROOT / "data"


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    """mock 环境启动进程内 Mock 服务（随机空闲端口）；真实环境直接用配置地址。"""
    if ENV != "mock":
        yield BASE_URL
        return

    server = create_server(port=0)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture(scope="session")
def api_client(base_url: str) -> Iterator[ApiClient]:
    """未登录的客户端。"""
    client = ApiClient(base_url=base_url)
    yield client
    client.close()


@pytest.fixture(scope="session")
def auth_client(base_url: str) -> Iterator[ApiClient]:
    """已登录的客户端：session 级复用同一 Token。"""
    spectator = ApiClient(base_url=base_url)
    resp = login(spectator, TEST_USER, TEST_PASSWORD)
    assert resp.status_code == 200, f"前置登录失败：{resp.status_code} {resp.text}"
    token = resp.json()["data"]["token"]
    spectator.close()

    client = ApiClient(base_url=base_url, token=token)
    yield client
    client.close()


@pytest.fixture(scope="session")
def users_data() -> list[dict[str, Any]]:
    """data/users.yaml 中的登录用例数据。"""
    with (DATA_DIR / "users.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)["users"]
