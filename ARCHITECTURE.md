# ARCHITECTURE.md

> 更新日期：2026-04-12

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
- 负责 retrieval service、knowledge block 渲染与 citation 结构
- 作为 Knowledge + Citation Layer 的内部实现域

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

1. 请求进入 `/chat`
2. API 校验并委托给 service
3. service 调用 `request_assembler`
4. assembler 按固定顺序装配：
   - system prompt
   - knowledge block
   - working memory block
   - rolling summary block
   - recent raw messages
   - current user input
5. service 调用 provider 非流式请求
6. provider 返回归一化结果
7. service 在有状态会话下执行 completed 态 context update
8. API 输出 `ChatResponse`

当前代码事实：

- 当前同步链路已支持 retrieval、knowledge block 与 citations

### 6.2 流式聊天链路

1. 请求进入 `/chat_stream`
2. API 建立 SSE 响应
3. service 生成 `request_id` 与 `assistant_message_id`
4. service 写入 user message 与 assistant placeholder
5. API 先输出 `response.started`
6. service 调用 provider 流式请求
7. provider 输出 canonical stream chunk
8. service 推进 lifecycle 并生成 canonical stream event
9. API 将 event 序列化为 SSE
10. 正常完成时：
   - service 写回 completed assistant message
   - service 执行 Phase 4 标准 context update
   - API 输出 `response.completed`
- `response.completed` 当前可附带 usage / latency / trace / citations
11. 异常或取消时：
   - service 写回 `failed` / `cancelled`
   - 不进入标准 memory update
   - API 输出 `response.error` 或 `response.cancelled`

当前代码事实：

- 当前流式链路在 completed 阶段返回 citations，delta 阶段不返回 citation 增量

### 6.3 知识导入链路

当前代码已实现知识导入最小链路：

1. parser（raw text / `.txt` / `.md`）
2. cleaner
3. 结构感知 + token-aware + overlap chunking
4. embedding provider 抽象调用
5. vector index upsert（in-memory / qdrant 封装）

### 6.4 离线构建链路

当前阶段离线构建链路应在不破坏在线主链路的前提下持续增强：

1. 文档导入进入 `app/rag/ingestion/`
2. parser / cleaner / chunker 完成标准化处理
3. embedding provider 生成向量表达
4. index 写入向量存储
5. 构建产物补充 `build_id`、`version_id`、`chunk_strategy_version`、`embedding_model_version` 等元数据
6. 构建阶段执行最小质量门禁与统计输出

当前代码事实补充：

- `KnowledgeIngestionPipeline` 已提供 `build_documents` 离线构建入口
- 构建链路已支持 build metadata 透传至 chunk metadata
- 增量/局部重建当前通过 manifest + content hash + force document ids 约束
- 构建统计与质量门禁当前已覆盖 failure ratio、empty chunk ratio、upsert 一致性

### 6.5 评估链路

当前阶段评估链路应围绕已落地的 Phase 6 主链路构建：

1. 使用固定 query set 与标签集作为输入
2. 分别运行 retrieval、citation、answer 三层评估
3. 输出结构化 benchmark 结果
4. 不允许让评估 runner 反向侵入在线 chat / stream 主链路

当前代码事实补充：

- `app/rag/evaluation/` 已提供数据集模型、runner 与结构化结果落盘能力
- 评估执行仅消费 `RAGRuntime`，不侵入在线 `/chat`、`/chat_stream` 主链路

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
- `app/rag/` 是当前唯一知识与检索实现域
- 若后续需要 ingestion worker，可作为同仓库独立运行角色演进
- 当前阶段不额外建设独立 knowledge service

当前代码事实：

- `app/rag/` 已形成知识与检索实现代码

### 8.2 相似度与索引约束
- 默认向量库基线：Qdrant
- 默认相似度：Cosine
- 当前阶段不自研 ANN 算法
- 当前阶段只做文本 embedding 主链路

### 8.3 Citation 约束
- 当前代码基线中 citation 已进入对外响应契约
- `/chat` 返回完整 citations（为空时返回空数组）
- `/chat_stream` 仅在完成事件返回 citations
- delta 阶段不返回 citation 增量

### 8.4 降级约束
- retrieval 失败时，系统可退化为无知识增强聊天
- ingestion 失败不应拖垮在线 chat 主链路
- embedding/index 故障需可定位、可回归、可审查

### 8.5 Phase 7 约束
- 当前轮次允许增强离线构建与评估，不允许把在线主链路改造成实验脚手架
- 评估 runner 与评估数据集应服务于现有 RAG 主链路，不得重新定义新的回答契约
- 构建批次、版本、质量门禁等能力应围绕 `app/rag/` 与 `tests/` 组织，不得提前扩张成独立知识平台

### 8.6 架构边界约束
当前阶段不得以 Phase 7 名义扩展为：

- 独立 RAG 微服务
- Tool Calling / Agent Runtime
- 长期记忆平台
- 审批流
- Case Workspace
- 多模态检索主链路

---

## 9. 修改规则

1. 不允许在本文件中混入仓库级协作规则
2. 不允许在本文件中混入项目阶段路线图细节
3. 不允许在本文件中混入 code review 清单
4. 不允许把模块级实现细节写成总体架构要求
5. 不允许未经确认改变总体分层结构、章节顺序、标题层级与文风

---

## 10. 一句话总结

`ARCHITECTURE.md` 在当前阶段的职责，是作为项目总体架构文件，明确 `vi_ai_core_service` 的分层结构、依赖方向，以及当前已落地的同步 / 流式 / Knowledge + Citation 主链路，以及当前阶段的离线构建与评估支撑链路，确保系统在后续迭代中仍保持整体分层清晰、职责稳定、演进可控。
