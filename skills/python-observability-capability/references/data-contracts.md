# data-contracts.md

## 1. 目的

本文件用于说明 `app/observability/` 中关键观测字段的最小契约要求。

---

## 2. request 相关字段

至少应能表达：

- request_id
- session_id
- conversation_id
- provider
- model
- status
- latency_ms

---

## 3. stream 相关字段

至少应能表达：

- request_id
- assistant_message_id
- streaming
- stream_event_count
- status
- finish_reason
- error_code

---

## 4. retrieval 相关字段

至少应能表达：

- knowledge_retrieval_enabled
- retrieval_query
- retrieval_top_k
- retrieval_filters
- retrieved_chunk_count
- retrieved_document_ids
- embedding_model
- vector_index_backend
- citation_count

---

## 5. 原则

- 字段应以事实型为主
- 字段必须 JSON-safe
- 不应直接记录复杂对象
- 不应把原始大段正文作为标准观测字段