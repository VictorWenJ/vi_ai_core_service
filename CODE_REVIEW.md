# CODE_REVIEW.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `vi_ai_core_service` 的项目级 Code Review 标准。  
适用于整个仓库的通用审查原则、全局质量要求与跨模块检查点。

---

## 2. Review 目标

Code Review 不只是检查“能不能运行”，还要检查：

1. 是否符合分层结构
2. 是否遵守模块边界
3. 是否与总体架构一致
4. 是否可维护、可扩展、可测试
5. 是否破坏同步与流式两条主链路

---

## 3. 全局审查原则

- 先看边界，再看实现
- 先看结构，再看技巧
- 保守对待会扩大耦合的改动
- 可测试性是硬要求

---

## 4. 项目级通用审查问题

每次 review，至少回答：

1. 代码为什么在这个目录？
2. 逻辑属于哪个层？
3. 是否破坏七层边界？
4. 是否出现跨层绕过？
5. 是否需要同步更新文档？
6. 是否需要补测试？

---

## 5. 全局边界检查清单

### API 层
- 是否只做接入、校验、转发、返回
- SSE 序列化是否留在 API 层
- route 是否没有直接消费 provider 原始 chunk 或 context store

### Services 层
- 是否仍然是编排层
- 生命周期状态机、取消协调、完成态收口是否由 services 统一调度

### Context / Prompt / Provider
- 三个专项能力模块是否职责分离
- context 是否只在 completed 时执行标准 memory update
- provider 是否只做 canonical response / stream chunk 归一化

### Observability
- 是否仍是结构化日志基础设施，而不是业务状态机

### Schema
- 是否仍是契约层
- stream event / lifecycle / cancel contract 是否清晰稳定

---

## 6. 全局契约审查标准

必须检查：

- `/chat` 与 `/chat_stream` 输入语义是否尽量一致
- SSE 事件类型与 payload 是否稳定
- `request_id` / `assistant_message_id` / `finish_reason` / `usage` / `latency` / `error_code` 语义是否统一
- default scope 等内部实现细节是否未泄漏到外部协议

---

## 7. 全局错误处理审查标准

必须检查：

- client disconnect 是否与 explicit cancel 区分
- provider timeout 与 request timeout 是否区分
- `response.error` 与 `response.cancelled` 是否不混淆
- failed / cancelled assistant message 是否没有进入标准 memory update

---

## 8. 全局测试审查标准

以下改动原则上必须补测试：

- 主链路改动
- Provider 行为改动
- Context 行为改动
- Schema 契约改动
- 流式事件顺序、生命周期、取消与失败路径改动

---

## 9. Phase 5 专项审查清单

### 生命周期与状态机
- assistant message 是否严格走 `created -> streaming -> completed/failed/cancelled`
- placeholder 是否在 started 事件前建立

### 上下文收口
- 是否只有 completed assistant message 才进入标准 context update
- 是否错误地在每个 delta 上执行 summary / reducer / Redis 写回
- request assembly 是否默认忽略 non-completed assistant message

### SSE 协议
- 是否返回 `text/event-stream`
- 事件顺序是否稳定
- provider 原始 chunk 是否没有直接暴露给客户端

### 取消与超时
- 是否有明确 cancel 入口
- 取消语义与断链是否未混淆
- 超时是否有稳定错误码

### 同步兼容性
- `/chat` 是否仍然可用
- 流式新增是否没有破坏同步用例

---

## 10. 常见应拒绝的问题改动

- 为了快直接跨层调用
- 在 API 层堆业务逻辑
- provider 直接输出 SSE
- 在每个 delta 上写入 rolling summary / working memory
- 以 Phase 5 为名偷偷引入 WebSocket、Tool、RAG、长期记忆或 Agent runtime
