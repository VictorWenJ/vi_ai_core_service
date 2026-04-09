# app/context/AGENTS.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `app/context/` 的职责边界、演进约束、交付门禁与 review 标准。  
执行 context 相关任务时，必须先读根目录四文档，再读本文件，再执行 `skills/python-context-capability/`。

---

## 2. 模块定位

`app/context/` 是系统的短期会话上下文与短期记忆治理层。  
它负责 provider-agnostic 的 conversation-scoped 状态表示、策略执行、store 抽象与会话生命周期管理。

当前已完成：

- Phase 2：token-aware context pipeline
- Phase 3：持久化短期记忆
- Phase 4：layered short-term memory

当前阶段必须兼容：

- **Phase 5：Streaming Chat & Conversation Lifecycle**

---

## 3. 本层职责

1. 定义 canonical context models
2. 定义并实现 store contract 与 store adapter
3. 通过 `ContextManager` 暴露统一 façade
4. 管理 recent raw / rolling summary / working memory
5. 管理 message lifecycle 相关状态字段
6. 在 Phase 5 中明确：non-completed assistant message 不进入标准上下文装配

---

## 4. 本层不负责什么

1. 不负责 HTTP 路由
2. 不负责流式业务编排
3. 不负责 provider payload 协议
4. 不负责 SSE 文本协议
5. 不负责 RAG、长期记忆、向量检索、用户画像
6. 不负责外部事件顺序决策

---

## 5. 默认行为与 Phase 5 约束

默认 policy pipeline 顺序固定为：

`token-aware selection -> token-aware truncation -> deterministic summary -> serialization`

### 5.1 layered memory 结构不变
Phase 5 不改变 Phase 4 的 recent raw / rolling summary / working memory 结构。

### 5.2 lifecycle 必须进入 canonical context model
`ContextMessage` 或等价模型应能表达：

- `message_id`
- `role`
- `content`
- `status`
- `created_at`
- `updated_at`
- `finish_reason`
- `error_code`
- `metadata`

### 5.3 non-completed assistant message 默认不参与标准 request assembly
以下状态默认不参与：

- `created`
- `streaming`
- `failed`
- `cancelled`

### 5.4 delta 阶段不得触发标准 memory update
只有 completed 后才执行标准 `update_after_chat_turn`。

---

## 6. 当前阶段能力声明

本轮必须新增或补强：

- message lifecycle 状态表示
- placeholder / finalize / fail / cancel 的 manager/store 支持
- request assembly 默认忽略 non-completed assistant message
- 流式链路下 completed 与 non-completed 的不同收口规则

当前不要求落地：

- 长期记忆
- RAG / semantic recall
- 多会话记忆排序
- 实时协作状态同步系统

---

## 7. 修改规则

1. 不允许 context 层依赖 API route 或 StreamingResponse
2. 不允许 context 层依赖 provider SDK
3. 不允许把流式事件顺序逻辑写进 context 层
4. 不允许在 delta 阶段执行标准 layered memory 更新
5. `ContextWindow.messages` 仍只表示 recent raw messages

---

## 8. Code Review 清单

1. canonical model 是否清晰表达 message lifecycle？
2. store codec 是否正确序列化 / 反序列化 lifecycle 字段？
3. non-completed assistant message 是否默认被过滤？
4. completed 态是否才进入标准 memory update？
5. 是否破坏 Phase 2 policy pipeline？
6. 是否把流式业务编排错误地下沉到 context 层？

---

## 9. 测试要求

至少覆盖：

1. conversation scope 隔离
2. lifecycle 字段序列化 / 反序列化
3. placeholder -> completed / failed / cancelled
4. non-completed assistant message 不参与 request assembly
5. completed 才触发 layered memory 更新
6. reset_session / reset_conversation 在持久化 store 上行为正确

---

## 10. 一句话总结

`app/context/` 在 Phase 5 中不是流式交付层，而是为流式交付提供安全、稳定的 conversation-scoped 状态模型和 completed 态记忆收口规则。
