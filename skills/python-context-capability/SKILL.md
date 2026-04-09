---
name: python-context-capability
description: 用于在 vi_ai_core_service 中实现与治理短期会话上下文能力（Context Engineering）。当前聚焦 Phase 4 layered memory 的持续稳定化，以及与 Phase 5 Streaming Chat & Conversation Lifecycle 的兼容接入。
last_updated: 2026-04-09
---

# 目的

本 skill 用于指导 `app/context/` 相关任务，目标是让短期会话治理具备：

- 边界清晰
- 可配置
- 可测试
- 可回归
- 可分层
- 可兼容流式生命周期

---

# 当前阶段约束（必须遵守）

- Phase 2 policy pipeline 不变
- Phase 3 持久化短期记忆不变
- Phase 4 layered memory 不变
- Phase 5 中 only completed assistant message 才进入标准 memory update
- 不引入 RAG、向量检索、长期记忆、用户画像、分布式工作流系统

---

# 适用场景

- 修改 `app/context/models.py`、`manager.py`、`stores/*`
- 扩展 message lifecycle 字段
- 新增 placeholder / finalize / fail / cancel 相关 state 更新接口
- 修改 `request_assembler.py` 的 non-completed assistant message 过滤逻辑

---

# 设计规则

1. 默认策略顺序不可变：selection -> truncation -> summary -> serialization
2. `ContextWindow.messages` 在 Phase 4/5 中只表示 recent raw messages
3. non-completed assistant message 默认不得进入标准 request assembly
4. delta 阶段不得触发标准 rolling summary / working memory 更新
5. completed 后才执行标准 `update_after_chat_turn`

---

# 验证标准

至少验证：

- conversation scope 可正确隔离
- lifecycle 字段可正确序列化 / 反序列化
- `request_assembler` 默认忽略 non-completed assistant message
- completed 后 recent raw / rolling summary / working memory 正常更新
- failed / cancelled 不进入标准 memory update
