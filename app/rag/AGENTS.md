# app/rag/AGENTS.md

> 更新日期：2026-04-12

## 1. 文档定位

本文件定义 `app/rag/` 的职责、边界、结构约束、开发约束与 review 标准。

现阶段，`app/rag/` 板块仅使用 **一个 `AGENTS.md` 文件** 进行模块治理。
该文件**临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责**。

也就是说，在当前阶段，`app/rag/AGENTS.md` 同时用于约束：

- 本模块是什么
- 本模块做什么、不做什么
- 本模块当前阶段要实现什么
- 本模块的结构边界与依赖边界
- 本模块的 review 与测试标准
- 本模块后续演进时的文档维护规则

本文件不负责：

- 仓库级协作规则
- 你和我之间的交互流程
- 根目录阶段路线图
- 根目录级总体架构说明
- 根目录级 Code Review 总标准

这些内容分别由：

- 根目录 `AGENTS.md`
- 根目录 `PROJECT_PLAN.md`
- 根目录 `ARCHITECTURE.md`
- 根目录 `CODE_REVIEW.md`
- `CHAT_HANDOFF.md`

承担。

---

## 2. 模块定位

`app/rag/` 是系统在 Phase 6 落地的内部知识与检索子域。
截至当前代码基线，模块已具备 Python 运行时代码与最小 ingest/retrieval/citation 闭环，并进入 Phase 7 的离线构建与评估基础增强阶段。

当前阶段建议围绕以下职责组织：

- `models.py`
- `ingestion/`
- `retrieval/`
- `citation/`
- `runtime.py`
- 面向知识领域职责拆分的应用服务（如 document / build / inspector / evaluation）
- `AGENTS.md`

---

## 3. 本模块职责

1. 提供 Phase 6 知识对象模型与 citation 对象模型
2. 提供最小 ingest pipeline（loader adapter / parser / cleaner / chunker / embedding / index）
3. 提供 retrieval service 与 knowledge block 渲染
4. 提供 citation-ready retrieval 结果与可降级 runtime
5. 提供离线构建元数据与构建批次相关数据支撑
6. 为 RAG 评估数据集与 benchmark 提供可引用的知识对象与检索依据

---

## 4. 本模块不负责什么

1. 不负责 HTTP 路由
2. 不负责同步或流式 chat 主链路编排
3. 不负责 assistant message lifecycle 状态机
4. 不负责 conversation short-term memory
5. 不负责 request assembly 最终顺序决策
6. 不负责 `/chat` 或 `/chat_stream` 的最终响应封装
7. 不负责长期记忆平台、审批流、Case Workspace
8. 不负责完整知识运营后台或独立评估平台 UI
9. 不负责以消费者命名的控制台聚合服务长期驻留在 `app/rag/`

---

## 5. 依赖边界

### 允许依赖
- `app/providers/embeddings/`（embedding provider abstraction）
- `app/observability/`
- `app/context/policies/tokenizer.py`（token counter 复用）

### 禁止依赖
- `app/api/`
- `app/services/`
- `app/context/`

### 原则
`app/rag/` 是被编排方，不是主链路编排方。
在线 retrieval 由 `services` 调用，`rag` 不反向驱动 chat 或 context。
`rag` 只依赖 `app/providers/embeddings/` 的抽象与工厂入口，不持有任何 embedding 厂商实现代码。

---

## 6. 架构原则

### 6.1 先做内部子域，不拆独立服务
当前 Phase 6 中，RAG 只作为 `vi_ai_core_service` 内部子域实现。
本轮不拆独立知识服务，不引入额外微服务边界。

### 6.2 ingestion 与 online retrieval 分离
- ingestion 负责：parse / clean / chunk / embed / index
- online retrieval 负责：query / top-k / filter / 返回 retrieval 结果

两条链路要职责清晰，不混写。

### 6.3 retrieval 是知识 grounding，不替代 short-term memory
Phase 6 中 retrieval 结果用于：
- 外部知识增强
- knowledge block 注入
- citations 生成

它不替代：
- recent raw
- rolling summary
- working memory

### 6.4 citation 是核心能力，不是附属信息
- citation 必须来自 retrieval 结果
- citation 不应由模型自由生成
- citation 结构必须稳定、可读、可展示

### 6.5 检索失败必须可降级
RAG 是增强层，不应在当前阶段成为主链路单点故障。
检索失败时，应支持由 `services` 做可控降级。

