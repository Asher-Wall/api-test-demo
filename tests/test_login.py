"""登录接口用例：演示「状态码 → 结构 → 业务值 → JSON Schema」四层断言。"""

from __future__ import annotations

import json

import jsonschema
import pytest

from api.endpoints.auth import login
from config.settings import PROJECT_ROOT, TEST_PASSWORD, TEST_USER

SCHEMA_PATH = PROJECT_ROOT / "schemas" / "login_schema.json"


@pytest.mark.smoke
def test_login_success_returns_token(api_client):
    """正向用例：登录成功应返回 token 与用户名。"""
    resp = login(api_client, TEST_USER, TEST_PASSWORD)
    body = resp.json()

    assert resp.status_code == 200          # 第一层：状态码
    assert "token" in body["data"]          # 第二层：结构存在
    assert body["data"]["username"] == TEST_USER  # 第三层：业务值


@pytest.mark.parametrize(
    "username, password, expect_code",
    [
        (TEST_USER, TEST_PASSWORD, 200),
        (TEST_USER, "wrong_password", 401),
        (TEST_USER, "", 400),
        ("", TEST_PASSWORD, 400),
        ("not_exist_user", TEST_PASSWORD, 401),
    ],
    ids=["正确密码", "错误密码", "空密码", "空用户名", "不存在用户"],
)
def test_login_status_codes(api_client, username, password, expect_code):
    """异常用例：参数化覆盖典型的非法输入组合。"""
    resp = login(api_client, username, password)
    assert resp.status_code == expect_code


def test_login_response_matches_schema(api_client):
    """契约层断言：响应结构必须符合 schemas/login_schema.json。

    后端若悄悄改字段名或丢失字段，这条用例会先于前端发现问题。
    """
    resp = login(api_client, TEST_USER, TEST_PASSWORD)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=resp.json(), schema=schema)


def test_login_is_data_driven(api_client, users_data):
    """数据驱动：用例数据来自 data/users.yaml，改数据无需改代码。"""
    for case in users_data:
        resp = login(api_client, case["username"], case["password"])
        assert resp.status_code == case["expect"], (
            f"用例失败 → 用户名={case['username']!r} "
            f"密码={case['password']!r} 期望={case['expect']} 实际={resp.status_code}"
        )
