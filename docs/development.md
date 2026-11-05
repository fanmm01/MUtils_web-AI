# 开发说明

## 1. 分阶段依赖

| 阶段 | 内容 | 前置 |
| --- | --- | --- |
| P1 Contract Gate | DTO、Protocol、OpenAPI、SSE、错误码冻结 | — |
| P1-A1 | workspace、设置、FastAPI、普通路由、存储/任务/解析占位、SDK/CLI、TS 传输层 | 契约冻结 |
| P1-A2 | 问答核心、选库/检索、证据、模型绑定的类型化占位 | 契约冻结 |
| P1-B | WebUI/WebWidget 布局与占位 | P1-A1/A2 接口可用 |
| P2 | SQLite/文件存储、解析、CRUD、上传、增量、版本、任务租约 | 新 Contract Gate |
| P3 | 模型运行平台、向量检索、证据与流式一致性 | 新 Contract Gate |
| P4 | 验收工具、反馈闭环、分发检查 | 新 Contract Gate |
| P5 | 可选 Go 桌面与平台集成 | 新 Contract Gate |

A1/A2 平行开发，只通过冻结契约交互；阶段末才在 `tests/integration/cross_stream/` 合并验证。

## 2. 环境与依赖

```bash
uv sync --all-packages --group dev
npm ci
```

- Python 3.12（`.python-version`），依赖解析在 `uv.lock`。
- Node 24 + npm；TypeScript 工作区见 `package.json`。
- `scripts/check_environment.py` 报告 Python/Go/Node/转换工具/OCR 是否在 PATH；它不启动服务、不加载模型、不扫描其他主机。未在 PATH 找到不代表机器未安装。

## 3. 数据库初始化

P1 **没有**数据库文件。`Infrastructure/src/qa_infrastructure/sqlite.py` 的 `SQLiteStore.open()` 是占位，构造和调用都不会创建文件或目录；`var/`、`data/` 被 `.gitignore` 忽略。

P2 起由显式管理动作执行迁移，不在应用启动、包导入或测试收集时自动建库。迁移文件将放在 `Infrastructure/migrations/`，由 `qa-api` 之外的管理命令执行。

## 4. 后台任务

- `qa-worker` 入口已存在（`ServiceAPI/src/qa_service/worker.py`），P1 的 `run_worker` 直接拒绝运行：没有可消费的持久队列，就不假装消费。
- P1 的 `dispatch()` 对每种 `JobKind` 抛 `NotImplementedError`。
- P2 引入租约、心跳、恢复与幂等键；P3 增加模型安装任务的对账。

## 5. 解析与 OCR

- `KBManagement/src/kb_management/parsers.py` 只声明支持的格式（`.doc/.docx/.xls/.xlsx/.md/.txt/.pdf`）与能力标记；不读取文件、不调用转换器。
- OCR 适配器只报告“可能可用”，不执行识别。`scripts/check_environment.py` 仅检查 `soffice`、`tesseract` 是否在 PATH。
- 加密、损坏、不支持或超限文件在 P2 起返回逐文件诊断；扫描 PDF 无 OCR 时不得当作空文本成功。

## 6. 运行与验证

```bash
uv run qa-api                     # 仅回环地址；非回环绑定会被拒绝
uv run qa --help
uv run --all-packages ruff check .
uv run --all-packages pytest tests/scaffold tests/contracts -q
uv run --all-packages python scripts/export_contracts.py --check
node node_modules/typescript/bin/tsc -p Clients/typescript/tsconfig.json --noEmit
npm run test:scaffold -w @qa/client
uv run python scripts/check_distribution.py --check
```

`scripts/dev.py` 可启动 API 或 worker，并在退出时清理自己启动的进程；不会接管已有进程。

## 7. 配置

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `QA_MODE` | `scaffold` | `scaffold` / `operational` |
| `QA_HOST`、`QA_PORT` | `127.0.0.1`、`8000` | P1 仅回环 |
| `QA_DATA_DIR` | `var` | 运行数据目录；启动不创建 |
| `QA_ALLOWED_ORIGINS` | 空 | 逗号分隔；为空时禁用 CORS |
| `QA_RUNTIME_TARGETS` | 空 | JSON 数组，服务端 allow-list；只含 `target_id`/`kind`/`display_name` |
| `QA_MAX_CANDIDATE_KBS` / `QA_MAX_SELECTED_KBS` / `QA_PROBE_TIMEOUT_MS` | 20 / 3 / 1500 | 选库限额 |

`.env.example` 只有占位，不含凭据。

## 8. 模型缓存与分发边界

- 权重保存在部署器（如 Ollama）管理的独立缓存或显式配置的模型卷中，不进入 Git、wheel、前端产物、容器镜像或可选 EXE。
- 本地模型缓存路径独立于应用安装目录；应用启动不自动下载。
- 运行账户需要对模型缓存有读权限；容器部署时模型卷单独挂载，不能用镜像层承载权重。
- 可选桌面 EXE（P5）通过 HTTP 调用后端，不打包 Python 后端或权重；构建步骤在 P5 补充。

## 9. 分发检查

`scripts/check_distribution.py` 扫描 Git 追踪文件、指定的分发目录，按扩展名（`.gguf/.safetensors/.bin/...`）、路径（`models/`、`.ollama/` 等）和体积标记可疑文件。它只是防误打包的启发式检查，不能替代许可证审查。
