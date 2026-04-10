# module-boundaries.md

## 1. 目的

本文件用于说明 `app/observability/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

services 决定何时记录什么；
observability 提供记录能力。

---

## 3. 与 api 的边界

API 可以输出协议相关事实日志；
observability 不负责 API 协议实现。

---

## 4. 与 context 的边界

context 可以记录 lifecycle 相关事实；
observability 不负责 context 状态管理。

---

## 5. 与 providers / rag 的边界

providers 可以记录厂商调用事实；
rag 已落地运行时代码，RAG 观测属于现有默认边界。

---

## 6. 结论

`app/observability/` 是横切基础设施层，不是业务编排层；当前已覆盖 retrieval 生命周期观测但不承担 retrieval 业务实现。
