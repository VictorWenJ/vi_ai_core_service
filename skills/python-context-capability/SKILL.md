---
name: python-context-capability
description: 用于在 vi_ai_core_service 中实现与治理短期会话上下文能力（Context Engineering），当前聚焦 Phase 4：分层短期记忆（Layered Short-Term Memory）。
last_updated: 2026-04-09
---

# 目的

本 skill 用于指导 `app/context/` 相关任务的执行，目标是让短期会话历史治理具备：

- 边界清晰
- 可配置
- 可测试
- 可回归
- 可演进
- 可持久化
- 可分层

并确保与 `request_assembler`、`chat_service`、`/chat`、`/chat/reset` 联动一致。

---

# 当前阶段约束（必须遵守）

当前是 **Context Engineering Phase 4：分层短期记忆**，必须遵守：

- Phase 2 默认主链路已完成：`token-aware selection -> token-aware truncation -> deterministic summary -> serialization`
- Phase 3 的持久化短期记忆已落地：Redis backend / fallback / TTL / reset
- Phase 4 的核心是把 short-term memory 升级为 layered memory，而不是长期记忆平台
- 上下文主作用域必须统一为 `(session_id, conversation_id)`
- 必须通过 `ContextManager` 暴露统一 façade，不允许 API/service 直连 Redis
- rolling summary 仍采用确定性策略，不调用外部 LLM
- working memory reducer 先走高置信度规则版，不引入语义检索、向量召回、异步 worker
- 不引入 RAG、向量检索、长期记忆、用户画像、分布式工作流系统

---

# 适用场景

- 修改 `app/context/models.py`、`manager.py`、`stores/*`
- 新增 `memory_reducer.py`、`rendering.py`
- 修改 `app/context/policies/*` 与 Phase 4 兼容逻辑
- 修改 `app/services/request_assembler.py` 的 layered memory 读取链路
- 修改 `app/services/chat_service.py` 的 layered memory 写回链路
- 修改 reset 相关 service/API 行为
- 修改 context trace 字段、scope 语义或相关测试

---

# 不适用场景

- 实现长期记忆平台
- 实现 RAG / 向量检索 / semantic recall
- 在 context 层接入 provider SDK 或 HTTP 调用
- 在 context 层实现最终 prompt 顺序装配
- 在 summary / memory reducer 中实现外部 LLM 链路
- 把 Redis store 扩展成通用数据库平台

---

# 分层职责

Context 层负责：

- conversation-scoped state canonical 模型
- store 抽象与 store adapter
- manager façade
- token-aware 策略与 deterministic summary 策略
- 持久化短期记忆后端
- session / conversation lifecycle
- working memory reducer
- provider-agnostic context block rendering
- layered memory trace

Context 层不负责：

- API 接入
- 业务编排
- provider 协议
- prompt 资产管理
- RAG / 长期记忆 / 用户画像
- 最终 prompt 装配顺序决策

---

# 必要输入

开始前必须确认：

1. 当前任务是否属于 context 边界
2. `(session_id, conversation_id)` 作用域是否已经明确
3. `ContextPolicyConfig`、`ContextStorageConfig`、`ContextMemoryConfig` 的职责边界
4. store backend 目标（`memory` / `redis`）
5. recent raw budget / rolling summary limit / working memory item limit 的设计
6. reset 语义（session / conversation）
7. 是否影响 `request_assembler` trace 字段
8. 需要补哪些 reducer、store、assembler 与回归测试

---

# 预期输出

至少产出：

1. conversation-scoped layered memory contract 升级
2. `RollingSummaryState` 与 `WorkingMemoryState`（或等价模型）
3. `ContextManager` 的统一 façade 保持稳定
4. `memory_reducer.py`（或等价 reducer 抽象与默认实现）
5. `rendering.py`（或等价 provider-agnostic block rendering）
6. request-time 读路径与 response-time 写路径在 `request_assembler.py` / `chat_service.py` 中接通
7. session / conversation reset 与 TTL 行为清晰
8. 测试覆盖与文档回写完成

---

# 必要流程

