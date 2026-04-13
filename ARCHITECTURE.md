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
- 先把 `chat` / `chat_stream` 的执行骨架收敛清楚
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

### 应用入口与 façade 层（`app/services/`）
职责：
- 承接同步与流式两类会话用例入口
- 做 request/response 级适配
- 管理同步返回与 SSE 交付
- 作为 chat runtime 的 façade，而不是继续承载主编排内核

### Chat Runtime 执行层（`app/chat_runtime/`）
职责：
- 负责统一的 chat core 执行骨架
- 负责 workflow、hook、step dispatch 与 trace 收口
- 统一协调 scope 标准化、retrieval、request assembly、provider 调用、context 收口
- 为未来 tool calling、model routing、runtime skill 预留接口位

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
- 承接 chat runtime trace、离线构建与 benchmark 运行的事实型日志字段

### 数据模型层（`app/schemas/`）
职责：
- 承载共享契约与基础数据模型
- `app/api/schemas/` 负责对外 request / response contract
- `app/chat_runtime/models.py` 负责 chat runtime 内部执行态契约

### 数据库基础设施层（`app/db/`）
职责：
- 负责数据库连接、session、事务与公共持久化基础设施
- 为 `rag` 等子域提供共享数据库能力

### repository / 持久化实体分层
当前控制面持久化升级完成后，数据库访问应遵守以下分层：

- `app/db/`：提供数据库连接、session、事务、迁移等共享基础设施
- `app/rag/repository/`：提供 `rag` 子域的数据访问封装
- 持久化实体对象：用于表达表记录，例如 `DocumentRecord`、`BuildTaskRecord`、`ChunkRecord` 等
- 领域对象 / read model：用于表达上层业务语义或查询结果摘要

架构要求：

- `repository` 层内部允许直接操作 ORM 持久化实体对象
- `repository` 对外不应长期以裸 `dict` 作为核心返回形式
- `services`、`chat_runtime`、`inspector` 等上层应消费领域对象或 read model，而不是大量基于字符串键访问 `dict`
- `*_details` 字段内部允许保持半结构化 `dict`，但查询结果整体不应长期维持为裸 `dict`

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

`api -> services -> chat_runtime -> context/prompts/rag/providers -> schemas`

其中：

- `observability` 为横切基础设施层，可被 `api/services/chat_runtime/providers/rag` 依赖
- `providers` 不能依赖 `api/services/chat_runtime/context/rag`
- `context` 不能依赖 `api/services/chat_runtime/providers/rag`
- `rag` 不能依赖 `api`
- `rag` 的 retrieval 结果应由 `chat_runtime` 编排后进入 request assembly
- `services` 只依赖 `chat_runtime` 的稳定入口，不应重新散落主编排逻辑

### 依赖方向原则

1. API 只向下依赖，不反向被业务层依赖
2. services 是 façade 层，不承担主执行内核职责
3. chat_runtime 是 chat core 执行层，不承担 HTTP/SSE 协议职责
4. context 与 rag 并列存在，分别负责 short-term memory 与 external knowledge
5. providers 是能力提供层，不反向驱动业务编排
6. schemas 是共享契约层，不承担业务逻辑

---

## 6. 当前调用关系

### 6.1 同步聊天链路
`api/chat -> services/chat_service -> chat_runtime/engine -> request_assembler -> context/prompts/rag/providers -> response`。

### 6.2 流式聊天链路
`api/chat_stream -> services/streaming_chat_service -> chat_runtime/engine -> request_assembler -> context/prompts/rag/providers -> SSE serializer`。

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

### 7.1 Phase 4、Phase 5 与当前 Chat Runtime 收敛的衔接原则

- Phase 4 的 policy pipeline 不变：
  `selection -> truncation -> deterministic summary -> serialization`
- Phase 5 的 message lifecycle 与 SSE 协议不变
- 当前 chat runtime 收敛不改变 completed 才进入标准 memory update 的规则
- knowledge block 已纳入装配，不替代 working memory / rolling summary
- non-completed assistant message 默认不参与后续 request assembly
- citation 已落地并且只来自 retrieval 结果，不来自模型自由生成

### 7.2 memory 与 retrieval 的分层原则

- `context` 负责 short-term memory
- `rag` 负责 external knowledge grounding
- knowledge block 与 memory block 可以同时进入 request assembly
- retrieval 结果不是 working memory，也不是 rolling summary

### 7.3 编排与实现分离原则

- `services` 负责入口 façade 与交付
- `chat_runtime` 负责 chat core 编排
- `context` 负责状态
- `rag` 负责知识实现
- `providers` 负责厂商接入
- `api` 负责协议输出

---

## 8. 当前阶段架构约束

### 8.1 Chat Runtime 先做最小骨架，不做通用平台
`app/chat_runtime/` 当前只服务 `chat` 与 `chat_stream`，不做 Tool Calling / Agent Runtime 平台化。

### 8.2 workflow 必须显式声明
主流程必须显式定义为 `DEFAULT_CHAT_WORKFLOW = list[str]`，不得继续依赖隐式大函数顺序。

### 8.3 hook 必须与主 workflow 分离配置
lifecycle hook 必须以事件数组形式存在；step hook 必须以 step 前后事件形式存在；不得与主 workflow 混成同一个数组。

### 8.4 services 必须收口为 façade
`ChatService` 与 `StreamingChatService` 保持入口适配与交付职责，不得继续扩展为双编排内核。

### 8.5 request assembly 仍由唯一中枢负责
`ChatRequestAssembler` 继续是唯一装配中枢；chat runtime 只能调用它，不能绕过它重新定义装配顺序。

### 8.6 对外 contract 稳定性约束
- `/chat` 与 `/chat_stream` 的对外 contract 不得回退
- completed 事件的 citations 行为保持不变
- delta 阶段不新增 citations 增量

### 8.7 skill 只预留引用位
当前只允许在 workflow 中声明 `skills[]` 引用位；不得在本轮实现 runtime skill loader 或技能自动发现系统。

### 8.8 RAG 与未来控制面升级保持边界
当前 chat runtime 收敛不得破坏后续 `rag` 控制面持久化升级边界；`chat_runtime` 不接管 `rag` 子域内部持久化职责。

---

## 9. 修改规则

1. 不允许在本文件中混入仓库级协作规则
2. 不允许在本文件中混入项目阶段路线图细节
3. 不允许在本文件中混入 code review 清单
4. 不允许把模块级实现细节写成总体架构要求
5. 不允许未经确认改变总体分层结构、章节顺序、标题层级与文风

---

## 10. 一句话总结

`ARCHITECTURE.md` 在当前阶段的职责，是把 `vi_ai_core_service` 的聊天主链路从“同步一套、流式一套”升级为“services façade + chat_runtime 骨架 + context/rag/providers 能力层”的整体架构，并确保这一收敛过程不破坏已有 Phase 4~7 的上下文、流式、知识与引用能力基础。
