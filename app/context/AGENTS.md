# app/context/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `app/context/` 的职责、边界、结构约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。
执行 context 相关任务时，必须先读根目录`AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据skill `skills/python-context-capability/`执行。

---

## 2. 模块定位

`app/context/` 是系统的上下文与短期记忆管理层。  
它负责 conversation-scoped state、layered short-term memory、message lifecycle 状态的管理与持久化，不负责 chat 用例编排，也不负责知识检索实现。

当前阶段建议围绕以下职责组织：

- `models.py`：上下文核心数据模型
- `manager.py`：上下文读写与标准更新入口
- `stores/`：context store 抽象与实现
- `policies/`：selection / truncation / deterministic summary / serialization 等策略
- `memory_reducer.py`：working memory reducer（如当前仓库已有）
- `rendering.py`：working memory / rolling summary 渲染（如当前仓库已有）

---

## 3. 本层职责

1. 管理 conversation-scoped context state
2. 管理 recent raw messages
3. 管理 rolling summary
4. 管理 structured working memory
5. 管理 assistant message 生命周期相关状态
6. 管理 completed assistant turn 的标准 memory update
7. 为 request assembly 提供稳定、可序列化的上下文输入

---

## 4. 本层不负责什么

1. 不负责 HTTP 协议
2. 不负责同步或流式 chat 主用例编排
3. 不负责 provider 调用
4. 不负责 parser / chunker / embedding / index / retrieval
5. 不负责 citations 的生成与格式化
6. 不负责知识库导入链路
7. 不负责将 retrieval 结果直接落盘为短期记忆

---

## 5. 依赖边界

### 允许依赖
- `app/schemas/`（如需要共享基础契约）
- `app/observability/`

### 禁止依赖
- `app/api/`
- `app/services/`
- `app/providers/`
- `app/rag/`

### 原则
context 是会话状态层，不是业务编排层，也不是外部知识层。

---

## 6. 架构原则

### 6.1 context 只管理 short-term memory
Phase 4 已建立：
- recent raw messages
- rolling summary
- structured working memory

这些能力在 Phase 6 继续保持不变。

### 6.2 context 不等于 RAG
Phase 6 新增的 retrieval / knowledge block / citations 属于 `app/rag/` 与 `app/services/` 的协作结果，  
不属于 `app/context/` 的职责范围。

### 6.3 completed 才进入标准 memory update
必须继续保持：
- completed：走标准 update pipeline
- failed / cancelled：只更新消息状态，不进入标准 memory update
- delta：只做流式过程状态更新

### 6.4 non-completed assistant message 不进入后续装配
request assembly 仍只能使用 completed assistant message 参与后续上下文组装。

### 6.5 retrieval 不替代 short-term memory
Phase 6 中引入的知识检索是外部 grounding，不得把 retrieval 结果视为 working memory 或 rolling summary 的一部分。

---

## 7. 当前阶段能力声明

当前本轮必须保持稳定：

- conversation-scoped context
- recent raw / rolling summary / working memory 三层结构
- assistant message lifecycle 状态落盘
- completed 才触发标准 memory update
- non-completed assistant message 不参与后续 request assembly

当前本轮不要求在 `context` 中新增：

- 知识对象模型
- 文档切块
- embedding
- vector retrieval
- citation 生成

---

## 8. 修改规则

1. 不允许把 retrieval 结果直接写入 working memory
2. 不允许把 retrieved knowledge block 直接视作 rolling summary
3. 不允许让 context 依赖向量库或 embedding provider
4. 不允许以“提升记忆”为名，把外部知识与短期会话记忆混写
5. Phase 6 不在 context 层进行大规模 summary 架构改造；summary upgrade 属于后续阶段

---

## 9. Code Review 清单

1. context 是否仍保持为“会话短期状态层”？
2. 是否保持 recent raw / rolling summary / working memory 三层职责不变？
3. completed / failed / cancelled 的语义是否仍然正确？
4. non-completed assistant message 是否仍被正确排除在后续装配之外？
5. 是否没有将 retrieval 结果、citations、向量库概念引入到 context 内部模型中？
6. Phase 6 改动是否没有破坏 Phase 4 / Phase 5 已有行为？

---

## 10. 测试要求

至少覆盖：

1. conversation scope 不串
2. completed / failed / cancelled 状态正确
3. non-completed assistant message 不进入后续 request assembly
4. 在启用 retrieval 后，Phase 4 / Phase 5 原有上下文行为仍保持稳定

---

## 11. 一句话总结

`app/context/` 在 Phase 6 中继续只承担 short-term memory 与 conversation state 管理职责，不承接 retrieval、knowledge block 与 citation 相关实现，也不把外部知识增强混入会话短期记忆。