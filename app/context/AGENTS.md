# app/context/AGENTS.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `app/context/` 模块的职责边界、演进约束、交付门禁与 review 标准。  
执行 context 相关任务时，必须先读根目录四文档，再读本文件，再执行 `skills/python-context-capability/`。

---

## 2. 模块定位

`app/context/` 是系统的 **短期会话上下文与短期记忆治理层**。  
它负责 provider-agnostic 的 conversation-scoped state 表示、策略执行、store 抽象与会话生命周期管理。

当前已完成：

- Context Engineering Phase 2 主链路
  - token-aware window selection
  - token-aware truncation
  - deterministic summary / compaction
  - history serialization
  - session / conversation reset
- Context Engineering Phase 3：持久化短期记忆
  - Redis backend / fallback / TTL / reset

当前阶段已落地：

- **Context Engineering Phase 4：分层短期记忆（Layered Short-Term Memory）**

---

## 3. 本层职责

1. 定义 canonical context models（message / window / summary / working memory / runtime meta）
2. 定义并实现 store contract 与 store adapter
3. 通过 `ContextManager` 暴露统一 façade（get / append / replace / reset / update_state）
4. 实现 `WindowSelectionPolicy` / `TruncationPolicy` / `SummaryPolicy` / `HistorySerializationPolicy`
5. 通过 `ContextPolicyPipeline` 提供固定顺序执行与可观测 trace
6. 管理短期记忆的持久化后端、TTL、namespace 与 reset 语义
7. 在 Phase 4 中管理 recent raw / rolling summary / working memory 三层短期记忆
8. 在 Phase 4 中提供 working memory reducer 与 provider-agnostic context block rendering 能力

---

## 4. 本层不负责什么

1. 不负责 HTTP 接入与路由
2. 不负责业务流程编排
3. 不负责 provider payload 协议
4. 不负责 prompt 模板管理与 system prompt 选择
5. 不负责 RAG、长期记忆、向量检索、用户画像
6. 不负责外部 LLM 摘要编排或外部 LLM memory extraction
7. 不负责决定最终 `system + working_memory + summary + history + user` 的装配顺序
8. 不负责把分层短期记忆包装成“长期 memory platform”

---

## 5. 依赖边界

- 允许依赖：`app/schemas/`（必要契约）、`app/config.py`、标准库、必要的 Redis 客户端依赖（仅 store 层）
- 禁止依赖：`app/api/`、`app/services/`、`app/providers/` 的业务流程实现
- `services/request_assembler.py` 可调用 context 层；context 层不得反向依赖 assembler/service
- `context/rendering.py` 只输出 provider-agnostic block / text，不得导入 provider-specific 类型

---

## 6. 默认行为与 Phase 4 约束

默认 policy pipeline 顺序固定为：

`token-aware selection -> token-aware truncation -> deterministic summary -> serialization`

### 6.1 选择（selection）
- 有 recent raw history 时按 token budget 选择窗口，不再默认全量拼接

### 6.2 截断（truncation）
- 当 selected history 超预算时做 token-aware 截断
- 优先保留最近消息；必要时截断更旧消息内容

### 6.3 摘要（summary）
- 默认 `DeterministicSummaryPolicy`
- 不调用外部 LLM
- Phase 4 中 rolling summary 仍采用确定性 compaction / merge 思路

### 6.4 序列化（serialization）
- 输出 provider-agnostic 的 `{role, content}` 列表给 assembler
- `messages` 的语义在 Phase 4 中收敛为 **recent raw messages only**

### 6.5 追踪信息（trace）
- 必须区分 selection / truncation / summary 三阶段字段
- Phase 4 必须补充 layered memory 字段：scope、recent_raw_count、compaction_applied、summary_present、working_memory_fields_present
- `message_overhead_tokens` 仍属于当前阶段工程近似

---

## 7. Phase 4 当前现实（分层短期记忆）

在不改变 Phase 2 默认治理链路、在保留 Phase 3 persistence contract 基础上，本轮必须完成以下语义升级：

### 7.1 上下文作用域升级
- 所有读取、写入、replace、reset 都必须以 `(session_id, conversation_id)` 为主作用域
- 若缺少 `conversation_id`，仅允许 store 内部使用默认 scope
- 不允许继续以“session 读取全部历史 + conversation 只挂 metadata”的方式实现 Phase 4

### 7.2 分层状态升级
`ContextWindow` 必须至少包含：

- `messages`：recent raw messages
- `rolling_summary`
- `working_memory`
- `runtime_meta`

### 7.3 rolling summary
- 由 recent raw 挤出的较老消息生成并持续合并
- 持久化存储
- 不引入外部 LLM 调用
- 目标是保留主线，不是完整复写历史

