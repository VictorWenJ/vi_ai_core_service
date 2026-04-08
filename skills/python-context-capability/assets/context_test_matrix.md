# Context 测试矩阵

> 更新日期：2026-04-08

## 当前阶段必测项（Phase 3）

### 既有 Phase 2 核心行为
1. `TokenAwareWindowSelectionPolicy`：不同 token budget 下窗口选择行为
2. `TokenAwareTruncationPolicy`：超预算消息截断与 metadata 标记行为
3. `DeterministicSummaryPolicy`：确定性 summary 行为稳定
4. `ContextPolicyPipeline`：执行顺序固定为 selection -> truncation -> summary -> serialization
5. `DefaultHistorySerializationPolicy`：role/content 顺序保持稳定
6. `request_assembler`：有 session 时使用服务端 history，无 session 时不加载 history
7. `request_assembler`：context trace 关键字段完整

### Phase 3 新增能力
8. `RedisContextStore`：基本 get / append / replace 行为正确
9. `RedisContextStore`：reset_session 行为正确
10. `RedisContextStore`：reset_conversation 行为正确
11. `ContextManager`：在不同 backend 上 façade 行为一致
12. `request_assembler`：能从持久化 store 读取 session history
13. `chat_service`：能在响应后写回 user / assistant 历史
14. `ContextStorageConfig`：`CONTEXT_STORE_BACKEND` / `CONTEXT_REDIS_URL` / `CONTEXT_SESSION_TTL_SECONDS` / `CONTEXT_STORE_KEY_PREFIX` / `CONTEXT_ALLOW_MEMORY_FALLBACK` 解析正确
15. 持久化 backend 不可用时的预期 fallback / error 行为正确
16. `/chat/reset`：session 级 reset 行为正确
17. `/chat/reset`：conversation 级 reset 行为正确

## 回归必测项

1. 非流式 `/chat` 主链路不回退
2. provider 调用主路径不受 context persistence 改动影响
3. prompt 组装顺序仍为 `system -> history -> current user`
4. context manager/store 契约未被打穿
5. 既有 Phase 2 默认主链路未被 persistence 改动破坏

## 当前阶段不测项（仅预留）

1. 向量数据库 / RAG 检索
2. 外部 LLM 驱动的复杂摘要编排
3. 长期记忆系统与跨会话用户画像
4. 多区域分布式状态协调