1. 先读根目录四文档与 `app/context/AGENTS.md`
2. 审查 `models.py`、`manager.py`、`stores/base.py`、`stores/in_memory.py`、`stores/redis_store.py`
3. 先定义 scope 语义与 layered memory schema
4. 再升级 store contract 与 store codec
5. 再实现 `memory_reducer.py` 与 `rendering.py`
6. 再打通 `request_assembler.py` 读路径与 `chat_service.py` 写路径
7. 再补 trace / reset / TTL / namespace 行为
8. 再补测试
9. 最后回写根目录文档、模块文档与 skill 资产文档

---

# 设计规则

1. 默认策略顺序不可变：selection -> truncation -> summary -> serialization
2. layered memory 只影响 short-term memory 状态建模，不得打破 Phase 2 policy pipeline
3. Redis / 持久化细节只能存在于 `app/context/stores/`
4. `ContextManager` 继续是 façade，不允许上层绕过
5. `ContextPolicyConfig`、`ContextStorageConfig`、`ContextMemoryConfig` 不得职责混写
6. key prefix / TTL / namespace / scope 规则必须集中配置
7. reset 必须显式触发，并精确限定作用范围
8. `ContextWindow.messages` 在 Phase 4 中只表示 recent raw messages
9. rolling summary 默认保持确定性、可解释、可测试
10. working memory reducer 默认只记录高置信度信息，宁缺毋滥
11. 不要把 Phase 4 偷偷扩张成 RAG、长期记忆或语义检索工程

---

# 验证标准

至少验证：

- store backend 可配置（`memory` / `redis`）
- conversation scope 可正确隔离
- `ContextManager` 的 get/append/reset/replace/update_state 行为稳定
- `request_assembler` 能读取 layered memory 并按固定顺序装配
- `chat_service` 能在响应后写回 recent raw、rolling summary 与 working memory
- `reset_session` / `reset_conversation` 在持久化 store 上行为正确
- TTL / namespace / key prefix / scope 语义清晰、可测试
- Phase 2 默认 policy pipeline 不被打破
- API `/chat` 与 `/chat/reset` 主链路回归通过

---

# Done Criteria

本 skill 任务完成，至少表示：

1. layered short-term memory schema 已落地
2. `InMemoryContextStore` 仍可用于 dev/test fallback（对应 backend 值 `memory`）
3. manager/store contract 保持稳定
4. request-time 读路径与 response-time 写路径已经接通
5. reset / TTL / namespace / scope 行为已明确并测试
6. 文档、skill、代码、测试四者一致
7. 未越界进入长期记忆、RAG 或语义检索

---

# Notes

本 skill 适用于 **Context Engineering Phase 4：分层短期记忆**。  
未来若复杂度继续上升，可再拆分为：

- python-context-layered-memory-skill
- python-context-working-memory-reducer-skill
- python-context-summary-compaction-skill
- python-context-rag-boundary-skill

---

# 编码前输出要求

开始编码前，必须先输出：

1. 任务理解与范围边界（分层短期记忆，不是长期记忆）
2. models / stores / manager / reducer / rendering / request assembler / chat service / API 的文件级改动计划
3. 配置设计（policy config vs storage config vs memory config）
4. 风险与假设（scope 隔离、TTL 语义、fallback 行为、recent raw 预算）
5. 验证计划（scope、reducer、summary、顺序、回归）

---

# 编码后输出要求

完成编码后，必须输出：

1. 文件级变更清单与原因
2. layered short-term memory 行为变化说明
3. 测试与验证结果
4. 文档回写说明
5. 未做项与下一阶段建议

---

# 资产与验证索引

1. Checklist：`assets/context_capability_checklist.md`
2. Test Matrix：`assets/context_test_matrix.md`
3. References：`references/context_boundaries_and_acceptance.md`

---

# Governance Linkage

执行本 skill 时必须遵循统一闭环：

`根目录文档 -> app/context/AGENTS.md -> 本 skill -> 代码实现 -> review -> 文档回写`

强制要求：

1. 未完成根目录四文档与模块 AGENTS 阅读，不进入代码实现
2. 改动后必须按根 `CODE_REVIEW.md`、模块 `AGENTS.md`、本 skill checklist 联合自审
3. 若上下文模型、边界或测试事实变化，必须同步更新对应文档与测试
4. 未明确 scope、layered memory schema、配置边界和 reset 语义，不进入主链路代码改造
