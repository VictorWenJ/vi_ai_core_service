# module-boundaries.md

## 1. 目的

本文件用于说明 `app/api/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

api 负责接入与返回；
services 负责编排与生命周期收口。

---

## 3. 与 schemas 的边界

API 层的 request / response / SSE event 由 `app/api/schemas/` 承载；
`app/schemas/` 当前负责内部 `LLM*` 契约。

---

## 4. 与 context / rag / providers 的边界

API 不直接访问 context manager、rag 实现或 provider SDK。
这些能力都必须经由 services 暴露。

---

## 5. 结论

`app/api/` 是协议接入层，不是业务编排层，也不是当前代码中的 retrieval / citation 实现层。
