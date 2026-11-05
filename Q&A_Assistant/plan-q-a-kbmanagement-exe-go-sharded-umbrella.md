# 课程任务三：问答小助手——逐文件、逐方法实施计划

## Context

目标是完成课程任务三的知识库问答插件，并满足用户的额外要求：问答能力可以由其他 AI agent 或普通程序通过稳定 API 调用；问答检索核心、知识库管理、API 和界面分开组织；**随时切换检索知识库，调用者可显式选单库、多库组合，或让系统自动选库**；**问答同时支持外接模型与本地 Ollama，WebUI 检测常见本地部署器和已安装模型，支持选择与按需安装模型，部署包不自带模型权重，以降低测试费用**。`Q&A_Assistant/` 仅容纳问答检索核心（含选库与跨库检索），`KBManagement/` 负责知识库创建、资料处理、增量更新与版本；模型管理由 `ServiceAPI` 编排、`Infrastructure` 适配，界面放在 `WebUI`。若以后制作桌面 EXE，前端界面和事件使用 Go。

**本轮只做只读勘察和计划编写。下一次按照本计划实施时，每个阶段先经过一个短暂的 Contract Gate 冻结共享 DTO、Protocol、OpenAPI、SSE 和错误码，再拆为后端 Part A 与前端 Part B。后端 Part A 内部继续拆成两条互不统属的平行进程：A1「平台与确定性工程组，难度 D1–D2」和 A2「核心语义与一致性组，难度 D3–D4」；两组只依赖冻结契约，不修改对方文件或要求对方批准。P1-B「前端布局与浏览器端占位」在 P1-A1/P1-A2 契约和占位接口可用后接入；完成 P1-A1、P1-A2、P1-B 后停止。** P2–P5 沿用相同 Contract Gate → A1/A2 平行后端 → B 前端模式。

### 依据与现状

- 权威原文：`Q&A_Assistant/课程任务.md`，任务三在第 195–301 行，需求在 207–219 行，验收在 225–241 行，高档标准在 249–291 行。第 3 行允许学生自行设计技术路线。
- 目前只有课程文档；`KBManagement/` 为空，没有现有业务函数、数据库、依赖清单、测试或启动入口。因此下面的业务文件和方法全部是**拟新增**，不存在可以沿用的现成实现。
- 目录沿用现有的 `Q&A_Assistant/`，不再新建重复的中文目录。P1 拟将课程文档原样移动到 `docs/course/课程任务.md`，保留内容，使核心目录职责单一；本轮不移动。
- 七项功能维度按高档目标设计。仅暂缓 Agent Insight 的实际集成；通用网页插件仍必须实现。实际集成完成前，不宣称课程八项全部验收完成。
- 已只读确认：uv 0.10.8、Python 3.12.13、Go 1.27.1、Node 24.15.0、npm 11.12.1。`soffice/tesseract/gcc` 未在当前 PATH 找到，不能据此推断机器完全未安装。后续文档转换、OCR 和 Go GUI 构建阶段再核验其依赖。
- 本轮只读观察：Ollama 可执行文件位于 `C:/Users/fanmm/AppData/Local/Programs/Ollama/ollama.exe`；`127.0.0.1:11434` 的版本接口报告 **0.17.5**。模型列表报告已下载 **`qwen3:8b`**（8.2B，Q4_K_M，5,225,388,164 字节，约 5.23 GB）及 **`bge-m3:latest`**（566.70M，F16，1,157,672,605 字节，约 1.16 GB）；准确标签使用冒号。运行模型列表为空，表示检查时没有模型驻留。仅确认安装、服务可达和模型清单，**尚未加载模型或验证生成、嵌入、上下文容量及质量**；大小不等于运行内存需求。
- LM Studio 与 llama.cpp 在所查 PATH 和常见位置未发现；LM Studio 的已知回环端口未返回响应。自定义安装位置、非默认端口和其他运行用户的模型仍未知，不能据此认定机器未安装。默认模型目录的文件存在也不等于模型下载完整或可运行。
- 本轮访问 Ollama、LM Studio 官方文档未通过工具的域名安全/网络校验，未改用其他方式绕过。下述适配器是待实施契约，精确的 SDK/API、下载取消语义和支持版本需在相应阶段依据可访问的官方文档与集成测试核验；不把候选能力写成已验证功能。

## 1. 推荐技术路线和模块边界

采用 **Python 3.12 模块化单体 + FastAPI + 独立 TypeScript 网页管理端和网页插件**。先运行一个 API 服务和一个同部署后台工作进程，避免为课程项目引入多套微服务、消息队列和网络数据库。

| 部分 | 推荐方案 | 约束 |
| --- | --- | --- |
| 公共契约 | Pydantic v2 数据模型、Python Protocol | 不依赖 FastAPI、数据库或模型 SDK |
| 问答核心 | Python，关键词/语义检索融合、上下文处理、证据约束 | 不含 HTTP、会话持久化、文件上传、界面 |
| 知识库管理 | Python，解析/切分/增量/内容 CRUD/版本服务 | 独占知识内容写入与索引发布职责 |
| API | FastAPI、HTTP JSON、OpenAPI、SSE | 所有客户端共享同一业务入口 |
| 本地存储 | SQLite 元数据 + 内容寻址文件 + 不可变版本索引目录 | 默认面向课程语料规模；容量和延迟由后续实测验证 |
| 检索实现 | 中文分词 BM25 + 归一化向量余弦检索 + 库内 RRF 融合 | 初版向量索引可使用 NumPy 精确检索；单库重排可配置，多库合并使用公共文本相关性重排；效果由评测验证 |
| 模型 | 分离 `Embedder`、`Generator`、`TokenCounter`、`SupportChecker`、`Reranker`；本地 Ollama 与外接模型使用窄适配器 | 默认先验证本机已下载模型；提供全链路 `local_only` 策略，禁止隐式切换付费服务；P1 仅接口占位 |
| 模型管理 | ServiceAPI 编排发现、配置、验证和按需下载任务，Infrastructure 对接部署器，WebUI 展示与选择 | 应用安装包、仓库、前端资源、容器与可选 EXE 均不捆绑权重；模型保留在部署器管理的独立存储中 |
| 网页端 | TypeScript + Vite；管理端和插件独立构建 | 插件可用普通 script 标签接入，不要求宿主使用特定框架 |
| CLI / SDK | Typer CLI + 薄 Python HTTP client；共享 TS client | 不在客户端复制检索、版本或导入业务逻辑 |
| 可选 EXE | Go + Fyne 原生 GUI，通过 HTTP 调用服务 | Go 实际编写界面；Python 后端的运行与分发单独说明 |

BM25、向量索引和切分参数是推荐实现起点，不是已经验证的最优配置。中文语料、分词词典、切分边界和向量模型必须经过 P3 的真实评测再锁定。

### 后端并行分工、难度与治理边界

为允许两组真正并行、互不统属，后端工作按**技术不确定性和一致性风险**而不是按上下级关系拆分。难度仅用于排期和人员匹配，不代表审批权：

- **D1 工程搭建**：包、配置、生成脚本、简单路由/DTO 接线、基础测试；实现路径确定，风险较低。
- **D2 确定性系统**：SQLite/文件存储、解析、CRUD、任务租约、幂等、上传、构建/分发；复杂但输入输出可精确验证。
- **D3 算法与运行时适配**：混合检索、自动选库、跨库融合、上下文、Ollama 流式/嵌入/安装适配；存在协议和质量不确定性。
- **D4 高风险一致性**：证据支持校验、模型身份固定、local_only 全链路、并发状态机、取消/恢复、引用与流式一致性、质量评测；需要专门设计和对抗性测试。

**A1 平台与确定性工程组（D1–D2）独占目录/文件：** `Infrastructure/sqlite.py`、`repositories.py`、`migrations/`、`blobs.py`、`snapshots.py` 的文件存储部分，`KBManagement/service.py`、`content.py`、`imports.py`、`sources.py`、`parsers/`、`versions.py`，`ServiceAPI/app.py`、`settings.py`、`container.py`、普通 CRUD routes、`jobs.py` 的通用租约框架，Python SDK/CLI、工程脚本与对应 scaffold/integration 测试。

**A2 核心语义与一致性组（D3–D4）独占目录/文件：** `Q&A_Assistant/src/qa_assistant/` 全部，`KBManagement/chunking.py`、`indexing.py` 的检索/向量算法部分，`Infrastructure/indexes.py`、`providers.py`、`ollama/`、`catalog.py`，`ServiceAPI/selection.py`、`models.py`、`conversations.py` 的问答执行部分、`events.py` 的答案语义，模型/选库/回答 routes，Evaluation 与检索、选库、模型、证据、流式测试。

**Contract Gate 共享但只在阶段开头短暂协作：** `Contracts/`、`docs/openapi.json`、`docs/events.schema.json` 及跨组错误码。每个阶段开始先由双方提交契约变更提案，合并为带版本的冻结基线；冻结后 A1/A2 只消费契约。任何破坏性变更进入下一 Contract Gate，不在阶段中途直接改共享定义。兼容性新增必须通过契约测试且不得要求另一组同步重写。

**禁止交叉管辖：** A1 不修改 A2 独占文件，A2 不修改 A1 独占文件；两组各自决定内部实现、测试和提交顺序。跨组需要的新能力以 Protocol/DTO/fixture 请求表达，不直接给对方代码评审结论或合并前置许可。集成失败先由契约测试判定归属：提供方违反冻结契约则提供方修复，契约未覆盖则记入下一 Gate。

### 依赖方向

- 网页、插件、CLI、Go 桌面端 → HTTP API。
- `ServiceAPI` → `Q&A_Assistant`、`KBManagement`、`Contracts`；负责装配 `Infrastructure`。
- `Q&A_Assistant`、`KBManagement` → `Contracts`，不互相导入实现，不依赖 `ServiceAPI`。
- `Infrastructure` 实现 `Contracts` 的存储、模型和检索端口；不承载知识库发布规则或问答编排。
- CLI 和其他程序复用 `Clients/python`；管理网页与插件复用 `Clients/typescript`。插件不得导入管理网页代码。
- 反馈、任务、会话属于应用层，放在 `ServiceAPI`，不挤进问答核心。

### 顶层目录

```text
Q&A_Assistant/src/qa_assistant/        问答检索核心
KBManagement/src/kb_management/      知识库领域能力
Contracts/src/qa_contracts/          跨模块模型、错误和端口
Infrastructure/src/qa_infrastructure/ 存储、索引、模型适配
ServiceAPI/src/qa_service/          API、鉴权、会话、反馈、任务
Clients/python/src/qa_client/       Python HTTP SDK
Clients/cli/src/qa_cli/             CLI
Clients/typescript/src/             共用网页 HTTP/SSE SDK
Clients/desktop-go/                 可选 Go 原生桌面端
WebUI/                             知识库管理网页
WebWidget/                         可嵌入悬浮问答插件
Integrations/agent-insight/         延期的平台适配说明
Evaluation/                        语料清单、标注、评测脚本
examples/                          程序调用、两站点嵌入示例
tests/                             框架、业务、端到端测试
docs/                              课程原文、架构、契约、验收材料
scripts/                           启动、契约导出、环境检查
var/                               运行时数据，加入忽略，不提交
```

外层目录包含 `&` 不影响文件组织；Python 导入使用合法包名 `qa_assistant`，不用外层目录名作包名。所有涉及路径的命令正确引用路径。

## 2. 课程要求逐项映射

| 原文行号 | 最终目标 | 实现归属与验收依据 |
| --- | --- | --- |
| 207 / 225 / 249 | CLI、网页均能建库，本地/上传目录全部或部分导入，多格式解析 | `KBManagement`、CLI、WebUI；每种入口与选择方式均有样例，核对解析正文和位置 |
| 209 / 227 / 255 | 内容新增、删除、修改、查询完整，更新不破坏其他资料 | 内容服务、版本服务；发布后查询最新内容，未变更文档保持完整 |
| 211 / 229 / 261 | 源文档增量同步，直接录入问答对 | 来源清单、同步差异、QA 内容类型；验证仅变化内容重新解析/嵌入 |
| 213 / 231 / 267 | 任意网站便捷嵌入，悬浮图标和弹窗，多轮上下文 | WebWidget、会话服务、上下文处理；两个独立站点和至少三轮指代追问 |
| 215 / 233 / 273 | 有据回答、引用详情、证据不足友好拒答 | 证据校验、历史引用 API；逐条核验引用内容和版本，测试库外/冲突问题 |
| 217 / 235 / 279 | 检索改进有效、语义异写可召回、真实流式输出 | 混合检索、评测、SSE；基线对比、流式时序及异常测试 |
| 219 / 237 / 285 | 认可/不认可反馈，未回答问题可用于补库 | 反馈服务、问题列表、复测；关联原问题、补充修订、版本和验证结果 |
| 239 / 291 | Agent Insight 实际集成 | 延期；记录准确仓库 URL、版本和宿主接入点后补做 |
| 241 | 明确语料、文档、环境、满足情况与依据 | `docs/acceptance.md` + Evaluation 报告 + 可复现测试 |
| 用户补充 | 同会话随时切库，API 显式单库/多库组合/自动选库 | 核心 routing/federation、selection 契约、会话设置与插件选择器；第 3.5、5.1 节定义行为，第 7、8 节测试与评测 |
| 用户补充 | 外接模型与本地 Ollama 均可问答；检测常见部署器/已装模型；WebUI 选模型并按需安装，权重不随部署包分发 | 第 3.6 节模型策略、Infrastructure 部署器适配、ServiceAPI 模型管理、WebUI 模型页；第 5.4 节 API；验证本地完整问答链路、安装任务和无隐式云端调用 |

Word 和 Excel 的最终格式范围定为 `.doc/.docx/.xls/.xlsx`，并支持 `.md/.txt/.pdf`。现代格式使用对应解析库；旧 `.doc` 使用受控转换适配器，`.xls` 使用旧格式读取适配器。扫描 PDF 设置 OCR 扩展路径；最终验收若包含扫描件，必须配置并验证 OCR，不能把空文本当成功。加密、损坏、不支持或超限文件均返回逐文件诊断。

## 3. 公共契约和一致性规则

### 3.1 数据标识和结构

所有实体使用服务端生成的不透明 ID：`kb_id/document_id/revision_id/version_id/chunk_id/source_id/session_id/answer_id/job_id`。响应附 `request_id`；时间采用 UTC，列表使用游标分页。

- `KnowledgeBase`：名称、说明、领域标签、路由示例问题、活动版本、管理配置、ETag；路由描述更新会刷新目录 revision，发布摘要按版本保存。
- `Document` / `Revision`：逻辑文档、不可变修订、内容类型、来源 ID、相对路径、原件哈希、规范化正文、解析诊断。直接录入 QA 是一种内容类型，同样可以修改、删除和引用。
- `Snapshot`：文档修订集合、片段映射、索引文件清单、解析/分词/切分配置，以及可选的 embedding 配置指纹/构建时 `inference_binding_id`、状态、父版本。P2 的关键词快照可明确标记 `vector_index=absent`；P3 起向量快照必须保存 embedding 指纹（模型身份、维度、预处理、归一化和截断策略），不能只存可变模型标签。
- `Chunk`：原始位置与规范化文本映射、所属修订、内容哈希；不能只保存一段失去来源的字符串。
- `Locator`：MD/TXT 原文行号与标题；Word 段落/表格；Excel 工作表和单元格范围；PDF 实际页码及可选坐标；QA 记录和字段。没有稳定页码的格式不生成假页码。
- `Citation`：引用 ID、上述来源标识、原文引句、locator、内容哈希、可授权访问的详情路径。
- `Session`：主体、可修改的 `default_selection` / `scope_revision`、`default_inference` / `inference_revision`、分段的已完成对话轮次和状态；会话不永久绑定单库或模型。`Answer` 保存问题、请求选库与模型策略、实际 `resolved_scope`、`effective_inference`、`inference_binding`、检索证据、已验证片段、终态、错误/拒答原因及调用量。待绑定的字段为 null，不编造模型身份。模型默认值变化只影响之后接受的请求。
- `RetrievalSelection`：统一选库请求。`explicit` 携带非空 `targets:[{kb_id,version_id?}]`，一个 target 即单库，多个即组合；`auto` 携带可选 `candidate_kb_ids` 和 `max_kbs`。同一请求不重复选择同库的不同版本。
- `ResolvedScope`：`scope_id`、不可变 `targets:[{kb_id,version_id,embedding_profile}]`、选库策略版本和解析时间。`SelectionResult` 记录请求模式、选库结果/简要理由和 `resolved/no_match/needs_clarification` 状态；不同库没有一个共享的 `version_id`。
- `Feedback` / `Issue`：answer 关联、评价与说明、未解决问题、实际选库清单/版本、补库修订、复测范围和处理状态。
- `Job`：种类、状态、进度、逐文件诊断、幂等键、执行租约、结果版本、错误。问答生成与知识导入使用独立任务类别，互不堵塞。

