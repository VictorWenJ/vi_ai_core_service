# PROJECT_PLAN.md

> 更新日期：2026-04-13

## 1. 文档定位

本文件定义 `vi_ai_core_service` 的项目级阶段规划、路线图、阶段目标与验收口径。

本文件只负责回答以下问题：

- 当前项目整体要往哪里走
- 当前阶段是什么
- 当前阶段做什么、不做什么
- 后续阶段如何递进
- 当前轮次的验收重点是什么

本文件不负责：

- 仓库级协作规则
- 文档维护规则
- 模块边界细节
- 代码审查细则
- 具体实现策略

这些内容分别由：

- `AGENTS.md`
- `ARCHITECTURE.md`
- `CODE_REVIEW.md`
- 模块 `AGENTS.md`
- 对应 `skill`

承担。

---

## 2. 项目定位

`vi_ai_core_service` 是 VI AI Project 的 Python AI 核心服务。
它的目标不是做一个简单的本地 demo，而是逐步构建一个对标主流 C 端企业级 AI 应用的核心能力后端。

当前项目长期路线保持不变：

1. 先完成 LLM 核心能力与上下文工程
2. 再补齐流式会话交付能力
3. 再推进知识增强、引用与可追溯能力
4. 再逐步扩展到 tool calling、长期记忆、Agent Runtime、多模态等能力
5. 最终形成可承接真实产品场景的 AI Core Service 底座

---

## 3. 当前项目范围

当前项目仍聚焦 Python AI Core Service 主线，优先建立：

- 正确的分层与文档体系
- 正确的调用链
- 稳定的上下文工程
- 可交付的流式会话后端
- 可引用知识的检索增强能力运行时闭环
- 可复现的本地运行方式

当前阶段不把重点放在：

- 审批流
- Case Workspace
- 多租户大系统
- 独立知识平台
- 完整 Agent 平台
- 多模态主链路

这些属于后续阶段再逐步推进的内容。

---

## 4. 当前阶段主任务（强约束）

当前轮次为：

**RAG 持久化控制面升级（Post-Phase 7 主线）**

### 前置已落地（当前代码事实）

截至当前代码基线，以下内容已在仓库中落地：

- `app/rag/` 内部子域运行时代码
- 知识 ingest 与 retrieval 最小闭环
- retrieval 接入 chat request assembly
- `/chat` 返回 citations
- `/chat_stream` 的 completed 事件返回 citations
- Phase 7 评估执行器、离线构建基础与 Internal Console v1 已形成第一轮闭环
- 当前 RAG 控制面仍以进程内 `RAGControlState` 为真相源

### 本轮目标

当前轮次不扩张新的对外能力面，而是把已落地的 Knowledge + Citation Layer 与 Phase 7 工程基础升级为正式持久化控制面。
本轮应完成：

- 从内存控制面升级为：
  - MySQL 控制面
  - 文件存储内容面
  - Qdrant 向量数据面
- 文档、版本、构建任务、chunk 元数据正式落盘
- evaluation run / case 全量持久化
- 删除 `RAGControlState` 正式控制面职责
- 引入 `app/db/` 与 `app/rag/repository/` / `app/rag/content_store/` 分层
- 在尽量不破坏现有 API contract 的前提下完成底层替换

### 本轮默认技术方向

- 控制面数据库：MySQL
- 向量数据库：Qdrant
- 内容存储：本地文件系统优先，保留后续对象存储替换空间
- embedding：单一文本 embedding 基线
- chunking：结构感知 + token-aware + overlap
- 评估结果：run / case 全量落盘
- 向量查看：按 `vector_point_id` 从 Qdrant 回读，而不是冗余写入 MySQL

### 本轮明确不做

- 异步任务系统
- 审计平台
- 多租户 / 权限体系
- 复杂对象存储平台化
- Tool Calling / Agent Runtime
- 独立 RAG 微服务
- 用 MySQL 代替 Qdrant
- 跨存储强分布式事务体系

---


## 5. 阶段规划原则

### 5.1 先做产品级会话交付，再做知识 grounding
当前项目已经完成：
- API -> services -> context/prompts/providers 主链路稳定化
- streaming / cancel / timeout / failure 契约
- conversation-scoped layered short-term memory
- SSE 事件可被前端或调试工具消费

在此基础上，当前阶段再引入：
- Knowledge + Citation Layer

### 5.2 先做受控知识增强，再做更重业务流程
当前 Phase 6 先建设：

- 文档接入
- 切块
- embedding
- 向量索引
- retrieval
- citation

后续再逐步引入：

- Case Workspace
- Human Review / Approval
- 多租户权限
- 业务工作台

### 5.3 先做最小闭环，再做平台化扩展
Phase 6 的重点是：
- 让回答开始具备知识依据与引用能力

Post-Phase 7 的重点是：
- 先把控制面正式持久化
- 先让 build / evaluation / inspector 具备可恢复、可追溯基础

不是：
- 一步到位做知识平台
- 一步到位做长期记忆系统
- 一步到位做 Agentic RAG

---

## 6. 项目阶段划分

### 阶段一：文档治理与结构固化
建立根文档、模块文档、skill 协作链路。

### 阶段二：基础主链路稳定化
打通 API -> services -> prompts/context/providers。

### 阶段三：Provider 体系增强
稳定统一 provider 抽象与 registry。

