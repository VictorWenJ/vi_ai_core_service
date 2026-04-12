# ARCHITECTURE.md

> 更新日期：2026-04-13

## 1. 文档定位

本文件定义 `vi_ai_core_service` 的总体架构、分层职责、依赖方向、调用关系与当前阶段架构约束。

本文件只负责回答以下问题：

- 当前系统总体分层是什么
- 各层分别负责什么
- 各层之间如何依赖
- 同步、流式、知识导入、离线构建与评估链路如何协作
- 当前阶段有哪些架构级约束

本文件不负责：

- 仓库级协作规则
- 项目阶段路线图
- 代码审查细则
- 模块级局部实现说明
- 你和我之间的交互流程

这些内容分别由：

- `AGENTS.md`
- `PROJECT_PLAN.md`
- `CODE_REVIEW.md`
- 模块 `AGENTS.md`
- `CHAT_HANDOFF.md`

承担。

---

## 2. 架构定位

`vi_ai_core_service` 是 VI AI Project 的 Python AI 核心服务。
当前架构目标不是做“大而全”的统一平台，而是构建一个边界清晰、职责可分、可持续演进的 AI 应用核心后端。

当前架构重点包括：

- 让不同能力在不同目录中各司其职
- 让系统具备前端可接入的流式会话交付能力
- 为基于受控知识源进行 grounding 与 citation 提供运行时子域
- 为后续 Tool、Case Workspace、Agent 预留清晰边界
- 为 RAG 评估与离线构建提供可演进的工程基础

---

## 3. 当前总体分层

### API 接入层（`app/api/`）
职责：
- 暴露 HTTP 接口
- 解析请求
- 返回同步响应
- 输出 SSE 流式响应
- 暴露 cancel/reset 等控制入口

### 应用编排层（`app/services/`）
职责：
- 承接同步与流式两类会话用例
- 协调 context / prompts / providers
- 管理 assistant message 生命周期
- 管理 cancel / timeout / failure 收口
- 维护 request assembly、取消注册与 context completed 收口

### 上下文管理层（`app/context/`）
职责：
- 管理 conversation-scoped 短期状态
- 管理 recent raw / rolling summary / working memory
- 管理 message lifecycle 相关状态字段
- 规定 completed 才进入标准 memory update

### Prompt 资产层（`app/prompts/`）
职责：
- 管理 Prompt 模板
- 提供渲染能力

### 知识与检索子域（`app/rag/`）
职责：
- 负责知识对象模型
- 负责 ingest / parse / clean / chunk / embed / index
- 负责文档加载适配层（可接入成熟 loader 框架并转换为内部中间表示）
- 负责 retrieval service、knowledge block 渲染与 citation 结构
- 负责 `repository/`、`content_store/`、build task、evaluation 持久化编排
- 作为 Knowledge + Citation Layer 与 RAG 持久化控制面的内部实现域

### 模型 API 接入层（`app/providers/`）
职责：
- 对接不同厂商
- 归一化非流式结果
- 归一化流式 chunk / finish / usage / error
- 通过独立 embedding provider 抽象承接文本 embedding 能力
- 模块内部按能力分层为 `app/providers/chat/` 与 `app/providers/embeddings/`，并分别维护 chat registry 与 embedding registry

### 可观测性基础设施层（`app/observability/`）
职责：
- 统一结构化日志
- 通过 `log_report` 提供 JSON-safe 的事实型日志输出
- 承接离线构建与 benchmark 运行的事实型日志字段

### 数据模型层（`app/schemas/`）
职责：
- 承载共享契约与基础数据模型
- `app/api/schemas/` 负责对外 request / response contract

### 数据库基础设施层（`app/db/`）
职责：
- 负责数据库连接、session、事务与公共持久化基础设施
- 为 `rag` 等子域提供共享数据库能力
职责：
- 定义内部 `LLMMessage`、`LLMRequest`、`LLMResponse`、`LLMStreamChunk` 等共享契约
- API request / response 与 SSE event 当前位于 `app/api/schemas/`

---

## 4. 工程基础设施平面

`infra/` 负责：

- Dockerfile
- compose 编排
- app + redis 本地联调
- 后续 app + redis + qdrant 本地联调
- 运行时环境变量样例

当前代码事实：

- app + redis + qdrant 本地联调已具备

`infra/` 不进入业务依赖链。
它是工程基础设施平面，而不是业务层。

---

## 5. 总体依赖方向

业务依赖方向：

`api -> services -> context/prompts/rag/providers -> schemas`

其中：

- `observability` 为横切基础设施层，可被 `api/services/providers/rag` 依赖
- `providers` 不能依赖 `api/services/context/rag`
- `context` 不能依赖 `api/services/providers/rag`
- `rag` 不能依赖 `api`
- `rag` 的 retrieval 结果应由 `services` 编排后进入 request assembly

当前代码事实补充：

- 当前主链路已启用 `rag` 可降级分支
- `services` 当前少量用户请求入口会消费 `app/api/schemas/` 中的 Pydantic 模型

### 依赖方向原则