### 3.2 工作稿、发布和回滚

1. 内容编辑进入工作稿；变更操作返回 `ChangeReceipt` 和构建任务。默认提交后自动构建并发布，显式选择暂存时才停留在工作稿。界面清楚显示“处理中/已生效”，避免操作成功却一直不进入问答。
2. 版本经过 `draft → staging → ready`，构建失败标记 `failed`。写完并校验不可变文件后，再用数据库事务和 `expected_active_version` 比较交换活动指针。`published` 表示曾发布，当前版本由活动指针唯一确定。
3. 解析、嵌入或写索引失败不改变活动版本。进程崩溃留下的孤立 staging 文件可由后台清理；不能让指针指向半成品。
4. 回滚切换到已校验的旧快照，不覆盖旧文件，也不从当前正文重新生成所谓旧版本。回滚后的同步以选定基线重新比较源清单。
5. 一次搜索/回答固定一组 `ResolvedScope.targets`，每个知识库绑定自己的不可变版本。未指定版本时，在执行前一次解析为该库当时活动版本；显式版本保持原值。同一库不能在一次回答中切到新版本。会话允许随时更改下一轮默认选库，不必新建会话；在途回答保持原范围，新请求使用最新选库设置。每次访问仍重新检查当前权限。多库活动指针在同一数据库读事务中解析，这代表一个可追溯的版本组合，不宣称各库发布是跨库原子操作。
6. 删除内容会影响新发布快照；保留期内旧回答引用仍指向各自原修订。历史清理必须检查活动版本、显式版本默认配置、在途选库候选版本租约、已解析范围和历史引用依赖。资源确已清理则返回 410，不能跳到同名新文档。库被撤销访问或删除后，旧版本也不绕过授权。

### 3.3 增量规则

- 用来源 ID、标准化相对路径、内容哈希、解析/切分/embedding 配置指纹判断复用。无变化不重新解析或生成向量；配置变化需要重建时明确记录原因。
- 删除仅从**同一来源范围的完整、成功扫描**推断。部分导入、部分重传、目录不可读或扫描中断均不意味着未出现的文件被删除。
- 默认导入采用 merge；mirror 同步必须展示完整差异，并以预览摘要确认将删除的内容。提交时再次校验预览、文件哈希及版本，避免预览后文件变化。
- 手动编辑和源文件修改并发时返回冲突，选择保留手动修改、采用源文件或创建独立文档，不能静默覆盖。
- 服务端目录通过授权 `root_id` 和相对路径访问，提供显式同步与后台轮询。CLI 连接远程服务时，将客户端本地文件上传，不能把客户端盘符当服务端路径。
- 网页通过目录选择器保存相对路径、支持逐文件勾选；下一次同步需重选/重传。不得声称浏览器关闭后还能持续监听用户磁盘。
- 未变更片段及其向量复用。发布完整快照时允许从缓存重算 BM25 全局统计或组合向量映射，但这不应触发所有文档重新导入；验收检查实际解析/嵌入次数。

### 3.4 回答、引用和真实流式

检索链路为：捕获本轮选库与模型策略 → 提取允许使用的用户问题上下文 → 以确定性描述匹配确定候选，校验显式目标并一次固定候选快照 → 绑定所需角色模型并持久化 `InferenceBinding` → 在固定候选内进行可选指代改写、证据探测及自动选库 → 最终范围组成 `ResolvedScope` → 按当前范围整理历史 → 各库中文关键词与向量检索 → 公共文本评分合并 → 证据充分性检查 → 依据生成 → 引用/支持关系校验 → 输出。选库分为不调用模型的准备步骤和绑定后的探测步骤；没有候选时可直接返回无匹配，不加载模型。

模型生成的是待校验内容。服务端按句或短完整事实单元缓冲，检查引用 ID 存在、引文匹配、位置一致以及事实支持关系，再向客户端发送增量。资料和历史中的指令都作为数据处理；历史回答不能替代本次检索的证据。证据不足或矛盾未解时友好拒答。

结构校验不能证明语义一定正确，语义校验器也可能误判；最终需要固定语料人工核验和回归测试，不作普遍“零幻觉”保证。流式不得等全文完成后再定时切字。若尚未输出内容便无法验证，可终态 `refused`；已有部分输出后校验失败，则终态 `failed` 并标记内容不完整，不提交为正常历史。

### 3.5 单库、多库、自动选库与会话切换（新增要求）

**统一选择器。** `/search`、`/ask`、会话回答共用 `RetrievalSelection`，不会存在只能由网页切库的隐藏状态。`explicit.targets` 为一项时只查该库，为多项时检索组合；`auto` 在授权候选中为本轮问题选择一个或多个库。自动候选省略表示调用者当前有权检索的库，显式空列表属于参数错误，不解释为全部。调用者可以设置候选范围和 `max_kbs`，服务端设置最大候选数、检索并发及超时，实际值在 capabilities 中公布。

**优先级和切换。** 本次请求 `selection` 高于 `Session.default_selection`；都未指定则自动选库。单次覆盖不修改会话默认值；`PATCH /v1/sessions/{id}/selection` 通过 `expected_scope_revision` 更新以后轮次的默认值。该更新即使有在途回答也可以提交，返回“下轮生效”；在途回答不会改范围，需要立即使用新选择时取消后重新提交。提交回答以事务捕获本轮策略和 revision，防止更改默认值的并发请求意外改变已接收问题。多标签页使用 revision 检测过期设置，冲突返回 409。

**版本和历史。** 请求接受时保存选库策略，执行时一次解析候选/目标版本；自动探测后的最终范围只能从该批已固定的候选快照中选择，不再读取“最新版本”替换。最终选定的 `resolved_scope` 写入答案后不可改。每轮未指定版本的库读取当时活动版本，所以同一会话下一轮能查询新发布知识；指定版本可固定复现实验。范围集合或任一库版本变化时产生上下文分段标记，历史消息仍可查看，但默认不向模型转入旧段的答案、证据或旧库指代；用户可显式请求 `carry_user_questions`，仅携带仍获授权的用户问题用于意图解析，事实仍必须在本轮范围重新检索。范围不变时可按原多轮策略使用完整已完成历史。自动选库可利用当前段用户问题和前次已选库作辅助信号，但必须逐轮重新判断，不把上一库永久锁定；切换后发现未消解指代时询问澄清，不自行拿旧库补答案。

**自动选库过程。** 管理员维护各库的名称、领域说明、标签、示例问题，发布版本提供可追溯摘要；这些字段随 KB 管理维护。应用层先按当前权限和候选白名单取描述，再由核心 `KnowledgeRouter` 对问题和允许使用的用户上下文进行中文关键词/描述匹配，选出有预算的候选；对这批候选一次固定快照，以只读轻量探测确认是否含证据，对各库的探测片段使用同一文本评分器比较支持度，再选择最多 `max_kbs` 个；不直接比较不同 embedding/BM25 的原始分数。第一版不依赖生成模型挑库，因此纯检索在生成模型关闭时仍能自动选择；后续若使用模型辅助，只能建议当前允许列表内的 ID，仍须结构和权限复验。无候选或证据不足返回 `no_match`，歧义或必要库数量超出允许预算返回 `needs_clarification`，问答友好拒答/请用户明确范围；不静默扫描额外库。所有显式列出的 target 或 candidate 都逐项鉴权，列入无权限 ID 的请求整体失败；候选字段省略时则先过滤目录，仅使用可访问的库。授权外的库名、描述和数量不进入路由、日志、说明或客户端响应。选库结果给出策略标识和简短匹配依据，不暴露模型思维过程。

**多库合并。** 每库内部先完成关键词/向量融合，按各快照自己的 embedding profile 生成查询向量，不把不同模型/维度的向量或原始 BM25 分数直接混加。每库采用受限但公平的候选预算，合并后用同一个基于文本的相关性重排器形成总 top-k；库内 RRF 保留用于关键词/向量融合，不能把互不重合的各库局部名次直接当作跨库相关性。单库重排仍可配置，多库模式要求该统一重排能力可用；显式指定的每个库都必须实际尝试检索，不能再被自动路由排除。跨库标识始终使用 `(kb_id,version_id,chunk_id)`；重复正文可合并展示，但保留所有来源，冲突资料应并列说明或拒答。缓存键包含主体授权范围/授权版本、选库策略、各库版本、过滤条件和模型配置，不能沿用单库查询缓存。

**失败与可追溯性。** 显式选择含无权限、缺失、未发布或不兼容版本时整次请求明确报错，不自动少查一个库或换库；自动选择在候选描述和证据分数之外另记探测失败，有执行故障则返回错误，不能误报“没有知识”。版本固定后的任一选定库失败也终止本轮；不将部分检索伪装为完整组合答案。响应区分 `requested_selection`、`resolved_scope.targets`（实际检索的库及版本）和 `used_kb_ids`（最终有引用支持的库）。界面显示本轮实际范围，每条引用保留库名、库 ID 和版本；历史引用始终按该答案自己的范围授权访问。

### 3.6 本地/外接模型、发现与按需安装（新增要求）

**检测位置与状态。** WebUI 通过 ServiceAPI 检测**后端服务所在主机、该服务运行用户可见的部署器及模型**，页面显示主机标识和检测时间。本机运行服务时可复用当前 Ollama；远程服务器、容器、其他 Windows 账户的文件系统与回环地址不同，必须显式配置后端可达的部署器。浏览器不扫描用户电脑。发现范围限定为 PATH、少量标准安装位置、管理员配置的路径与端点；不遍历整盘或扫描局域网。只读发现不启动部署器、不加载模型、不下载权重、不进行推理。

状态分开记录 `installed`（可执行程序/安装证据）、`running`（协议服务可达）、`downloaded`（部署器登记的完整模型）、`loaded`（驻留）、`verified_roles`（通过哪些角色的最小调用验证）；均允许未知，并附时间、证据和诊断。发现接口得到的清单不直接使模型成为可用默认配置。轻量验证与完整质量评测分开；验证会占用计算资源，由管理端显式提交任务。普通调用者只能看到获授权的模型配置摘要，不获得本机路径、服务密钥或管理能力。

**运行时支持边界。** Ollama 是必须完成发现、模型枚举、流式生成、嵌入和按需拉取的首个部署器，首个验收版本以本机观察到的 **0.17.5** 为准，不宣称是最新版本。LM Studio、llama.cpp 同样列入常见部署器检测；按已验证的版本/build 和能力矩阵枚举模型。原生模型管理接口、兼容推理接口与本地文件证据分别记录；兼容接口的模型列表不能证明磁盘上所有权重均已下载。llama.cpp 的单模型服务只能报告其暴露的模型，其他 GGUF 文件仅在已配置目录内作为待验证候选。未验证的管理操作标为不支持/未知；安装部署器软件本身提供官方安装及启动指引，不运行任意安装脚本或提升权限。Ollama 缺失时先完成其安装配置，再由本系统下载模型。

**本地优先与各角色。** 以本机 `qwen3:8b` 作为生成、可选改写和结构化支持校验的首个验证候选，`bge-m3:latest` 作为嵌入候选。支持校验通过独立的 `PromptSupportChecker` 适配并验证输出结构与证据，不因生成模型可用而标为已支持。跨库公共评分初版采用 `SharedEmbeddingReranker`：使用同一已验证本地嵌入模型，重新编码各库候选原文与查询后统一评分，缓存带模型摘要；这是一条公共文本相关性基线，不称为专用 cross-encoder，也不混用各库原始向量分数。效果不足时再在相同端口接入经过评测的本地重排模型。纯检索及自动选库不需要生成模型；若公共评分、必要嵌入或支持校验缺失，对相应操作明确报错，不能静默跳过。

**配置、请求与费用策略。** 模型选择与知识库 `selection` 独立，统一使用 `InferenceSelection{profile_id,policy}`。`InferenceProfile` 为不可变修订，逐项指明生成、改写（可禁用）、支持校验、公共重排、计数器及允许的嵌入绑定；包含模型来源、精确标签/模型 ID、可获取的摘要、量化、参数和预算。默认 `policy=local_only`；显式 `configured` 才允许使用管理员已配置且调用者有权使用的外接模型。每次请求可覆盖，会话可通过 `expected_inference_revision` 修改以后轮次的默认配置；优先级为请求、会话、服务端默认，单次覆盖不修改默认。没有合格本地配置时返回配置缺失，不选择云端备选。

`local_only` 覆盖文档入库嵌入、查询向量、路由探测、改写、生成、支持校验、重排及评测。所有端口使用同一策略约束，即使直接从 Python 调用核心也必须提供绑定。仅检查 URL 是 localhost 不足以证明本地执行：应识别部署器提供的云模型/代理标识，禁用 HTTP 环境代理和重定向，核验运行时本地模式；若本地执行属性未知则拒绝标记为 `local_only`。验收中检查后端及受控部署器的外网推理出口；对未受控部署器不能作不可验证的保证。模型下载的外网授权单独绑定安装预览，不放宽推理策略。外接服务的端点、模型与凭据引用由管理员配置，浏览器仅收发配置 ID 和脱敏摘要；不得把问答 API 变成任意 URL 代理。调用预算覆盖所有角色，超限与超时有明确错误，无隐式云端或其他付费 fallback。

**一次请求内固定配置。** 幂等检查先于读取当前默认配置。接收问题时捕获 `EffectiveInference`（选项、profile 不可变修订和参数）；执行时从授权目录以确定性描述匹配确定探测候选，固定候选快照及其 embedding profile，在任何模型调用前构造并持久化 `InferenceBinding`。可选模型改写只能在已固定候选/绑定内执行；不得用改写结果重新扩大候选。绑定包含所有候选所需嵌入、各角色精确模型标识、执行位置和预算；自动选择的最终范围仅取该候选集合。纯检索、选库预览和导入任务按同一规则绑定各自实际所需角色。已接受的回答不因修改模型默认值而变化；同键重试返回原绑定。调用前复验摘要和权限，检测标签漂移则报 `MODEL_CHANGED`，不替换成同名新模型。

**嵌入兼容与身份限制。** 索引快照固化嵌入模型摘要/可识别版本、维度、归一化、文本预处理和截断策略；查询使用相同指纹。用户换生成模型不重建索引；换嵌入模型必须创建新快照，保留旧版本。多库使用不同嵌入模型时分别生成查询向量，`local_only` 不允许为某个库悄悄调用远程嵌入；必要模型缺失或策略不兼容明确失败。验收优先使用运行时支持的不可变模型引用；若仅支持可变标签，则保存前后核验记录并注明竞态限制，要求严格复现时拒绝该绑定，不能把数据库内固定配置等同于外部权重永远不变。

**按需安装流程。** 模型页选择已配置运行时和受支持来源的模型 → 生成安装预览 → 显示准确标签、来源、已知摘要、大小/缺失层、目标缓存、剩余磁盘估计、许可信息链接及未知项 → 用户确认预览 → 后台拉取 → 核验完整模型清单/摘要 → 刷新列表 → 单独进行角色验证。预览不会下载权重；需要查询远程元数据时仅发送模型标识，不发送问答资料。总大小未知时显示已下载字节及不定进度，不编造百分比或可用内存结论。目标/已知摘要发生变化或预览过期须重新确认；源接口不支持事前摘要时将 `identity_status=unresolved` 明示并纳入确认摘要，完成后登记实际身份，验证和启用前仍需核对，不能声称下载已按未知摘要固定。已有相同摘要的模型直接复用，不能为满足流程重复下载。

**下载任务与恢复。** 复用 `JobService`，增加 `model_install`、`model_verify` 任务类别；下载并发和推理并发分别限额。同目标的活动下载通过数据库唯一键及租约合并，持久化运行时传输句柄、分层进度、预览摘要和检查点。取消先进入 `cancel_requested`；经适配器确认停止或完成后再进入对应终态。关闭 HTTP 连接不被当作已验证的上游取消；不杀共享 Ollama 进程，不删除其他模型的共享层。取消语义未知时保留待对账状态并显示原因。重启后先查询部署器/传输状态及实际模型摘要，确认已完成则收敛到完成；确认中断且已验证支持恢复时续传，不支持则显示需要重新开始，身份变化须新预览。部分文件与某层 100% 均不算整模型成功。断网、磁盘不足、鉴权失败、损坏下载、运行时退出分别诊断。

权重保存在部署器管理的独立缓存或明确配置的模型卷中，不加入 Git、Python wheel、前端静态资源、容器镜像或 Go EXE；应用首次启动也不自动拉取。模型目录的可见性、备份与卸载由部署文档说明。问答运行时缺少模型时仅返回可操作诊断，不自动创建下载任务。