### 阶段四：Prompt 与 Context 能力增强
完成 Phase 1~4 上下文工程，建立 layered short-term memory。

### 阶段五：Streaming Chat & Conversation Lifecycle
在保持同步聊天可用前提下，引入 SSE、message lifecycle、cancel/timeout/error 收口语义，以及与 Phase 4 兼容的流式会话交付链路。

### 阶段六：Knowledge + Citation Layer
在保持 chat、streaming、context memory 主链路稳定的前提下，引入内部 `rag` 子域，完成知识导入、切块、embedding、向量检索、citation-aware request assembly 与 response citation 契约。

### 阶段七：RAG Evaluation + Offline Build Foundation
在 Knowledge + Citation 主链路落地后，补齐 RAG 黄金评估集、benchmark runner、离线构建元数据、增量构建与基础质量门禁。

### 阶段八：RAG Control Plane Persistence Upgrade
在 Phase 7 基础上，把 RAG 从“内存控制面 + Qdrant 数据面”升级为“MySQL 控制面 + 文件存储内容面 + Qdrant 向量数据面”，并让 build / evaluation / inspector 正式落盘。

### 阶段九：Tool Calling / Action Layer
在 RAG 控制面正式持久化、Internal Console 与评估链路稳定后，再做工具调用与基础 workflow 执行层。

### 阶段十：Workflow / Agent Runtime Foundation
在 Tool Calling Foundation 落地后，再建设可循环、可重规划、可持久化的 workflow / agent runtime 基础层。

### 阶段十一：Summary & Compression Upgrade
在工具调用与 workflow 基础具备后，再升级 conversation summary、长文档摘要与结构化压缩能力，解决当前“摘要质量弱、状态提炼粗”的问题。

### 阶段十二：Case Workspace / Business Scenario MVP
结合具体业务场景，建设案件工作台、结构化业务对象与最小业务闭环。

### 阶段十三：Production Hardening / Governance Upgrade
最后再做权限、租户、配置治理、成本治理、线上评估与更完整的工程化加固。

---


## 7. 当前阶段能力声明

当前阶段已实现并要求保持稳定：

- HTTP 服务化运行方式
- Phase 2 token-aware context
- Phase 3 持久化短期记忆
- Phase 4 conversation-scoped layered short-term memory
- Phase 5 Streaming Chat & Conversation Lifecycle
- Phase 6 Knowledge + Citation Layer
- Phase 7 RAG Evaluation + Offline Build Foundation
- Docker / compose 本地运行方式

当前代码事实补充：

- `app/rag/` 已落地治理文档 + 运行时代码
- retrieval 主链路已在代码中落地并支持可降级
- `/chat` 与 `/chat_stream` completed 已返回 citations
- Internal Console v1 已具备 Chat Playground、Knowledge Ingest、Chunk / Vector Inspector、Evaluation Dashboard、Runtime / Config View 页面
- 当前控制面仍以进程内 `RAGControlState` 为正式事实来源

当前阶段新增（本轮目标）：

- MySQL 控制面正式落地
- 文件存储内容面正式落地
- `repository` 与 `content_store` 分层正式落地
- `build_tasks` / `build_documents` / `chunks` 正式落盘
- `evaluation_runs` / `evaluation_cases` 全量持久化
- Runtime / Inspector 查询从内存切换到持久化控制面

当前阶段不得因为控制面升级而破坏：

- 同步 chat 主链路
- 流式 chat 主链路
- Phase 4 short-term memory 语义
- Phase 5 message lifecycle 语义
- Phase 6 citation 契约
- Phase 7 evaluation / offline build 基础能力

---


## 8. 当前轮次验收口径

本轮交付的重点不是新增聊天玩法，而是把已落地的 RAG 能力升级为正式可恢复、可追溯、可持续演进的持久化控制面。
当前轮次验收口径应聚焦：

验收优先级：

1. `RAGControlState` 退出正式控制面角色
2. 文档上传后可落 `documents` 与 `document_versions`
3. build 能从 MySQL + 内容存储读取输入并生成 `build_tasks / build_documents / chunks`
4. 向量继续写入 Qdrant，向量详情可按 `vector_point_id` 回读
5. evaluation run / case 全量持久化
6. Runtime / Inspector 查询改为基于持久化控制面
7. 不破坏 Phase 4、Phase 5、Phase 6 与 Phase 7 已有能力

---


## 9. 阶段推进约束

1. 当前阶段仅推进 RAG 控制面正式持久化范围内内容
2. 不得以本轮名义提前引入异步任务系统、审计平台、多租户 / 权限体系、复杂对象存储平台化
3. Tool Calling / Workflow / Agent Runtime 属于后续阶段，不在本轮混做
4. Summary Upgrade 与 Case Workspace 属于后续阶段，不在本轮混做
5. API 命名、控制面服务命名与前后端契约统一属于当前收口工作，应在不破坏既有行为的前提下尽快完成
6. 后续每一阶段都必须保持与上一阶段主链路兼容，不允许推倒重来

---


## 10. 一句话总结

`PROJECT_PLAN.md` 在当前阶段的职责，是作为项目级路线图文件，明确 `vi_ai_core_service` 的阶段递进顺序、当前轮次目标、当前阶段边界与验收口径，确保项目按既定主线逐步演进，而不是在实现过程中发生阶段漂移。
