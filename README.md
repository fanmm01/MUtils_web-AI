# 问答小助手（知识库问答插件）

课程任务三的实现仓库。当前处于 **P1 框架阶段**：平台、契约、路由、SDK/CLI 与前端传输层已建立，业务行为尚未实现，所有业务端点诚实返回 `501 FEATURE_NOT_IMPLEMENTED`。

实施计划见 [Q&A_Assistant/plan-q-a-kbmanagement-exe-go-sharded-umbrella.md](Q&A_Assistant/plan-q-a-kbmanagement-exe-go-sharded-umbrella.md)，课程原始要求见 [docs/course/课程任务.md](docs/course/课程任务.md)。

## 模块职责

| 目录 | 职责 | P1 状态 |
| --- | --- | --- |
| [Contracts/](Contracts/) | 共享 DTO、错误码、Protocol、SSE/事件定义；不依赖 FastAPI、数据库或模型 SDK | 冻结基线（`schema_version = 1`） |
| [Q&A_Assistant/](Q&A_Assistant/) | 问答核心：选库、检索融合、上下文、证据、生成、模型绑定 | A2 占位，调用即 `FeatureNotImplemented` |
| [KBManagement/](KBManagement/) | 知识库、内容、导入、来源、版本、解析 | 占位；解析器只声明能力，不读取文件 |
| [Infrastructure/](Infrastructure/) | SQLite/文件存储、索引、Ollama 适配器等具体实现 | 占位；构造不建库、不联网 |
| [ServiceAPI/](ServiceAPI/) | FastAPI 应用工厂、设置、依赖注入、路由、错误映射、worker 入口 | 路由已注册，业务返回 501 |
| [Clients/python/](Clients/python/) | 薄 Python HTTP/SSE SDK | 已实现传输与错误映射 |
| [Clients/cli/](Clients/cli/) | Typer CLI（`qa`） | 已实现命令与参数校验 |
| [Clients/typescript/](Clients/typescript/) | 共享 TypeScript HTTP/SSE 传输层（`@qa/client`） | 已实现，供 P1-B 消费 |
| [WebUI/](WebUI/)、[WebWidget/](WebWidget/) | 浏览器管理端与网页插件 | P1-B 布局、导航与插件生命周期已完成；业务操作如实显示服务端 501 |
| [docs/](docs/) | 架构、API、验收、开发、模型说明；生成契约 | 见各文件 |
| [scripts/](scripts/) | 契约导出、环境检查、分发检查、开发启动 | 已实现 |

依赖方向：界面/CLI/插件 → HTTP API → 领域包 → `Contracts`；`ServiceAPI` 负责装配 `Infrastructure`。领域包不得导入传输或存储实现。

## P1 未实现状态（必须明确）

- `GET /healthz` → `200`，响应含 `"mode": "scaffold"`。
- `GET /readyz` → `503`，明确说明没有持久化、worker 和模型提供方。
- `GET /v1/capabilities` → 列出已实现与未实现功能。
- CRUD、导入、检索、问答、选库、模型管理、任务等有效业务请求 → `501 FEATURE_NOT_IMPLEMENTED`，不返回假数据、假命中、假模型、假事件。
- 参数错误 → `422 VALIDATION_FAILED`，使用统一错误封装。

## 安装

要求 Python 3.12 与 Node 24（仅 TypeScript 包需要）。

```bash
uv sync --all-packages --group dev
npm ci
```

## 启动

```bash
uv run qa-api                 # 默认 127.0.0.1:8000；P1 只允许回环地址
uv run qa --help              # CLI
uv run qa --base-url http://127.0.0.1:8000 capabilities
uv run python scripts/check_environment.py
```

## 最短 API 调用链

```bash
curl -s http://127.0.0.1:8000/healthz
# {"status":"ok","mode":"scaffold","schema_version":1}

curl -s -X POST http://127.0.0.1:8000/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"question":"如何升级？","selection":{"mode":"explicit","targets":[{"kb_id":"kb_product"}]}}'
# HTTP 501，{"error":{"code":"FEATURE_NOT_IMPLEMENTED",...},"request_id":"..."}
```

统一错误封装与 `X-Request-ID` 回显见 [docs/api.md](docs/api.md)。

## 测试与检查

```bash
uv run --all-packages ruff check .
uv run --all-packages pytest tests/scaffold tests/contracts -q
uv run --all-packages python scripts/export_contracts.py --check
node node_modules/typescript/bin/tsc -p Clients/typescript/tsconfig.json --noEmit
npm run test:scaffold -w @qa/client
```

## 后续阶段

P2 持久化与知识库业务 → P3 模型运行平台与高质量问答 → P4 验收与分发检查 → P5 可选桌面/平台集成。每阶段先冻结契约，A1/A2 平行实现，B 只消费公开客户端。Agent Insight 集成延期，未完成前不宣称课程验收全部完成。