## 4. 逐文件、逐方法设计

以下路径相对项目根。`ID=str`；`Page[T]` 为游标分页；`Optional[T]` 表示可空。签名省略 `self`，服务端 I/O 方法采用 `async`，迭代式输出标明 `AsyncIterator`。构造函数仅接收所在行列出的依赖，不做联网、建库或模型加载；自动生成的数据模型方法、空 `__init__.py` 不另造业务逻辑。Contract Gate 先冻结公共契约；P1-A1 建立平台、存储/API、SDK/CLI 与共享传输层占位，P1-A2 建立问答核心、检索/模型端口与一致性状态机占位，P1-B 单独建立 WebUI/WebWidget 布局。各组只修改自己的 owner 文件；除明确工程接线外均不实现业务方法体。

### 4.1 根配置和说明文件

| 文件 | 内容 / 入口 |
| --- | --- |
| `pyproject.toml` | uv workspace，纳入七个 Python 包，统一 Python 3.12、测试、lint 和开发依赖；不把重型模型库放入基础安装 |
| 各 Python 包的 `pyproject.toml`、`src/<package>/__init__.py` | 最小构建信息、声明式导出；例如 `Q&A_Assistant/pyproject.toml`、`KBManagement/pyproject.toml`；依赖服从第 1 节方向 |
| `.python-version`、`uv.lock` | 固定选用的 Python 系列与已解析依赖；锁文件仅在 P1 安装/解析时生成 |
| `package.json`、`package-lock.json`、`tsconfig.base.json` | TS client/WebUI/WebWidget workspace，统一 typecheck/build/test 命令，锁文件 P1 生成 |
| `.gitignore`、`.env.example` | 忽略运行数据、密钥、模型缓存和构建物；示例只列空值/占位，不内置凭据 |
| `README.md` | 模块职责、P1 未实现状态、安装/启动方式、API 最短调用链、后续阶段 |
| `docs/course/课程任务.md` | P1 原样迁移课程文档 |
| `docs/architecture.md` | 模块依赖、版本规则、状态机、目录职责 |
| `docs/api.md`、`docs/openapi.json`、`docs/events.schema.json` | HTTP/SSE 契约；JSON 由代码模型导出，避免维护相互矛盾的两份 schema |
| `docs/acceptance.md` | 七项验收表、语料/环境、实际结果和证据链接；集成单列延期 |
| `docs/development.md` | 分阶段依赖、数据库初始化、后台任务、解析/OCR 与可选桌面构建说明；本地模型缓存独立于安装包、运行账户和容器模型卷配置 |
| `docs/models.md` | 本地/外接模型配置、角色验证、按需安装、取消/恢复、仅本地策略和已验收部署器版本/build 能力矩阵；记录官方接口依据、观察时间、未知项及模型身份保证的限制 |

### 4.2 Contracts：只放公共定义

目录前缀：`Contracts/src/qa_contracts/`。

| 文件 | 类、函数与职责 |
| --- | --- |
| `knowledge.py` | 定义 `KnowledgeBase, Document, Revision, QAPair, BlobRef, Source, SourceManifest, Selection, Locator, ParsedBlock, ParsedDocument, Chunk, Snapshot, SearchScope`；定义 `CreateKB, UpdateKB, PutDocument, PutQA, ImportRequest, ImportPreview, ChangeSet, ChangeReceipt, PublishRequest, RollbackRequest`；类型校验，不访问服务 |
| `selection.py` | 定义 `KBTarget, ExplicitSelection, AutoSelection, RetrievalSelection, KBDescriptor, CatalogQuery, RoutingContext, RankedKB, ProbeBudget, ProbeResult, ProfileGroup, SelectionPreviewRequest, PreparedSelection, SelectionResult, ResolvedScope, EffectiveSelection, SessionSelection, ScopeChange, HistoryPolicy, UpdateSessionSelection`；`RetrievalSelection` 是按 mode 区分的严格联合，校验非空 targets/候选、唯一 KB、max_kbs 和互斥字段；`PreparedSelection` 保存授权候选、排序、一次固定的候选快照及租约，准备阶段无模型调用；预览请求也接收 `inference`；不复用文件导入的 `Selection` |
| `models.py` | 定义 `RuntimeTarget, RuntimeEvidence, RuntimeStatus, RuntimeCapability, ModelCapabilities, DiscoveryRequest, DiscoveryReport, ModelQuery, ModelRef, ModelRole, ModelIdentity, InferencePolicy, InferenceSelection, InferenceProfile, ProfileSummary, PutInferenceProfile, EffectiveInference, RoleBinding, InferenceBinding, BindingOwner, SessionInference, UpdateSessionInference, InstallRequest, InstallPreview, InstallConfirmation, InstallPlan, InstallResult, InstallJobStatus, TransferHandle, TransferState, CancelResult, VerifyModelRequest, ModelVerification, ModelCall, CallResult, UsageSummary`；状态、未知项、角色能力、身份、请求策略及安装确认字段按第 3.6 节定义；profile 修订不可变，公开摘要与内部端点/凭据引用分离；DiscoveryRequest 只能引用服务端已配置 target_id，不含 URL、路径或凭据 |
| `answers.py` | 定义 `SearchRequest, SearchResult, Hit, CreateSession, Session, Turn, AnswerContext, SubmitAnswer, AskRequest, AnswerHandle, Answer, Citation, CitationDetail, DraftFragment, DraftSentence, VerifiedSentence, GenerationRequest, EvidenceDecision`；检索/提问请求含独立的 `selection`、可选 `inference`，会话含两组默认值与各自 revision；回答与检索结果保存 SelectionResult/ResolvedScope 及实际模型绑定摘要，Hit/Citation 必须带 kb_id 和各自 version_id；GenerationRequest 明确绑定生成角色、提示、参数和调用编号 |
| `operations.py` | 定义 `Principal, AccessScope, APIError, Page, Job, JobCommand, FeedbackInput, Feedback, Issue, IssueResolution, RetestRequest, WidgetTicket, Capabilities, AnswerEvent, JobEvent, SSEEvent`；`SSEEvent` 为按类型区分的答案/任务事件联合，任务事件使用 job_id，不伪造 answer_id；Job 增加 model_install/model_verify 类别、下载检查点与取消待确认状态；RetestRequest 含 selection/inference，票据限定允许的 profile 与推理策略 |
| `errors.py` | `FeatureNotImplemented(feature)`、`ValidationFailed(details)`、`NotFound(resource)`、`Conflict(expected,actual)`、`PermissionDenied(action)`、`ProviderUnavailable(reason)`、`EvidenceInsufficient(reason)`；补充 `ModelUnavailable(model_id,reason)`、`ModelChanged(expected,actual)`、`InferencePolicyViolation(role)`、`ModelCapabilityMissing(role)`；稳定错误码，不暴露底层密钥/路径 |
| `ports.py` | 读取接口：`KnowledgeCatalog.list_authorized(access:AccessScope,query:CatalogQuery)->Page[KBDescriptor]`、`get_authorized(access:AccessScope,kb_ids:list[ID])->list[KBDescriptor]`；`SnapshotReader.resolve(kb_id,version_id)->Snapshot`、`resolve_many(targets:list[KBTarget],access:AccessScope)->ResolvedScope`（同一读事务解析所有版本）、`load_chunks(version_id,ids)->list[Chunk]`、`load_revision(revision_id)->Revision`；`KeywordReader.search(query,scope,k)->list[Hit]`、`VectorReader.search(vector,scope,k)->list[Hit]`。模型接口：`Embedder.embed(texts,profile,binding:RoleBinding)->Vectors`、`Generator.stream(request:GenerationRequest)->AsyncIterator[DraftFragment]`、`TokenCounter.count(request,binding:RoleBinding)->TokenCount`、`SupportChecker.check(sentence,chunks,binding:RoleBinding)->SupportDecision`、`Reranker.rank(query,hits,binding:RoleBinding)->list[Hit]`；角色绑定携带策略、确切模型/算法和预算，公共重排的嵌入子调用继承其绑定。写入接口：`BlobStore.put(stream)->BlobRef`、`get(ref)->BinaryIO`、`verify(ref)->bool`、`delete_unreferenced(refs)->GCResult`；`SnapshotWriter.stage(manifest)->StagingHandle`、`seal(handle)->SnapshotFiles`；`KeywordIndexWriter.build(chunks,profile)->IndexRef`、`VectorIndexWriter.build(vectors,mapping)->IndexRef`；`EmbeddingCache.get_many(keys)->CachedVectors`、`put_many(items)->None`。均只声明接口，使领域模块无需导入具体存储/模型类 |
| `model_ports.py` | `RuntimeDiscovery.discover(targets:list[RuntimeTarget])->DiscoveryReport`；`ModelRuntime.probe(target)->RuntimeStatus`、`list_models(target,query:ModelQuery)->list[ModelRef]`、`inspect(ref:ModelRef)->ModelRef`；`ModelInstaller.preview(req:InstallRequest)->InstallPreview`、`start(plan:InstallPlan)->TransferHandle`、`follow(handle:TransferHandle)->AsyncIterator[TransferState]`、`cancel(handle)->CancelResult`、`reconcile(plan,handle:Optional[TransferHandle])->TransferState`、`resume(plan,state)->TransferHandle`；`InferenceGuard.check(binding:RoleBinding)->None` 在模型调用前检查策略、身份、权限与预算。可选操作通过能力矩阵声明；所有协议不依赖具体部署器 SDK |
| `repositories.py` | 定义下列仓储和事务方法；所有实体参数/返回值使用上述模型，写操作受 UoW 事务约束 |

`repositories.py` 的方法逐项如下：

- `UnitOfWork.transaction()->AsyncContextManager[UnitOfWork]`：事务边界，异常回滚；事务内仓储共享连接。
- `KnowledgeRepository.get(kb_id)->KnowledgeBase`、`list(query:KBQuery)->Page[KnowledgeBase]`、`put(kb:KnowledgeBase,expected_etag:Optional[str])->KnowledgeBase`、`delete(kb_id,expected_etag)->None`。
- `SourceRepository.get(source_id)->Source`、`list(kb_id)->list[Source]`、`put(source:Source,expected_revision:Optional[ID])->Source`、`remove(source_id)->None`、`get_manifest(source_id,version_id)->SourceManifest`、`save_manifest(source_id,version_id,manifest)->None`：来源配置与同步基线不能仅存在进程内存。
- `ContentRepository.get(document_id,revision_id:Optional[ID])->DocumentDetail`、`list(query:DocumentQuery)->Page[Document]`、`append_revision(document_id,revision:Revision,expected_revision:Optional[ID])->Revision`；删除表现为新修订中的 tombstone，不直接抹掉历史引用。
- `SnapshotRepository.get(version_id)->Snapshot`、`list(kb_id)->list[Snapshot]`、`save(snapshot:Snapshot)->None`、`compare_and_swap_active(kb_id,expected_active:Optional[ID],target:ID)->bool`。
- `ConversationRepository.get_session(session_id)->Session`、`get_answer(answer_id)->Answer`、`create_session(session:Session)->Session`、`update_selection(session_id,selection:RetrievalSelection,history_policy:HistoryPolicy,expected_scope_revision:int)->Session`、`update_inference(session_id,inference:InferenceSelection,expected_inference_revision:int)->Session`、`list_turns(session_id)->list[Turn]`、`find_idempotent(principal_id,operation,key)->Optional[AnswerHandle]`、`accept_answer(session_id,request:SubmitAnswer,effective_selection:RetrievalSelection,scope_revision:int,effective_inference:EffectiveInference,inference_revision:int,key,request_hash)->AnswerHandle`、`bind_inference(answer_id,prepared:PreparedSelection,binding:InferenceBinding,expected_state)->Answer`、`bind_scope(answer_id,result:SelectionResult,expected_state)->Answer`、`append_event(answer_id,event:AnswerEvent)->AnswerEvent`、`read_events(answer_id,after:int,limit:int)->list[AnswerEvent]`、`finalize_answer(answer_id,result:Answer,expected_state)->Answer`；捕获两组默认配置与接收问题同事务，绑定后的候选、模型和最终范围不可重写；最终状态、历史轮次及终态事件同事务提交。
- `JobRepository.enqueue(command:JobCommand,key)->Job`、`get(job_id)->Job`、`claim(kind,worker_id,lease_until)->Optional[Job]`、`update(job:Job,expected_revision)->Job`、`recover(now)->list[Job]`；新增 `find_active_transfer(target_key)->Optional[Job]`、`save_transfer(job_id,state:TransferState,expected_revision)->Job`、`append_event(job_id,event:JobEvent)->JobEvent`、`read_events(job_id,after:int,limit:int)->list[JobEvent]`。下载去重依赖事务内目标唯一约束，不能仅靠先查后写；事件和检查点用于界面重连及进程恢复。
- `ModelRepository.list_runtimes()->list[RuntimeStatus]`、`save_discovery(report:DiscoveryReport)->None`、`get_model(model_id)->ModelRef`、`list_models(query:ModelQuery)->Page[ModelRef]`、`save_model(model:ModelRef)->None`、`get_profile(profile_id,revision:Optional[ID])->InferenceProfile`、`list_profiles(access:AccessScope)->Page[ProfileSummary]`、`put_profile(profile:InferenceProfile,expected_revision:Optional[ID])->InferenceProfile`、`disable_profile(profile_id,expected_revision)->InferenceProfile`、`save_preview(preview:InstallPreview)->None`、`get_preview(preview_id)->InstallPreview`、`save_verification(result:ModelVerification)->None`、`save_binding(owner:BindingOwner,binding:InferenceBinding)->None`、`get_binding(binding_id)->InferenceBinding`；配置修改追加修订，旧答案不读取可变默认值，验证结果绑定运行时版本、模型身份和角色；BindingOwner 支持答案、任务及短期检索/预览请求。
- `ModelCallRepository.begin(call:ModelCall)->ModelCall`、`get(call_id)->ModelCall`、`finish(call_id,result:CallResult,expected_state)->ModelCall`、`mark_unknown(call_id,reason)->ModelCall`、`summarize(owner:BindingOwner)->UsageSummary`：调用前持久化唯一步骤编号和预算占用，记录实际用量；上游结果不明不能自动重放计费步骤。
- `FeedbackRepository.upsert(feedback:Feedback)->Feedback`、`create_issue(issue:Issue)->Issue`、`get_issue(issue_id)->Issue`、`list_issues(query:IssueQuery)->Page[Issue]`、`update_issue(issue:Issue,expected_revision)->Issue`。

模型字段详细 schema 由上述模型文件按领域维护；业务输入不得使用无约束的 `dict` 代替已定义请求。查询 DTO 声明筛选、分页和作用范围，仓储不向客户端暴露 SQL。

### 4.3 Q&A_Assistant：问答检索核心

目录前缀：`Q&A_Assistant/src/qa_assistant/`。

