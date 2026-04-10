# app/schemas/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `app/schemas/` 的职责、边界、结构约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。

---

## 2. 模块定位

`app/schemas/` 是系统的共享数据契约层。  
它负责请求、响应、stream event、cancel contract、message lifecycle contract、citation contract 等结构化 schema。

---

## 3. 本层职责

1. 定义 `/chat` request / response schema
2. 定义 `/chat_stream` 事件数据 schema
3. 定义 `/chat/cancel` request / response schema
4. 定义 message lifecycle 相关 schema
5. 在 Phase 6 中定义 citation 相关 schema

---

## 4. 本层不负责什么

1. 不负责 chat 编排
2. 不负责 retrieval 逻辑
3. 不负责 provider 调用
4. 不负责 request assembly
5. 不负责 context state 更新
6. 不负责 parser / chunker / embedding / index

---

## 5. 架构原则

### 5.1 契约优先
响应字段必须先有 schema 语义，再进入 API / service。

### 5.2 向后兼容优先
Phase 6 中新增 citations 时，应尽量保持既有同步与流式契约稳定。

### 5.3 外部契约不暴露不必要内部实现
不应直接暴露：
- 向量库内部结构
- embedding 维度
- collection 配置
- 内部 SDK 类型

### 5.4 citation 契约应简单、稳定、可展示
citation 不是内部 retrieval 对象的完整透传，而是可被前端/调试工具直接消费的对外结构。

---

## 6. 当前阶段能力声明

当前本轮必须保持稳定：

- `/chat` request / response
- `/chat_stream` started / delta / completed / error / cancelled / heartbeat 契约
- `/chat/cancel` request / response
- message lifecycle 相关字段语义

当前本轮新增要求：

- citation schema
- `/chat` response 中的 citations 字段
- `/chat_stream` completed 事件中的 citations 字段

---

## 7. 修改规则

1. 不允许无 schema 地新增响应字段
2. 不允许把内部 retrieval 结果对象直接透传给客户端
3. 不允许在 delta 阶段混入 citations
4. citation 字段命名必须清晰、稳定、可读

---

## 8. Code Review 清单

1. schemas 是否仍然只是“共享契约层”？
2. `/chat` 是否定义了稳定的 citations 结构？
3. `/chat_stream` completed 事件是否定义了稳定的 citations 结构？
4. 是否没有泄漏底层向量库和 embedding 细节？
5. 是否保持与 Phase 5 事件契约兼容？

---

## 9. 测试要求

至少覆盖：

1. `/chat` citations 字段结构正确
2. `/chat_stream` completed 事件 citations 结构正确
3. delta 阶段无 citations
4. citation 为空时行为明确
5. 现有 schema 回归不被破坏

---

## 10. 一句话总结

`app/schemas/` 在 Phase 6 中新增 citation 契约，但仍然只承担共享数据结构定义职责，不参与 retrieval、knowledge block 或上下文编排实现。