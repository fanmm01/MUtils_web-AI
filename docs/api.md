# HTTP / SSE 契约

本文件描述调用方可见的 API 形态。机器可读的权威定义是代码导出的 [openapi.json](openapi.json) 与 [events.schema.json](events.schema.json)，由 `scripts/export_contracts.py` 生成；不要手工编辑这两个 JSON。

## 1. 通用规则

- 基础路径：`http://127.0.0.1:8000`（当前只部署回环单用户服务）。所有业务接口位于 `/v1`。默认 `QA_MODE=scaffold` 仍拒绝有效业务请求；显式迁移并设置 `QA_MODE=operational` 后 P2 管理路由可用。
- 管理请求与响应主要为 JSON；上传 PUT 发送原始二进制；当前 `GET /v1/jobs/{id}/events` 为可重放 **JSON**，不是 SSE。答案 SSE 与任务 SSE 在 P3 实施后才是 `text/event-stream`。
- 响应头 `X-Request-ID`：服务端回显调用方提供的值，否则生成新的 ID；错误体中的 `request_id` 与之一致。
- 时间均为 UTC、带时区；列表使用游标分页（`limit`、`cursor`）。
- ID 均为服务端生成的不透明字符串；客户端不得解析其结构。
- HTTP 请求/响应契约版本为 `2`（健康检查、capabilities 及请求 fixtures）；SSE 事件仍使用 `schema_version=1`，以便重放 P1 已保存的事件。事件版本不是 HTTP 版本，旧 HTTP v1 请求不保证兼容新的导入接口。

### 1.1 错误封装

所有非 2xx 响应（**包括参数校验 422**）使用同一错误信封；目前 OpenAPI 对该信封的声明尚不完整，P3 Gate 必须冻结响应形状和状态映射：

```json
{
  "error": {
    "code": "FEATURE_NOT_IMPLEMENTED",
    "message": "search is not implemented in this build",
    "details": [{"field": "question", "reason": "missing"}]
  },
  "request_id": "b1f0…"
}
```

| code | HTTP | 含义 |
| --- | --- | --- |
| `VALIDATION_FAILED` | 422 | 请求体/查询参数不合法 |
| `UNAUTHENTICATED` | 401 | 缺少或无效身份 |
| `PERMISSION_DENIED` | 403 | 无权访问该 KB/资源 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 版本/ETag/幂等冲突 |
| `GONE` | 410 | 资源已删除且不可恢复 |
| `RATE_LIMITED` | 429 | 触发限额 |
| `FEATURE_NOT_IMPLEMENTED` | 501 | 当前阶段未实现 |
| `PROVIDER_UNAVAILABLE` | 503 | 模型/部署器不可达 |
| `MODEL_UNAVAILABLE` | 503 | 所需模型缺失或未就绪 |
| `MODEL_CHANGED` | 409 | 模型身份与绑定不一致 |
| `MODEL_CAPABILITY_MISSING` | 503 | 模型缺少所需角色能力 |
| `INFERENCE_POLICY_VIOLATION` | 403 | 策略（如 `local_only`）禁止该调用 |
| `EVIDENCE_INSUFFICIENT` | 200 | 正常业务结果：证据不足而拒答 |
| `INTERNAL_ERROR` | 500 | 未预期错误；不泄露内部细节 |

参数校验失败映射为 `422 VALIDATION_FAILED`，`details[].field` 指向出错字段。额外字段一律拒绝（DTO `extra="forbid"`）。

## 2. 系统接口

| 方法 | 路径 | 当前模式行为 |
| --- | --- | --- |
| GET | `/healthz` | `200`；默认 scaffold 时 `{"status":"ok","mode":"scaffold","schema_version":2}`，运营模式显示 operational |
| GET | `/readyz` | 当前实现始终 `503`，包括 operational 模式；不能把迁移/管理 API 可用等同于完整服务就绪（模型/问答仍缺失） |
| GET | `/v1/capabilities` | `200`，分别列出当前已实现/未实现功能与选库上限 |

## 3. 业务接口（P2 当前状态）

所有路由均有 DTO 校验。**scaffold** 模式有效业务请求仍 501；显式迁移后的 **operational** 模式已经提供知识库/内容/上传/来源/导入/版本和导入 Job 的管理 API（下述前三类及 Job 部分）。检索、问答、会话、选库、反馈、模型和 Widget 票据仍返回 501，不得凭已接通的 A2 关键词核心推断外部 `/v1/search` 已可用。

