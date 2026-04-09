# app/api/AGENTS.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `app/api/` 的职责、边界、结构约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。

---

## 2. 模块定位

`app/api/` 是系统的 API 接入层。  
它负责把内部应用编排能力暴露为稳定、清晰、可测试的 HTTP 接口。

当前阶段核心接口：

- `/health`
- `/chat`
- `/chat/stream`
- `/chat/cancel`
- `/chat/reset`

---

## 3. 本层职责

1. 定义 HTTP 路由
2. 接收并解析请求
3. 做基础输入校验与错误映射
4. 调用 `app/services/`
5. 返回同步响应
6. 输出 SSE 流式事件
7. 透传 `session_id` / `conversation_id` / `request_id` / `assistant_message_id`

---

## 4. 本层不负责什么

1. 不负责 provider SDK / HTTP 适配
2. 不负责 Prompt 渲染
3. 不负责 context store 持久化
4. 不负责业务状态机
5. 不负责 provider chunk 归一化
6. 不负责 Redis / key / TTL / default scope 细节

---

## 5. 依赖边界

### 允许依赖
- `app/services/`
- `app/schemas/`
- FastAPI 与必要框架基础设施

### 禁止直接依赖
- `app/context/stores/*`
- `app/providers/` 作为常规调用路径
- Redis client
- provider 原始 stream chunk 类型

---

## 6. 设计原则

### 6.1 薄路由原则
route handler 只做：

- 请求接收
- 参数校验
- service 调用
- HTTP / SSE 响应输出

### 6.2 SSE 是 API 协议，不是业务状态机
API 层可以序列化 started / delta / completed / error / cancelled / heartbeat。  
但不决定这些事件何时发生。

### 6.3 不泄漏 layered memory 实现细节
API 层最多承接 `session_id` / `conversation_id`。  
不得把 store key、默认 scope、working memory schema 等内部实现细节暴露到外部协议层。

### 6.4 同步与流式输入尽量对齐
`/chat` 与 `/chat/stream` 优先复用同一套请求结构。

---

## 7. 当前阶段能力声明

本轮必须新增并验收：

- `/chat/stream`
- `/chat/cancel`
- 标准 SSE 输出
- started / delta / completed / error / cancelled 事件对外协议

当前不要求落地：

- WebSocket
- conversation CRUD 全家桶
- 多模态接口
- Tool / RAG 专用 API

---

## 8. 修改规则

1. 不允许在 API 层读写 store 私有状态
2. 不允许在路由里拼接 Redis key、设置 TTL 或写默认 scope
3. 不允许在路由里手写上下文治理逻辑
4. 不允许在路由里消费 provider 原始 chunk
5. 变更接口契约必须同步更新 schema、测试与文档

---

## 9. Code Review 清单

1. 路由层是否保持薄？
2. SSE `Content-Type` 是否正确？
3. `conversation_id` / `session_id` / `request_id` / `assistant_message_id` 是否正确透传？
4. 是否破坏现有 `/chat` 与 `/chat/reset` 契约？
5. cancel 接口是否清晰、最小、无业务算法泄漏？

---

## 10. 测试要求

至少覆盖：

1. `/health` 成功路径
2. `/chat` 成功路径
3. `/chat/stream` 返回 `text/event-stream`
4. `/chat/stream` 的 started -> delta -> completed 顺序
5. `/chat/stream` 的 error / cancelled 路径
6. `/chat/cancel` 成功路径
7. `/chat/reset` session / conversation 路径

---

## 11. 一句话总结

`app/api/` 的职责是接入、校验、转发、返回。  
Phase 5 新增 SSE 对外协议输出，但流式业务状态机与记忆收口细节仍不应进入路由层。
