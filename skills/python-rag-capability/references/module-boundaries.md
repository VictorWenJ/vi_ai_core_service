# module-boundaries.md

## 1. 目的

本文件用于说明 `app/rag/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

### rag 负责
- 知识实现
- retrieval
- citation-ready 数据

### services 负责
- chat / stream 主链路编排
- request assembly 时机
- 完成态收口

---

## 3. 与 context 的边界

context 负责 short-term memory；
rag 负责 external knowledge grounding。
retrieval 结果不是 working memory，也不是 rolling summary。

---

## 4. 与 providers 的边界

如后续需要 embedding，可通过 providers 接入；
rag 不直接承担 chat provider 主链路。

---

## 5. 与 api 的边界

API 不直接访问 rag 内部实现。
RAG 对外暴露的结果由 services / API 再进行编排与输出。

---

## 6. 结论

`app/rag/` 是内部知识与检索子域。当前代码尚未落地运行时代码，后续实现也不得替代 services、context、providers 或 api 的职责。