| 文件 | 方法签名与职责 | 注入依赖 |
| --- | --- | --- |
| `service.py` | `QAService.prepare_selection(query:str,selection:RetrievalSelection,context:RoutingContext,access:AccessScope)->PreparedSelection`：无模型调用地准备并固定候选；`select(query:str,prepared:PreparedSelection,context:RoutingContext,binding:InferenceBinding)->SelectionResult`：绑定后探测并选择；`search(req:SearchRequest,scope:ResolvedScope,binding:InferenceBinding)->SearchResult`：按已绑定多库范围检索；`answer(req:SubmitAnswer,context:AnswerContext,scope:ResolvedScope,binding:InferenceBinding)->AsyncIterator[QAEvent]`：检索、证据和生成，不保存会话或二次改选范围 | KnowledgeRouter、FederatedRetriever、ContextBuilder、EvidenceGuard、GroundedGenerator |
| `routing.py` | `KnowledgeRouter.prepare(query,selection,context,access)->PreparedSelection`：鉴权、描述排序、一次固定候选快照；`select(query,prepared,context,binding)->SelectionResult`；`rank_candidates(query,descriptors:list[KBDescriptor],context)->list[RankedKB]`：确定性描述/标签排序；`probe(query,scope:ResolvedScope,budget:ProbeBudget,binding:InferenceBinding)->list[ProbeResult]`：仅在已固定候选上探测；`decide(ranked,probes,max_kbs)->SelectionResult`：选取/无匹配/需要澄清；显式模式在 prepare 校验全部目标，select 保留全部指定库 | KnowledgeCatalog、SnapshotReader、HybridRetriever、公共 Reranker、路由预算/策略配置 |
| `federation.py` | `FederatedRetriever.retrieve(query:str,scope:ResolvedScope,binding:InferenceBinding)->list[Hit]`：按库并发、有界调用单库检索；`group_profiles(scope)->list[ProfileGroup]`：仅兼容 profile 复用查询向量；`merge(query:str,per_kb:Mapping[ID,list[Hit]],k:int,binding:InferenceBinding)->list[Hit]`：公平候选预算后统一文本相关性重排；`deduplicate_preserving_sources(hits)->list[Hit]`：相同正文保留各库来源；缺库/出错不隐式降级 | HybridRetriever、Embedder、多库必需的公共 Reranker |
| `retrieval.py` | `HybridRetriever.retrieve(query:str,scope:SearchScope,binding:InferenceBinding)->list[Hit]`：取绑定中匹配该快照指纹的嵌入角色，执行两路召回；`fuse(keyword:list[Hit],semantic:list[Hit])->list[Hit]`：按排名融合；`deduplicate(hits)->list[Hit]`：相邻重叠证据去重；`rerank(query,hits,binding:InferenceBinding)->list[Hit]`：单库可关闭，启用时遵守同一策略 | KeywordReader、VectorReader、Embedder、可选 Reranker |
| `context.py` | `ContextBuilder.bound(turns:list[Turn],budget:int,binding:InferenceBinding)->list[Turn]`：按完整轮次和绑定计数器限制历史；`routing_context(question,turns,history_policy,access)->RoutingContext`：无模型调用地提取允许的用户问题；`filter_for_scope(turns,scope:ResolvedScope,policy:HistoryPolicy)->list[Turn]`：按范围变更分段；`rewrite(question:str,turns:list[Turn],binding:InferenceBinding)->RewrittenQuery`：绑定后可选改写，保留原问题及歧义；`build(question,hits,turns,scope,binding)->AnswerContext`：有界上下文，不扩大本轮范围 | TokenCounter、可选改写 Generator |
| `generation.py` | `GroundedGenerator.generate(req:GenerationRequest)->AsyncIterator[DraftSentence]`：请求含明确生成角色绑定；`SentenceBuffer.feed(fragment:DraftFragment)->list[DraftSentence]`、`finish()->list[DraftSentence]`：缓冲完整事实单元，处理截断，不将原始 token 直接透传 | Generator |
| `evidence.py` | `EvidenceGuard.check_retrieval(hits,question,binding:InferenceBinding)->EvidenceDecision`：证据不足/冲突判断；`validate(sentence:DraftSentence,evidence:list[Chunk],binding:InferenceBinding)->VerifiedSentence`：结构、引文和支持关系校验；`resolve(citation:Citation,scope:ResolvedScope)->CitationDetail`：读取该答案原范围的固定修订；`refusal(reason)->Refusal`：友好说明 | SnapshotReader、SupportChecker |
| `prompts.py` | `build_rewrite_prompt(question,turns)->Prompt`、`build_grounded_prompt(context)->Prompt`、`build_support_prompt(sentence,evidence)->Prompt`：提示模板与输入分隔；历史与文档均不能作为系统指令 | 无 |

可复用路径：API 的 `/search`、`/ask`、会话问答和反馈复测均调用 `QAService`，不各写一条 RAG 流程。

### 4.4 KBManagement：内容、来源和版本

目录前缀：`KBManagement/src/kb_management/`。

| 文件 | 方法签名与职责 |
| --- | --- |
| `service.py` | `KBService.create(req:CreateKB)->KnowledgeBase`、`get(kb_id)->KnowledgeBase`、`list(query)->Page[KnowledgeBase]`、`update(kb_id,req:UpdateKB,expected_etag)->KnowledgeBase`、`delete(kb_id,expected_etag)->Job`：库级生命周期和冲突检查 |
| `content.py` | `ContentService.put(req:PutDocument)->ChangeReceipt`：新建/替换/编辑内容；`get(document_id,revision_id)->DocumentDetail`、`list(query)->Page[Document]`、`delete(document_id,expected_revision)->ChangeReceipt`；`put_qa(req:PutQA)->ChangeReceipt`、`get_qa(id)->QAPair`、`list_qa(query)->Page[QAPair]`、`delete_qa(id,expected_revision)->ChangeReceipt`：问答对复用文档修订链。原始二进制替换或规范化文本编辑产生新修订，不假装回写原 Word 文件 |
| `imports.py` | `ImportService.preview(req:ImportManifest)->ImportPreview`：逐文件、增改删与冲突预览；`apply(req:ImportRequest,expected_preview_hash)->Job`：按已确认选择提交；`execute(job:Job)->ImportResult`：后台解析、索引与发布；`SyncPlanner.diff(previous,current,scope)->ChangeSet`、`resolve_conflict(req)->ChangeSet`：按第 3.3 节执行 |
| `sources.py` | `SourceService.register(req:RegisterSource)->Source`、`get(source_id)->Source`、`list(kb_id)->list[Source]`、`update(source_id,req)->Source`、`remove(source_id)->None`；`LocalSource.scan(root_id,selection)->SourceManifest`：完整性标记及相对路径；`UploadSource.begin(manifest)->UploadBatch`、`write(batch_id,relative_path,stream)->UploadPart`、`finish(batch_id)->SourceManifest`：流式上传、校验和完整清单；`DirectoryPoller.tick(source_id)->SyncResult`：调用同一 diff/apply，不另写同步逻辑 |
| `parsers/registry.py` | `ParserRegistry.register(kind,parser)->None`、`parse(blob:BlobRef,options:ParseOptions)->ParsedDocument`、`capabilities()->list[ParserCapability]`：分派解析器、明确格式/依赖支持情况 |
| `parsers/text.py` | `TextParser.parse(blob,options)->ParsedDocument`；`decode(data,encoding)->str`、`locate_blocks(text,kind)->list[ParsedBlock]`：编码诊断、MD 标题、TXT 原始行号 |
| `parsers/word.py` | `WordParser.parse(blob,options)->ParsedDocument`；`parse_docx(path)->ParsedDocument`、`convert_doc(path,workdir)->ConvertedDocument`、`locate_paragraphs_and_tables(document)->list[ParsedBlock]`：旧格式转换记录映射，不虚构原文页码 |
| `parsers/excel.py` | `ExcelParser.parse(blob,options)->ParsedDocument`；`read_xlsx(path)->WorkbookData`、`read_xls(path)->WorkbookData`、`table_blocks(workbook)->list[ParsedBlock]`：保留 sheet、表头和单元格范围，区分公式文本与缓存值，不执行宏 |
| `parsers/pdf.py` | `PDFParser.parse(blob,options)->ParsedDocument`；`extract_pages(path)->list[ParsedBlock]`、`needs_ocr(pages)->bool`：真实页号、文本层诊断；无有效文本时显式转 OCR 或报 `OCR_REQUIRED` |
| `parsers/ocr.py` | `OCRAdapter.extract(path,options)->list[ParsedBlock]`、`check_dependencies()->CapabilityStatus`：扫描页识别和坐标/页码映射；依赖不可用不返回空成功 |
| `chunking.py` | `Chunker.split(document:ParsedDocument,profile:ChunkProfile)->list[Chunk]`、`split_table(block,profile)->list[Chunk]`、`map_locator(chunk,source_blocks)->Locator`：按结构切分、表头继承、保留定位；长度由语料分析确定 |
| `indexing.py` | `IndexBuilder.build(change:ChangeSet,base:Optional[Snapshot])->StagedSnapshot`、`reuse_unchanged(change,base)->ReusePlan`、`validate(staged)->ValidationReport`：P2 先增量解析并构建关键词快照，P3 在存在已验证嵌入角色后再构建/复用向量索引；每阶段写出完整可读快照并验证清单、维度、来源与引用，失败不切换活动版本 |
| `versions.py` | `VersionService.list(kb_id)->list[Snapshot]`、`get(version_id)->Snapshot`、`publish(version_id,expected_active)->Snapshot`、`rollback(kb_id,target,expected_active)->Snapshot`、`diff(left,right)->VersionDiff`、`retain(policy)->RetentionReport`：状态、原子切换、保留和清理规则 |

解析库初步候选为 `python-docx/openpyxl/xlrd/pypdf` 和受控 LibreOffice/OCR 适配。P2 安装时核实与 Python 3.12、Windows 的兼容性并锁定版本。每次转换使用独立临时目录，脚本与输入分离，超时/大小受限；正文与引用内容经安全渲染后展示。

### 4.5 Infrastructure：技术适配

目录前缀：`Infrastructure/src/qa_infrastructure/`。

| 文件 | 方法签名与职责 |
| --- | --- |
| `sqlite.py` | `SQLiteStore.open(settings)->ConnectionPool`、`transaction()->AsyncContextManager[UnitOfWork]`、`close()->None`；`migrate(target)->MigrationResult` 为显式管理动作，模块导入不自动迁移 |
| `repositories.py` | `SQLiteKnowledgeRepository`、`SQLiteSourceRepository`、`SQLiteContentRepository`、`SQLiteSnapshotRepository`、`SQLiteConversationRepository`、`SQLiteJobRepository`、`SQLiteModelRepository`、`SQLiteModelCallRepository`、`SQLiteFeedbackRepository` 分别逐项实现第 4.2 节对应端口；使用参数化查询、事务、唯一约束/比较交换，不重写领域规则 |
| `migrations/001_initial.sql` | 表：库及路由描述、来源、修订、版本及成员、会话的选库/模型默认值与两组 revision、上下文分段、答案及实际范围成员、不可变 inference profile 修订、运行时发现、模型身份/验证、安装预览、回答/任务模型绑定、模型调用审计、事件、任务、反馈/问题；范围成员关联 `(answer_id,kb_id,version_id)`；在途模型下载对规范化目标设条件唯一约束；记录 schema 版本、幂等键、租约和检查点；不把多库版本或多角色模型绑定压进单值列 |
| `catalog.py` | `AuthorizedKnowledgeCatalog.list_authorized(access,query)->Page[KBDescriptor]`、`get_authorized(access,kb_ids)->list[KBDescriptor]`：实现 KnowledgeCatalog，只读取授权库的路由描述/已发布状态；`refresh_descriptor(kb_id,version_id)->None`：发布或元数据变化后刷新可追溯目录缓存，权限变化须使缓存失效 |
| `blobs.py` | `FileBlobStore.put(stream)->BlobRef`、`get(ref)->BinaryIO`、`verify(ref)->bool`、`delete_unreferenced(refs)->GCResult`：按内容寻址、流式读写、引用保护 |
| `snapshots.py` | `FileSnapshotStore.stage(manifest)->StagingHandle`、`seal(handle)->SnapshotFiles`、`open(version_id)->SnapshotHandle`、`load_chunks(version_id,ids)->list[Chunk]`、`load_revision(revision_id)->Revision`；`PublishedSnapshotReader.resolve(kb_id,version_id)->Snapshot`、`resolve_many(targets:list[KBTarget],access:AccessScope)->ResolvedScope`：同一读事务解析目标版本、校验所属库/授权/保留状态，组合快照仓储与文件存储，并代理同签名的 `load_chunks/load_revision`；先固化文件后由版本服务切换数据库指针，Windows 不覆盖仍打开的旧索引文件 |
| `indexes.py` | `ChineseTokenizer.tokenize(text)->list[str]`；`BM25Index.build(chunks,profile)->IndexRef`、`search(query,scope,k)->list[Hit]`；`DenseIndex.build(vectors,mapping)->IndexRef`、`search(vector,scope,k)->list[Hit]`；`EmbeddingCache.get_many(keys)->CachedVectors`、`put_many(items)->None`；缓存键包含模型/维度/处理配置 |
| `providers.py` | `ConfiguredEmbedder.embed(texts,profile,binding)->Vectors`、`ConfiguredGenerator.stream(req)->AsyncIterator[DraftFragment]`、`ConfiguredTokenCounter.count(req,binding)->TokenCount`、`ConfiguredSupportChecker.check(sentence,chunks,binding)->SupportDecision`、`ConfiguredReranker.rank(query,hits,binding)->list[Hit]`（同一文本评分模型用于路由探测和跨库合并）；`build_provider(settings)->ProviderBundle`：仅装配已配置实现，不联网探测；P1 为占位。新增 `ollama/discovery.py`：`OllamaDiscovery.discover(targets)->DiscoveryReport`；`ollama/runtime.py`：`OllamaRuntime.probe(target)->RuntimeStatus`、`list_models(target,query)->list[ModelRef]`、`inspect(ref)->ModelRef`、`embed(...)`、`stream(...)`、`cancel_call(...)`；`ollama/installer.py`：`preview(req)->InstallPreview`、`start(plan)->TransferHandle`、`follow(handle)->AsyncIterator[TransferState]`、`cancel(handle)->CancelResult`、`reconcile(plan,handle)->TransferState`、`resume(plan,state)->TransferHandle`；这些类逐项实现 Contracts 端口，P3 首先完成 Ollama。LM Studio/llama.cpp 仅在官方接口与实测能力矩阵确认具体操作后增加同类窄适配；不能承诺其不支持的安装/取消/恢复操作 |

初期不用通用 ORM 仓储生成器、插件发现系统或多套向量数据库驱动。不同客户端通过 API 共享上述实现，而不是直接读取 SQLite 或索引目录。

### 4.6 ServiceAPI：应用层

目录前缀：`ServiceAPI/src/qa_service/`。

| 文件 | 方法签名与职责 |
| --- | --- |
| `settings.py` | `Settings`：运行模式、监听地址、数据目录、来源根、模型配置、超时、允许嵌入站点，以及自动候选/选库数量上限、单库候选预算、检索并发、路由阈值和默认历史策略；模型运行时候选只来自服务端配置的本机标准位置与 allow-listed `RuntimeTarget`，客户端不得提交端点或本机路径；`load_settings()->Settings`：读取并校验配置，不输出密钥，选库限制和脱敏模型能力同时供 capabilities 发布 |
| `container.py` | `build_container(settings)->Container`、`close_container(container)->None`：唯一组合根，注入真实/占位端口；构建 scaffold 容器没有数据库、运行时探测、模型加载或联网副作用 |
| `app.py` | `create_app(settings:Optional[Settings])->FastAPI`、`lifespan(app)->AsyncContextManager`、`require_business_capability(feature)->None`：注册路由、生命周期、占位业务前置检查，SSE 建连前也检查；生命周期不自动探测部署器或下载模型 |
| `__main__.py` | `main()->None`：`qa-api` 入口，解析工程参数、启动应用；P1 绑定回环地址，不能当可用生产服务发布 |
| `security.py` | `authenticate(credentials)->Principal`、`authorize(principal,action,resource)->None`、`issue_widget_ticket(req,principal)->WidgetTicket`、`validate_widget_ticket(token)->Principal`：读取/管理权限分离、KB/会话范围、允许的 profile/策略与票据有效期；发现、安装和 profile 修改要求模型管理权限，P1 不实现认证业务，业务路由先返回 501 |
| `conversations.py` | `ConversationService.create(req,principal)->Session`、`get_selection(session_id,principal)->SessionSelection`、`update_selection(session_id,req:UpdateSessionSelection,principal)->Session`、`get_inference(session_id,principal)->SessionInference`、`update_inference(session_id,req:UpdateSessionInference,principal)->Session`、`history(session_id,principal)->list[Turn]`、`submit(session_id,req,key,principal)->AnswerHandle`、`ask(req:AskRequest,key,principal)->AskResponse`、`execute(answer_id)->Answer`、`get_answer(answer_id,principal)->Answer`、`cancel(answer_id,principal)->Answer`、`get_citation(answer_id,citation_id,principal)->CitationDetail`：同一事务捕获本轮选库、模型策略及两组 revision，执行前绑定候选版本与各角色模型；幂等、并发控制、调用 QA 核心和提交结果；`ask` 复用 submit + wait |
| `selection.py` | `SelectionService.catalog(principal,query:CatalogQuery)->Page[KBDescriptor]`：问答读权限的可选库目录；`prepare(request_selection:Optional[RetrievalSelection],session:Optional[Session],principal)->EffectiveSelection`：优先级、输入/权限和默认值；`resolve(question,prepared,history,binding:InferenceBinding)->SelectionResult`：调用 QAService.select；`preview(req:SelectionPreviewRequest,principal)->SelectionResult`：先捕获有效 inference 并绑定探测所需角色，再预览自动/显式选库，不创建回答；`validate_current_access(scope,principal)->None`：执行及引用前复验。纯检索与回答共用这套服务 |
| `models.py` | `ModelManagementService.capabilities(principal)->ModelCapabilities`、`discover(req:DiscoveryRequest,principal)->DiscoveryReport`、`list_runtimes(principal)->list[RuntimeStatus]`、`list_models(query,principal)->Page[ModelRef]`、`inspect_model(model_id,principal)->ModelRef`、`list_profiles(principal)->Page[ProfileSummary]`、`get_profile(profile_id,revision,principal)->InferenceProfile`、`put_profile(req:PutInferenceProfile,expected_revision,principal)->InferenceProfile`、`disable_profile(profile_id,expected_revision,principal)->InferenceProfile`、`preview_install(req:InstallRequest,principal)->InstallPreview`、`confirm_install(req:InstallConfirmation,key,principal)->Job`、`verify_model(req:VerifyModelRequest,key,principal)->Job`、`execute_install(job)->InstallResult`、`execute_verification(job)->ModelVerification`：只使用服务端 allow-list 目标，预览不下载，确认后才入队；完成下载先核验完整模型身份，再以独立任务验证角色；不接受任意 URL/路径，不因问答缺模型自动安装。会话默认 inference 的读取/更新由 ConversationService 负责，避免两个服务各写一套 revision 规则 |
| `jobs.py` | `JobService.enqueue(command,key)->Job`、`get(job_id)->Job`、`cancel(job_id)->Job`、`run_next(kind)->Optional[Job]`、`recover_expired()->RecoveryReport`：持久任务、租约、重启恢复；模型任务使用唯一目标键、检查点与运行时对账，取消未知保持待确认状态且不得杀共享部署器；导入重试幂等，已部分生成的答案不自动当新成功回答重放 |
| `worker.py` | `main()->None`、`run_worker(container,stop_signal)->None`、`dispatch(job)->JobResult`：显式启动后台执行循环，分派 import/model_install/model_verify 等类别；P1 仅保留入口/帮助，任务运行未实现 |
| `events.py` | `AnswerEventService.append(answer_id,event)->SSEEvent`、`subscribe(answer_id,after)->AsyncIterator[SSEEvent]`；`JobEventService.append(job_id,event)->SSEEvent`、`subscribe(job_id,after)->AsyncIterator[SSEEvent]`；`encode(event)->bytes`：答案与任务事件分别使用 answer_id/job_id，先持久化再发布、序号重放、心跳、终态，权限在订阅和重连时检查 |
| `feedback.py` | `FeedbackService.submit(answer_id,req,principal)->Feedback`、`record_unanswered(answer)->Issue`、`list_issues(query)->Page[Issue]`、`get_issue(issue_id)->Issue`、`resolve(issue_id,req)->Issue`、`retest(issue_id,req:RetestRequest)->AnswerHandle`：复测显式携带 selection/inference 并复用 ConversationService 的捕获、绑定和幂等规则；收集、人工处理、关联补库和复测，负反馈不自动变成可信知识 |
| `http_errors.py` | `exception_response(error,request_id)->JSONResponse`、`install_handlers(app)->None`：统一 HTTP 错误映射，区分 501、输入错误、冲突、权限、依赖失败 |

