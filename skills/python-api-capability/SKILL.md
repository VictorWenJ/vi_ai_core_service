---
name: python-api-capability
description: 用于在 vi_ai_core_service 中实现与治理面向主流 C 端 AI 应用的 API 接入层能力。当前聚焦 Phase 5：Streaming Chat & Conversation Lifecycle，重点是同步与 SSE 流式聊天接口、取消接口、稳定外部契约与薄路由边界。
last_updated: 2026-04-09
---

# 目的

本 skill 用于指导 `app/api/` 相关任务，目标是让 API 层具备：

- 边界清晰
- 契约稳定
- 薄路由
- 流式可消费
- 可测试
- 可回归

---

# 当前阶段约束（必须遵守）

- `/chat` 必须继续可用
- 新增 `/chat/stream`，协议固定为 **SSE**
- 新增 `/chat/cancel`
- API 层只负责接入、校验、转发、返回与 SSE 文本输出
- API 层不负责业务状态机、provider chunk 归一化、context memory 更新
- 不泄漏 default scope、Redis key、working memory schema 等内部实现细节
- 不引入 WebSocket、Tool、RAG、长期记忆接口

---

# 适用场景

- 修改 `app/api/chat.py`
- 新增或调整 `/chat/stream`、`/chat/cancel`
- 新增 SSE 序列化辅助模块
- 修改 `app/api/schemas/chat.py`
- 补充 API 层与 HTTP 集成测试

---

# 设计规则

1. 薄路由优先
2. SSE 是 API 协议，不是业务状态机
3. `/chat` 与 `/chat/stream` 输入尽量复用
4. 不泄漏 layered memory 实现细节
5. 不提前做实时平台工程

---

# 验证标准

至少满足：

- `/chat` 继续可用
- `/chat/stream` 返回 `text/event-stream`
- started -> delta -> completed 顺序稳定
- error / cancelled 路径稳定
- `/chat/cancel` 语义清晰
- 无 provider / Redis / context 私有逻辑泄漏到 route
