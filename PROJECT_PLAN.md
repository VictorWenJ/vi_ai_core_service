# PROJECT_PLAN.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `vi_ai_core_service` 的项目级阶段规划与路线图。  
只描述阶段目标、优先级与里程碑，不展开模块内部实现细节。

---

## 2. 项目总体目标

构建一个边界清晰、结构可扩展、具备多模型接入能力，并可承接前端实时聊天体验的 Python AI 核心服务。

当前优先建立：

- 正确的分层与文档体系
- 正确的调用链
- 稳定的上下文工程
- 可交付的流式会话后端
- 可复现的本地运行方式

---

## 3. 当前阶段建设原则

### 3.1 先做产品级会话交付，再做更复杂智能能力

当前优先保障：

- API -> services -> context/prompts/providers 主链路稳定
- app + redis 本地联调稳定
- 流式事件可被前端或 Postman 稳定消费
- cancel / timeout / failure 有清晰契约

后续再逐步引入：

- Tool calling
- RAG / 长期记忆
- Agent
- 多模态

---

## 4. 当前阶段能力声明（强约束）

当前阶段已实现并要求稳定：

- HTTP 服务化运行方式
- Phase 2 token-aware context
- Phase 3 持久化短期记忆
- Phase 4 conversation-scoped layered short-term memory
- Docker / compose 本地运行方式

当前轮次必须新增：

- **Phase 5：Streaming Chat & Conversation Lifecycle**

### 本轮必须完成

- `/chat/stream`（SSE）
- `/chat/cancel`
- assistant lifecycle 状态机
- provider streaming 归一化
- completed 才进入标准 memory update
- 流式链路测试与回归保护

### 本轮明确不做

- WebSocket
- Tool calling
- 多模态 streaming
- RAG / embedding / vector DB
- 长期记忆平台
- Agent runtime

---

## 5. 项目阶段划分

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

### 阶段六：Tool Calling / Action Layer
在流式聊天后端稳定后再做工具调用。

### 阶段七：RAG / Long-Term Memory
在短期记忆与流式交付稳定后，再做检索与跨会话记忆。

### 阶段八：Agent Runtime
最后再做 planning、多步执行与 workflow orchestration。

---

## 6. 当前轮次验收口径

本轮交付的重点不是“更聪明”，而是“更像主流 C 端 AI 应用的可交互会话后端”。

验收优先级：

1. 流式契约稳定
2. 生命周期清晰
3. 半成品输出不污染上下文
4. provider streaming 抽象不越层
5. cancel 与失败语义清晰
6. 回归测试可持续