1. API 只向下依赖，不反向被业务层依赖
2. services 是编排层，不承担底层实现域职责
3. context 与 rag 并列存在，分别负责 short-term memory 与 external knowledge
4. providers 是能力提供层，不反向驱动业务编排
5. schemas 是共享契约层，不承担业务逻辑

---

## 6. 当前调用关系

### 6.1 同步聊天链路
`api/chat -> services/chat_service -> request_assembler -> context/prompts/rag/providers -> response`。

### 6.2 流式聊天链路
`api/chat_stream -> services/streaming_chat_service -> request_assembler -> context/prompts/rag/providers -> SSE serializer`。

### 6.3 知识导入链路
`api/knowledge -> rag/document_service -> rag/ingestion/* -> rag/content_store -> rag/repository -> MySQL`。

### 6.4 离线构建链路
`api/knowledge -> rag/build_service -> rag/repository(document/version/build_task/build_document/chunk) -> rag/content_store(normalized text) -> providers/embeddings -> rag/retrieval/vector_store(Qdrant)`。

### 6.5 评估链路
`api/evaluation -> rag/evaluation_service -> rag/evaluation/runner -> rag/retrieval/runtime -> rag/repository(evaluation_run/evaluation_case)`。

### 6.6 Runtime / Inspector 查询链路
`api/runtime | api/knowledge inspector -> services/runtime_service | rag/inspector_service -> rag/repository -> MySQL`；当需要查看向量详情时，由 `rag/inspector_service` 按 `vector_point_id` 向 Qdrant 回读。

---


## 7. 分层衔接原则

### 7.1 Phase 4、Phase 5 与 Phase 6 的衔接原则

- Phase 4 的 policy pipeline 不变：
  `selection -> truncation -> deterministic summary -> serialization`
- Phase 5 的 message lifecycle 与 SSE 协议不变
- Phase 6 不改变 completed 才进入标准 memory update 的规则
- Phase 6 中 knowledge block 已纳入装配，不替代 working memory / rolling summary
- non-completed assistant message 默认不参与后续 request assembly
- citation 已落地并且只来自 retrieval 结果，不来自模型自由生成

### 7.2 memory 与 retrieval 的分层原则

- `context` 负责 short-term memory
- `rag` 负责 external knowledge grounding
- knowledge block 与 memory block 可以同时进入 request assembly
- retrieval 结果不是 working memory，也不是 rolling summary

### 7.3 编排与实现分离原则

- `services` 负责编排
- `context` 负责状态
- `rag` 负责知识实现
- `providers` 负责厂商接入
- `api` 负责协议输出

---

## 8. 当前阶段架构约束

### 8.1 RAG 先做内部子域，不拆独立服务
`app/rag/` 继续作为内部知识与检索子域，不拆独立微服务。

### 8.2 相似度与索引约束
向量检索仍以 Qdrant + cosine 为基线；MySQL 不承担向量检索职责。

### 8.3 Citation 约束
citation 必须继续来自 retrieval 结果，不得退化为模型自由生成装饰文本。

### 8.4 降级约束
检索失败时，chat 与 stream 主链路必须允许降级，不得因 RAG 构建或控制面故障直接拖垮主链路。

### 8.5 Post-Phase 7 控制面升级约束
- 删除 `RAGControlState` 作为正式控制面真相源
- MySQL 负责控制面与治理数据
- 文件存储负责原始文件与 normalized text 快照
- Qdrant 继续负责 embeddings、payload 与 retrieval
- `build_tasks`、`evaluation_runs` 必须按任务对象建模，即使当前仍同步执行

### 8.6 控制面契约与命名约束
- API 仍按领域命名，不再按 console / playground / debug 命名长期接口
- `app/api/schemas/` 只承载对外 request / response contract
- 领域内部对象保留在 `app/rag/`、`app/context/` 等模块内

### 8.7 文档加载适配层约束
LangChain loader 只作为 ingest 输入适配层；不得接管 chunk、metadata、build、evaluation、retrieval 主链路。

### 8.8 repository 分层约束
- `app/db/` 只承载共享数据库基础设施
- `app/rag/repository/` 承载 `rag` 子域的数据访问封装
- 不得在 API / service / inspector 中散落 SQL

### 8.9 结构化字段命名约束
- 详情对象字段优先使用 `*_details`
- 标识集合字段优先使用 `*_ids`
- 不再以 `*_json` 作为业务语义命名

---


## 9. 修改规则

1. 不允许在本文件中混入仓库级协作规则
2. 不允许在本文件中混入项目阶段路线图细节
3. 不允许在本文件中混入 code review 清单
4. 不允许把模块级实现细节写成总体架构要求
5. 不允许未经确认改变总体分层结构、章节顺序、标题层级与文风

---

## 10. 一句话总结

`ARCHITECTURE.md` 在当前阶段的职责，是作为项目总体架构文件，明确 `vi_ai_core_service` 的分层结构、依赖方向，以及当前已落地的同步 / 流式 / Knowledge + Citation / Evaluation 主链路，以及本轮控制面持久化升级所需的 MySQL / 文件存储 / Qdrant 三层分工，确保系统在后续迭代中仍保持整体分层清晰、职责稳定、演进可控。