`JobService` 负责运行状态，`KBManagement.ImportService.execute` 负责导入步骤；`ConversationService.execute` 负责回答持久化，`QAService.answer` 负责问答本身。不会把一个职责在两个模块里重复实现。

### 4.7 HTTP 路由文件与处理函数

目录前缀：`ServiceAPI/src/qa_service/routes/`。每个 handler 接收对应请求 DTO 与注入服务/主体，返回对应响应 DTO；不写业务规则。以下同时是路由函数清单。

| 文件 | HTTP 路由 → handler → 服务方法 |
| --- | --- |
| `system.py` | `GET /healthz → health()`；`GET /readyz → readiness()`；`GET /v1/capabilities → capabilities()`；框架期明确 mode 和未实现能力 |
| `knowledge.py` | `POST/GET /v1/kbs → create_kb(CreateKB)/list_kbs(KBQuery)`；`GET/PATCH/DELETE /v1/kbs/{id} → get_kb(id)/update_kb(id,UpdateKB)/delete_kb(id)`；调用 KBService |
| `content.py` | `POST/GET /v1/kbs/{id}/documents → create_document(id,PutDocument)/list_documents(id,Query)`；`GET/PATCH/DELETE /v1/documents/{id} → get_document/update_document/delete_document`；`POST/GET /v1/kbs/{id}/qa-pairs → create_qa/list_qa`；`GET/PATCH/DELETE /v1/qa-pairs/{id} → get_qa/update_qa/delete_qa`；对应 ContentService |
| `imports.py` | `POST /v1/uploads → begin_upload(UploadManifest)`；`PUT /v1/uploads/{id}/files → upload_file(id,relative_path,body_stream)`；`POST /v1/uploads/{id}/complete → complete_upload(id)`；`POST /v1/kbs/{id}/imports/preview → preview_import(id,ImportManifest)`；`POST /v1/kbs/{id}/imports → import_documents(id,ImportRequest)`；`POST /v1/sources/{id}/sync → sync_source(id,SyncRequest)` |
| `sources.py` | `GET /v1/source-roots → list_roots()`；`POST /v1/source-roots/{id}/scan → scan_source(id,Selection)`；`POST/GET /v1/kbs/{id}/sources → create_source/list_sources`；`GET/PATCH/DELETE /v1/sources/{id} → get_source/update_source/delete_source` |
| `versions.py` | `GET /v1/kbs/{id}/versions → list_versions(id)`；`GET /v1/versions/{id} → get_version(id)`；`GET /v1/kbs/{id}/version-diff → diff_versions(id,left,right)`；`POST /v1/versions/{id}/publish → publish_version(id,PublishRequest)`；`POST /v1/kbs/{id}/rollback → rollback_version(id,RollbackRequest)` |
| `answers.py` | `POST /v1/search → search(SearchRequest)`；`POST /v1/ask → ask(AskRequest)`；`POST /v1/sessions → create_session(CreateSession)`；`GET /v1/sessions/{id}/history → history(id)`；`POST /v1/sessions/{id}/answers → submit_answer(id,SubmitAnswer)`；`GET /v1/answers/{id} → get_answer(id)`；`GET /v1/answers/{id}/events → answer_events(id,last_event_id)`；`POST /v1/answers/{id}/cancel → cancel_answer(id)`；`GET /v1/answers/{id}/citations/{citation_id} → get_citation(id,citation_id)` |
| `feedback.py` | `POST /v1/answers/{id}/feedback → submit_feedback(id,FeedbackInput)`；`GET /v1/issues → list_issues(IssueQuery)`；`GET/PATCH /v1/issues/{id} → get_issue/resolve_issue`；`POST /v1/issues/{id}/retest → retest_issue(id,RetestRequest)` |
| `selection.py` | `GET /v1/knowledge-catalog → list_retrievable_kbs(CatalogQuery)`：查询调用者可检索的库，无需管理权限；`POST /v1/knowledge-selection/preview → preview_selection(SelectionPreviewRequest)`：预览本题选库；`GET/PATCH /v1/sessions/{id}/selection → get_session_selection(id)/update_session_selection(id,UpdateSessionSelection)`：查看/切换同一会话默认范围 |
| `models.py` | `GET /v1/models/capabilities → model_capabilities()`；`POST /v1/models/discovery → discover_runtimes(DiscoveryRequest)`（仅选择服务端已配置 target ID，不接收 URL/路径）；`GET /v1/models/runtimes → list_runtimes()`；`GET /v1/models → list_models(ModelQuery)`；`GET /v1/models/{id} → get_model(id)`；`GET/POST /v1/inference-profiles → list_profiles()/create_profile(PutInferenceProfile)`；`GET/PUT /v1/inference-profiles/{id} → get_profile(id,revision)/update_profile(id,PutInferenceProfile)`；`POST /v1/inference-profiles/{id}/disable → disable_profile(id,expected_revision)`；`GET/PATCH /v1/sessions/{id}/inference → get_session_inference(id)/update_session_inference(id,UpdateSessionInference)`；`POST /v1/model-installs/preview → preview_install(InstallRequest)`；`POST /v1/model-installs → confirm_install(InstallConfirmation)`；`POST /v1/models/{id}/verifications → verify_model(id,VerifyModelRequest)`。安装与验证返回通用 Job；profile 修改为追加不可变修订，不覆盖旧绑定 |
| `operations.py` | `GET /v1/jobs/{id} → get_job(id)`；`GET /v1/jobs/{id}/events → job_events(id,last_event_id)`：导入、安装、验证共用可重放任务 SSE；`POST /v1/jobs/{id}/cancel → cancel_job(id)`；`POST /v1/widget/tickets → issue_ticket(WidgetTicketRequest)` |

路径型 ID 的归属关系必须校验；知道 `answer_id` 或 `citation_id` 不等于拥有读取权限。文档修改采用 expected revision / `If-Match`，版本切换采用 expected active，错误为 409，不静默覆盖。

### 4.8 SDK 与 CLI

| 文件 | 函数/方法与职责 |
| --- | --- |
| `Clients/python/src/qa_client/client.py` | `Client(base_url,credential,timeout)`；知识与问答方法沿用现有清单并增加 `get_session_inference(session_id)->SessionInference`、`set_session_inference(session_id,inference,expected_revision)->Session`；模型管理方法：`model_capabilities()->ModelCapabilities`、`discover_runtimes(target_ids)->DiscoveryReport`、`list_runtimes()->list[RuntimeStatus]`、`list_models(query)->Page[ModelRef]`、`list_profiles()->Page[ProfileSummary]`、`get_profile(id,revision)->InferenceProfile`、`put_profile(req,expected_revision)->InferenceProfile`、`disable_profile(id,expected_revision)->InferenceProfile`、`preview_install(req)->InstallPreview`、`confirm_install(confirmation,key)->Job`、`verify_model(model_id,req,key)->Job`、`job(id)->Job`、`job_events(id,last_id)->Iterator[SSEEvent]`、`cancel_job(id)->Job`、`close()->None`；search/ask/submit 接受 selection 与 inference，安装只能消费服务端预览 ID/摘要，SDK 不提供绕过确认的拉取方法 |
| `Clients/python/src/qa_client/sse.py` | `decode_sse(byte_chunks)->Iterator[SSEEvent]`、`resume_cursor(events)->Optional[int]`、`subscribe_answer(...)`、`subscribe_job(...)`：正确处理 UTF-8 跨块、多行 data、心跳、重复序号和终态；按事件联合区分 answer_id/job_id，不以 TCP 块边界当事件边界 |
| `Clients/python/src/qa_client/files.py` | `collect_upload(root,selection)->UploadManifest`、`upload_directory(client,root,selection)->UploadBatch`：客户端本地文件清单与字节传输；服务端重新验证，客户端不决定发布/删除 |
| `Clients/cli/src/qa_cli/main.py` | 管理/问答命令沿用现有清单并增加 `get_session_inference`、`set_session_inference`、`model_capabilities`、`discover_models(target_ids)`、`list_runtimes`、`list_models`、`list_profiles`、`show_profile`、`put_profile`、`disable_profile`、`preview_model_install(runtime_id,model_ref)`、`confirm_model_install(preview_id,preview_hash)`、`verify_model(model_id,roles)`、`job_events(job_id)`、`cancel_job(job_id)`；`search/ask` 可显式传 `--inference-profile` 与 `--inference-policy`。安装必须先生成预览再由用户以预览 ID/摘要确认，CLI 不接受任意 provider URL，也不在非交互模式隐式确认；均调用 SDK/HTTP，提供 JSON 输出与稳定退出码 |
| `Clients/typescript/src/client.ts` | `createClient(options):Client`；知识与问答方法沿用现有清单并增加 `getSessionInference`、`setSessionInference`；模型管理方法：`modelCapabilities`、`discoverRuntimes`、`listRuntimes`、`listModels`、`listProfiles`、`getProfile`、`putProfile`、`disableProfile`、`previewInstall`、`confirmInstall`、`verifyModel`、`getJob`、`cancelJob`；共享传输、selection/inference 和错误处理，凭证获取器由宿主注入，前端不能传任意端点或密钥 |
| `Clients/typescript/src/sse.ts` | `subscribeAnswer(id,after,onEvent,signal):Promise<void>`、`subscribeJob(id,after,onEvent,signal):Promise<void>`、`parseSSE(chunks):AsyncGenerator<SSEEvent>`：fetch 流式请求，支持 Authorization、取消和重连；答案/任务各用稳定 ID，避免把 bearer token 塞进 URL |
| `Clients/typescript/src/types.ts` | 从 OpenAPI/事件 schema 导出的请求、响应和事件类型，禁止与后端手写不同版本 |
| `Clients/typescript/src/index.ts` | 显式导出公共 SDK，不导出页面内部组件 |

CLI 检索/问答参数统一提供可重复 `--kb`（单项/多项显式模式）、互斥的 `--auto`，以及自动模式的 `--candidate-kb`、`--max-kbs`；版本通过每库映射指定，不能拿一个 `--version` 模糊作用到所有库。CLI 的本地目录入口既支持上传客户端目录，也支持通过配置使用服务端授权 root；两者在帮助信息中明确区分。P1 命令帮助与参数检查可运行，真正命令调用报告未实现并以非零退出码退出。

### 4.9 WebUI：管理端

目录前缀：`WebUI/`。采用轻量 TypeScript 页面，不要求搭建企业级管理框架。

| 文件 | 函数与职责 |
| --- | --- |
| `package.json`、`tsconfig.json`、`vite.config.ts`、`index.html` | build/dev/typecheck 及入口；构建配置无业务方法 |
| `src/main.ts` | `mount(root):void`、`navigate(route):void`、`dispose():void`：应用入口、页面切换和清理；导航显式包含“模型”页，按权限隐藏管理动作但不依赖前端作授权 |
| `src/pages/knowledge.ts` | `renderKnowledgePage(state):HTMLElement`、`createKB(form):Promise<void>`、`updateKB(id,form):Promise<void>`、`deleteKB(id):Promise<void>`、`saveRoutingProfile(id,description,tags,exampleQuestions):Promise<void>`：库级管理及自动选库描述维护 |
| `src/pages/models.ts` | `renderModelsPage(state):HTMLElement`、`loadCapabilities():Promise<void>`、`discoverRuntimes(targetIds):Promise<void>`、`loadModels(query):Promise<void>`、`loadProfiles():Promise<void>`、`editProfile(form):Promise<void>`、`previewInstall(runtimeId,modelRef):Promise<void>`、`confirmInstall(previewId,previewHash):Promise<void>`、`verifyModel(modelId,roles):Promise<void>`、`watchModelJob(jobId,signal):Promise<void>`、`cancelModelJob(jobId):Promise<void>`：展示后端主机标识/观测时间，严格区分 installed/running/downloaded/loaded/verified_roles/unknown；只列服务端配置的运行时，预览显示大小、摘要、许可和未知项，显式确认后才启动任务；页面不扫描浏览器主机、不接收任意端点、不保存密钥，也不把已下载误标为已验证 |
| `src/pages/qa.ts` | `renderQAPage(state):HTMLElement`、`mountQAWidget(container,options):WidgetHandle`：管理端试问页复用独立插件；展示可选库、单/多/自动模式、推理 profile/policy 与每轮实际范围/模型绑定摘要，不复制检索/选库或模型策略算法 |
| `src/pages/imports.ts` | `renderImportPage(state)`、`selectDirectory(files):UploadSelection`、`toggleFile(path,selected):void`、`previewImport():Promise<void>`、`submitImport():Promise<void>`、`syncSource(id):Promise<void>`：目录/逐文件选择、失败清单和任务进度 |
| `src/pages/content.ts` | `renderContentPage(state)`、`loadDocument(id)`、`saveDocument(form)`、`deleteDocument(id)`、`saveQAPair(form)`、`deleteQAPair(id)`：文档、原件替换、规范化文本及问答对维护 |
| `src/pages/versions.ts` | `renderVersionPage(state)`、`loadDiff(left,right)`、`publishVersion(id)`、`rollbackVersion(id)`：版本差异、状态及活动版本 |
| `src/pages/issues.ts` | `renderIssuesPage(state)`、`filterIssues(query)`、`openIssue(id)`、`linkRevision(issueId,revisionId)`、`retestIssue(id,selection:RetrievalSelection)`、`resolveIssue(id)`：反馈补库闭环 |
| `src/components/jobs.ts` | `renderJob(job):HTMLElement`、`watchJob(id,signal):Promise<void>`：共享任务进度、逐文件失败与重试入口 |
| `src/state.ts` | `createStore(initial)`、`dispatch(action)`、`subscribe(listener)`：页面状态和请求取消；不保存模型密钥 |
| `src/styles.css` | 管理端布局、状态和可访问性样式 |

P1 各页面只有真实可点击的布局/导航和“尚未实现”状态；不放伪造知识库数据或成功提示。错误提示区统一使用 SDK 错误模型。

### 4.10 WebWidget：独立嵌入插件

目录前缀：`WebWidget/`。

