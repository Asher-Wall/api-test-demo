"""多环境配置：通过 TEST_ENV 环境变量切换 base_url，避免地址硬编码在用例里。

默认环境为 mock —— 指向仓库内置的 Mock API，
因此克隆仓库后无需任何外部服务即可跑通全部用例。
"""

from __future__ import annotations

import os
from pathlib import Path

# 项目根目录（config/settings.py 的上两级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 目标环境：mock（默认） / dev / test / prod
ENV = os.getenv("TEST_ENV", "mock")

BASE_URLS = {
    "mock": "http://127.0.0.1:8000",
    "dev": "https://api.dev.example.com",
    "test": "https://api.test.example.com",
    "prod": "https://api.example.com",
}

# 优先级：显式环境变量 > 按 TEST_ENV 查表 > mock 兜底
BASE_URL = os.getenv("API_BASE_URL") or BASE_URLS.get(ENV, BASE_URLS["mock"])

# 默认请求超时（秒）
DEFAULT_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))

# 测试账号（真实项目里应由 CI Secret 注入，不写死在代码中）
TEST_USER = os.getenv("TEST_USER", "test_user")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "test_pass")
