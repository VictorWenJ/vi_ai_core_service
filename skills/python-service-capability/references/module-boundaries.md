# module-boundaries.md

## 1. 目的

本文件用于说明 `app/services/` 与其他模块之间的边界关系。

---

## 2. 与 api 的边界

### services 负责
- chat / stream 入口 façade
- runtime 结果交付
- SSE 事件转发协作

### api 负责
- HTTP / SSE 协议接入
- 请求 / 响应 schema
- SSE 文本序列化

---

## 3. 与 chat_runtime 的边界

### services 负责
- 把外部请求映射为 runtime 输入
- 调用 runtime
- 把结果交付给 API

### chat_runtime 负责
- workflow / hook / trace 主执行语义
- sync / stream 共语义收口

---

## 4. 与 context 的边界

### services 负责
- 不直接管理 context 底层实现

### context 负责
- 状态模型
- layered memory
- store / policy / codec

---

## 5. 与 prompts 的边界

services 不重新定义 prompt 资产治理；
prompts 负责模板资产、registry 与 renderer。

---

## 6. 与 providers 的边界

services 不直接散落调用厂商 SDK；
providers 负责厂商适配与 canonical result。

---

## 7. 与 rag 的边界

services 不直接承担 retrieval 主调度；
rag 负责知识实现。

---

## 8. 结论

`app/services/` 是 façade 层，不是协议层、不是 SDK 层、不是存储层，也不是 chat runtime 主执行层。
