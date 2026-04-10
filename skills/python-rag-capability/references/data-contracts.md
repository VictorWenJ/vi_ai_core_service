# data-contracts.md

## 1. 目的

本文件用于说明 `app/rag/` 后续开始实现时核心对象的最小契约要求。

---

## 2. KnowledgeDocument

至少应能表达：

- document_id
- title
- source_type
- content
- origin_uri
- file_name
- jurisdiction
- domain
- tags
- effective_at
- updated_at
- visibility
- metadata

---

## 3. KnowledgeChunk

至少应能表达：

- chunk_id
- document_id
- chunk_text
- chunk_index
- token_count
- embedding_model
- metadata

---

## 4. RetrievedChunk

至少应能表达：

- chunk_id
- document_id
- text
- score
- title
- origin_uri
- source_type
- jurisdiction
- domain
- effective_at
- updated_at
- metadata

---

## 5. Citation

至少应能表达：

- citation_id
- document_id
- chunk_id
- title
- snippet
- origin_uri
- source_type
- updated_at
- metadata

---

## 6. 原则

- 上述对象当前已在代码中落地
- citation 必须来自 retrieval 结果
- 不直接把内部 SDK 对象透传为模型