| 文件 | 函数与职责 |
| --- | --- |
| `package.json`、`tsconfig.json`、`vite.config.ts` | 输出 ESM 与普通 script 可加载入口；配置独立版本号和资源路径 |
| `src/index.ts` | `mount(options:WidgetOptions):WidgetHandle`：公开入口；options 含 `initialSelection`、凭证获取器及允许的界面行为，返回 `open/close/setSelection/getSelection/destroy`；每个实例独立状态，权限范围由票据决定，不信任前端配置 |
| `src/loader.ts` | `autoMount(script:HTMLScriptElement):WidgetHandle`：读取非敏感 data 属性，避免重复挂载；暴露 `window.QAWidget` |
| `src/view.ts` | `createLauncher():HTMLElement`、`createPanel():HTMLElement`、`renderMessage(message):HTMLElement`、`renderStatus(state):void`、`showCitation(detail):void`：悬浮图标、弹窗、消息、引用详情；采用 Shadow DOM 隔离样式 |
| `src/selector.ts` | `createKnowledgeSelector(catalog,selection):HTMLElement`、`setMode(mode):void`、`toggleKnowledge(kbId,selected):void`、`readSelection():RetrievalSelection`、`renderResolvedScope(result):void`：单库/多库/自动模式、自动候选范围、每轮实际检索库、版本和无匹配提示；提供运行中“下轮生效”的状态 |
| `src/controller.ts` | `WidgetController.open()`、`close()`、`loadKnowledgeCatalog():Promise<void>`、`setSelection(selection,historyPolicy):Promise<void>`、`getSelection():RetrievalSelection`、`send(text):Promise<void>`、`cancel():Promise<void>`、`newSession():Promise<void>`、`loadCitation(id):Promise<void>`、`feedback(answerId,rating,comment):Promise<void>`、`destroy()`：选择器调用会话设置 API，消息发送捕获选择 revision，维护在途/下轮两套状态；其余调用共享 SDK，管理焦点、订阅和事件解绑 |
| `src/state.ts` | `createState(options):WidgetState`、`reduce(state,event):WidgetState`、`canSubmit(state):boolean`：按 seq 去重，处理完整/拒答/失败/取消，防止并发重复提交 |
| `src/render.ts` | `renderSafeText(text):DocumentFragment`、`renderCitationLink(citation):HTMLElement`：安全呈现文本和受控链接，不直接插入模型/文档 HTML |
| `src/styles.css` | 桌面/手机尺寸、键盘焦点、层级与减少动画偏好；不污染宿主页面 |
| `README.md` | 一段 script 接入方法、令牌获取回调、允许站点、事件、销毁、多实例和引用展示说明 |

插件使用短期且限定知识库允许集合、会话和用途的票据；范围切换不能扩大票据权限。公开知识库可以显式配置匿名问答并限额；私有知识库由宿主后端完成身份检查后换取票据。Origin 白名单/CORS 只是辅助限制，不替代身份验证；插件代码不携带管理 key。P4 测试两个独立站点和单库/多库/自动模式切换，记录 HTTPS、CSP 和宿主层级等正常部署条件。

### 4.11 程序调用示例、评测和工程脚本

| 文件 | 函数/内容 |
| --- | --- |
| `examples/python_agent.py` | `search_knowledge(question,selection:RetrievalSelection,inference:InferenceSelection)->SearchResult`、`ask_knowledge(question,selection:RetrievalSelection,inference:InferenceSelection,session_id)->Answer`、`main()`：示范单库、多库组合、限制候选的自动选库、local_only/显式配置 profile、同会话分别切换知识库和模型；普通 agent 可包装成工具调用，不依赖特定框架 |
| `examples/curl.md` | capabilities、模型发现/profile/安装预览与确认、search、ask、会话 selection/inference、答案/任务 SSE、引用、反馈的完整 HTTP 示例；使用环境变量占位凭据，不示范客户端提交 provider URL 或秘密 |
| `examples/widget-site-a/index.html`、`examples/widget-site-b/index.html` | 两个不同样式的普通宿主网页，使用同一发布插件演示 CSS 和会话隔离 |
| `Evaluation/dataset.py` | `load_cases(path)->list[Case]`、`validate_labels(cases,manifest)->ValidationReport`、`split_by_group(cases)->DatasetSplit`：校验来源/引用标注，按文档来源与会话组划分调参和保留集 |
| `Evaluation/analyze_corpus.py` | `analyze_corpus(manifest)->CorpusProfile`、`compare_chunking(profiles,documents)->ChunkingReport`：以真实正文统计格式、结构、长度和边界样例；P1 不产生虚构结果 |
| `Evaluation/evaluate.py` | `run_selection(cases,config)->SelectionRun`、`run_retrieval(cases,config)->RetrievalRun`、`run_answers(cases,config)->AnswerRun`、`run_multiturn(cases,config)->ConversationRun`：调用实际 API，记录候选范围、实际多库快照与配置，测选库准确性、跨库证据覆盖、混合检索及重排 |
| `Evaluation/metrics.py` | `selection_precision_recall(predicted_kbs,required_kbs)`、`routing_abstention_accuracy(labels,decisions)`、`precision_at_k(ids,relevant,k)`、`recall_at_k(ids,relevant,k)`、`mrr_at_k(runs,k)`、`ndcg_at_k(runs,k)`、`citation_metrics(labels,answers)`、`refusal_metrics(labels,answers)`、`latency_quantiles(events)`：公开且一致的计算口径，区分选库失败与库内召回失败 |
| `Evaluation/report.py` | `write_report(run,metrics,environment,outdir)->ReportPaths`：JSON 与 Markdown 报告，逐题失败证据、版本和环境；当前不生成成绩 |
| `Evaluation/fixtures/manifest.json`、`cases.jsonl`、`qrels.json` | 后续固定语料清单、问题/参考回答/拒答标签、相关证据标注；P1 仅 schema/空模板，不当成已评测数据集 |
| `scripts/export_contracts.py` | `export_openapi(app,path)`、`export_events(path)`、`check_contracts()->CheckResult`：从 scaffold 应用/模型导出契约，无数据库或模型调用 |
| `scripts/check_environment.py` | `inspect_runtime()->EnvironmentReport`、`inspect_optional_tools()->CapabilityReport`、`inspect_model_runtime_candidates(config)->DiscoveryHintReport`、`main()`：仅报告 Python/Go/Node、转换/OCR，以及当前服务运行账户在 PATH/标准位置/服务端 allow-list 中可见的部署器候选；不扫描浏览器电脑或局域网，不启动服务、不加载模型、不下载权重，真实协议探测仍走受权 API 动作 |
| `scripts/check_distribution.py` | `scan_artifacts(paths)->DistributionReport`、`assert_no_model_weights(report)->None`：检查 Git 追踪文件、wheel、前端产物、容器上下文和可选 EXE 分发目录，不含 GGUF/safetensors/部署器缓存及其他模型层；仅以扩展名、路径、体积和已知清单作防误打包检查，不能代替许可证审查 |
| `scripts/dev.py` | `main()`、`start(component,settings)->ProcessHandle`、`stop(handles)->None`：分别启动 API、worker、管理端、示例宿主，退出清理自己启动的进程 |
| `Integrations/agent-insight/README.md` | 标记延期；记录后续所需仓库 URL、版本、挂载位置、配置和验证步骤；P1 不添加猜测性的宿主修改 |

HTTP/OpenAPI + Python SDK 已满足 agent/程序便捷调用的基本要求，本计划不额外要求 MCP 才能使用系统。未来若确有客户端只支持 MCP，可在 `Integrations` 增加薄适配，仍调用同一 SDK。

### 4.12 可选 Go 原生桌面端（P5）

不作为课程网页插件的替代物，也不列入 P1 默认创建/安装内容。

| 文件 | Go 函数/方法 |
| --- | --- |
| `Clients/desktop-go/go.mod` | 独立 Go module，锁定 Fyne 等依赖 |
| `Clients/desktop-go/main.go` | `main()`：加载配置、创建 Go GUI、退出时清理请求 |
| `Clients/desktop-go/config.go` | `LoadConfig(path string) (Config,error)`：后端地址/界面配置，密钥不写入界面资源 |
| `Clients/desktop-go/client.go` | `NewClient(cfg Config) *Client`、`ListKnowledge(ctx,query) (Catalog,error)`、`SetSelection(ctx,sessionID,selection,expectedRevision) (Session,error)`、`Search(ctx,req) (SearchResult,error)`、`Ask(ctx,req) (Answer,error)`、`Submit(ctx,req) (AnswerHandle,error)`、`Stream(ctx,id,emit) error`、`Citation(ctx,answerID,citationID) (CitationDetail,error)`、`Feedback(ctx,id,input) error`：调用同一 API，支持三种选库模式 |
| `Clients/desktop-go/ui.go` | `NewWindow(client *Client) fyne.Window`、`BuildKnowledgeSelector(client) fyne.CanvasObject`、`BuildChatPanel(client) fyne.CanvasObject`、`BuildKnowledgePanel(client) fyne.CanvasObject`、`ShowCitation(window,detail)`、`ApplyEvent(event)`：Go 原生控件支持单选/多选/自动、当前轮与下轮范围展示，UI 更新回到 UI 线程 |
| `Clients/desktop-go/README.md` | 构建工具链、系统依赖、远程/本地服务连接、分发目录和 EXE 测试步骤 |

若要求双击 EXE 同时启动本地服务，再独立增加 `backend_process.go` 的 `StartBackend(ctx,cfg)`、`WaitReady(ctx,endpoint)`、`StopBackend()`，并明确 Python runtime、文档转换器和模型资源如何分发。不得把 Go 客户端 EXE 描述为整个系统已经单文件离线化。Fyne 当前构建前置条件在 P5 以官方文档与本机编译验证为准；本轮外网文档未能访问，不声称已确认可打包。

## 5. 面向 AI agent / 普通程序的 API 契约

### 5.1 单库、多库、自动选库的统一调用

普通调用方使用同一个 `/v1/ask`；`selection` 同样适用于 `/v1/search` 和 `/v1/sessions/{id}/answers`。

```http
POST /v1/ask
Authorization: Bearer <scoped-token>
Idempotency-Key: <unique-key>
Content-Type: application/json

{"question":"如何修改配置？","selection":{"mode":"explicit","targets":[{"kb_id":"kb_product"}]}}
```

多库组合（每个库也可独立指定版本）：

```json
{
  "question": "结合产品说明和运维规范，说明升级步骤。",
  "selection": {
    "mode": "explicit",
    "targets": [
      {"kb_id": "kb_product", "version_id": "v_product_3"},
      {"kb_id": "kb_ops"}
    ]
  }
}
```

自动选库（也可省略 candidate_kb_ids，在当前授权目录内选）：

```json
{
  "question": "升级失败如何回滚？",
  "selection": {
    "mode": "auto",
    "candidate_kb_ids": ["kb_product", "kb_ops", "kb_faq"],
    "max_kbs": 2
  }
}
```

同一会话临时切库：在本次提问中同时传 `session_id` 与 `selection`，只覆盖这一轮。要持久修改下一轮起的默认范围，调用：

```http
PATCH /v1/sessions/session_123/selection
Content-Type: application/json

{"selection":{"mode":"explicit","targets":[{"kb_id":"kb_ops"}]},"expected_scope_revision":2,"history_policy":"reset_on_scope_change"}
```

没有 `session_id` 时创建会话：有 selection 则把它作为初始默认值，否则默认 auto；已有会话的请求未传 selection 就使用会话默认值。响应始终有 `session_id/answer_id`，已执行后包含 `requested_selection`、`resolved_scope:{scope_id,targets:[{kb_id,version_id}]}`、`used_kb_ids` 和选库状态/简短理由；未解析的 pending 响应使用 `resolved_scope:null`，不能编造版本。引用逐项携带自身的 kb_id/version_id。单库也使用同一列表结构，避免客户端专门分支处理。

声明的等待时限内结束返回 200 和结构化 `Answer`；仍在处理则返回 202、`AnswerHandle`、查询地址及重试提示。SDK 隐藏有界轮询，调用方始终拿到可继续查询的 answer_id。无匹配/歧义在问答中映射为带原因的 refused 和澄清提示，属于业务终态；纯检索返回 SelectionResult 和空 hits，不伪装为模型故障。

纯检索 `/v1/search` 无需生成模型，默认自动选库也不依赖生成模型。`GET /v1/knowledge-catalog` 可发现当前可用库；`POST /v1/knowledge-selection/preview` 可让 agent 单独预览自动选择，再决定使用哪些库。预览不修改会话、不保证之后的活动版本不变；需要精确重用时将返回的各库版本作为 explicit.targets 传入，服务端重新鉴权。需要完全控制流式时创建 session、提交 answer，再订阅 events。

### 5.2 统一错误、权限与幂等

- 错误形状：`{error:{code,message,details},request_id}`。稳定映射：400/422 输入、401 未认证、403 无权限、404 不存在、409 冲突、410 历史资源或事件已清理、429 限流、501 未实现、503 必要依赖不可用。
- 幂等键绑定主体、操作及原始规范化请求摘要（包括 selection、inference、会话 ID 与相应的预期 revision）；相同键和不同内容返回 409。先查幂等记录再创建会话或读取最新默认值；同键重试返回第一次捕获的选库/模型策略及已绑定结果，即使会话默认值、模型 profile 修订或库的活动版本已变化，也不重新选库、换模型或生成。模型安装确认同样以 preview ID、preview hash、目标身份和主体绑定幂等键。
- 每个会话同时只接受一个运行中的回答；会话记录与运行状态由数据库约束/事务保护，不能只用单进程内存锁。切换下一轮的 selection 或 inference 不受此生成锁阻塞，分别通过 scope_revision / inference_revision 并发检查，已接受答案不受影响。
- 源目录、上传、检索过滤、会话、引用、反馈全部检查主体与资源范围。供 agent 使用的读令牌不默认具有知识库管理权限。
- 管理上传限制文件数量/大小、路径规范化和授权根范围；转换器/模型异常不将本机路径、凭据或堆栈直接返回网页。

### 5.3 SSE

提交回答返回 202；`GET /v1/answers/{id}/events` 为 `text/event-stream`。所有答案事件有 `schema_version, answer_id, session_id, scope_revision, inference_revision, binding_id, scope_id, seq, timestamp`；模型绑定前 binding_id 为 null，选库完成前 scope_id 为 null，`id` 使用可重放序号。完整的模型绑定摘要放在 inference.bound/最终 Answer，库/版本映射放在 selection.resolved/最终 Answer；各引用携带自身的 kb_id/version_id，不再使用会话级单值 version_id。

事件顺序为：

```text
answer.accepted
inference.bound
selection.resolved
retrieval.completed
citation.ready / answer.delta（可以多次）
answer.completed | answer.refused | answer.failed | answer.cancelled
```

`inference.bound` 在第一次模型调用前给出不可变 binding ID、profile 修订、policy 与各角色的脱敏身份/执行位置摘要；纯关键词且无需模型的操作仍生成仅含确定性角色或空模型角色的绑定记录。`selection.resolved` 给出选库状态、实际 targets 和简短理由。无匹配/需要澄清时不进入 retrieval.completed，直接 refused；绑定或选库前故障/取消可从 accepted 或 inference.bound 进入对应终态。已绑定 inference/scope 的事件保持一致，设置下轮 inference/selection 不改动本轮事件或重放内容。

- `answer.delta` 包含 `sentence_id,text,citation_ids`；它引用的 citation 先可读取，再发送该 delta。
- 四种终态只能出现一种。最终状态和已完成历史持久化之后才发 completed。失败/取消只作为诊断记录，不进入正常回答上下文；正常拒答可以进入历史，但没有事实证据权重。
- 服务端持久事件先写再发，支持 `Last-Event-ID`；客户端按 seq 去重。重放窗口过期返回 410，客户端查询答案状态；不能自动再生成。
- 连接断开与取消是不同事件。断线可以重连；取消通过显式接口，停止上游生成并原子确认终态。完成与取消竞争由单次状态转换决定。
- 进程重启后，过期的生成租约标记中断；若无法安全恢复上游生成，保留部分结果并 failed，不拼接一段新的生成冒作续传。
- 心跳只维持连接，不当作答案进度。流内错误使用结构化终态；建立 HTTP 流之前发生的认证/参数/未实现错误仍返回普通 HTTP 错误。
- JSON 模式与 SSE 模式引用同一个 Answer；最终文本、引用与状态必须一致。

### 5.4 模型发现、配置、安装与推理选择

