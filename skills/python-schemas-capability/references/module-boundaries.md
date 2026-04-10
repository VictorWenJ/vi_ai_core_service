# module-boundaries.md

## 1. 目的

本文件用于说明 `app/schemas/` 与其他模块之间的边界关系。

---

## 2. 与 api 的边界

`app/api/schemas/` 负责对外 request / response / SSE 事件契约；
`app/schemas/` 负责内部 `LLM*` canonical contract。

---

## 3. 与 services 的边界

services 消费 `LLM*` 契约进行编排；
services 不应各自发明新的内部 canonical contract。

---

## 4. 与 providers 的边界

providers 输出 canonical result / chunk；
`app/schemas/` 定义这些 canonical 对象如何表达。

---

## 5. 与 rag 的边界

当前 `app/schemas/` 不承接 rag 的 citation / retrieval 模型。
若未来新增，必须先明确是否属于内部 canonical contract。

---

## 6. 结论

`app/schemas/` 是内部规范化 LLM 契约层，不是 API 契约层，也不是当前代码中的 RAG 契约层。
