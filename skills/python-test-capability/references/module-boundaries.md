# module-boundaries.md

## 1. 目的

本文件用于说明 `tests/` 与其他模块之间的边界关系。

---

## 2. 与 api / services 的边界

tests 负责验证 API contract 与 services 编排语义；
tests 不负责实现 route 或 service。

---

## 3. 与 context 的边界

tests 负责验证 lifecycle 与 memory 收口；
tests 不负责实现 context state 管理。

---

## 4. 与 providers / prompts / schemas 的边界

tests 负责验证这些基础模块的稳定性与回归面；
tests 不负责实现它们本身。

---

## 5. 与 rag 的边界

当前代码中 rag 已落地运行时代码。
tests 需要持续扩展并维护对应测试边界。

---

## 6. 结论

`tests/` 是回归保护层，不是实现层；当前已包含 RAG 测试面但仍不承担 RAG 实现职责。
