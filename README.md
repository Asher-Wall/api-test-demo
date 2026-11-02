# API Test Demo · pytest 接口自动化示例

基于 **Python + pytest + requests** 的接口自动化测试示例项目。
内置 Mock API，**克隆后无需任何外部服务即可跑通全部用例**，适合作为「前端转测试开发 / SDET」的练习与简历作品。

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows PowerShell；其他终端见「激活命令」表
pip install -r requirements.txt
pytest
```

## 目录结构

```
api-test-demo/
├─ .github/workflows/pytest-api.yml   # CI：PR 触发 + Allure 归档
├─ api/
│  ├─ client.py                       # ApiClient：请求封装与鉴权注入
│  └─ endpoints/
│     ├─ auth.py                      # 登录 / 登出接口定义
│     └─ order.py                     # 订单接口定义
├─ tests/
│  ├─ conftest.py                     # 全局 fixture：Mock 服务 / 登录态 / 数据源
│  ├─ test_login.py                   # 登录用例（含参数化、Schema、数据驱动）
│  └─ test_order.py                   # 下单用例（含鉴权、边界值、隔离性验证）
├─ mock_api/
│  └─ app.py                          # 内置 Mock API（仅标准库，零额外依赖）
├─ data/users.yaml                    # 数据驱动的用例数据
├─ schemas/login_schema.json          # 响应结构契约
├─ config/settings.py                 # 多环境配置
├─ pytest.ini
├─ requirements.txt
├─ .env.example
└─ .gitignore
```

分层原则：**tests（业务步骤） ↔ api（请求细节） ↔ mock\_****api（被测服务） ↔ config（环境）**。
用例只表达业务意图，接口路径与参数拼装下沉到 `api/`，环境差异收敛到 `config/`。

## 快速开始

```bash
# 1. 创建虚拟环境（.venv 已在 .gitignore 中，不会误提交）
python -m venv .venv

# 2. 激活虚拟环境（命令因终端而异，见下方「激活命令」表）
.\.venv\Scripts\Activate.ps1          # PowerShell 示例
source .venv/Scripts/activate         # Git Bash（Windows）示例
source .venv/bin/activate             # macOS / Linux 示例

# 3. 安装依赖
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. 运行全部用例（自动启动内置 Mock API，随机端口）
pytest

