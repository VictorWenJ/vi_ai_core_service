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
- metadata

---

## 3. KnowledgeChunk

至少应能表达：

- chunk_id
- document_id
- chunk_text
- chunk_index
- token_count
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
- metadata

---

## 6. 原则

- 上述对象当前仍属待实现目标
- citation 必须来自 retrieval 结果
- 不直接把内部 SDK 对象透传为模型
