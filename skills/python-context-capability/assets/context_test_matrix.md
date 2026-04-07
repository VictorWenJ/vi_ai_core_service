# Context Test Matrix

> 更新日期：2026-04-07

## 当前阶段必测项（Phase 2）

1. `manager -> store` 基础调用链。
2. `get_window` 空窗口读取行为。
3. `append_message` 追加顺序与 metadata 保留。
4. 会话隔离（不同 `session_id`）。
5. `reset_session` 全量清空行为。
6. `reset_conversation` 仅清空目标 `conversation_id` 行为。
7. `TokenAwareWindowSelectionPolicy` 在不同 token 预算下的选窗行为。
8. `TokenAwareTruncationPolicy` 超预算时的截断行为。
9. `SummaryPolicy` 默认压缩行为（确定性、可重复）。
10. `ContextPolicyPipeline` 顺序：selection -> truncation -> summary -> serialization。
11. `request_assembler` 输出消息顺序：system -> selected history -> current user。
12. `request_assembler` metadata trace 字段完整性。

## 当前阶段不测项（仅预留）

1. Redis/DB 持久化上下文存储。
2. 外部 LLM 驱动的复杂摘要策略。
3. RAG/semantic retrieval 记忆链路。

