# app/context/AGENTS.md

> 更新日期：2026-04-08

## 1. 文档定位

本文件定义 `app/context/` 模块的职责边界、演进约束、交付门禁与 review 标准。  
执行 context 相关任务时，必须先读根目录四文档，再读本文件，再执行 `skills/python-context-capability/`。

---

## 2. 模块定位

`app/context/` 是短期会话上下文治理层，负责 provider-agnostic 的会话历史表示、存储抽象和策略执行。  
当前处于 **Context Engineering Phase 2 收尾阶段**，默认主链路已落地：

- token 感知窗口选择（token-aware window selection）
- token 感知截断（token-aware truncation）
- 确定性摘要/压缩（deterministic summary/compaction）
- 历史序列化（history serialization）
- 会话/对话重置（session/conversation reset）

---

## 3. 本层职责

1. 定义 canonical context models（message/window 与策略中间结果）。
2. 定义并实现 store contract 与 in-memory store。
3. 通过 `ContextManager` 暴露统一 façade（get/append/reset/replace）。
4. 实现 `WindowSelectionPolicy` / `TruncationPolicy` / `SummaryPolicy` / `HistorySerializationPolicy`。
5. 通过 `ContextPolicyPipeline` 提供固定顺序执行与可观测 trace。
6. 保持 token 预算、fallback、summary 开关等参数可配置。

---

## 4. 本层不负责什么

1. 不负责 HTTP 接入与路由。
2. 不负责业务流程编排。
3. 不负责 provider payload 协议。
4. 不负责 prompt 模板管理与 system prompt 选择。
5. 不负责 RAG、长期记忆、Redis/DB 持久化。
6. 不负责外部 LLM 摘要编排。

---

## 5. 依赖边界

- 允许依赖：`app/schemas/`（必要契约）、`app/config.py`、标准库。
- 禁止依赖：`app/api/`、`app/services/`、`app/providers/` 的业务流程实现。
- `services/request_assembler.py` 可调用 context 层；context 层不得反向依赖 assembler/service。

---

## 6. 当前默认行为（Phase 2 收尾版）

默认管线顺序固定为：

`token-aware selection -> token-aware truncation -> summary/compaction -> serialization`

### 6.1 选择（selection）

- 有 session 历史时按 token budget 选择窗口，不再默认全量拼接。

### 6.2 截断（truncation）

- 当 selected history 超预算时做 token-aware 截断。
- 优先保留最近消息；必要时截断更旧消息内容。

### 6.3 摘要（summary）

- 默认 `DeterministicSummaryPolicy`，不调用外部 LLM。
- 默认 `fallback_behavior=summary_then_drop_oldest` 必须遵守：
  1. 不吞掉最近 raw message；
  2. 先截短 summary；
  3. 再删除更旧 raw history。
- `drop_oldest` 作为独立 fallback，允许直接按最老优先丢弃（包含 summary）。

### 6.4 序列化（serialization）

- 输出 provider-agnostic 的 `{role, content}` 列表给 assembler。

### 6.5 追踪信息（trace）

- 必须区分 selection / truncation / summary 三阶段计数与预算字段。
- 必须包含 token counter 类型（例如 `tokenizer.tiktoken_cl100k_base` / `tokenizer.character_fallback`）。
- `message_overhead_tokens` 属于当前阶段工程近似，不是精确计费。

---

## 7. 修改规则

1. 任何策略改动必须保持 provider-agnostic。
2. 不允许在 context 层直接接入外部 LLM 做摘要。
3. 不允许在 context 层拼接最终 `system + history + user` 顺序。
4. reset 行为必须通过 manager 暴露，不允许 API/service 直改 store 私有状态。
5. 变更策略语义时必须同步更新测试与 skill 文档。

---

## 8. Code Review 清单

1. 是否存在 context 反向依赖 service/api 的越层行为？
2. 管线顺序是否仍为 selection->truncation->summary->serialization？
3. `summary_then_drop_oldest` 与 `drop_oldest` 是否行为有差异？
4. 默认 summary 是否会吞掉最近 raw message（必须为否）？
5. token 预算与 overhead 是否可配置且语义清晰？
6. trace 字段是否可用于阶段级排查，命名是否无歧义？

---

## 9. 测试门禁

至少覆盖：

1. token-aware selection 在不同预算下的行为；
2. token-aware truncation 对超长消息的处理；
3. summary 默认行为不吞最近 raw；
4. 两种 fallback 行为差异；
5. summary disabled 的 no-op 路径；
6. 会话级重置（reset session）/ 对话级重置（reset conversation）；
7. assembler 的 message 顺序与 trace 字段。

---

## 10. 一句话总结

`app/context/` 在 Phase 2 的目标是：在不引入长期记忆平台的前提下，把短期会话历史治理做成可配置、可测试、可演进、可排查的 token-aware 策略管线。
