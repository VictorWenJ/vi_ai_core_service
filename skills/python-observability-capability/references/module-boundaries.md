# module-boundaries.md

## 1. 目的

本文件用于说明 `app/observability/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

### observability 负责
- 记录 request / stream / retrieval 事实
- 提供 JSON-safe 日志能力

### services 负责
- chat / stream 编排
- lifecycle 推进
- cancel / reset 决策
- retrieval 调度

---

## 3. 与 api 的边界

API 可调用 observability 输出 HTTP / SSE 相关事实。  
observability 不负责 route、schema 或 SSE 协议实现。

---

## 4. 与 context 的边界

context 负责状态；observability 负责记录状态变化事实。  
observability 不替代 context state 管理。

---

## 5. 与 rag 的边界

rag 负责知识实现；observability 负责记录检索事实。  
observability 不实现 parser / chunker / embedding / index / retrieval。

---

## 6. 与 providers 的边界

providers 负责厂商调用；observability 负责记录厂商调用事实。  
observability 不直接调用 provider SDK。

---

## 7. 结论

`app/observability/` 是横切基础设施层，只提供观测能力，不承担业务决策与状态推进职责。