模型管理 API 只操作 ServiceAPI 所在主机且由管理员预先配置/allow-list 的运行时候选。`POST /v1/models/discovery` 的请求仅含 `target_ids` 与检测选项，不接受 URL、端口、可执行路径、模型目录、代理或凭据；默认 discovery 只做只读探测/枚举，不启动运行时、不加载模型、不下载权重。`GET /v1/models/capabilities` 返回本服务支持的运行时类型、已验证版本/build 范围、每类可用/未知操作、安装确认要求和 `mode=scaffold|operational`，不返回密钥或不必要的本机绝对路径。普通问答调用者只可读取获授权的 `ProfileSummary`；运行时发现、profile 修改、模型安装和验证要求模型管理权限。

模型清单分别返回 `installed/running/downloaded/loaded/verified_roles`、`observed_at`、身份/摘要状态及脱敏诊断。`GET /v1/models` 不把可变展示标签当不可变身份；`GET /v1/models/{id}` 返回该次发现记录与可用角色验证。`POST/PUT /v1/inference-profiles` 追加不可变 profile 修订，逐角色引用经过验证的 `ModelIdentity` 或明确的确定性本地算法；更新需要 `expected_revision`。删除/禁用 profile 不能破坏历史答案和快照绑定，已被默认值引用时必须先迁移或返回 409。

安装分两步且无旁路：

```text
POST /v1/model-installs/preview       -> InstallPreview（不下载）
POST /v1/model-installs               -> Job（必须带 preview_id、preview_hash、显式确认与 Idempotency-Key）
GET  /v1/jobs/{id}                    -> 当前 Job/InstallJobStatus
GET  /v1/jobs/{id}/events             -> 可重放 JobEvent SSE
POST /v1/jobs/{id}/cancel             -> cancel_requested/已确认终态/待对账状态
POST /v1/models/{id}/verifications    -> 独立 model_verify Job
```

确认时重新读取预览、校验主体、有效期、运行时目标、模型标识/已知摘要和剩余磁盘观测；发生变化返回冲突并要求新预览。完成拉取后由服务端枚举/检查实际完整模型身份，身份不符或未知时不得自动绑定角色；角色验证另行执行最小生成、嵌入或结构化输出测试并保存运行时版本/模型身份。取消不会杀共享运行时或删除共享层；上游取消不可确认时返回 `cancel_requested`/`outcome_unknown`，重启后通过 reconcile 对账。任务事件使用 `job_id,seq,timestamp,progress,bytes_downloaded,total_bytes?,phase,diagnostic`；总大小未知时不伪造百分比。

问答请求的 `inference:{profile_id,policy}` 与 `selection` 并列；缺省优先级为请求 → 会话默认 → 服务默认。`PATCH /v1/sessions/{id}/inference` 只影响以后接受的轮次，使用 `expected_inference_revision`。`policy=local_only` 必须覆盖入库嵌入、查询嵌入、自动选库探测、重排、改写、生成和支持校验；任一必需角色不满足时返回结构化 503/策略错误，绝不隐式使用外接模型。外接模型仅可引用管理员预配置 profile 与后端凭据引用，客户端不能提交任意 endpoint。响应和任务记录 `effective_inference`、绑定 ID、角色/模型身份摘要、执行位置和实际用量；不暴露秘密。

P1 中以上 schema、路由和静态 scaffold capabilities 均可生成，但 discovery/profile/install/verification 和会话 inference 的有效业务请求统一返回 501；不得探测本机、创建任务、写数据库、下载或调用模型。

## 6. P1 框架交付的精确定义

P1 不是一个混合实现批次，而是 Contract Gate、两个平行后端流和一个前端 Part。**P1-A1 与 P1-A2 同时开始、互不统属；P1-B 不补写后端逻辑。** 共享 TypeScript SDK 的契约/传输层归 A1，实际浏览器页面、组件、状态、样式与交互归 B。

### P1 Contract Gate：冻结跨组契约

1. 只处理 `Contracts/`、错误码、OpenAPI、SSE schema、跨组 fixtures 和 Protocol；给所有共享对象增加 `schema_version` 或明确的兼容规则。
2. 将后端方法按 A1/A2 的独占文件清单登记；同名职责只允许一个 owner。冻结后不再在 P1 中破坏性修改契约。
3. 输出 contract tests，证明 A1 的占位适配器与 A2 的核心调用方可以在没有彼此实现的情况下分别运行。

### P1-A1：平台与确定性工程框架（D1–D2）

1. 建立 Python workspace、A1 独占包/文件、FastAPI 应用工厂、设置、依赖注入、普通路由注册、异常映射、schema 导出与工程参数校验。
2. 建立 SQLite/文件存储/仓储/任务/解析等端口的占位实现，Python SDK、CLI 和共享 TypeScript HTTP/SSE 传输层；不创建 WebUI/WebWidget 页面。
3. `GET /healthz` 返回 200 且明确 `mode=scaffold`，`/readyz` 返回 503；CRUD、导入、任务和管理路由的有效业务请求为 501，参数错误为 422。
4. 启动、导入包、生成 schema 和 CLI 帮助不得创建数据库/文档/任务或访问网络。
5. 独立验收 `test_packages.py`、A1 路由/CLI/仓储占位测试和契约 provider tests；不等待 A2 代码即可完成。

### P1-A2：核心语义与一致性框架（D3–D4）

1. 建立 `Q&A_Assistant` 核心、选库/联邦检索、上下文、证据、生成、模型角色绑定、Ollama/索引端口和问答事件状态机的类型化占位。
2. A2 只依赖 Contract Gate 的 Protocol/DTO 和测试替身；不得导入 A1 的 SQLite、FastAPI handler 或具体仓储实现。
3. 自动选库、跨库检索、模型发现/安装、真实推理和证据校验均抛 `FeatureNotImplemented`，不得返回假命中、假模型、假引用或假流式事件。
4. 独立验收选库/模型/回答的 consumer contract tests、状态机 schema 测试和无 provider 调用测试；使用内存 fake，不等待 A1 数据库或 API 完成。

### P1-B：前端布局与浏览器端占位

1. 建立 `WebUI/` 与 `WebWidget/` 的构建配置、入口、导航、页面/组件骨架、状态容器与样式；使用 Contract Gate 冻结、由 P1-A1 导出的 OpenAPI/共享 TypeScript SDK，以及 P1-A2 提供的事件语义 fixtures，不在前端重复定义业务规则。
2. WebUI 提供知识库、导入、内容、版本、问题反馈、试问和模型页的可点击布局；WebWidget 提供悬浮入口、展开/收起/销毁、单库/多库/自动选库控件和 inference 占位控件。
3. 所有页面明确显示“尚未实现”；模型页只显示字段说明和 scaffold 状态，不扫描浏览器主机、不读取真实运行时、不伪造模型、不保存密钥，也不提供看似成功的安装操作。
4. 前端只允许调用 Contract Gate 规定、由 A1 暴露并由 A2 语义 fixtures 覆盖的 501 占位接口；不得导入任一后端内部包，也不得通过 mock 数据向默认构建展示成功、任务进度、知识库、答案或模型状态。测试夹具只能用于测试。
5. P1-B 验收使用 `tests/frontend/scaffold.spec.ts`、TypeScript typecheck/build 和静态无副作用检查；验证页面导航、模型页、Widget 生命周期及未实现状态。

### P1-A1、P1-A2 与 P1-B 完成后停止

A1、A2 各自通过独立测试，且集成层仅通过冻结契约连接后，才允许把 P1 后端标为完成；任一组不得以等待另一组为理由接管其文件。P1-B 只消费生成契约和 501 占位接口，不补做解析器、增量算法、向量构建、真实问答、数据库 CRUD、模型发现或下载。交付报告分列 Contract Gate、P1-A1、P1-A2、P1-B 的结果与跳过项；四项均完成后停止。

## 7. 测试文件与测试方法

表中是计划的具名测试。`tests/contracts/` 由 Contract Gate 维护，只检查 schema、Protocol、provider/consumer fixtures 与兼容性；A1 维护 scaffold、API、SDK/CLI、存储、解析、任务和工程集成测试；A2 维护检索、选库、模型适配消费侧、证据、回答、流式和 Evaluation 测试；B 维护 TypeScript/WebUI/WebWidget/浏览器 E2E。A1/A2 的默认测试命令都必须使用各自 fake 独立运行，不把另一组服务启动作为前置条件；只有阶段末的 `tests/integration/cross_stream/` 验证双方按冻结契约组合。

| 文件 | 测试方法及覆盖点 |
| --- | --- |
| `tests/contracts/test_schemas.py`、`test_protocols.py`、`test_compatibility.py` | Contract Gate 独占：验证 DTO 判别联合、错误码、OpenAPI/SSE schema、Protocol 签名、fixture 版本和向后兼容；不导入 A1/A2 具体实现 |
| `tests/contracts/providers/`、`tests/contracts/consumers/` | A1/A2 分别运行 provider/consumer contract tests；同一冻结 fixture 可由任一组独立消费，失败只按契约归属，不按组织层级裁决 |
| `tests/integration/cross_stream/` | 每阶段末唯一跨流测试：用 A1 真实适配器接 A2 真实核心，验证契约装配、事务边界和事件顺序；不得在此目录承载任一组本应独立完成的业务测试 |
| `tests/scaffold/test_packages.py` | `test_import_has_no_side_effects`：临时 HOME/数据目录且禁止网络，导入和工厂不写业务文件；`test_dependency_boundaries`：核心不依赖传输/存储/页面；`test_required_public_signatures`：公开契约能导入 |
| `tests/scaffold/test_api.py` | `test_health_reports_scaffold`、`test_readiness_is_false`、`test_business_routes_return_501`（参数化全部路由）、`test_invalid_payload_is_422`、`test_selection_union_and_nonempty_targets`、`test_inference_policy_and_profile_schema`、`test_discovery_rejects_client_url_or_path`、`test_model_routes_return_501_without_provider_calls`、`test_install_confirmation_requires_preview_and_idempotency`、`test_selection_and_model_routes_and_event_schema_export`、`test_sse_preflight_returns_501`、`test_openapi_and_event_schema_export` |
| `tests/scaffold/test_cli.py` | `test_help_lists_management_qa_and_model_commands`、`test_install_has_no_bypass_confirmation_command`、`test_unimplemented_command_exits_nonzero`、`test_json_error_is_machine_readable` |
| `tests/frontend/scaffold.spec.ts` | `testAdminNavigationIncludesModels`、`testModelsPageNeverScansOrShowsFakeRuntime`、`testWidgetOpenCloseDestroy`、`testSelectionAndInferenceControlsRemainScaffold`、`testVisibleNotImplementedState`、`testNoFakeSuccessOrAnswer` |
| `tests/integration/test_model_persistence.py` | `test_profile_revisions_are_immutable`、`test_session_inference_revision_conflict`、`test_answer_retry_reuses_inference_binding`、`test_install_target_unique_constraint`、`test_model_call_unknown_outcome_not_replayed`、`test_job_event_resume_and_recovery`：P2 仓储/任务基础，不需要真实模型 |
| `tests/integration/test_ollama_adapter.py` | `test_discovery_only_uses_allowlisted_targets`、`test_installed_running_downloaded_loaded_are_distinct`、`test_model_identity_drift_rejected`、`test_generation_stream_adapter`、`test_embedding_adapter_and_dimension`、`test_install_progress_unknown_total`、`test_cancel_unknown_does_not_kill_runtime`、`test_reconcile_completed_or_interrupted_transfer`：默认使用录制/模拟协议，live marker 仅在显式配置 Ollama 时运行 |
| `tests/integration/test_model_lifecycle.py` | `test_preview_has_no_download_side_effect`、`test_confirm_requires_matching_unexpired_preview`、`test_confirm_is_idempotent`、`test_download_completion_requires_full_identity`、`test_downloaded_model_not_usable_before_role_verification`、`test_verify_generation_embedding_support_roles_separately`、`test_worker_restart_reconciles_install`、`test_missing_model_never_auto_installs`、`test_local_only_blocks_every_remote_role_and_fallback`、`test_external_profile_requires_explicit_configured_policy` |
| `tests/integration/test_imports.py` | `test_cli_and_web_create_kb`、`test_local_and_uploaded_directory`、`test_full_and_partial_import`、`test_doc_docx_xls_xlsx_md_txt_pdf`、`test_scan_pdf_requires_or_uses_ocr`、`test_corrupt_or_encrypted_file_is_reported`、`test_unsafe_relative_path_is_rejected` |
| `tests/integration/test_content.py` | `test_document_crud`、`test_qa_pair_crud`、`test_binary_replace_and_text_revision`、`test_other_documents_unchanged`、`test_optimistic_edit_conflict` |
| `tests/integration/test_sync_versions.py` | `test_unchanged_files_not_reprocessed`、`test_source_add_modify_delete_rename`、`test_partial_manifest_never_deletes`、`test_unreadable_root_never_deletes`、`test_manual_source_conflict`、`test_publish_failure_preserves_active`、`test_concurrent_publish_conflict`、`test_rollback_and_next_sync`、`test_retention_protects_references` |
| `tests/integration/test_retrieval.py` | `test_chinese_keyword_and_vector_fusion`、`test_paraphrase_and_exact_identifier`、`test_filters_apply_before_results`、`test_one_version_per_kb_per_request`、`test_embedding_profile_mismatch_rejected` |
| `tests/integration/test_selection.py` | `test_explicit_single_kb_never_searches_other_kbs`、`test_explicit_combination_queries_every_target`、`test_request_override_does_not_mutate_session_default`、`test_session_switch_applies_next_turn`、`test_switch_during_stream_keeps_current_scope`、`test_scope_revision_conflict`、`test_switch_resets_context_without_deleting_history`、`test_auto_selects_one_or_multiple_relevant_kbs`、`test_auto_candidate_allowlist_and_max_kbs`、`test_no_match_or_ambiguity_requests_clarification`、`test_empty_candidates_do_not_mean_all`、`test_unauthorized_metadata_not_exposed`、`test_catalog_updates_after_publish`、`test_idempotent_retry_reuses_captured_scope` |
| `tests/integration/test_federation.py` | `test_query_vectors_grouped_by_embedding_profile`、`test_cross_kb_ranking_does_not_mix_raw_scores`、`test_duplicate_text_preserves_all_provenance`、`test_conflicting_cross_kb_facts_are_reported`、`test_missing_or_failed_target_never_silently_skipped`、`test_scope_cache_isolated_by_permission_and_versions`、`test_old_citation_after_switch_uses_answer_scope`、`test_preview_reused_with_explicit_versions` |
| `tests/integration/test_answers.py` | `test_multiturn_pronouns_and_topic_change`、`test_history_budget_preserves_turns`、`test_out_of_scope_abstains`、`test_conflicting_evidence_abstains`、`test_claim_citation_support`、`test_old_citation_reads_original_revision`、`test_document_instructions_are_not_executed`、`test_partial_answers_excluded_from_context` |
| `tests/integration/test_streaming.py` | `test_citation_available_before_delta`、`test_only_verified_sentences_stream`、`test_terminal_state_exactly_once`、`test_last_event_id_resume_without_regeneration`、`test_replay_expiry_queries_final_answer`、`test_utf8_and_multiline_sse`、`test_cancel_completion_race`、`test_provider_failure_and_worker_restart`、`test_json_equals_final_stream_result` |
| `tests/integration/test_api_access.py` | `test_search_without_generator`、`test_one_call_ask_and_polling`、`test_idempotency_request_hash`、`test_cross_session_and_kb_access_denied`、`test_widget_cannot_manage_kb`、`test_citation_requires_current_access` |
| `tests/integration/test_feedback.py` | `test_like_dislike_persist`、`test_refusal_creates_issue`、`test_feedback_update_is_idempotent`、`test_issue_links_revision_version_and_retest` |
| `tests/frontend/widget.spec.ts` | `testTwoIndependentHosts`、`testFloatingLauncherAndKeyboard`、`testMultiTurnAndSessionIsolation`、`testSingleMultiAutoSelector`、`testScopeSwitchDuringStreaming`、`testResolvedScopeShownPerAnswer`、`testStreamingCancelReconnect`、`testCitationDetailAndFeedback`、`testMobileAndCssIsolation`、`testNoManagementCredential` |
| `tests/frontend/admin.spec.ts` | `testSelectAndImportDirectory`、`testEditAndPublishContent`、`testVersionRollback`、`testIssueSupplementAndRetest`、`testModelsPageShowsBackendHostAndObservedTime`、`testDiscoveryDistinguishesRuntimeAndModelStates`、`testInstallPreviewRequiresExplicitConfirmation`、`testInstallProgressReconnectCancelAndUnknownState`、`testRoleVerificationBeforeProfileSelection`、`testSessionInferenceSwitchAppliesNextTurn`、`testNoEndpointOrSecretEditableInBrowser` |
| `tests/distribution/test_no_model_weights.py` | `test_git_and_python_packages_exclude_weights`、`test_frontend_build_excludes_weights`、`test_container_context_excludes_runtime_cache`、`test_optional_desktop_distribution_excludes_weights`、`test_startup_never_auto_downloads` |
| `tests/unit/test_metrics.py` | `test_precision_uses_k_denominator`、`test_no_answer_cases_not_in_recall`、`test_duplicate_hits_not_double_counted`、`test_split_keeps_document_and_conversation_groups` |
| `tests/conftest.py`、`tests/fixtures/` | `temporary_store`、`fake_embedder`、`fake_generator`、`two_principals`、`versioned_corpus` 测试夹具；无需真实模型密钥进行确定性契约/异常测试，质量验收另外走真实模型 |

