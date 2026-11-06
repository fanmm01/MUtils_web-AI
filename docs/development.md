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

P1 阶段没有数据库。P2 `SQLiteStore` 已实现：构造/导入不建库，`open()` 只接入已有数据库；显式管理命令 `uv run --all-packages python -m qa_service.migrate --target head` 才创建 `QA_DATA_DIR/qa.sqlite3` 并应用 `Infrastructure/migrations/`。应用启动和测试收集不自动迁移；`var/`、`data/` 是 `.gitignore` 忽略的运行目录。

## 4. 后台任务

- P2 `qa-worker` 处理持久化导入 Job：认领租约、构建 READY 快照、显式取消的协作检查与事件按 seq 回放；没有已迁移数据库时拒绝运行，不能把业务未就绪伪装为成功。
- 模型安装/验证 Job 和上游对账仍属于 P3；P2 的 `GET /v1/jobs/{id}/events` 是可重放 JSON，不是 SSE。P3 Gate 将冻结取消未知结果、租约续期和 SSE 协商。

## 5. 解析与 OCR

- `KBManagement/src/kb_management/parsers.py` 已解析 `.md/.txt/.docx/.xls/.xlsx/.pdf` 并保留结构定位；旧 `.doc` 需要已安装的受控 LibreOffice 转换器，未配置时明确报告 `CONVERSION_UNAVAILABLE`，不能以能力声明代替实测。
- OCR 执行尚未配置；无文本层的扫描 PDF 返回 `OCR_REQUIRED` / `OCR_UNAVAILABLE`，不返回空成功。`scripts/check_environment.py` 只报告 `soffice`、`tesseract` 等候选，不启动外部程序。
- 损坏、加密、不支持或超限文件给逐文件诊断；哪些格式在当前机器真实跑通过，以 P2 复核报告和测试夹具为准。

## 6. 运行与验证

```bash
uv run --all-packages python -m qa_service.migrate --target head  # operational 模式先显式迁移
uv run --all-packages qa-api                                      # 仅回环地址
uv run --all-packages qa-worker                                   # 单独终端
uv run --all-packages qa --help
uv run --all-packages ruff check .
uv run --all-packages pytest -q
uv run --all-packages pytest tests/integration/cross_stream -q
uv run --all-packages python scripts/export_contracts.py --check
uv run --all-packages python scripts/check_distribution.py --check
npm run typecheck && npm run build && npm run test:scaffold
npm run test:e2e  # 当前固定临时端口，同一时刻只跑一个实例
```

`scripts/dev.py` 可启动 API 或 worker，并在退出时清理自己启动的进程；不会接管已有进程。

## 7. 配置

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `QA_MODE` | `scaffold` | `scaffold` / `operational`；只有后者开放 P2 管理业务 |
| `QA_HOST`、`QA_PORT` | `127.0.0.1`、`8000` | 当前单用户回环部署，不代表多用户鉴权已实现 |
| `QA_DATA_DIR` | `var` | 运行数据目录；**仅显式迁移**创建数据库 |
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

## 10. P2-A1 运营步骤（确定性业务）

1. 配置环境：`QA_MODE=operational`、`QA_DATA_DIR`、`QA_CHUNK_TARGET_TOKENS` 与 `QA_CHUNK_OVERLAP_TOKENS`（无隐式默认，须由真实语料分析确定）。
2. 显式迁移（导入/启动都不会建库）：`uv run python -m qa_service.migrate --target head`。
3. 启动 API：`uv run qa-api`；后台导入：`uv run qa-worker`（或 `--once` 单轮）。
4. 本地目录来源：`QA_SOURCE_ROOTS` 只允许服务端授权 `root_id`；同源 `source_id` 使用 `kind=local_root` + `root_id`，导入时服务端自行扫描，客户端不提交路径。
5. 上传来源：`kind=upload`；客户端 `PUT /v1/uploads/{batch}/files?relative_path=...` 的字节必须与清单摘要、大小一致，`complete` 只在全部匹配时返回 `complete=true`。
6. 预览与确认：`POST /v1/kbs/{kb}/imports/preview` 得到 `preview_hash`，再 `POST /v1/kbs/{kb}/imports`；预览后文件变化返回 409。
7. 版本：导入任务成功后产生 `ready` 快照，`POST /v1/versions/{id}/publish`（或 `/v1/kbs/{id}/publish`）以 `expected_active_version_id` 比较交换；失败或冲突不切换活动版本；`rollback` 同样基于已校验的旧快照。
8. 任务事件：`GET /v1/jobs/{id}/events` 目前返回持久化 JSON 事件（同样的 `seq` 可重放）；SSE 流式在 P3。

尚未验收：`.doc` 转换需要本机 LibreOffice；扫描 PDF 的 OCR 尚未配置（分别返回 `CONVERSION_UNAVAILABLE` / `OCR_REQUIRED` / `OCR_UNAVAILABLE`，不会当空成功）。A2 核心关键词检索和选库可在后端端口直接运行，但外部检索/选库/问答 HTTP 路由仍为 501，模型/向量/真实问答属于 P3。
