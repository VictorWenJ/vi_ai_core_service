# Context 能力检查清单

> 更新日期：2026-04-08

## 目录与落位

- [ ] Context 相关代码位于 `app/context/`，未越层散落
- [ ] `request_assembler.py` 作为上下文装配入口，未反向下沉到 API / chat_service
- [ ] 未新增与当前阶段无关的新系统层

## 基础结构

- [ ] `models.py` 定义 canonical message/window 与策略结果模型
- [ ] `stores/base.py` 契约清晰，包含 get / append / replace / reset 能力
- [ ] `stores/in_memory.py` 行为与 store 契约一致
- [ ] `manager.py` 仅做 façade，不承担业务编排

## 策略链路（Phase 2 既有能力）

- [ ] 默认顺序固定：selection -> truncation -> summary -> serialization
- [ ] 默认 selection 为 token-aware
- [ ] 默认 truncation 为 token-aware
- [ ] 默认 summary 为 deterministic，不调用外部 LLM
- [ ] Phase 3 改动未破坏 Phase 2 默认主链路

## Phase 3：持久化短期记忆

- [ ] store backend 可配置（至少 `memory` / `redis`）
- [ ] `RedisContextStore`（或等价持久化 store）位于 `app/context/stores/`
- [ ] Redis/持久化细节未泄漏到 API / service 层
- [ ] `ContextStorageConfig`（或等价配置）与 `ContextPolicyConfig` 职责分离
- [ ] `CONTEXT_STORE_BACKEND` / `CONTEXT_REDIS_URL` / `CONTEXT_SESSION_TTL_SECONDS` / `CONTEXT_STORE_KEY_PREFIX` / `CONTEXT_ALLOW_MEMORY_FALLBACK` 已接入并可测试
- [ ] session TTL / key prefix / namespace 有明确配置
- [ ] `ContextManager` 继续是统一 façade，不被上层绕过
- [ ] request-time 能读取持久化 session history
- [ ] response-time 能稳定写回 user / assistant 历史
- [ ] `reset_session` 与 `reset_conversation` 在持久化 store 上行为正确
- [ ] dev/test 可使用 `InMemoryContextStore` 作为 fallback

## Token 与 Trace 语义

- [ ] token 计数保持 provider-agnostic
- [ ] `message_overhead_tokens` 可解释、可配置或可覆写
- [ ] trace 中能看到 token counter 类型与关键预算字段
- [ ] trace 字段区分 selection / truncation / summary 三阶段语义
- [ ] 文档明确当前 token accounting 仍是工程近似，不是精确计费

## Reset 与生命周期

- [ ] `/chat/reset` 通过 service 调用 manager，不直接操作 store 私有状态
- [ ] conversation 级 reset 不误删其他 conversation
- [ ] session TTL 行为清晰、可测试
- [ ] reset / replace / append 语义未互相冲突

## 当前阶段约束

- [ ] 未引入 Redis 以外的复杂持久化平台
- [ ] 未引入 RAG / 语义检索 / 长期记忆系统
- [ ] 未引入 streaming / tools / multimodal 的真实链路

## 验证与测试

- [ ] context policy 核心行为测试已覆盖
- [ ] request assembler trace / 顺序测试已覆盖
- [ ] Redis store 基本读写测试已覆盖
- [ ] reset session / conversation 测试已覆盖
- [ ] 主链路回归测试通过
