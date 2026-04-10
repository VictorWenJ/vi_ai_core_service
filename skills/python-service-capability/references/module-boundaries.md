# module-boundaries.md

## 1. 目的

本文件用于说明 `app/services/` 与其他模块之间的边界关系。

---

## 2. 与 api 的边界

### services 负责
- chat / stream / cancel / reset 编排
- 生命周期收口
- request assembly

### api 负责
- HTTP / SSE 协议接入
- 请求 / 响应 schema
- SSE 文本序列化

---

## 3. 与 context 的边界

### services 负责
- 何时读写上下文
- 何时进入 completed 收口

### context 负责
- 状态模型
- layered memory
- store / policy / codec

---

## 4. 与 prompts 的边界

services 决定何时取默认 system prompt、何时装配消息；
prompts 负责模板资产、registry 与 renderer。

---

## 5. 与 providers 的边界

services 决定何时调用 provider；
providers 负责厂商适配与 canonical result。

---

## 6. 与 rag 的边界

当前代码尚未接入 rag。
后续若落地：services 负责编排，rag 负责知识实现。

---

## 7. 结论

`app/services/` 是应用编排层，不是协议层、不是 SDK 层、不是存储层，也不是当前代码中的 RAG 实现层。
