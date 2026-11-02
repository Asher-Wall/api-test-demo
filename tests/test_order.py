"""下单接口用例：演示依赖登录态、鉴权校验、参数校验与用例隔离。"""

from __future__ import annotations

import pytest

from api.client import ApiClient
from api.endpoints.auth import login, logout
from config.settings import TEST_PASSWORD, TEST_USER


@pytest.mark.smoke
def test_create_order_success(auth_client):
    """正向用例：已登录下单成功。"""
    resp = auth_client.post("/order/create", json={"sku": "SKU_001", "qty": 2})
    body = resp.json()

    assert resp.status_code == 200
    assert body["data"]["status"] == "created"
    assert body["data"]["qty"] == 2
    assert body["data"]["amount"] > 0
    assert body["data"]["order_id"]


def test_create_order_without_token_is_rejected(api_client):
    """鉴权用例：未登录直接下单必须被拒绝（越权防护）。"""
    resp = api_client.post("/order/create", json={"sku": "SKU_001", "qty": 1})
    assert resp.status_code in (401, 403)


@pytest.mark.parametrize(
    "payload, expect_code",
    [
        ({"sku": "SKU_001", "qty": 0}, 400),
        ({"sku": "SKU_001", "qty": 100}, 400),
        ({"sku": "SKU_001"}, 400),
        ({"sku": "", "qty": 1}, 400),
        ({"sku": "SKU_001", "qty": "2"}, 400),
        ({"sku": "SKU_001", "qty": -1}, 400),
    ],
    ids=["数量为0", "数量超上限", "缺少数量", "sku为空", "数量为字符串", "数量为负数"],
)
def test_create_order_param_validation(auth_client, payload, expect_code):
    """参数校验用例：边界值与类型错误应被后端正确拦截。"""
    resp = auth_client.post("/order/create", json=payload)
    assert resp.status_code == expect_code


def test_logout_invalidates_token(api_client):
    """鉴权闭环：登出后原 Token 立即失效。

    注意本用例自行申请独立 Token，不触碰 auth_client 的登录态，
    因此不会污染其他用例 —— 用例之间保持隔离。
    """
    client = ApiClient(base_url=api_client.base_url)
    token = login(api_client, TEST_USER, TEST_PASSWORD).json()["data"]["token"]
    client.set_token(token)

    assert client.post("/order/create", json={"sku": "SKU_001", "qty": 1}).status_code == 200
    assert logout(client).status_code == 200
    assert client.post("/order/create", json={"sku": "SKU_001", "qty": 1}).status_code == 401
    client.close()
