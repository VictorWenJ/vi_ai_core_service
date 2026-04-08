# Context 层边界与验收标准

> 更新日期：2026-04-08

## 一、边界定义

### Context 层负责什么

- 会话历史 canonical model（message/window/策略中间结果）。
- store 抽象与 in-memory 实现。
- manager façade（get/append/reset/replace）。
- token-aware selection/truncation。
- deterministic summary/compaction。
- history serialization 与策略 trace。

### Context 层不负责什么

- API 协议接入。
- service 业务编排。
- provider SDK / HTTP 调用。
- prompt 模板管理与 system prompt 选择。
- RAG/检索/长期记忆/持久化平台。

---

## 二、必须遵守的原则

1. Context 层必须 provider-agnostic。
2. 默认策略顺序必须固定：selection -> truncation -> summary -> serialization。
3. 默认 summary 行为必须保留最近 raw message，不允许 summary 吞掉最新原始上下文。
4. `summary_then_drop_oldest` 与 `drop_oldest` 必须有可测试的行为差异。
5. token accounting 允许工程近似，但必须可配置且语义透明。
6. reset 必须显式触发，通过 manager/service/API 逐层调用，不允许 API 直改 store 私有状态。

---

## 三、典型反模式

1. 在 `chat_service` 或 API 层手写 token budget/summary 逻辑。
2. `summary_then_drop_oldest` 默认吞掉最近 raw message。
3. fallback 配置有两个值，但代码路径行为几乎一致。
4. trace 只有一个 `dropped_message_count` 且无法区分阶段来源。
5. context 层直接接入 provider 或外部 LLM 摘要。
6. reset 逻辑跨 session/conversation 误删数据。

---

## 四、验收标准

一个合格的 Phase 2 收尾结果至少满足：

1. 默认 token-aware 主链路稳定运行。
2. summary 默认不吞最近 raw message。
3. fallback 两条路径语义明确且测试覆盖。
4. trace 字段可用于 selection/truncation/summary 分阶段排查。
5. `/chat/reset`、`reset_session`、`reset_conversation` 行为可回归验证。
6. 文档、skill、代码、测试四者一致。
7. 未越界进入长期记忆、RAG、持久化平台。

---

## 五、一句话总结

Context Phase 2 的收尾目标是：在保持短期会话边界稳定的前提下，让 token-aware 策略、summary 行为、reset 能力和 trace 语义都“可解释、可测试、可交付”。
