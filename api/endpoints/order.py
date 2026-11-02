"""订单接口定义。"""

from __future__ import annotations

import requests

from api.client import ApiClient


def create_order(client: ApiClient, sku: str, qty: int) -> requests.Response:
    """POST /order/create（需带 Token）"""
    return client.post("/order/create", json={"sku": sku, "qty": qty})


def get_order(client: ApiClient, order_id: str) -> requests.Response:
    """GET /order/{order_id}（演示路径参数拼装方式）"""
    return client.get(f"/order/{order_id}")
