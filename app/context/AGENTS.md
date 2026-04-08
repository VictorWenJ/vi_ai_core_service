# app/context/AGENTS.md

> 更新日期：2026-04-08

## 1. 文档定位

本文件定义 `app/context/` 模块的职责边界、演进约束、交付门禁与 review 标准。  
执行 context 相关任务时，必须先读根目录四文档，再读本文件，再执行 `skills/python-context-capability/`。

---

## 2. 模块定位

`app/context/` 是系统的 **短期会话上下文与短期记忆治理层**。  
它负责 provider-agnostic 的会话历史表示、策略执行、store 抽象与会话生命周期管理。

当前已完成 Context Engineering Phase 2 主链路：

- token-aware window selection
- token-aware truncation
- deterministic summary / compaction
- history serialization
- session / conversation reset

当前模块已完成 **Context Engineering Phase 3：持久化短期记忆（Persistent Session Memory）** 的核心落地。

---

## 3. 本层职责

1. 定义 canonical context models（message/window 与策略中间结果）
2. 定义并实现 store contract 与 store adapter
3. 通过 `ContextManager` 暴露统一 façade（get/append/reset/replace）
4. 实现 `WindowSelectionPolicy` / `TruncationPolicy` / `SummaryPolicy` / `HistorySerializationPolicy`
5. 通过 `ContextPolicyPipeline` 提供固定顺序执行与可观测 trace
6. 管理短期记忆的持久化后端、TTL、namespace 与 reset 语义
7. 保持 token 预算、fallback、summary 开关与 storage backend 可配置

---

## 4. 本层不负责什么

1. 不负责 HTTP 接入与路由
2. 不负责业务流程编排
3. 不负责 provider payload 协议
4. 不负责 prompt 模板管理与 system prompt 选择
5. 不负责 RAG、长期记忆、向量检索、用户画像
6. 不负责外部 LLM 摘要编排
7. 不负责把持久化短期记忆包装成“长期 memory platform”

---

## 5. 依赖边界

- 允许依赖：`app/schemas/`（必要契约）、`app/config.py`、标准库、必要的 Redis 客户端依赖（仅 store 层）
- 禁止依赖：`app/api/`、`app/services/`、`app/providers/` 的业务流程实现
- `services/request_assembler.py` 可调用 context 层；context 层不得反向依赖 assembler/service

---

## 6. 当前默认行为（Phase 2 已完成）

默认管线顺序固定为：

`token-aware selection -> token-aware truncation -> summary/compaction -> serialization`

### 6.1 选择（selection）
- 有 session 历史时按 token budget 选择窗口，不再默认全量拼接

### 6.2 截断（truncation）
- 当 selected history 超预算时做 token-aware 截断
- 优先保留最近消息；必要时截断更旧消息内容

### 6.3 摘要（summary）
- 默认 `DeterministicSummaryPolicy`
- 不调用外部 LLM
- 当前阶段只做确定性 compaction，不做高级语义摘要

### 6.4 序列化（serialization）
- 输出 provider-agnostic 的 `{role, content}` 列表给 assembler

### 6.5 追踪信息（trace）
- 必须区分 selection / truncation / summary 三阶段字段
- 应暴露 token counter 类型与关键预算字段
- `message_overhead_tokens` 仍属于当前阶段工程近似

---

## 7. Phase 3 当前现实（持久化短期记忆）

在不改变 Phase 2 默认治理链路的前提下，当前已具备以下能力：

### 7.1 store backend 升级
- 引入 `RedisContextStore`（推荐主实现）
- 保留 `InMemoryContextStore` 作为 dev/test fallback
- 对上层保持 `BaseContextStore` 契约稳定

### 7.2 生命周期治理
- session TTL
- conversation 级 reset
- session 级 reset
- key prefix / namespace
- 序列化与反序列化版本管理

### 7.3 持久化读写路径
- request-time 从持久化 store 读取 context window
- response-time 通过 manager/store 统一写回 user / assistant 历史
- replace / clear / reset 仍走统一 façade，不允许上层绕过

### 7.4 可恢复性与降级
- Redis 不可用时，开发环境可回退到 `memory`
- 生产语义必须清晰，不允许无声吞错

### 7.5 配置入口（ContextStorageConfig）
- `CONTEXT_STORE_BACKEND`
- `CONTEXT_REDIS_URL`
- `CONTEXT_SESSION_TTL_SECONDS`
- `CONTEXT_STORE_KEY_PREFIX`
- `CONTEXT_ALLOW_MEMORY_FALLBACK`

---

## 8. 修改规则

1. 任何持久化逻辑必须落在 `app/context/stores/`，不得泄漏到 service/API 层
2. 不允许在 context 层直接接入 provider SDK 做摘要
3. 不允许在 context 层拼接最终 `system + history + user` 顺序
4. reset 行为必须通过 `ContextManager` 暴露，不允许 API/service 直改 store 私有状态
5. TTL、namespace、序列化格式必须集中管理，不允许多处硬编码
6. 变更策略语义或 store contract 时必须同步更新测试与 skill 文档

---

## 9. 推荐结构（Phase 3）

当前建议结构至少包括：

- `models.py`
- `manager.py`
- `stores/base.py`
- `stores/factory.py`
- `stores/in_memory.py`
- `stores/redis_store.py`（本阶段新增）
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
5. store contract 是否稳定，append/get/reset/replace 是否齐全？
6. TTL / namespace / key prefix 是否语义清晰且集中配置？
7. 是否误把 Phase 3 变成长期记忆或 RAG？
8. trace/metadata 是否仍清晰、可测试？
9. 是否提供 dev/test fallback 而不污染生产语义？

---

## 11. 测试要求

至少覆盖：

1. 基础上下文读写
2. manager 与 store 协作行为
3. in-memory store 正确性
4. Redis store 基本读写
5. Redis store reset_session / reset_conversation 行为
6. session history 持久化后再次读取
7. token-aware policy 核心行为回归
8. `request_assembler` 读取持久化历史
9. `chat_service` 响应后写回持久化历史
10. TTL / 配置解析 / fallback 行为

---

## 12. 禁止事项

以下做法应避免：

- 在 service 或 API 层直接操作 Redis
- 在 context 层直接生成 provider-specific payload
- 在 context 层偷偷实现 RAG / retrieval / long-term memory
- 在 store 里硬编码多套 key 规则且未集中管理
- 把 Phase 3 直接做成用户画像记忆或长期知识记忆

---

## 13. 一句话总结

`app/context/` 在 Phase 2 中已经完成 token-aware 上下文治理主链路；Phase 3 的目标是把它升级为**持久化短期记忆能力**。  
本阶段仍然是 session / conversation short-term memory，不是长期记忆系统，也不是 RAG。

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
- 未定义持久化 store contract 与配置边界，不进入 Phase 3 实现
- 未明确 TTL / reset / namespace 语义，不允许上线持久化短期记忆能力