# 5. 只跑冒烟用例
pytest -m smoke
```

预期结果：**17 个用例全部通过**，无需任何外部依赖。

> 若只想快速验证，激活后也可直接用 `python -m pytest`——它始终调用当前解释器的 pytest，不依赖 PATH 解析。

### 为什么必须用虚拟环境

本仓库依赖 `pytest>=8.0`，而 pytest 8 存在 breaking change（插件接口与 fixture 行为均有调整）。装进全局 Python 后会与其他锁定 pytest 7.x 的项目互相污染，且全局环境装了什么没有任何记录，问题极难回溯。

| 理由 | 说明 |
| --- | --- |
| 依赖隔离 | 项目依赖互不干扰，`requirements.txt` 是唯一事实来源 |
| 环境可重现 | 本地与 CI 执行同一组命令，行为一致 |
| 保护系统 Python | Linux 下 PEP 668 会直接拒绝全局安装；Windows 下全局安装需要管理员权限，装乱后难以清理 |
| 可丢弃 | 环境损坏时删除 `.venv/` 重建即可，耗时约 10 秒 |

### 激活命令（按终端选择）

| 终端 | 激活命令 |
| --- | --- |
| PowerShell（Windows） | `.\.venv\Scripts\Activate.ps1` |
| CMD（Windows） | `.venv\Scripts\activate.bat` |
| Git Bash（Windows） | `source .venv/Scripts/activate` |
| macOS / Linux | `source .venv/bin/activate` |

> **注意 Windows 与 macOS / Linux 的目录差异**：Windows 创建的 venv 只有 `Scripts\`，**没有 **`bin\`。所以在 Windows 的 Git Bash 里同样要指向 `Scripts/activate`，写成 `.venv/bin/activate` 会报 `No such file or directory`。`bin/` 只存在于 macOS / Linux。

退出虚拟环境：`deactivate`

### Windows 两个高频问题

**1. PowerShell 报「禁止运行脚本」**

```
无法加载文件 ...\Activate.ps1，因为在此系统上禁止运行脚本
```

原因是默认执行策略为 `Restricted`。仅对当前用户放开即可，无需管理员权限：

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

若不便修改执行策略，有两种等价做法：直接调用 venv 内的解释器 `.venv\Scripts\python.exe -m pytest`，或改用 CMD 的 `activate.bat`。

**2. **`pytest`** 命令指向全局版本**

激活后 `pytest` 应来自 `.venv\Scripts\pytest.exe`。用 `where pytest` 确认首行为 venv 路径；更稳妥的做法是**始终使用 **`python -m pytest`，完全不依赖 PATH 解析。

### 验证环境是否生效

```bash
python -c "import sys; print(sys.executable)"
python -c "import pytest; print(pytest.__file__)"
```

`pytest.__file__` 的路径应包含 `api-test-demo\.venv\Lib\site-packages\`（macOS / Linux 为 `.venv/lib/*/site-packages/`）。若指向系统 Python 或 `AppData\Roaming\Python`，说明激活未生效。

编辑器选择解释器：VS Code 按 `Ctrl+Shift+P` → `Python: Select Interpreter` → 选中 `.venv\Scripts\python.exe`；PyCharm 在 Settings → Python Interpreter → Add → Existing 中选中同一文件。

### 常用命令

| 命令 | 用途 |
| --- | --- |
| `pytest` | 运行全部用例 |
| `pytest -m smoke` | 只跑核心链路冒烟用例 |
| `pytest tests/test_login.py` | 只跑某个文件 |
| `pytest -k "schema"` | 按关键字过滤 |
| `pytest --alluredir=allure-results` | 生成 Allure 原始数据 |
| `pytest --reruns 2` | 失败重试 2 次，缓解偶发网络抖动 |
| `pytest -n auto` | 多进程并行，缩短反馈时间 |
| `python -m mock_api.app` | 单独启动 Mock API，便于 Postman 手工联调 |

## 用例覆盖矩阵

| 场景 | 用例 | 断言层级 |
| --- | --- | --- |
| 登录成功返回 Token | `test_login_success_returns_token` | 状态码 + 结构 + 业务值 |
| 错误密码 / 空密码 / 空用户名 / 不存在用户 | `test_login_status_codes` | 状态码（参数化 5 例） |
| 响应结构符合契约 | `test_login_response_matches_schema` | JSON Schema |
| 数据驱动登录 | `test_login_is_data_driven` | 状态码（读 YAML） |
| 下单成功 | `test_create_order_success` | 状态码 + 结构 + 业务值 |
| 未登录下单被拒 | `test_create_order_without_token_is_rejected` | 状态码（越权防护） |
| 下单参数校验（6 组边界/类型） | `test_create_order_param_validation` | 状态码 |
| 登出后 Token 失效 | `test_logout_invalidates_token` | 状态码 + 时序验证 |

断言遵循**四层递进**：状态码 → 结构存在 → 业务值 → JSON Schema。
只断言状态码的用例是脆弱的——后端返回 `200` 但字段全错时，它依然会「通过」。

## 多环境切换

`config/settings.py` 通过环境变量选择目标地址，代码中不出现任何硬编码 URL：

```bash
# 默认 mock：使用仓库内置 Mock API（用例唯一能开箱即跑的环境）
pytest

# 指向真实环境
export TEST_ENV=test
# 或显式指定地址（优先级最高）
export API_BASE_URL=https://api.test.example.com
export TEST_USER=your_account
export TEST_PASSWORD=your_password
pytest
```

> 说明：`mock` 是唯一能离线跑通的环境；`dev / test / prod` 为占位地址，替换后即可对真实服务运行。
> 真实凭据请通过 CI Secret 注入，不要提交到仓库（`.env` 已在 `.gitignore` 中）。

## CI 流水线

`.github/workflows/pytest-api.yml` 在 PR 与 main 推送时触发：

1. 矩阵构建 Python 3.11 / 3.12，提前暴露版本兼容问题；
2. `pytest --alluredir=allure-results --reruns 2 -n auto` 并行执行并归档 Allure 原始数据；
3. `if: always()` 上传测试产物——**用例失败时报告同样保留**，这是排查的前提；
4. `concurrency` 取消同一分支的过期流水线，节省额度。

增强参数（`--alluredir` / `--reruns` / `-n auto`）刻意放在 CI 命令而非 `pytest.ini`，
这样本地「装完依赖直接 pytest」永远可用，工程配置不因插件缺失而阻塞。

