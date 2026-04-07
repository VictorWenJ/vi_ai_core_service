# app/context/AGENTS.md

> 更新日期：2026-04-07

## 1. 文档定位

本文件约束 `app/context/` 的模块职责、边界、演进和 review 标准。

执行 context 相关任务时，必须先读根目录四文档，再读本文件，再执行 `skills/python-context-capability/`。

---

## 2. 模块定位

`app/context/` 是短期会话上下文治理层，负责历史消息的表示、选择、截断、压缩与存储抽象。

当前阶段为 **Context Engineering Phase 2**，已落地：

- token-aware window selection
- token-aware truncation
- deterministic summary/compaction
- session/conversation reset

---

## 3. 本层职责

1. 定义 provider-agnostic 的 context canonical models。
2. 定义并实现 store contract 与 in-memory store。
3. 通过 `ContextManager` 暴露统一入口。
4. 提供 `WindowSelectionPolicy` / `TruncationPolicy` / `SummaryPolicy` / `HistorySerializationPolicy`。
5. 通过 `ContextPolicyPipeline` 输出可观测 trace 数据。

---

## 4. 本层不负责什么

1. 不负责 HTTP 接口接入。
2. 不负责业务主流程编排。
3. 不负责 provider 协议与请求 payload 细节。
4. 不负责 prompt 模板管理与最终 prompt 顺序装配。
5. 不负责 RAG、长期记忆、Redis/DB 持久化。

---

## 5. 依赖边界

- 允许依赖：`app/schemas/`（必要契约）、基础配置、标准库。
- 禁止依赖：`app/api/`、`app/services/`、`app/providers/` 的业务流程实现。
- `request_assembler.py` 调用 context 层策略；context 层不得反向依赖 assembler。

---

## 6. 当前默认策略（Phase 2）

默认 pipeline 顺序固定为：

`token-aware selection -> token-aware truncation -> summary/compaction -> serialization`

默认行为：

1. 有 `session_id` 时读取服务端历史。
2. 按 token budget 选择最近历史。
3. 超预算时执行 token-aware 截断。
4. 仍有被丢弃历史且 summary 开启时，插入 deterministic summary message。
5. 输出结构化 trace（policy 名称、计数、预算、是否截断/摘要）。

---

## 7. 修改规则

1. 任何策略改动必须保持 provider-agnostic。
2. 不允许在 context 层直接调用外部 LLM 做摘要。
3. 不允许在 context 层实现最终 `system + history + user` 装配。
4. reset 行为必须通过 manager 对外暴露，不允许 API/service 直接操作 store 私有状态。
5. 改动策略契约时必须同步更新测试和 skill 资产文档。

---

## 8. Code Review 清单

1. 是否存在越层依赖（尤其 context 反向依赖 service/api）。
2. 策略顺序是否仍是 selection->truncation->summary->serialization。
3. token budget 是否配置化，避免硬编码散落。
4. summary 是否保持确定性、低耦合、可测试。
5. reset 是否仅作用于目标 session/conversation。
6. metadata trace 是否完整且可用于排查。

---

## 9. 测试门禁

至少验证：

1. token-aware selection 行为。
2. token-aware truncation 行为。
3. summary 默认行为与预算约束。
4. reset session / reset conversation 行为。
5. assembler 接入后的顺序与 trace 字段。

---

## 10. 一句话总结

`app/context/` 在 Phase 2 的目标是：在不引入长期记忆平台的前提下，把短期会话历史治理做成可配置、可测试、可演进的 token-aware pipeline。