**知识库**：`GET/POST /v1/kbs`，`GET/PATCH/DELETE /v1/kbs/{kb_id}`，`GET /v1/kbs/{kb_id}/documents`，`POST /v1/kbs/{kb_id}/documents`，`GET/POST /v1/kbs/{kb_id}/qa-pairs`，`GET/PATCH/DELETE /v1/qa-pairs/{qa_id}`，`GET/PATCH/DELETE /v1/documents/{document_id}`。

**导入与来源**：`POST /v1/kbs/{kb_id}/imports/preview`，`POST /v1/kbs/{kb_id}/imports`，`GET/POST /v1/kbs/{kb_id}/sources`，`GET/PATCH/DELETE /v1/sources/{source_id}`，`POST /v1/sources/{source_id}/sync`，`GET /v1/source-roots`，`POST /v1/source-roots/{root_id}/scan`，`POST /v1/uploads`，`PUT /v1/uploads/{batch_id}/files`，`POST /v1/uploads/{batch_id}/complete`。

**版本**：`GET /v1/kbs/{kb_id}/versions`，`GET /v1/versions/{version_id}`，`POST /v1/versions/{version_id}/publish`，`POST /v1/kbs/{kb_id}/publish`，`POST /v1/kbs/{kb_id}/rollback`，`GET /v1/kbs/{kb_id}/version-diff`。

**检索与问答**：`POST /v1/search`，`POST /v1/ask`，`POST /v1/sessions`，`POST /v1/sessions/{session_id}/answers`，`GET /v1/sessions/{session_id}/history`，`GET /v1/answers/{answer_id}`，`POST /v1/answers/{answer_id}/cancel`，`GET /v1/answers/{answer_id}/citations/{citation_id}`，`GET /v1/answers/{answer_id}/events`（当前建流预检即 501，未来 SSE 在 P3）。

**选库**：`GET /v1/knowledge-catalog`，`POST /v1/knowledge-selection/preview`，`GET/PATCH /v1/sessions/{session_id}/selection`，`GET/PATCH /v1/sessions/{session_id}/inference`。

**反馈**：`POST /v1/answers/{answer_id}/feedback`，`GET /v1/issues`，`GET/PATCH /v1/issues/{issue_id}`，`POST /v1/issues/{issue_id}/retest`。

**模型**：`GET /v1/models/capabilities`（P2 仍返回静态 scaffold 能力，不能作模型就绪证明）、`POST /v1/models/discovery`（只接受 `target_ids`）、`GET /v1/models/runtimes`，`GET /v1/models`，`GET /v1/models/{model_id}`，`POST /v1/models/{model_id}/verifications`，`GET/POST /v1/inference-profiles`，`GET/PUT /v1/inference-profiles/{profile_id}`，`POST /v1/inference-profiles/{profile_id}/disable`，`POST /v1/model-installs/preview`，`POST /v1/model-installs`。除静态 capabilities 外均待 P3。

**任务与插件**：`GET /v1/jobs/{job_id}`，`POST /v1/jobs/{job_id}/cancel`，`GET /v1/jobs/{job_id}/events`（operational 模式仅对导入 Job 可用且当前返回 JSON），`POST /v1/widget/tickets`（501）。

## 4. 导入、上传与镜像确认（P2 operational）

- `POST /v1/uploads` 接收 `{source_id, selection?, files:[{relative_path,digest,size}]}`，返回 `{batch_id,source_id}`；selection 记录客户端选择范围，不能自行授权删除，客户端也不可提交 `complete`。`PUT /v1/uploads/{batch_id}/files?relative_path=...` 使用原始字节、逐文件核验 hash/size；失败不得当成成功继续。`POST /v1/uploads/{batch_id}/complete` 返回服务端验证的 `SourceManifest`，包含 `scan_scope`、`scan_status`、`complete`；部分上传/失败不触发 mirror 删除，批次核验后内容单独存放。
- `POST /v1/kbs/{kb_id}/imports/preview` 接受 `ImportPreviewRequest`（kb_id/source_id/mode/selection），预览不删除。确认的 `ImportRequest` 带非空 `expected_preview_hash`，服务端复验来源、范围、baseline、文件集及字节，变化返回 409；成功仅入队，worker 构建 READY 版本，仍需显式发布。未完成或失败的导入不变更活动指针。
- 最终 `ResolvedScope.targets` 必须非空、每库至多一次、每项含不可变 `version_id`；请求 `explicit.targets` 仍允许省略 version_id，在执行前固定。关键词读取使用带 kb/version、keyword profile 和 index ref 的单库 `SearchScope`，由受权 SnapshotReader 返回；不能混用多个库的原始 BM25 分数。