### 6.6 当前代码事实
- 当前仓库已创建 `models.py`、`ingestion/`、`retrieval/`、`citation/`、`runtime.py`
- 当前 `/chat` 与 `/chat_stream` completed 已接入本模块并返回 citations
- 当前 retrieval 失败路径支持可降级，主 chat 链路不被拖垮

### 6.7 Phase 7 演进原则
- 本轮优先补齐离线构建元数据与构建质量门禁
- 本轮允许为 benchmark 与评估标签提供稳定数据支撑
- 本轮不把 `app/rag/` 扩张成独立知识运营平台或复杂 agentic retrieval 层

### 6.8 文档加载器适配原则
- 文档加载器允许通过成熟框架接入，例如 LangChain document loaders
- loader 框架只位于 `ingestion/` 的输入适配层
- loader 输出必须先转换为本项目内部中间表示，再进入 clean / chunk / metadata / build 主链路
- 不允许让外部框架 Document/loader 直接替代内部领域模型

### 6.9 控制面服务拆分原则
- `app/rag/` 中面向控制面或操作面的应用服务，应按 document / build / inspector / evaluation 等领域职责拆分
- 不再长期维持以消费者命名的 `console_service.py` 作为聚合服务
- runtime summary / config / health 等系统级摘要能力不应继续固化在 `app/rag/` 内部

---

## 7. 当前阶段能力声明

当前代码现状：

- `app/rag/` 已落地运行时代码
- 仓库已具备 ingest -> embed -> index -> retrieve 主链路
- `/chat` 与 `/chat_stream` completed 已接入 citations
- `tests/` 已具备 RAG / citation 测试

当前前置已落地目标：

- `app/rag/` 子域运行时代码
- 知识对象模型
- 文档导入最小闭环
- 结构感知 + token-aware + overlap 的 chunking
- 文本 embedding 主链路
- 向量索引抽象与默认实现
- retrieval service
- citation-ready retrieval 结果
- 与 `/chat` 和 `/chat_stream` completed 收口兼容的 citation 数据支撑

当前前置默认基线：

- 向量数据库：**Qdrant**
- 相似度度量：**Cosine**
- embedding：单一文本 embedding 基线
- 检索：top-k + metadata filter
- retrieval 结果进入 request assembly 的位置由 `services / request_assembler` 决定

当前本轮新增（本轮已落地）：

- 构建批次与版本元数据（build_id / version_id / chunk_strategy_version / embedding_model_version）
- 增量构建 / 局部重建边界（manifest + content hash + force rebuild ids）
- 基础质量门禁与构建统计（failure ratio / empty chunk ratio / upsert 一致性）
- 与 retrieval / citation / answer benchmark 对齐的数据支撑（`app/rag/evaluation/`）
- 允许在 loader adapter 层接入成熟文档加载器框架，并继续保持内部 ingest 主链路控制权

当前本轮不要求落地：

- 独立 RAG 微服务
- complex rerank
- hybrid retrieval
- 重型 rerank 体系
- graph retrieval
- agentic retrieval
- 多模态检索主链路
- 自动写回知识库
- 知识审批流
- 知识运营后台

---

## 8. 核心模型要求

一旦开始编码，至少应定义以下模型：

### 8.1 KnowledgeDocument
表示知识文档主对象。

至少包含：
- `document_id`
- `title`
- `source_type`
- `content`
- `origin_uri`
- `file_name`
- `jurisdiction`
- `domain`
- `tags`
- `effective_at`
- `updated_at`
- `visibility`
- `metadata`

### 8.2 KnowledgeChunk
表示可检索切块。

至少包含：
- `chunk_id`
- `document_id`
- `chunk_text`
- `chunk_index`
- `token_count`
- `embedding_model`
- `metadata`

### 8.3 RetrievedChunk
表示 retrieval 输出结果。

至少包含：
- `chunk_id`
- `document_id`
- `text`
- `score`
- `title`
- `origin_uri`
- `source_type`
- `jurisdiction`
- `domain`
- `effective_at`
- `updated_at`
- `metadata`

### 8.4 Citation
表示对外引用项。

至少包含：
- `citation_id`
- `document_id`
- `chunk_id`
- `title`
- `snippet`
- `origin_uri`
- `source_type`
- `updated_at`
- `metadata`

### 8.5 Phase 7 构建元数据要求
如本轮新增离线构建能力，至少应考虑以下元数据：
- `build_id`
- `version_id`
- `chunk_strategy_version`
- `embedding_model_version`

