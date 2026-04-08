---
name: python-context-capability
description: 用于在 vi_ai_core_service 中实现与治理短期会话上下文能力（Context Engineering），当前聚焦 Phase 2 收尾：token-aware selection/truncation、deterministic summary、reset、trace 与测试一致性。
last_updated: 2026-04-08
---

# 目的

本 skill 用于指导 `app/context/` 相关任务的执行，目标是让短期会话历史治理具备：

- 边界清晰
- 可配置
- 可测试
- 可回归
- 可演进

并确保与 `request_assembler`、`chat_service`、API reset 路由联动一致。

---

# 当前阶段约束（必须遵守）

当前是 **Context Engineering Phase 2 收尾阶段**，必须遵守：

- 默认主链路已是 `token-aware selection -> token-aware truncation -> deterministic summary -> serialization`。
- summary 为确定性策略，不调用外部 LLM。
- 必须保留最近 raw message，不允许默认 summary 吞掉最新原始上下文。
- `summary_then_drop_oldest` 与 `drop_oldest` 必须有真实行为差异。
- 支持 `reset_session` / `reset_conversation` 与 `/chat/reset`。
- 不引入 Redis/DB、RAG、长期记忆、语义检索、分布式状态系统。

---

# 适用场景

- 修改 `app/context/models.py`、`manager.py`、`stores/*`。
- 修改 `app/context/policies/*`（selection/truncation/summary/serialization/tokenizer）。
- 修改 `app/services/request_assembler.py` 的 context pipeline 接入逻辑。
- 修改 reset 相关 service/API 行为。
- 修改 context trace 字段或 context 相关测试。

---

# 不适用场景

- 实现长期记忆平台、RAG、向量检索。
- 引入持久化存储（Redis/DB）。
- 在 context 层接入 provider SDK 或 HTTP 调用。
- 在 context 层实现最终 prompt 顺序装配。
- 在 summary 中实现外部 LLM 摘要链路。

---

# 分层职责

Context 层负责：

- 会话历史 canonical 模型
- store 抽象与 in-memory 实现
- manager façade
- token-aware 策略与 deterministic summary 策略
- 策略执行 trace

Context 层不负责：

- API 接入
- 业务编排
- provider 协议
- prompt 资产管理

---

# 必要输入

开始前必须确认：

1. 当前任务是否属于 context 边界。
2. `ContextPolicyConfig` 的预算与 fallback 配置。
3. 是否影响 `request_assembler` trace 字段。
4. 是否影响 reset 语义（session/conversation）。
5. 需要补哪些策略与回归测试。

---

# 预期输出

至少产出：

1. context 策略实现（含 fallback 语义差异）。
2. trace 字段收敛（分阶段计数与预算语义）。
3. token accounting 近似策略可配置（如 `message_overhead_tokens`）。
4. reset 路由/服务行为稳定。
5. 测试覆盖与文档回写完成。

---

# 必要流程

1. 先读根目录四文档与 `app/context/AGENTS.md`。
2. 审查 `app/context/*`、`request_assembler.py`、reset API/service 流程。
3. 先修边界与策略语义，再修 trace，再补测试。
4. 跑测试验证主链路回归。
5. 回写根目录文档、模块文档、skill 资产文档。

---

# 设计规则

1. 默认策略顺序不可变：selection -> truncation -> summary -> serialization。
2. summary 默认行为必须“保最近 raw、压 summary、删更旧 raw”。
3. fallback 行为必须可区分、可测试、可解释。
4. token 计数保持 provider-agnostic；允许工程近似，但要显式说明。
5. trace 命名必须稳定，避免多义字段混用。
6. reset 只影响目标 session/conversation，不做跨范围删除。

---

# 验证标准

至少验证：

- token-aware selection 在不同预算下行为正确；
- truncation 对超长消息处理正确；
- summary 默认不吞最近 raw；
- 两种 fallback 行为有差异；
- summary disabled 为 no-op；
- serialization 顺序正确；
- assembler trace 字段齐全且语义一致；
- reset session/conversation 行为正确。

---

# 完成标准

任务完成至少表示：

1. Phase 2 主链路行为正确且收尾一致；
2. 代码、测试、文档、skill 四者一致；
3. 未越界进入 persistence/RAG/长期记忆；
4. 主链路回归测试通过。

---

# 备注

- `message_overhead_tokens` 属于当前阶段工程近似，不等于生产级精确计费。
- phase 3/4 才考虑长期记忆、RAG 和记忆来源融合。

---

# 编码前输出要求

必须先输出：

1. in scope / out of scope；
2. 文件级改动计划；
3. 风险与假设；
4. 验证计划。

---

# 编码后输出要求

必须输出：

1. 文件级变更清单；
2. 行为变化说明；
3. 测试结果；
4. 文档回写说明；
5. 下一阶段建议（不实现）。

---

# 资产与验证索引

1. 检查清单：`assets/context_capability_checklist.md`
2. 测试矩阵：`assets/context_test_matrix.md`
3. 参考文档：`references/context_boundaries_and_acceptance.md`

---

# 治理联动

统一闭环：

`根目录文档 -> app/context/AGENTS.md -> 本 skill -> 代码实现 -> review -> 文档回写`

禁止跳步执行。
