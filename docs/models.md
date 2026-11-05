# 模型管理说明

P1 只冻结模型相关的契约、路由与占位；没有发现、安装、验证或推理行为。本文说明已冻结的语义与后续实现边界。

## 1. 角色与运行位置

| 角色 | 说明 | 契约 |
| --- | --- | --- |
| `generator` | 生成答案 | `Generator` Protocol |
| `embedder` | 文档/查询向量 | `Embedder` Protocol，`EmbeddingProfile` 固定维度与模型身份 |
| `token_counter` | 上下文预算 | `TokenCounter` |
| `support_checker` | 证据支持校验 | `SupportChecker` |
| `reranker` | 可选重排 | `Reranker` |

角色分别验证，不因一个角色通过就宣称另一个可用。`ModelCapabilities` 与 `RuntimeCapability` 记录支持情况。

## 2. 发现（Discovery）

- 只能对服务端 allow-list（`QA_RUNTIME_TARGETS`）中的 `target_id` 发起：`POST /v1/models/discovery` 的请求体只接受 `target_ids`。
- 请求中不得携带 URL、路径、令牌；DTO `extra="forbid"` 会拒绝这些字段。
- P1 不探测任何运行时；`/v1/models/capabilities` 返回静态 scaffold 状态。
- 状态区分：`installed`、`running`、`downloaded`、`loaded`、`verified_roles` 相互独立；未知就是未知，不推断。

## 3. 推理选择与策略

```json
{"inference": {"profile_id": "local-default", "policy": "local_only"}}
```

- `policy`：`local_only`（默认）或 `configured`。
- `local_only` 下任何远程角色或缺角色都返回 `INFERENCE_POLICY_VIOLATION` 或 `MODEL_CAPABILITY_MISSING`，不得静默 fallback。
- `configured` 只允许管理员预配置的外接 profile；调用方不能提交端点或凭据。
- 选库（`RetrievalSelection`）与推理（`InferenceSelection`）独立，互不影响。
- 会话内变更 inference 只影响下一轮；在途回答保持绑定的 `binding_id` 与 `inference_revision`，历史答案保留原模型身份。

## 4. 安装生命周期

```
preview → confirm → transfer(job) → identity → verify roles → usable
```

1. **预览** `POST /v1/model-installs/preview`：返回 `preview_id`、`preview_hash`、身份状态、已知大小、缺失层数、目标缓存、许可证链接与未知字段。零下载。
2. **确认** `POST /v1/model-installs`：必须携带 `preview_id` + `preview_hash` + `confirmed: true` + `Idempotency-Key`。预览过期或不匹配即失败。
3. **传输**：后台任务，SSE 事件带 `job_id`；`total_bytes` 未知时为 `null`，不编造百分比。
4. **身份**：下载完成后先登记实际完整身份（摘要、大小、层），再单独验证角色。
5. **取消**：返回“已请求取消/结果未知”，不得声称已终止运行时侧传输，不得杀共享部署器或删除共享层。
6. **恢复**：worker 重启后对账，区分完成、中断与未知。

没有绕过确认的 API、CLI 命令或 SDK 方法（`tests/scaffold/test_cli.py`、`test_sdk.py` 校验）。

## 5. 已观察的环境（只读，2026-11-05）

| 项 | 观察结果 | 限制 |
| --- | --- | --- |
| Ollama 可执行文件 | `C:/Users/fanmm/AppData/Local/Programs/Ollama/ollama.exe` | 仅本机单账户 |
| Ollama 版本接口 | `127.0.0.1:11434` 返回 0.17.5 | 未验证生成/嵌入/上下文容量 |
| 已下载模型 | `qwen3:8b`（约 5.23 GB，Q4_K_M）、`bge-m3:latest`（约 1.16 GB，F16） | 未加载、未验证角色、未评测质量 |
| 运行中模型 | 检查时为空 | 之后可能变化 |
| LM Studio / llama.cpp | 常见位置与默认端口未发现 | 不能认定未安装 |

官方文档在本轮未通过工具的网络校验，因此适配器协议、下载取消语义与支持版本仍是**待核验契约**，实现阶段须以可访问的官方文档和集成测试确认。

## 6. 未验证项

- 部署器版本/build 能力矩阵：未建立。
- 模型身份保证的边界（摘要与运行时不一致时如何处置）：契约定义了 `MODEL_CHANGED`，实现未验证。
- 生成质量、嵌入维度、中文召回、上下文预算：未测量。
- 安装取消/恢复的真实运行时行为：未验证。
