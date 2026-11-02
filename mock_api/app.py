"""内置 Mock API —— 让本仓库不依赖任何外部服务即可跑通全部用例。

只使用 Python 标准库（http.server），因此没有额外依赖。

单独启动（用于手工调试、Postman 联调）：
    python -m mock_api.app          # 监听 127.0.0.1:8000

测试中由 tests/conftest.py 以「进程内线程 + 随机空闲端口」方式启动，
这样既不会端口冲突，也不会在测试结束后残留进程。

接口一览：
    POST /auth/login      登录，返回 token
    POST /auth/logout     登出，使 token 失效
    POST /order/create    下单（需带 Token）
    GET  /health          健康检查
"""

from __future__ import annotations

import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlsplit

# 内置账号（真实项目应由环境变量 / Secret 注入）
USERS: dict[str, str] = {"test_user": "test_pass"}

# 已签发的有效 Token 集合
VALID_TOKENS: set[str] = set()

# 简化演示：单价固定
UNIT_PRICE = 100

# 已创建订单
ORDERS: dict[str, dict[str, Any]] = {}

_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "MockApi/1.0"
    protocol_version = "HTTP/1.1"

    # ---------- 基础设施 ----------

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        """静默访问日志，避免污染 pytest 输出。"""

    def _read_json(self) -> dict[str, Any] | None:
        """读取并解析请求体；非法 JSON 返回 None。"""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def _respond(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _bearer_token(self) -> str:
        auth = self.headers.get("Authorization") or ""
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
        return ""

    def _target_path(self) -> str:
        """归一化请求目标，返回纯路径。

        RFC 7230 §5.3.2 规定服务端必须同时接受两种请求行形式：
          - origin-form：    POST /auth/login HTTP/1.1
          - absolute-form：  POST http://host:port/auth/login HTTP/1.1

        走 HTTP 代理（环境变量 http_proxy，且未配置 no_proxy）时，
        requests / urllib3 会在复用连接上以 absolute-form 发送，
        若直接用 self.path 匹配路由表会全部落到 404。
        """
        raw = self.path or "/"
        path = urlsplit(raw).path or "/"
        return path.rstrip("/") or "/"

    # ---------- 路由 ----------

    def do_POST(self) -> None:  # noqa: N802
        path = self._target_path()
        body = self._read_json()
        if body is None:
            self._respond(400, {"code": 400, "message": "invalid json body"})
            return

        routes = {
            "/auth/login": self._login,
            "/auth/logout": self._logout,
            "/order/create": self._create_order,
        }
        handler = routes.get(path)
        if handler is None:
            self._respond(404, {"code": 404, "message": f"no route: {path}"})
            return
        handler(body)

    def do_GET(self) -> None:  # noqa: N802
        path = self._target_path()
        if path == "/health":
            self._respond(200, {"code": 0, "message": "ok"})
            return
        self._respond(404, {"code": 404, "message": f"no route: {path}"})

    # ---------- 业务逻辑 ----------

    def _login(self, body: dict[str, Any]) -> None:
        username = body.get("username")
        password = body.get("password")
        # 参数校验：缺失或空串都视为非法参数
        if not username or not password:
            self._respond(
                400,
                {"code": 400, "message": "username and password are required"},
            )
            return
        if USERS.get(username) != password:
            self._respond(401, {"code": 401, "message": "invalid credentials"})
            return

        token = f"tok_{username}_{uuid.uuid4().hex[:12]}"
        with _LOCK:
            VALID_TOKENS.add(token)
        self._respond(
            200,
            {
                "code": 0,
                "message": "ok",
                "data": {"token": token, "username": username},
            },
        )

    def _logout(self, _body: dict[str, Any]) -> None:
        token = self._bearer_token()
        if not token:
            self._respond(401, {"code": 401, "message": "missing token"})
            return
        with _LOCK:
            VALID_TOKENS.discard(token)
        self._respond(200, {"code": 0, "message": "ok", "data": {}})

    def _create_order(self, body: dict[str, Any]) -> None:
        token = self._bearer_token()
        with _LOCK:
            authorized = bool(token) and token in VALID_TOKENS
        if not authorized:
            self._respond(401, {"code": 401, "message": "unauthorized"})
            return

        sku = body.get("sku")
        qty = body.get("qty")
        if not sku:
            self._respond(400, {"code": 400, "message": "sku is required"})
            return
        # bool 是 int 的子类，需显式排除
        if isinstance(qty, bool) or not isinstance(qty, int) or not 1 <= qty <= 99:
            self._respond(
                400,
                {"code": 400, "message": "qty must be an integer between 1 and 99"},
            )
            return

        order = {
            "order_id": f"ORD{uuid.uuid4().hex[:10].upper()}",
            "sku": sku,
            "qty": qty,
            "amount": qty * UNIT_PRICE,
            "status": "created",
        }
        with _LOCK:
            ORDERS[order["order_id"]] = order
        self._respond(200, {"code": 0, "message": "ok", "data": order})


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """创建（尚未启动）Mock 服务；port=0 表示由系统分配空闲端口。"""
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    server = create_server(port=8000)
    host, port = server.server_address
    print(f"Mock API listening on http://{host}:{port}  (Ctrl+C 退出)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
