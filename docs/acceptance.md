# 验收记录

本文件按课程任务三的七项功能与模型/分发补充要求记录验收。**P1 只完成框架，业务功能均未验收**；下表的“P1 状态”指框架层证据，不代表业务通过。

## 1. 七项课程功能

| # | 课程要求（原文行号） | 最终目标 | P1 状态 | 业务验收阶段 |
| --- | --- | --- | --- | --- |
| 1 | 207 / 225 / 249 | CLI、网页均能建库，本地/上传目录全部或部分导入，多格式解析 | 路由、DTO、CLI 命令与解析器能力声明已就位；有效请求 501 | P2 |
| 2 | 209 / 227 / 255 | 内容增删改查完整，更新不破坏其他资料 | 路由与 DTO 已冻结；501 | P2 |
| 3 | 211 / 229 / 261 | 源文档增量同步，直接录入问答对 | 路由、来源清单与 QA DTO 已冻结；501 | P2 |
| 4 | 213 / 231 / 267 | 任意网站便捷嵌入，悬浮图标与弹窗，多轮上下文 | 仅共享 TS 传输层；WebWidget 页面属 P1-B（未开始） | P1-B / P3 |
| 5 | 215 / 233 / 273 | 有据回答、引用详情、证据不足友好拒答 | 引用/证据 DTO 与错误码已冻结；回答为 501 | P3 |
| 6 | 217 / 235 / 279 | 检索改进有效、语义异写可召回、真实流式输出 | SSE 事件 schema 与终态规则已冻结；流式端点预检即 501 | P3 / P4 |
| 7 | 219 / 237 / 285 | 认可/不认可反馈，未回答问题可用于补库 | 反馈 DTO 与路由已冻结；501 | P3 |
| — | 239 / 291 | Agent Insight 实际集成 | **延期**；未识别仓库 URL、版本与挂载点 | 未排期 |

用户补充要求：

| 要求 | P1 状态 | 验收阶段 |
| --- | --- | --- |
| 同会话随时切库；显式单库/多库/自动选库 | `RetrievalSelection` 联合已冻结并校验；接口 501 | P3 |
| 外接模型与本地 Ollama 均可问答；发现/选择/按需安装；权重不随包分发 | 模型 DTO、发现/安装/验证路由与占位已冻结；无真实探测 | P3 |
| 工程与分发：无权重、无自动下载 | `scripts/check_distribution.py` 可运行；无模型缓存路径引用 | P4 |

## 2. P1 框架层证据

环境：Windows 11（10.0.26200），Python 3.12.13，uv 0.10.x，Node 24.15.0，Go 1.27.1；仓库根 `D:\Datastruct\MUtils_web&AI`。

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| 包边界与无副作用 | `pytest tests/scaffold/test_packages.py` | 通过：导入/工厂不建目录、不联网 |
| 路由行为 | `pytest tests/scaffold/test_api.py` | 通过：health 200 `mode=scaffold`；readyz 503；业务 501；参数 422 |
| CLI | `pytest tests/scaffold/test_cli.py` | 通过：无安装绕过；未实现退出码 3；JSON 错误 |
| 存储/解析占位 | `pytest tests/scaffold/test_storage_placeholders.py` | 通过：构造不建库，方法抛 `FeatureNotImplemented` |
| SDK | `pytest tests/scaffold/test_sdk.py` | 通过：错误封装映射、非 JSON 安全、SSE UTF-8 分块 |
| 契约 | `pytest tests/contracts` | 通过：DTO 判别联合、错误码、OpenAPI/SSE schema、provider/consumer fixtures |
| 契约制品 | `python scripts/export_contracts.py --check` | 退出码 0，`docs/openapi.json`、`docs/events.schema.json` 与代码一致 |
| Lint | `ruff check .` | 通过 |
| TS 传输层 | `tsc --noEmit`、`node --test` | 通过 |
| 环境报告 | `python scripts/check_environment.py` | 输出 JSON；仅查 PATH，未启动服务、未探测模型 |
| 分发检查 | `python scripts/check_distribution.py --check` | 扫描 Git 追踪文件与源码树，未发现权重（启发式） |
| 工程脚本 | `pytest tests/scaffold/test_scripts.py` | 通过：只读、不探测、不联网，权重标记与跳过依赖目录正确 |

全套 Python 测试：`150 passed`（`tests/scaffold` + `tests/contracts`），1 条 Starlette 弃用警告。

启动冒烟（真实进程，临时数据目录）：`qa-api --port 8765` → `/healthz` 200 `{"status":"ok","mode":"scaffold","schema_version":1}`、`/readyz` 503、`GET /v1/kbs` 501、`POST /v1/search {}` 422（`field=question`）；运行后临时数据目录未被创建。

## 3. 未验证与延期项

- P1-A2（问答核心语义）由另一并行会话负责，本记录不包含其结果。
- P1-B（WebUI/WebWidget）按用户安排暂停，未创建页面；对应的四项前端验收未执行。
- 真实语料、多格式解析、OCR、数据库、任务队列、模型发现/安装/推理、检索质量与延迟：全部未执行，不得引用为通过。
- 本轮未访问 Ollama/LM Studio 官方文档（网络校验未通过），适配器协议与取消语义仍是待核验契约；本机只读观察到 0.17.5 与两个已下载模型，未加载、未验证角色。
- Agent Insight：延期，验收材料缺失。

## 4. 复现

```bash
uv sync --all-packages --group dev
uv run --all-packages pytest tests/scaffold tests/contracts -q
uv run --all-packages python scripts/export_contracts.py --check
uv run --all-packages ruff check .
uv run qa-api   # 另开终端：curl -s http://127.0.0.1:8000/healthz
```
