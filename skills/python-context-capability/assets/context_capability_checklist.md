# Context 能力检查清单

> 更新日期：2026-04-08

## 目录与落位

- [ ] Context 相关代码位于 `app/context/`，未越层散落。
- [ ] `request_assembler.py` 作为上下文装配入口，未反向下沉到 API/chat_service。
- [ ] 未新增与当前阶段无关的新系统层。

## 基础结构

- [ ] `models.py` 定义 canonical message/window 与策略结果模型。
- [ ] `stores/base.py` 契约清晰，包含 reset 与 replace 能力。
- [ ] `stores/in_memory.py` 行为与 store 契约一致。
- [ ] `manager.py` 仅做 façade，不承担业务编排。

## 策略链路（Phase 2）

- [ ] 默认顺序固定：selection -> truncation -> summary -> serialization。
- [ ] 默认 selection 为 token-aware，不再以 last-N 作为主策略。
- [ ] 默认 truncation 为 token-aware，支持超长消息截断。
- [ ] 默认 summary 为 deterministic，不调用外部 LLM。
- [ ] `summary_then_drop_oldest` 不吞掉最近 raw message。
- [ ] `drop_oldest` 与 `summary_then_drop_oldest` 行为有真实差异。

## Token 语义

- [ ] token 计数保持 provider-agnostic。
- [ ] `message_overhead_tokens` 可配置或可覆写。
- [ ] trace 中能看到 token counter 类型与关键预算字段。
- [ ] 文档明确当前 token accounting 是工程近似，不是精确计费。

## Reset 行为

- [ ] `reset_session` 与 `reset_conversation` 均可用。
- [ ] `/chat/reset` 通过 service 调用 manager，不直接操作 store 私有状态。
- [ ] conversation 级 reset 不误删其他 conversation。

## Trace 与契约

- [ ] `context_assembly` 字段区分 selection/truncation/summary 三阶段语义。
- [ ] dropped 计数语义不混淆（阶段计数 + 总计数）。
- [ ] 保留兼容字段时有明确标注，不与 canonical 字段冲突。

## 当前阶段约束

- [ ] 未引入 Redis/DB 持久化。
- [ ] 未引入 RAG/语义检索/长期记忆系统。
- [ ] 未引入 streaming/tools/multimodal 的真实链路。

## 验证与测试

- [ ] context policy 核心行为测试已覆盖。
- [ ] request assembler trace/顺序测试已覆盖。
- [ ] reset session/conversation 测试已覆盖。
- [ ] 主链路回归测试通过。
