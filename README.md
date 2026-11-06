# 问答小助手（知识库问答插件）

课程任务三的实现仓库。P2 的知识库管理、上传/导入、关键词检索内核、版本快照与管理端已交付；P3 的模型运行、向量检索、有据回答、完整会话与 Widget 问答**尚未实现**，这些接口仍诚实返回 `501 FEATURE_NOT_IMPLEMENTED`。P2 审查与 P3 分工见 [docs/P2阶段复核与P3分工计划.md](docs/P2阶段复核与P3分工计划.md)，P1 审查与 P2 Gate 见 [docs/P1阶段复核与P2分工计划.md](docs/P1阶段复核与P2分工计划.md)。

实施计划见 [Q&A_Assistant/plan-q-a-kbmanagement-exe-go-sharded-umbrella.md](Q&A_Assistant/plan-q-a-kbmanagement-exe-go-sharded-umbrella.md)，课程原始要求见 [docs/course/课程任务.md](docs/course/课程任务.md)。

## 模块职责

| 目录 | 职责 | P2 交付状态 |
| --- | --- | --- |
| [Contracts/](Contracts/) | 共享 DTO、错误码、Protocol、SSE/事件定义；不依赖 FastAPI、数据库或模型 SDK | HTTP 契约 v2；事件 v1；P3 将另做 Contract Gate |
| [Q&A_Assistant/](Q&A_Assistant/) | 问答核心：选库、检索融合、上下文、证据、生成、模型绑定 | 中文关键词检索和无模型选库核心可用；向量/生成/证据待 P3 |
| [KBManagement/](KBManagement/) | 知识库、内容、导入、来源、版本、解析 | SQLite CRUD、解析、上传/增量、不可变关键词快照、显式发布与回滚可用 |
| [Infrastructure/](Infrastructure/) | SQLite/文件存储、索引、Ollama 适配器等具体实现 | SQLite/文件/BM25 可用；Ollama/向量适配器待 P3 |
| [ServiceAPI/](ServiceAPI/) | FastAPI 应用工厂、设置、依赖注入、路由、错误映射、worker 入口 | 管理路由和导入 worker 可用；问答、模型、反馈路由仍 501 |
| [Clients/python/](Clients/python/) | 薄 Python HTTP/SSE SDK | 管理/上传/版本 HTTP 调用可用；答案 SSE 依赖 P3 |
| [Clients/cli/](Clients/cli/) | Typer CLI（`qa`） | 管理与目录上传命令可用；模型/问答命令待 P3 |
| [Clients/typescript/](Clients/typescript/) | 共享 TypeScript HTTP/SSE 传输层（`@qa/client`） | OpenAPI/事件类型生成及 parity 门；管理端复用 |
| [WebUI/](WebUI/)、[WebWidget/](WebWidget/) | 浏览器管理端与网页插件 | 管理端五页可用；Widget 外壳可嵌入，真实问答/模型页待 P3 |
| [docs/](docs/) | 架构、API、验收、开发、模型说明；生成契约 | 阶段验收以 P2 报告为准 |
| [scripts/](scripts/) | 契约导出、环境检查、分发检查、开发启动 | 基础检查已实现 |

依赖方向：界面/CLI/插件 → HTTP API → 领域包 → `Contracts`；`ServiceAPI` 负责装配 `Infrastructure`。领域包不得导入传输或存储实现。

## 运行模式与尚未实现功能

- 默认 `QA_MODE=scaffold`：`/healthz` 为 200，`/readyz` 为 503，业务操作仍返回 501；启动、导入与生成契约不建库、不探测运行时。
- 显式迁移、配置 `QA_MODE=operational` 并启动 API 与 worker 后，管理 CRUD/导入/任务/版本路由工作；`GET /v1/capabilities` 列出当前已实现/未实现功能。当前 `/readyz` 即使在 operational 模式仍返回 503，不把管理功能可用误报为完整问答就绪。
- 检索、问答、会话、反馈、模型管理 HTTP 入口仍为 501；Job 事件目前是持久化 JSON 回放，**不是 SSE**。`/search` 不能因 A2 内核关键词路径通过就声称外部 API 已可用。
- 参数错误为 `422 VALIDATION_FAILED`，统一错误信封；不要把当前仅单用户回环部署的管理端误用作有多用户鉴权的公网服务。

## 安装

要求 Python 3.12 与 Node 24（仅 TypeScript 包需要）。

```bash
uv sync --all-packages --group dev
npm ci
```

## 启动

P2 运营模式须先设置 `QA_MODE=operational`、独立的 `QA_DATA_DIR` 和经语料选择的 `QA_CHUNK_TARGET_TOKENS` / `QA_CHUNK_OVERLAP_TOKENS`，再显式迁移（不在启动时自动建库）。运行顺序见 [docs/development.md](docs/development.md) §10。

```bash
uv run --all-packages python -m qa_service.migrate --target head
uv run --all-packages qa-api      # 默认仅监听 127.0.0.1:8000
uv run --all-packages qa-worker   # 另一个终端；处理持久导入任务
uv run --all-packages qa --help
```

## 最短 API 调用链

```bash
curl -s http://127.0.0.1:8000/healthz
# {"status":"ok","mode":"scaffold","schema_version":2}

curl -s -X POST http://127.0.0.1:8000/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"question":"如何升级？","selection":{"mode":"explicit","targets":[{"kb_id":"kb_product"}]}}'
# HTTP 501，{"error":{"code":"FEATURE_NOT_IMPLEMENTED",...},"request_id":"..."}
```

统一错误封装与 `X-Request-ID` 回显见 [docs/api.md](docs/api.md)。

## 测试与检查

```bash
uv run --all-packages pytest -q
uv run --all-packages pytest tests/integration/cross_stream -q
uv run --all-packages ruff check .
uv run --all-packages python scripts/export_contracts.py --check
uv run --all-packages python scripts/check_distribution.py --check
npm run typecheck && npm run build && npm run test:scaffold
npm run test:e2e     # 真实 Edge + 临时 qa-api/qa-worker；同一时刻只运行一次
```

当前有独立旧 `qa-api.exe` 进程占用本机 `.venv` entrypoint 时，`uv run` 的环境同步可能报 WinError 32；测试可临时使用 `uv run --no-sync --all-packages ...`，不能以此取代未来正常 `uv sync` 验收，也不要擅自终止他人的进程。TypeScript 类型更新用 `npm run gen:types -w @qa/client`，生成物新鲜度由 typecheck 门禁检查。

## 后续阶段

P3 按 [P2 复核与 P3 分工](docs/P2阶段复核与P3分工计划.md) 先执行短 Contract Gate，再由 A1 模型运行平台与 A2 向量/问答核心并行实现，后端验收后 B 接入模型页和 Widget；P4 负责质量与分发/反馈验收，P5 才是可选桌面/平台集成。Agent Insight 实际集成延期，完成前不宣称课程八项全部达标。
