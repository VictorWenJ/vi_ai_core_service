# PROJECT_PLAN.md

> 更新日期：2026-04-12

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

这些属于后续阶段再逐步推进的内容。:contentReference[oaicite:1]{index=1}

---

## 4. 当前阶段主任务（强约束）

当前轮次为：

**Phase 7：RAG Evaluation + Offline Build Foundation**

### 前置已落地（当前代码事实）

截至当前代码基线，以下内容已在仓库中落地：

- `app/rag/` 内部子域运行时代码
- 知识 ingest 与 retrieval 最小闭环
- retrieval 接入 chat request assembly
- `/chat` 返回 citations
- `/chat_stream` 的 completed 事件返回 citations
- retrieval trace 与测试回归保护

### 本轮目标

当前轮次不再扩张新的对外能力面，而是为已落地的 Phase 6 建立可持续优化能力。
本轮应完成：

- RAG 黄金评估集与标签结构
- retrieval / citation / answer 三层评估执行器
- 离线构建元数据与构建批次语义
- 增量构建 / 局部重建的最小能力边界
- 基础质量门禁与构建统计

### 本轮默认技术方向

- 向量库：Qdrant
- 相似度：Cosine
- embedding：单一文本 embedding 基线
- chunking：结构感知 + token-aware + overlap
- 评估集：人工黄金集优先，规则扩展为辅
- RAG：继续作为知识 grounding，不承接长期记忆

### 本轮明确不做

- 独立 RAG 微服务
- 长期记忆平台
- Agentic RAG
- Tool Calling / Agent Runtime
- 审批流 / Case Workspace
- 多模态检索主链路
- 全量知识运营后台

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

### 阶段八：Summary & Compression Upgrade
在评估与离线构建基础具备后，升级 conversation summary、长文档摘要与结构化压缩能力，解决当前“按字符切分、摘要质量弱”的问题。

### 阶段九：Tool Calling / Action Layer
在知识 grounding 与评估体系稳定后，再做工具调用与基础 workflow 执行层。

### 阶段十：Case Workspace / Business Scenario MVP
结合具体业务场景，建设案件工作台、结构化业务对象与最小业务闭环。

### 阶段十一：Agent Runtime
最后再做 planning、多步执行与 workflow orchestration。

---

## 7. 当前阶段能力声明

当前阶段已实现并要求保持稳定：

- HTTP 服务化运行方式
- Phase 2 token-aware context
- Phase 3 持久化短期记忆
- Phase 4 conversation-scoped layered short-term memory
- Phase 5 Streaming Chat & Conversation Lifecycle
- Docker / compose 本地运行方式

当前代码事实补充：

- `app/rag/` 已落地治理文档 + 运行时代码
- retrieval 主链路已在代码中落地并支持可降级
- `/chat` 与 `/chat_stream` completed 已返回 citations
- retrieval observability 与对应测试已落地

当前阶段新增（本轮已落地）：

- RAG 黄金评估集与标签结构（query / retrieval / citation / answer）
- retrieval / citation / answer benchmark runner 与结果落盘输出
- 离线构建元数据与构建批次语义（build/version/strategy/model 版本信息）
- 增量构建 / 局部重建约束（manifest + content hash）
- 基础质量门禁与构建统计（failure ratio、empty chunk ratio、upsert 统计）

当前阶段不得因为引入 RAG 而破坏：

- 同步 chat 主链路
- 流式 chat 主链路
- Phase 4 short-term memory 语义
- Phase 5 message lifecycle 语义

---

## 8. 当前轮次验收口径

本轮交付的重点不是继续扩张对外聊天能力，而是让已落地的 RAG 具备可评估、可比较、可演进的工程基础。
截至当前代码基线，本轮 Phase 7 验收口径应聚焦：

验收优先级：

1. 黄金评估集与标签结构可落地
2. retrieval / citation / answer benchmark 可执行
3. 离线构建具备 build/version 元数据
4. 增量构建与局部重建边界清晰
5. 基础质量门禁与构建统计可回归
6. 不破坏 Phase 4、Phase 5 与 Phase 6 已有能力

---

## 9. 阶段推进约束

1. 当前阶段仅推进 Phase 7 范围内内容
2. 不得以 Phase 7 名义提前引入 Tool Calling、长期记忆平台、审批流、Case Workspace、Agent Runtime 或多模态主链路
3. Summary Upgrade 属于后续阶段，不在本轮混做
4. 后续每一阶段都必须保持与上一阶段主链路兼容，不允许推倒重来

---

## 10. 一句话总结

`PROJECT_PLAN.md` 在当前阶段的职责，是作为项目级路线图文件，明确 `vi_ai_core_service` 的阶段递进顺序、当前轮次目标、当前阶段边界与验收口径，确保项目按既定主线逐步演进，而不是在实现过程中发生阶段漂移。
