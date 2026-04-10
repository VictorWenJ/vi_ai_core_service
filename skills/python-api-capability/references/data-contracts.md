# data-contracts.md

## 1. 目的

本文件用于说明 `app/api/` 中关键数据契约的最小要求。

---

## 2. ChatRequest / ChatResponse

必须能表达：

- 用户输入
- 会话标识
- provider / model 选择（如当前项目支持）
- stream 标记（如当前项目支持）
- answer
- usage / finish_reason（如当前契约已有）
- citations（Phase 6）

---

## 3. ChatStreamRequest

必须能表达：

- 用户输入
- 会话标识
- stream_options
- 其他与流式会话必要相关的字段

---

## 4. SSE 事件契约

至少应包含：

- `response.started`
- `response.delta`
- `response.completed`
- `response.error`
- `response.cancelled`
- `response.heartbeat`

要求：

- event name 稳定
- payload 结构稳定
- completed 可附带 citations
- delta 不附带 citations

---

## 5. Cancel / Reset 契约

### cancel
必须能表达：
- request_id
- assistant_message_id（如当前实现支持）
- session / conversation 信息

### reset
必须能表达：
- session_id
- conversation_id（可选）
- reset 结果

---

## 6. 原则

- 不允许无 schema 追加对外字段
- 不允许泄漏底层实现细节
- citations 是对外可展示结构，不是内部 retrieval 对象透传