## 8. 完整业务验收与评测

### 8.1 必须执行的端到端流程

1. 准备包含中文、嵌套目录、Word 表格、Excel 多工作表、文本 PDF 和扫描 PDF 的资料；记录文件哈希、预期答案和定位。损坏/加密样本有明确失败预期。
2. CLI 与网页分别建库，分别测试全部/部分导入；网页验证上传本机目录和选择服务端授权目录。查看任务结果与解析正文，不能只验证 HTTP 成功码。
3. 文档和 QA 各做增删改查，等待发布后用同一会话的新轮次查询最新活动版本（未显式固定版本时）；同时验证未修改文档和旧引用。
4. 同步测试无变化、增加、修改、删除、重命名、部分上传、扫描失败和手动修改冲突。用任务审计/测试计数证明只变化项触发解析/嵌入。
5. 构建中途失败、并发发布和进程重启保持旧活动版本可用；回滚后核对新查询及旧引用，同次回答对每个库只用已经绑定的版本，允许不同库各有自己的版本。
6. 在两个独立普通网页真实加载同一插件，验证悬浮、弹窗、键盘、手机宽度、CSS 隔离、销毁和重新挂载。
7. 至少三轮指代追问、话题变化、长历史和双用户并发；验证会话与权限隔离、重复提交幂等。
8. 对可回答、库外、错误前提、证据矛盾与文档嵌入指令的用例逐条检查。事实与引用匹配，证据不足友好告知。
9. 检查真实多个增量事件、首个有效片段时间、UTF-8 分块、取消、断线重连、中途失败和终态丢失；查询最终答案可恢复状态。
10. 提交认可/不认可，查看自动记录的未回答问题；人工补充 QA 或文档、发布、复测，保留问题到修订/版本/结果的链路。
11. 完全不打开网页，使用 Python 和 cURL 完成检索、问答、SSE、引用、反馈，证明 API 是独立可用入口。
12. 建立产品、运维和 FAQ 三个库，同一会话依次查询单库 A、单库 B、A+B 组合及 auto；设计必须分别引用两个库才能回答的问题，验证两库都实际检索、引用分别有库 ID/版本。在途生成时更新默认选择，当前回答维持旧范围、下一轮使用新范围，历史引用不变。
13. 让 API 调用者分别提供候选名单和不提供名单，验证 auto 只在授权范围内工作，能选一库或多库；测试无关问题、含糊问题、必要库超过预算、无权限/不存在/未发布的库、目录更新、不同 embedding profile 和某库检索失败，确保有明确结果或错误、无静默扩大或缩小范围。
14. 在运行 ServiceAPI 的同一账户下进入模型页，显示后端主机标识和检测时间；只读检测服务端 allow-list 中的 Ollama/LM Studio/llama.cpp 候选，不扫描浏览器主机或局域网。核对 installed/running/downloaded/loaded/verified_roles 的独立状态；对未发现/未支持能力明确显示未知或不支持。
15. 对一个未下载且许可允许测试的模型执行安装预览，核对准确标签、来源、身份状态、已知大小/未知项、目标缓存和磁盘观测；不确认时证明零下载。显式确认后观察可重连 job SSE，分别测试成功、断网、磁盘不足、取消、上游取消未知和 worker 重启对账；不得杀共享 Ollama 或删除共享层。下载完成后必须先登记实际完整身份，再单独验证角色。为控制带宽和时间，正式验收可选小型测试模型，现有 `qwen3:8b`/`bge-m3:latest` 用于复用与角色验证场景，不重复拉取相同摘要。
16. 建立全本地 profile，分别验证生成、嵌入、支持校验和公共重排角色，再以 `local_only` 完成入库、单/多/自动选库和问答；故意移除任一必要角色，确认返回明确错误且没有远程 fallback。建立管理员预配置的外接 profile 做显式对照，确认浏览器/API 调用者看不到凭据且未选择 configured 策略时不会调用。会话中切换 inference 默认值时，当前回答保持旧 binding，下一轮使用新修订，历史答案仍显示原模型身份。
17. 构建 Python 包、前端产物、容器上下文和可选 Go 分发目录，运行 `scripts/check_distribution.py`，证明均不含模型权重或部署器缓存；清空模型缓存后启动应用，确认不会自动下载，问答仅返回可操作的模型缺失诊断。

### 8.2 真实质量评测

- 使用真实业务语料进行切分比较，给出 2–3 个边界样例再确定配置；课程说明文档不是目标语料，不用它冒充应用评测集。
- 建立独立调参集和保留验收集。建议验收集至少包含 60 个可回答问题、20 个无答案/证据不足问题，以及 10 组三轮以上会话；按来源文档/会话分组防止改写泄漏。
- 固定相同知识版本组合和问题，比较关键词、向量、融合、融合+重排。报告 Recall@k、Precision@k、MRR@k、nDCG@k 和逐题失败，不只提供一项平均分。
- 新增跨库选取标注：每题记录允许候选、必要知识库集合、相关片段所属库和是否需要澄清；数据集至少覆盖单库路由、多库取证、无匹配、歧义和会话换库。单独报告选库 precision/recall、无匹配/澄清正确率、每库证据覆盖及额外延迟；用人工指定正确库组合的结果对比自动选库，区分“库选错”与“库内检索错”。有确定答案的路由验收子集建议必要库召回率 ≥0.95，同时列出不相关库选入率；权限泄漏、越候选集合检索和切库历史污染作为必须全部通过的确定性检查。
- `Precision@k = top-k 中相关片段数 / k`，不足 k 按缺失计；`Recall@k` 分母为标注相关片段数。无答案题单独评估拒答，不混入正例 Recall；去重后按固定片段/证据标注计分。
- 建议工程目标：可回答集 `Recall@10 ≥ 0.90`、`MRR@10 ≥ 0.80`；融合在预先指定的异写子集优于关键词基线，整体不低于基线。以上是拟定目标，不是课程原文数字或实测成绩。
- 验收集的引用 ID、版本和位置有效率应为 100%；逐题人工检查事实支持和拒答。发现捏造或错误引用即修复重测，不能以平均分掩盖。仅描述固定验收集结果，不推导普遍零错误。
- 记录首个状态事件、首个已核验答案片段、总耗时的 p50/p95，并注明设备、文档数、片段数、并发和模型。对本地模型分别记录冷启动加载与已加载情况下的延迟、CPU/GPU、可用内存/显存、量化、上下文预算和超时；本轮未测这些值，文件体积不能充当硬件适配结论。得到真实基线后再冻结延迟预算。
- 先用本机现有模型建立本地评测基线。`qwen3:8b` 和 `bge-m3:latest` 是基于当前已下载清单的候选，生成效果、向量维度、中文召回及引用支持仍需实测；本地模型不会因为没有 API 账单而降低验收标准。固定相同语料快照与问题比较生成模型时保持检索配置不变；比较嵌入模型时分别构建对应版本，不能复用不兼容向量。
- 常规测试及默认评测采用仅本地模式，记录每种模型调用（含嵌入、改写、重排、支持校验）的实际执行位置与调用量。云端对照评测需显式选择已配置的外部 profile 并给出调用上限；成本按当时核实的定价估算，无价格依据时标为未知。本地执行只意味着没有外部模型 API 调用费用，仍有计算、存储、下载和耗电成本。
- 每次只修改一个重要检索/切分/重排变量，保存配置及前后结果；不能以保留集反复调参后仍称其为独立验收。

已只读检查 `rag-architect` 技能附带评测脚本：内置 TF-IDF 用 ASCII 分词，且其 Precision 分母采用返回数量，因此不能直接作为本项目中文系统验收器。复用其评测维度和语料先行方法，正式数字由本项目实际 API 与校准后的 `Evaluation/metrics.py` 产生。本轮未运行评测，也没有填写成绩。

每项验收记录：课程条款、测试步骤、预期、实际结果、语料/版本/模型配置、环境、时间与证据路径。Agent Insight 项明确保持“延期、未验收”。

## 9. 执行顺序和验证命令

| 阶段 | 并行流 | 难度 | 独占工作 | 独立退出条件 |
| --- | --- | --- | --- | --- |
| P0 | 计划 | — | 只读核对并维护两份计划 | 两份计划一致；源码未修改 |
| P1 | Contract Gate | D2 | 冻结 DTO、Protocol、OpenAPI、SSE、错误码、fixtures 与文件 owner | provider/consumer contract tests 可分别运行 |
| P1 | P1-A1 平台框架 | D1–D2 | workspace、设置、FastAPI、普通路由、存储/任务/解析占位、SDK/CLI、共享 TS 传输层 | A1 独立启动；A1 路由为 501；无数据库/网络副作用 |
| P1 | P1-A2 核心框架 | D3–D4 | QA 核心、选库/融合、上下文/证据、模型/索引端口和状态机占位 | A2 使用 fake 独立通过 consumer/schema 测试；无假业务输出 |
| P1 | P1-B 前端布局 | D1–D2 | WebUI/WebWidget 页面、组件、状态、样式和占位交互 | 只消费冻结契约；可构建；无假数据或本机扫描；完成后停止 |
| P2 | Contract Gate | D2 | 冻结持久化实体、任务事件、导入/发布和关键词检索接口 | A1/A2 可用各自 fake 对接同一版本契约 |
| P2 | P2-A1 确定性业务 | D2 | SQLite/文件、解析、CRUD、上传、来源增量、版本、Job 租约/恢复 | 多格式/CRUD/增量/发布/恢复测试独立通过 |
| P2 | P2-A2 检索基础 | D3 | 分块、中文分词、BM25、快照检索读取、目录描述与关键词自动选库基线 | 无真实模型即可独立通过检索/选库基线测试 |
| P2 | P2-B 基础管理 UI | D2 | 知识库、导入、内容、版本、任务和错误页面 | 通过 API 驱动 P2-A1/A2；不实现模型安装或语义问答 |
| P3 | Contract Gate | D3 | 冻结模型身份、binding、向量指纹、答案/任务事件和取消/恢复语义 | 录制协议、fake runtime 和契约兼容测试通过 |
| P3 | P3-A1 模型运行平台 | D2–D3 | Ollama 发现/枚举/安装传输、profile/verification 仓储、worker 对账、调用审计 | 安装、取消、恢复、身份记录和任务测试独立通过 |
| P3 | P3-A2 高难问答核心 | D3–D4 | 嵌入/向量、自动选库、跨库融合、上下文、证据、local_only、生成/引用/SSE 一致性 | 完整本地问答与对抗性一致性测试独立通过 |
| P3 | P3-B 问答/模型 UI | D2–D3 | Widget、选库/inference、引用、流式、模型发现/安装/验证/profile 页面 | 只通过 API 消费 A1/A2；浏览器不接触端点、路径或密钥 |
| P4 | Contract Gate | D2 | 冻结验收 API、报告 schema、反馈/复测和分发检查输出 | 验收工具和 UI 读取同一稳定结果格式 |
| P4 | P4-A1 工程验收 | D2 | CLI/Python/cURL、权限/幂等/恢复、反馈持久闭环、构建和权重排除 | 无网页完成业务流程；工程与分发检查留证 |
| P4 | P4-A2 质量验收 | D4 | 语料分析、检索/选库/答案评测、失败归因、延迟和 local_only 审计 | 指标、逐题证据和失败分类报告留证 |
| P4 | P4-B 前端验收 | D2–D3 | 两宿主站点、响应式/可访问性、完整管理与反馈场景 | 前七项前端场景及模型 UI 逐项留证 |
| P5 | Contract Gate | D2 | 冻结桌面 API、进程控制协议和 Agent Insight 挂载契约 | Go/平台端可基于生成契约开发 |
| P5 | P5-A1 桌面运行适配 | D2–D3 | 本地后端进程启动/就绪/停止、打包边界、API 适配 | 进程生命周期和分发测试通过 |
| P5 | P5-A2 平台语义适配 | D3 | Agent Insight 工具映射、范围/inference/引用语义适配 | 平台调用与核心语义一致性测试通过 |
| P5 | P5-B Go/平台界面 | D2–D3 | Go/Fyne 界面及宿主侧挂载/展示 | EXE 实际构建；平台 UI 按确定版本验收 |

下列命令是 **P1 及以后要建立和执行的命令**，不是本轮已执行结果。仓库目前还没有相应配置，必须先创建框架。

```bash
# 每阶段 Contract Gate：先冻结并校验共享契约
uv run --all-packages pytest tests/contracts -q
uv run --all-packages python scripts/export_contracts.py --check

# A1 可独立运行：平台、存储、API、SDK/CLI、解析和任务
uv sync --all-packages --group dev
uv run --all-packages ruff check .
uv run --all-packages pytest tests/scaffold/test_packages.py tests/scaffold/test_api.py tests/scaffold/test_cli.py -q
uv run --all-packages pytest tests/integration/test_model_persistence.py tests/integration/test_imports.py tests/integration/test_content.py tests/integration/test_sync_versions.py -q
uv run --package qa-service qa-api
uv run --package qa-cli qa --help
uv run --package qa-cli qa models --help

# A2 可独立运行：核心检索、选库、模型消费、证据、回答和评测（默认使用 fake/录制协议）
uv run --all-packages pytest tests/integration/test_retrieval.py tests/integration/test_selection.py tests/integration/test_federation.py -q
uv run --all-packages pytest tests/integration/test_ollama_adapter.py tests/integration/test_model_lifecycle.py -q
uv run --all-packages pytest tests/integration/test_answers.py tests/integration/test_streaming.py -q
uv run --all-packages python Evaluation/analyze_corpus.py --manifest Evaluation/fixtures/manifest.json
uv run --all-packages python Evaluation/evaluate.py --config Evaluation/config.json
# 仅在显式提供受控 Ollama target 和测试模型预算时启用 live marker
uv run --all-packages pytest -m ollama_live -q

# 阶段末唯一跨后端流检查：只验证冻结契约集成，不转移文件 owner
uv run --all-packages pytest tests/integration/cross_stream -q

# B 独立构建并通过生成 SDK/API 接入
npm ci
npm run typecheck
npm run build
npm run test:scaffold
npm run test:e2e

# P4-A1 分发检查
uv run --all-packages python scripts/check_distribution.py --check
```

A1 生成并提供基础 API/SDK 适配，A2 提供符合冻结 Protocol 的核心实现；两者平行开发，阶段中不互相等待源码，只在 `tests/integration/cross_stream/` 汇合。B 只消费生成 TypeScript SDK 和公开 HTTP/SSE，不依赖任一后端组的内部模块。Python 包名/入口固定为 `qa-service:qa-api/qa-worker`、`qa-cli:qa`。P2–P4 的 `Evaluation/config.json` 保存 API 地址、数据集、语料版本、检索配置与输出目录，不保存凭据。

网页端到端验证使用 Playwright 启动两个宿主站点与 API；框架期验证布局和占位，业务期使用真实服务验证完整链路。模型质量测试记录真实提供商与模型配置，确定性单元测试使用测试替身，两种结果分开报告。

## 10. 当前交付边界

本计划已经覆盖七项课程功能、外部程序调用、动态切库/多库组合/自动选库、目录隔离、本地/外接模型的发现—安装—验证—选择生命周期、权重不随部署分发、条件性的 Go 前端，以及逐文件/逐方法的实现和验收安排。当前未修改项目文件、未安装依赖、未启动应用、未调用模型、未下载权重、未生成索引或评测成绩。唯一写入的是本计划文件。

框架阶段无需用户先提供模型密钥、真实语料或 Agent Insight 仓库。首次实施先完成 P1 Contract Gate，然后 A1（D1–D2 平台/确定性工程）与 A2（D3–D4 核心语义/一致性）由两组同时推进，各自拥有文件、测试、提交和技术决策；它们只以冻结 DTO/Protocol/fixtures 交互，不互相统属、管辖、审批或代写。P1-B 独立建立 WebUI/WebWidget，占位接入公开 API；Contract Gate、A1、A2、B 全部完成后停止。P2–P5 重复同样结构：阶段开头短暂冻结契约，A1/A2 平行，B 通过公开客户端接入。任何跨组修改先进入下一 Contract Gate；任何 B Part 都不得直接导入或补写后端内部逻辑。
