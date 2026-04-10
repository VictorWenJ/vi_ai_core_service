# capability-scope.md

## 1. 目的

本文件用于说明 `python-context-capability` 当前阶段的能力范围，避免 skill 在执行过程中发生边界漂移。

---

## 2. 当前能力范围

当前能力范围限定为：

- canonical context model
- conversation-scoped state
- recent raw / rolling summary / working memory
- lifecycle 字段表达
- placeholder / finalize / fail / cancel 状态治理
- store contract / codec / adapter
- context manager
- request assembly 的 non-completed assistant message 过滤支持
- context 相关测试

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- HTTP 路由
- SSE 文本协议
- chat 主链路编排
- retrieval / chunking / embedding / index
- citation 生成
- 长期记忆平台
- 审批流
- Case Workspace
- Agent Runtime

---

## 4. 当前默认技术基线

- conversation scope：`session_id + conversation_id`
- layered short-term memory：recent raw + rolling summary + working memory
- lifecycle：created / streaming / completed / failed / cancelled
- only completed assistant message 进入标准 memory update
- non-completed assistant message 默认不参与 request assembly

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。