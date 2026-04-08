---
name: python-context-capability
description: 用于在 vi_ai_core_service 中实现与治理短期会话上下文能力（Context Engineering），当前聚焦 Phase 3：持久化短期记忆（Persistent Session Memory）。
last_updated: 2026-04-08
---

# 目的

本 skill 用于指导 `app/context/` 相关任务的执行，目标是让短期会话历史治理具备：

- 边界清晰
- 可配置
- 可测试
- 可回归
- 可演进
- 可持久化

并确保与 `request_assembler`、`chat_service`、`/chat`、`/chat/reset` 联动一致。

---

# 当前阶段约束（必须遵守）

当前是 **Context Engineering Phase 3：持久化短期记忆**，必须遵守：

- Phase 2 默认主链路已完成：`token-aware selection -> token-aware truncation -> deterministic summary -> serialization`
- summary 仍为确定性策略，不调用外部 LLM
- Phase 3 的核心是持久化 short-term session memory，而不是长期记忆平台
- 推荐引入 `RedisContextStore`，保留 `InMemoryContextStore` 作为 dev/test fallback
- 必须通过 `ContextManager` 暴露统一 façade，不允许 API/service 直连 Redis
- 必须支持 session / conversation reset 与 TTL 语义
- 不引入 RAG、向量检索、长期记忆、语义检索、用户画像、分布式工作流系统

---

# 适用场景

- 修改 `app/context/models.py`、`manager.py`、`stores/*`
- 新增 `stores/redis_store.py`
- 修改 `app/context/policies/*` 与持久化读写兼容逻辑
- 修改 `app/services/request_assembler.py` 的持久化读取链路
- 修改 `app/services/chat_service.py` 的持久化写回链路
- 修改 reset 相关 service/API 行为
- 修改 context trace 字段、TTL 语义或相关测试

---

# 不适用场景

- 实现长期记忆平台
- 实现 RAG / 向量检索
- 在 context 层接入 provider SDK 或 HTTP 调用
- 在 context 层实现最终 prompt 顺序装配
- 在 summary 中实现外部 LLM 摘要链路
- 把 Redis store 扩展成通用数据库平台

---

# 分层职责

Context 层负责：

- 会话历史 canonical 模型
- store 抽象与 store adapter
- manager façade
- token-aware 策略与 deterministic summary 策略
- 持久化短期记忆后端
- session / conversation lifecycle
- 策略执行 trace

Context 层不负责：

- API 接入
- 业务编排
- provider 协议
- prompt 资产管理
- RAG / 长期记忆 / 用户画像

---

# 必要输入

开始前必须确认：

1. 当前任务是否属于 context 边界
2. `ContextPolicyConfig` 与 `ContextStorageConfig`（或等价命名）的职责边界
3. store backend 目标（`memory` / `redis`）
4. 持久化配置键（`CONTEXT_STORE_BACKEND`、`CONTEXT_REDIS_URL`、`CONTEXT_SESSION_TTL_SECONDS`、`CONTEXT_STORE_KEY_PREFIX`、`CONTEXT_ALLOW_MEMORY_FALLBACK`）
5. session TTL / key prefix / namespace 设计
6. reset 语义（session / conversation）
7. 是否影响 `request_assembler` trace 字段
8. 需要补哪些策略、store 与回归测试

---

# 预期输出

至少产出：

1. `BaseContextStore` 的持久化短期记忆契约升级
2. `RedisContextStore`（或等价持久化 store）
3. `ContextManager` 的统一 façade 保持稳定
4. 持久化读写主链路在 `request_assembler.py` / `chat_service.py` 中接通
5. session / conversation reset 与 TTL 行为清晰
6. 测试覆盖与文档回写完成

---

# 必要流程

1. 先读根目录四文档与 `app/context/AGENTS.md`
2. 审查 `models.py`、`manager.py`、`stores/base.py`、`stores/in_memory.py`
3. 先定义持久化 store contract 与配置边界
4. 再新增 `RedisContextStore`（或等价实现）
5. 再打通 `request_assembler.py` 读路径与 `chat_service.py` 写路径
6. 再补 TTL / reset / namespace 行为
7. 再补测试
8. 最后回写根目录文档、模块文档与 skill 资产文档

---

# 设计规则

1. 默认策略顺序不可变：selection -> truncation -> summary -> serialization
2. 持久化后端只影响短期记忆读写，不得打破 Phase 2 policy pipeline
3. Redis / 持久化细节只能存在于 `app/context/stores/`
4. `ContextManager` 继续是 façade，不允许上层绕过
5. `ContextPolicyConfig` 与 `ContextStorageConfig` 不得职责混写
6. key prefix / TTL / namespace 必须集中配置
7. reset 必须显式触发，并精确限定作用范围
8. token 计数仍保持 provider-agnostic；当前阶段允许工程近似，但要可解释
9. 不要把 Phase 3 偷偷扩张成 RAG 或长期记忆工程

---

# 验证标准

至少验证：

- store backend 可配置（`memory` / `redis`）
- Redis store 基本读写正确
- `ContextManager` 的 get/append/reset/replace 行为稳定
- `request_assembler` 能读取持久化 session history
- `chat_service` 能在响应后写回持久化历史
- `reset_session` / `reset_conversation` 在持久化 store 上行为正确
- TTL / namespace / key prefix 语义清晰、可测试
- Phase 2 默认 policy pipeline 不被打破
- API `/chat` 与 `/chat/reset` 主链路回归通过

---

# Done Criteria

本 skill 任务完成，至少表示：

1. 持久化短期记忆 store 已落地
2. `InMemoryContextStore` 仍可用于 dev/test fallback（对应 backend 值 `memory`）
3. manager/store contract 保持稳定
4. request-time 读路径与 response-time 写路径已经接通
5. reset / TTL / namespace 行为已明确并测试
6. 文档、skill、代码、测试四者一致
7. 未越界进入长期记忆、RAG 或语义检索

---

# Notes

本 skill 适用于 **Context Engineering Phase 3：持久化短期记忆**。  
未来若复杂度继续上升，可再拆分为：

- python-context-persistent-store-skill
- python-context-lifecycle-skill
- python-context-redis-adapter-skill
- python-context-structured-memory-skill

---

# 编码前输出要求

开始编码前，必须先输出：

1. 任务理解与范围边界（持久化短期记忆，不是长期记忆）
2. models / stores / manager / request assembler / chat service / API 的文件级改动计划
3. 配置设计（policy config vs storage config）
4. 风险与假设（Redis 可用性、TTL 语义、fallback 行为）
5. 验证计划（store、reset、TTL、回归）

---

# 编码后输出要求

完成编码后，必须输出：

1. 文件级变更清单与原因
2. 持久化短期记忆行为变化说明
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
4. 未明确持久化 store contract、配置边界和 TTL/reset 语义，不进入主链路代码改造