### 7.4 working memory
建议先控制在以下字段：

- `active_goal`
- `constraints`
- `decisions`
- `open_questions`
- `next_step`
- `updated_at`

要求：
- 只记录高置信度信息
- 宁缺毋滥
- 去重、限长、可解释

### 7.5 配置边界
必须清晰区分：

- `ContextPolicyConfig`：请求时窗口治理
- `ContextStorageConfig`：backend / TTL / prefix / fallback
- `ContextMemoryConfig`：recent raw / rolling summary / working memory

---

## 8. 修改规则

1. 任何持久化逻辑必须落在 `app/context/stores/`，不得泄漏到 service/API 层
2. 不允许在 context 层直接接入 provider SDK 做摘要或记忆抽取
3. 不允许在 context 层决定最终 prompt 装配顺序
4. reset 行为必须通过 `ContextManager` 暴露，不允许 API/service 直改 store 私有状态
5. TTL、namespace、序列化格式、scope 规则必须集中管理，不允许多处硬编码
6. `ContextWindow.messages` 语义变更后，所有相关逻辑必须同步校正
7. 变更策略语义、store contract 或 layered memory schema 时必须同步更新测试与 skill 文档

---

## 9. 推荐结构（Phase 4）

当前建议结构至少包括：

- `models.py`
- `manager.py`
- `memory_reducer.py`
- `rendering.py`
- `stores/base.py`
- `stores/factory.py`
- `stores/in_memory.py`
- `stores/redis_store.py`
- `policies/base.py`
- `policies/context_policy.py`
- `policies/window_selection.py`
- `policies/truncation.py`
- `policies/summary.py`
- `policies/serialization.py`
- `policies/tokenizer.py`
- `policies/defaults.py`

如持久化编码逻辑复杂，可以新增：
- `stores/codec.py`

但必须保持轻量，不提前做平台化扩张。

---

## 10. Code Review 清单

1. 是否存在 context 反向依赖 service/api 的越层行为？
2. 默认策略顺序是否仍为 `selection -> truncation -> summary -> serialization`？
3. Redis/持久化逻辑是否仅存在于 `stores/`？
4. `ContextManager` 是否仍只是 façade，而非业务编排中心？
5. `ContextWindow.messages` 是否只表示 recent raw messages？
6. `rolling_summary` 与 `working_memory` 是否作为独立状态层被正确编码与持久化？
7. `(session_id, conversation_id)` scope 是否贯穿读写与 reset？
8. 是否误把 Phase 4 变成长期记忆、RAG 或语义检索？
9. trace/metadata 是否仍清晰、可测试？
10. 是否提供 dev/test fallback 而不污染生产语义？

---

## 11. 测试要求

至少覆盖：

1. 基础上下文读写
2. manager 与 store 协作行为
3. in-memory store 正确性
4. Redis store 基本读写
5. Redis store reset_session / reset_conversation 行为
6. 同一 session 下不同 conversation 的隔离行为
7. recent raw 超预算后的 compaction 与 rolling summary 更新
8. working memory reducer 的更新、去重、限长与空输入行为
9. `request_assembler` 读取 layered memory 并保持固定顺序
10. `chat_service` 响应后写回 recent raw / summary / working memory
11. TTL / 配置解析 / fallback 行为

---

## 12. 禁止事项

以下做法应避免：

- 在 service 或 API 层直接操作 Redis
- 在 context 层直接生成 provider-specific payload
- 在 context 层偷偷实现 RAG / retrieval / long-term memory
- 在 context 层引入外部 LLM 二次摘要或二次抽取
- 在 store 里硬编码多套 key 规则且未集中管理
- 把 Phase 4 直接做成用户画像记忆或长期知识记忆

---

## 13. 一句话总结

`app/context/` 在 Phase 4 中的目标不是继续堆消息历史，而是把短期会话状态升级为**conversation-scoped layered short-term memory**。  
本阶段仍然是 short-term memory，不是长期记忆系统，也不是 RAG。

---

## 14. 本模块任务执行链路（强制）

1. 先读根目录四文档
2. 再读本文件
3. 再执行 `skills/python-context-capability/SKILL.md` 与其 checklist/reference
4. 再改 `app/context/` 代码
5. 再按根 `CODE_REVIEW.md` + 本文件 + skill checklist 自审
6. 若上下文模型/边界事实变化，回写文档

---

## 15. 本模块交付门禁

- 未通过 `python-context-capability` checklist，不视为完成
- 发现 context 层承担 provider/API/service 主流程职责时必须先整改
- 变更 manager/store/models 契约时必须补测试
- 未定义 layered memory schema 与配置边界，不进入 Phase 4 实现
- 未明确 scope / reset / namespace / recent raw 语义，不允许上线分层短期记忆能力