这些字段可按当前代码结构选择落位到文档对象、chunk 对象、构建结果对象或专用构建元数据对象中，但必须保证可追踪、可比较、可回归。

---

## 9. 文档维护规则（强约束）

本文件属于 `app/rag/` 模块的治理模板资产。
后续任何更新，必须严格遵守以下规则：

### 9.1 基线规则
- 必须以当前文件内容为基线进行增量更新
- 不涉及变动的内容不得改写
- 未经明确确认，不得重写文件整体风格

### 9.2 冻结规则
未经明确确认，不得擅自改变以下内容：

- 布局
- 排版
- 标题层级
- 写法
- 风格
- 章节顺序

### 9.3 允许的修改范围
允许的修改仅包括：

1. 在原有章节内补充当前阶段内容
2. 新增当前阶段确实需要的新章节
3. 更新日期、阶段、默认基线等必要信息
4. 删除已明确确认废弃且必须移除的旧约束

### 9.4 禁止事项
禁止：

1. 把原文档整体改写成另一种风格
2. 把模块文档从“模块治理文件”改写成“泛项目说明书”
3. 每次更新都擅自改变标题层级与章节结构
4. 未经确认新增大段不属于本模块职责的内容

### 9.5 模板升级规则
如果未来需要升级 `app/rag/AGENTS.md` 的模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 10. 修改规则

1. 不允许在 `rag` 中直接编排 `/chat` 或 `/chat_stream`
2. 不允许让 `rag` 依赖 `app/api/`、`app/services/`、`app/context/`
3. 不允许把当前不存在的 RAG 能力写成已落地实现
4. 不允许回退为“按字符硬切分”作为正式主 chunking 策略
5. 不允许把 Qdrant SDK 调用散落到多个无边界业务文件中
6. 不允许把 citation 做成模型自由输出字符串
7. 不允许在当前轮次中把 Tool Calling、长期记忆、审批流、Case Workspace、Agent runtime 混入 `rag` 子域
8. 不允许把评估 runner 直接塞进 `app/rag/` 运行时主路径并污染在线链路
9. `app/rag/` 中的知识对象模型、chunk 模型、retrieval 结果模型、citation 模型，其 dataclass 字段必须逐项补充中文注释。
10. 涉及 score、token_count、updated_at、effective_at、metadata、filter 等字段时，注释中必须明确语义，不得含糊。
11. 不允许删除仍在使用的 RAG 模型字段中文注释。

---

## 11. Code Review 清单

1. `app/rag/` 是否仍保持为“内部知识与检索子域”？
2. 当前提交是否真的新增了 RAG 代码，而不是只在文档中宣称已实现？
3. 若已新增实现，ingestion 与 retrieval 是否职责清晰？
4. 若已新增实现，是否按结构感知 + token-aware + overlap 实现正式 chunking？
5. 若已新增实现，embedding 是否通过抽象接入，而不是把厂商细节写死在 retrieval 中？
6. 若已新增实现，向量索引是否通过统一接口暴露？
7. 默认技术基线是否与当前轮次一致：
   - Qdrant
   - Cosine
   - 文本 embedding
8. retrieval 结果是否足以支撑 citation，而不是只返回一段裸文本？
9. 是否没有把 retrieval 与 short-term memory 混为一体？
10. citation 是否可追溯、可展示、结构稳定？
11. 检索失败时是否可被 services 安全降级？
12. 本次文档更新是否遵守了“文档维护规则”？
13. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 12. 测试要求

当前代码现状下，本模块已存在运行时代码。
当前测试至少覆盖：

1. parser 解析正确
2. cleaner 行为稳定（如实现）
3. chunker 切块稳定
4. chunk metadata 继承正确
5. embedding 输出结构正确
6. index upsert / query 正确
7. retrieval top-k 正确
8. filter 行为正确
9. citation 格式化正确
10. retrieval 失败可降级
11. 不依赖真实外部向量服务做主回归时，仍可用 in-memory / fake 实现保障测试稳定
12. 若本轮新增离线构建元数据或质量门禁，必须补对应测试

---

## 13. 一句话总结

`app/rag/` 在当前代码基线中已是 Phase 6 的运行时子域，负责知识导入、检索、citation-ready 输出与可降级 runtime，并在后续更新中继续严格遵守模块文档的模板冻结规则。
