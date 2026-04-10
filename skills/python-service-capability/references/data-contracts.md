# data-contracts.md

## 1. 目的

本文件用于说明 `app/services/` 当前会消费或产出的核心数据契约。

---

## 2. 输入契约

当前 services 会直接消费两类输入：

- `app/api/schemas/chat.py` 中的用户请求模型
- `app/schemas/` 中的 `LLMRequest`

---

## 3. 输出契约

当前 services 主要输出：

- 同步路径：`ChatServiceResult`（含 `LLMResponse + citations + retrieval_trace`），由 API 再转为 `ChatResponse`
- 流式路径：canonical event dict，再由 API 序列化为 SSE

---

## 4. request assembly contract

`ChatRequestAssembler` 当前必须保证：

- system prompt 在前
- knowledge block 在 working memory 前
- working memory 在 rolling summary 前
- recent raw messages 在用户输入前
- user prompt 最后入列

---

## 5. 流式 completed contract

当前 `response.completed` 相关数据至少包含：

- request_id
- assistant_message_id
- status
- finish_reason
- usage（按配置）
- latency_ms
- trace（按配置）
- citations

---

## 6. 原则

- services 不直接发明新的对外 contract
- 未落地的 Phase 6 字段不得写入当前 contract
- contract 变更必须同步补测试
