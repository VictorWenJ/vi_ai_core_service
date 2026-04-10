# data-contracts.md

## 1. 目的

本文件用于说明 `app/api/` 当前对外契约的最小要求。

---

## 2. `/chat`

当前至少应能表达：

- user_prompt
- provider / model 覆盖
- temperature / max_tokens 覆盖
- session_id / conversation_id / request_id
- metadata
- 返回 `content / provider / model / usage / finish_reason / metadata / raw_response / citations`

---

## 3. `/chat_stream`

当前至少应能表达：

- `response.started`
- `response.delta`
- `response.completed`
- `response.error`
- `response.cancelled`
- `response.heartbeat`
- `response.completed` 中包含 `citations`

---

## 4. cancel / reset / health

当前至少应能表达：

- cancel 身份字段校验
- reset scope
- health 基础探活

---

## 5. 原则

- citations 仅通过稳定 schema 透传
- 不暴露底层 Qdrant / embedding / SDK 细节
- contract 变更必须同步补测试
