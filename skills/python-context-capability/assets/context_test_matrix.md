# Context 测试矩阵

> 更新日期：2026-04-08

## 当前阶段必测项（Phase 2 收尾）

1. `TokenAwareWindowSelectionPolicy`：不同 token budget 下窗口选择行为。
2. `TokenAwareTruncationPolicy`：超预算消息截断与 metadata 标记行为。
3. `DeterministicSummaryPolicy`：默认路径不吞最近 raw message。
4. `fallback_behavior` 差异：`summary_then_drop_oldest` vs `drop_oldest`。
5. `summary_enabled=false`：退回 no-op summary 路径。
6. `DefaultHistorySerializationPolicy`：role/content 顺序保持稳定。
7. `ContextPolicyPipeline`：执行顺序固定为 selection -> truncation -> summary -> serialization。
8. `request_assembler`：有 session 时使用服务端 history，无 session 时不加载 history。
9. `request_assembler`：context trace 关键字段完整（policy 名称、预算、计数、token counter）。
10. `/chat/reset`：session 级 reset 行为正确。
11. `/chat/reset`：conversation 级 reset 行为正确。
12. `ContextManager`：reset_session/reset_conversation 契约行为正确。

## 回归必测项

1. 非流式 `/chat` 主链路不回退。
2. provider 调用主路径不受 context 收尾改动影响。
3. prompt 组装顺序仍为 `system -> history -> current user`。
4. context manager/store 契约未被打穿。

## 当前阶段不测项（仅预留）

1. Redis/DB 持久化上下文存储。
2. 外部 LLM 驱动的复杂摘要编排。
3. RAG/语义检索记忆链路。
4. 长期记忆系统与跨会话画像记忆。
