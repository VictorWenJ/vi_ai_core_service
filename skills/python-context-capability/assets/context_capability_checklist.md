# Context 能力检查清单
> 更新日期：2026-04-09

## 目录与落位
- [ ] 上下文核心实现只落在 `app/context/`（models / stores / manager / policies / reducer / rendering）
- [ ] `request_assembler.py` 作为请求组装入口，未在 API 或 chat service 中重复实现上下文策略
- [ ] 未新增与当前阶段无关的新系统层

## 作用域与模型（Phase 4）
- [ ] 上下文主作用域统一为 `(session_id, conversation_id)`
- [ ] 同一 `session_id` 下不同 `conversation_id` 完全隔离
- [ ] `ContextWindow.messages` 语义已收敛为 `recent raw messages`
- [ ] `ContextWindow` 包含 `rolling_summary`、`working_memory`、`runtime_meta`

## 策略链路
- [ ] 默认顺序固定：`selection -> truncation -> summary -> serialization`
- [ ] selection/truncation 为 token-aware，未退回全量原样拼接
- [ ] summary 保持确定性实现（不引入外部 LLM 二次调用）
- [ ] serialization 输出 provider-agnostic 的 `role/content` 结构

## 读链路（request-time）
- [ ] request 组装顺序固定：`system -> working_memory -> rolling_summary -> recent_raw -> user`
- [ ] working memory 为空时可优雅跳过
- [ ] rolling summary 为空时可优雅跳过
- [ ] context trace 包含 scope、分层状态与策略信息

## 写链路（response-time）
- [ ] 先写入本轮 user/assistant recent raw
- [ ] 超预算触发 recent raw compact，优先压缩最旧片段
- [ ] compact 片段进入 rolling summary（而不是直接丢弃）
- [ ] working memory 通过 reducer 更新，具备去重、限长、空值保护
- [ ] 最终持久化完整 conversation-scoped `ContextWindow`

## Store / TTL / Reset
- [ ] `BaseContextStore` 接口显式支持 `session_id + conversation_id`
- [ ] In-memory 与 Redis store 对外语义一致
- [ ] Redis key schema 使用 conversation scope，支持 session 级索引
- [ ] `reset_conversation` 仅清目标 conversation scope
- [ ] `reset_session` 清目标 session 下所有 conversation scope
- [ ] TTL 行为与配置一致，写入时刷新

## 配置边界
- [ ] `ContextPolicyConfig`、`ContextStorageConfig`、`ContextMemoryConfig` 职责分离
- [ ] memory 配置覆盖 recent raw / rolling summary / working memory 开关与预算
- [ ] 未把 store 配置、policy 配置、memory 配置混写

## 测试与回归
- [ ] conversation 作用域隔离测试通过
- [ ] recent raw compaction 测试通过
- [ ] rolling summary 合并与持久化测试通过
- [ ] working memory reducer 规则测试通过
- [ ] assembler 顺序与 metadata/trace 测试通过
- [ ] in-memory / redis backend parity 测试通过
- [ ] `/chat` 与 `/chat_reset` 回归通过

## 当前阶段禁止项
- [ ] 未引入向量检索、RAG、embedding
- [ ] 未引入长期记忆平台
- [ ] 未引入外部 LLM 二次摘要链路
- [ ] 未把 provider 细节泄漏到 context 层
