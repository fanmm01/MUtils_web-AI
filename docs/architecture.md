# 架构

## 1. 模块依赖

```
WebUI / WebWidget / Go EXE ─┐
CLI (qa) ───────────────────┼─→ HTTP/SSE API (ServiceAPI)
Python SDK (qa_client) ─────┘             │
                                          ├─→ Q&A_Assistant      问答核心（选库、检索融合、上下文、证据、生成）
                                          ├─→ KBManagement       知识库、内容、导入、来源、版本、解析
                                          ├─→ Infrastructure     存储、索引、部署器适配（仅由 ServiceAPI 装配）
                                          └─→ Contracts          共享 DTO / Protocol / 错误码
```

约束（由 `tests/scaffold/test_packages.py` 校验）：

- `qa_contracts` 不导入 FastAPI、uvicorn、sqlite3、任何具体实现包。
- `qa_assistant` 不导入 FastAPI、uvicorn、sqlite3、`qa_service`、`qa_infrastructure`。
- `kb_management` 不导入 FastAPI、uvicorn、`qa_service`。
- `qa_client` 不导入 `qa_service`、`qa_infrastructure`、`qa_assistant`、`kb_management`；SDK 不复制业务规则。
- `qa_cli` 不导入 `qa_service`、`qa_infrastructure`。

`ServiceAPI` 是唯一组合根：设置 → 容器 → 路由。容器的构造只读取设置，不建库、不探测模型、不联网。

## 2. Contract Gate 与版本规则

- `Contracts/src/qa_contracts/` 是跨组冻结面；破坏性修改只能在阶段开头的 Contract Gate 进行。
- `qa_contracts.base.SCHEMA_VERSION` 当前为 `1`，出现在健康检查、能力声明和事件 payload 中。
- 生成的契约文件 [openapi.json](openapi.json)、[events.schema.json](events.schema.json) 由 `scripts/export_contracts.py` 从代码导出；`--check` 在仓库中校验其未漂移，禁止手工编辑。
- 兼容性新增（可选字段、新事件类型在非终态集合之外）必须通过契约测试，且不得要求另一组同步重写。
- 错误码集合与 HTTP 状态映射见 [events.schema.json](events.schema.json) 的 `error_codes`。

## 3. 状态机（P1 只冻结语义，不实现）

### 3.1 回答（Answer）

```
accepted → inference.bound → selection.resolved → retrieval.completed
        → citation.ready → answer.delta* → {completed | refused | failed | cancelled}
```

- 终态四个，恰好出现一次；`answer.completed/refused/failed/cancelled` 之后不得再有事件。
- 每个事件携带 `answer_id`、`session_id`、`seq`（从 1 单调递增）；`Last-Event-ID` 映射到 `seq`，客户端按序去重。
- 证据不足是正常业务结果（`answer.refused`），不是传输错误。

### 3.2 任务（Job）

```
accepted → progress* → {completed | failed | cancelled}
```

- 每个事件携带 `job_id`，绝不伪造 `answer_id`。
- 进度未知时 `total_bytes` 为 `null`，不编造百分比。
- 租约、恢复与幂等在 P2 实现；P1 的 worker 拒绝启动处理循环。

### 3.3 模型安装

```
preview（无副作用）→ confirm(preview_id + preview_hash + confirmed + Idempotency-Key)
→ 下载/传输 → 身份校验 → 按角色验证 → 可用
```

- 预览与确认分离；没有绕过确认的接口、CLI 命令或 SDK 方法。
- 取消结果为“已请求取消/结果未知”，不得声称已终止运行时侧传输。
- 身份漂移（`MODEL_CHANGED`）拒绝继续；模型下载不等于可用。

## 4. 目录职责

| 目录 | 归组 | P1 内容 |
| --- | --- | --- |
| `Contracts/` | Contract Gate | DTO、错误、Protocol、SSE 事件 |
| `ServiceAPI/` | A1（路由/装配）+ A2（选库/模型/回答语义） | 应用工厂、设置、DI、错误映射、普通路由、worker 入口 |
| `Infrastructure/` | A1（SQLite/文件/快照）+ A2（索引/提供方/Ollama/目录） | 全部占位，方法抛 `FeatureNotImplemented` |
| `KBManagement/` | A1（服务/解析）+ A2（切分/索引算法） | 占位；解析器只做能力声明 |
| `Q&A_Assistant/` | A2 | 核心与状态机占位 |
| `Clients/python/`、`Clients/cli/` | A1 | SDK 与 CLI |
| `Clients/typescript/` | A1 | 共享 HTTP/SSE 传输层 |
| `WebUI/`、`WebWidget/` | B | P1-B 才创建页面 |

`var/`、`data/`、`models/` 为运行期目录，已被 `.gitignore` 忽略；启动和导入不得创建它们。

## 5. 运行期边界

- P1 API 只绑定回环地址；非回环绑定由 `qa-api` 直接拒绝。
- CORS 仅在 `QA_ALLOWED_ORIGINS` 显式配置时启用，且不携带凭据。
- 所有响应回显 `X-Request-ID`；未提供时由服务端生成。
- 内部异常只返回 `INTERNAL_ERROR`，不泄露路径、凭据或堆栈。