## 5. 选库请求

`selection` 是严格判别联合，`mode` 决定分支，两个分支的字段互斥：

```json
{"mode": "explicit", "targets": [{"kb_id": "kb_product", "version_id": "v3"}]}
```

```json
{"mode": "auto", "candidate_kb_ids": ["kb_product", "kb_ops"], "max_kbs": 2}
```

- `explicit.targets` 至少 1 项，`kb_id` 不得重复；省略 `version_id` 表示使用该库当前活动版本。
- `auto.candidate_kb_ids` 省略或 `null` 表示在授权范围内的全部库中挑选；空数组非法；`max_kbs` 受服务端限额约束。
- 客户端不得同时提交 `targets` 与 `candidate_kb_ids`，也不得提交未知字段。

推理选择独立于选库：

```json
{"inference": {"profile_id": "local-default", "policy": "local_only"}}
```

`policy` 取 `local_only`（默认）或 `configured`。`configured` 仅允许服务器预配置的外接 profile，不表示可自由填写端点或密钥。

## 6. 模型发现与安装（P3 计划，当前 501）

以下请求/响应为 Contract Gate 草案，不代表 P2 的运行时已可发现、安装、核验或调用。

- 发现请求只接受 `{"target_ids": ["ollama"]}`；URL、路径、凭据等字段因 `extra="forbid"` 被拒绝。目标必须在服务端 allow-list 中。
- 安装两步走，没有捷径：

```json
POST /v1/model-installs/preview
{"target_id": "ollama", "model_ref": "qwen3:8b"}
```

返回 `preview_id`、`preview_hash`、身份状态、已知大小/缺失层数和未知项。预览不下载任何数据。

```json
POST /v1/model-installs
Idempotency-Key: <client-generated>
{"preview_id": "…", "preview_hash": "…", "confirmed": true}
```

`confirmed` 必须为 `true` 且 `preview_id`/`preview_hash` 匹配未过期的预览。CLI 的 `install-confirm` 要求显式 `--yes`。

## 7. SSE 事件（P3 目标契约；P2 Job 仍为 JSON 回放）

- P2 已持久化 Job 事件；`GET /v1/jobs/{job_id}/events` 接收 `Last-Event-ID`，返回 JSON 事件信封列表并使用 `job_id`、`seq`。目前**没有**实时 SSE 输出或心跳，前端通过轮询实现任务进度。
- 回答事件端点 `/v1/answers/{answer_id}/events` 当前有效请求 501；以下答案与 Job SSE 序列约束将在 P3 Gate 冻结并实现，不把 P2 的 JSON 直接称为 `text/event-stream`。
- 断线重连（P3 SSE 目标）：请求头 `Last-Event-ID: <seq>`，服务端从下一条事件续传；客户端应丢弃重复 `seq`。P2 的 JSON Job 回放已接受该头但不提供连续流。
- 回答的四个终态（P3）`answer.completed`、`answer.refused`、`answer.failed`、`answer.cancelled` 恰好出现一个；终态之后不得再有事件。
- 心跳（P3）以 SSE 注释形式发送；客户端解析器必须忽略注释行。
- 事件类型全集与 payload schema 见 [events.schema.json](events.schema.json)。

## 8. 客户端

- Python：[Clients/python/](../Clients/python/) 的 `qa_client.Client`，错误映射为 `QAError(code, message, status, details, request_id)`。
- CLI：`qa --help`；未实现命令以退出码 `3` 结束，并在 stderr 输出 JSON 错误。
- TypeScript：`Clients/typescript/` 的 `@qa/client`，提供 `createClient`、`subscribeAnswer`、`subscribeJob`；凭据由宿主注入，不落盘。
