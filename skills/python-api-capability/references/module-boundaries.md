# module-boundaries.md

## 1. 目的

本文件用于说明 `app/api/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

### api 负责
- 接入
- 校验
- 转发
- 返回 JSON
- 返回 SSE

### services 负责
- chat 主链路编排
- 流式状态机推进
- cancel / reset 内部逻辑
- retrieval 调度
- citations 数据准备

---

## 3. 与 schemas 的边界

### schemas 负责
- request / response 数据契约
- SSE event payload 契约
- cancel / reset 契约

### api 负责
- 使用这些契约承接输入与输出
- 不绕开 schema 临时拼字段

---

## 4. 与 context 的边界

API 不直接操作 context。  
上下文读取、更新、重置都应通过 service 触发。

---

## 5. 与 rag 的边界

API 不直接操作：

- parser
- chunker
- embedding
- vector index
- retrieval

API 只承接 citations 结果输出。

---

## 6. 与 providers 的边界

API 不直接调用 provider SDK。  
chat completion、streaming、embedding 都不属于 API 层职责。

---

## 7. 结论

`app/api/` 是协议接入层，不是业务编排层，不是知识检索层，也不是状态管理层。