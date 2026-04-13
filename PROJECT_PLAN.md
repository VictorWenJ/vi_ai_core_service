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
- 面向后续升级的统一 chat runtime 骨架

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

**Chat Runtime 骨架收敛（统一 `chat` / `chat_stream` 主链路）**

### 前置已落地（当前代码事实）

截至当前代码基线，以下内容已在仓库中落地：

- `app/rag/` 内部子域运行时代码
- 知识 ingest 与 retrieval 最小闭环
- retrieval 接入 chat request assembly
- `/chat` 返回 citations
- `/chat_stream` 的 completed 事件返回 citations
- Phase 7 评估执行器、离线构建基础与 Internal Console v1 已形成第一轮闭环
- `ChatService` 与 `StreamingChatService` 共同承接聊天主链路，但核心业务语义已开始双轨分布

### 本轮目标

当前轮次不扩张新的对外能力面，而是把已落地的同步与流式 chat 主链路收敛为统一执行骨架。
本轮应完成：

- 新增 `app/chat_runtime/`
- 显式定义 `DEFAULT_CHAT_WORKFLOW`
- 显式定义 lifecycle hooks 与 step hooks
- 统一 `chat` / `chat_stream` 的 scope 规范化、retrieval、request assembly、provider invoke、context 收口、trace 收口
- 让 `ChatService` / `StreamingChatService` 降级为 façade
- 为未来 tool calling、runtime skill、model routing 预留接口位，但本轮不实现这些能力

### 本轮默认技术方向

- 模块命名：`chat_runtime`
- workflow 形式：数组配置
- hook 形式：事件数组配置
- skill 形式：引用数组预留
- stream 与 sync 共用同一套业务语义
- 不改变现有 `/chat` 与 `/chat_stream` 对外 contract

### 本轮明确不做

- Tool Calling / Action Layer
- Agent Runtime
- Planner / Executor
- runtime policy center
- runtime skill loader
- 多 Agent
- 前端适配
- 长期记忆平台

---

## 5. 阶段规划原则

### 5.1 先统一 chat core，再扩能力面
当前项目已经完成：
- API -> services -> prompts/context/providers 主链路稳定化
- streaming / cancel / timeout / failure 契约
- conversation-scoped layered short-term memory
- SSE 事件可被前端或调试工具消费
- retrieval / citation 基础接入

在此基础上，当前阶段先建设：
- Chat Runtime 骨架

### 5.2 先收敛执行骨架，再推进执行型能力
当前轮次先建设：

- workflow 显式配置
- sync / stream 统一执行语义
- lifecycle hook 插槽
- trace 收口

后续再逐步引入：

- Tool Calling
- model routing
- runtime skill
- Agent workflow

### 5.3 先做最小闭环，再做平台化扩展
本轮重点是：
- 让聊天主链路有统一执行骨架
- 让未来能力有清晰落点

不是：
- 一步到位做通用 workflow 平台
- 一步到位做 Agent Runtime
- 一步到位做插件系统

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

### 阶段八：Chat Runtime Skeleton Upgrade
在 Phase 7 基础上，先把 `chat` 与 `chat_stream` 双编排收敛为统一 chat runtime，为后续执行型能力预留骨架。

### 阶段九：RAG Control Plane Persistence Upgrade
在 chat runtime 骨架稳定后，再把 RAG 从“内存控制面 + Qdrant 数据面”升级为“MySQL 控制面 + 文件存储内容面 + Qdrant 向量数据面”。

### 阶段十：Tool Calling / Action Layer
在 chat runtime 与 RAG 控制面具备稳定底座后，再做工具调用与基础执行层。

### 阶段十一：Workflow / Agent Runtime Foundation
在 Tool Calling Foundation 落地后，再建设可循环、可重规划、可持久化的 workflow / agent runtime 基础层。

### 阶段十二：Summary & Compression Upgrade
在工具调用与 workflow 基础具备后，再升级 conversation summary、长文档摘要与结构化压缩能力。

### 阶段十三：Case Workspace / Business Scenario MVP
结合具体业务场景，逐步引入更完整的执行型产品能力。

---

## 7. 当前轮次验收口径

当前轮次完成后，至少应满足：

1. `app/chat_runtime/` 已新增并承担 chat core 统一执行骨架。
2. `DEFAULT_CHAT_WORKFLOW` 已显式存在，且能表达同步与流式共用主步骤。
3. lifecycle hook 与 step hook 已具备最小可配置能力。
4. `ChatService` 与 `StreamingChatService` 已降级为 façade / 交付入口。
5. `/chat` 与 `/chat_stream` 对外 contract 不回退。
6. `ChatRequestAssembler` 仍是唯一装配中枢。
7. citations 仍仅来自 retrieval 结果。
8. 已补同步、流式、hook、trace 相关测试。

---

## 8. 一句话总结

当前项目本轮的唯一主任务，不是继续扩能力面，而是先把 `chat` 与 `chat_stream` 收敛成统一的 chat runtime 骨架，让会话后端从“功能可用”升级到“主链路清晰、可持续演进”。
