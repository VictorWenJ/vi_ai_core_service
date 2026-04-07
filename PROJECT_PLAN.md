# PROJECT_PLAN.md

> 更新日期：2026-04-07


## 1. 文档定位

本文件定义 `vi_ai_core_service` 的项目级阶段规划与演进路线。

本文件只描述项目整体层面的建设目标、阶段重点、优先级与里程碑，  
不展开到具体模块内部实现细节。  
模块内部计划应写在各模块自身文档中，而不是写在本文件中。

---

## 2. 项目总体目标

`vi_ai_core_service` 的总体目标是：

构建一个边界清晰、结构可扩展、具备多模型接入能力的 Python AI 核心服务，为后续更完整的 AI 应用能力建设提供稳定基础。

当前阶段，项目重点不是追求能力数量，而是先建立：

- 正确的目录结构
- 正确的分层方式
- 正确的文档体系
- 正确的调用链
- 正确的能力边界

---

## 3. 当前阶段的建设原则

### 3.1 先打基础，再扩能力

当前优先级是：

1. 项目级文档治理
2. 模块级文档治理
3. 基础调用链稳定
4. 基础 Provider 能力稳定
5. 基础 Prompt / Context 能力稳定
6. 测试与回归保护

而不是立即扩展大量新能力模块。

### 3.2 先做主链路，再做高级特性

当前优先保障：

- 请求能够正确进入系统
- 能正确完成 Prompt / Context / Provider 协作
- 能得到一致、可测试的返回结果

高级特性如：

- RAG
- Agent
- Tool orchestration
- 多模态
- Streaming 深度治理

可以后续逐步引入。

### 3.3 先保证边界正确，再考虑复杂度提升

如果边界不清晰，即使功能跑通，也会让后续演进成本快速上升。  
所以当前阶段，架构边界和文档治理优先级很高。

### 3.4 当前阶段能力声明（强约束）

当前阶段只要求“基础设施 + 主链路可运行可测试”，实现边界明确如下：

- 已实现并要求稳定：
  - HTTP 服务化调用方式（`app/server.py`）为唯一运行入口
  - LLM API 单轮会话
  - 非流式输出（`stream=False`）
  - API -> services -> prompts/context/providers 主链路
  - 最小必要测试回归
  - observability 最小基础设施实现（`log_until.py` 统一日志上报 + 前缀/`message=<json>` 输出）
- 仅预留，不作为本阶段验收项：
  - streaming
  - 多模态真实落地
  - tools/function calling 真正实现
  - structured output 真正实现
  - context persistence / summary / compaction
  - prompt orchestration engine
  - 新 provider 的完整接入

### 3.5 当前阶段 observability 建设目标（新增）

当前阶段 observability 只做最小基础设施落地，不做平台化建设。范围限定为：

- 统一 logging 基础设施实现（Python 标准库 `logging`）
- 统一前缀日志输出（`<time> <level> [<thread>] <logger> <file>:<line> event=<event>`）
- 统一业务日志体输出（`message=<json>`）
- 统一日志上报函数（`app/observability/log_until.py`）
- startup/API/service/provider 的主链路摘要日志
- 当前阶段业务 payload 默认可输出（调试优先）
- `LOG_*` 配置项保留在 `AppConfig`，但当前尚未接入日志运行时开关
- 凭据字段（如 API key、Authorization）必须禁止输出

当前阶段明确不做：

- tracing 平台
- metrics 平台
- alerting 平台
- APM 平台

---

## 4. 当前已确认的系统层次

当前项目先按以下七层组织：

1. API 接入层
2. 应用编排层
3. 上下文管理层
4. Prompt 资产层
5. 模型 API 接入层
6. 可观测性基础设施层
7. 数据模型层

本阶段不继续额外拆出更多系统层次，除非出现明确需求。

---

## 5. 项目阶段划分

## 阶段一：文档治理与结构固化

### 目标

建立项目级与模块级文档体系，明确项目边界、模块边界、依赖方向与开发规则。

### 重点

- 完成根目录：
  - `AGENTS.md`
  - `PROJECT_PLAN.md`
  - `ARCHITECTURE.md`
  - `CODE_REVIEW.md`
- 完成各模块目录的 `AGENTS.md`
- 固化当前七层系统划分（含 observability 横切层）
- 明确根目录文档与模块文档的职责边界

### 本阶段完成标准

- 项目总纲清晰
- 模块职责清晰
- 文档边界清晰
- Codex 协作入口清晰

---

## 阶段二：基础主链路稳定化

### 目标

让系统当前已有的基础主链路结构稳定，做到可运行、可理解、可测试。

### 重点

- 稳定 API -> services -> prompts/context/providers 的主链路
- 稳定 LLM 调用流程
- 稳定 Prompt 读取与渲染行为
- 稳定 Provider 注册与归一化能力
- 稳定 Context 的基础管理能力
- 固化 observability 的统一日志上报规范（`log_until.py` + 前缀/`message=<json>`）
- 维持 Schema 层的共享契约清晰性

### 本阶段完成标准

- 主调用链清晰
- 层间职责未混乱
- 基础单元测试可支撑回归

---

## 阶段三：Provider 体系增强

### 目标

让模型接入层从“能接多个厂商”进一步演进到“接入规则统一、维护成本可控”。

### 重点

- 统一 provider 抽象
- 明确兼容族基类复用方式
- 稳定 provider registry
- 补齐 provider 归一化测试
- 为未来 streaming / usage / error normalization 留出扩展点

### 本阶段完成标准

- 新增 provider 有清晰接入规范
- provider 差异尽量在模块内部被吸收
- 上层不承受大量厂商特例

---

## 阶段四：Prompt 与 Context 能力增强

### 目标

让 Prompt 与 Context 从“基础可用”进入“可治理、可扩展”状态。

### 重点

- Prompt 模板组织进一步规范化
- 渲染行为进一步稳定
- 上下文模型与存储抽象进一步清晰
- 为未来上下文裁剪、摘要、持久化等能力预留接口

### 本阶段完成标准

- Prompt 资产不再零散
- Context 结构不再混乱
- 后续扩展不会推翻现有基础

### 阶段四-A：Context Engineering Phase 1

#### 目标

将当前最小可用的上下文读写骨架，升级为可治理、可扩展、面向 C 端 AI 对话产品的上下文装配骨架。

本阶段重点不是构建长期记忆平台，而是把一次模型请求中的上下文治理流程做正确，包括：

- 上下文 source of truth 明确化
- 上下文窗口选择接口化
- 截断策略接口化
- 历史序列化接口化
- request assembly 中的上下文装配流程正式化

#### In Scope

1. `ContextPolicy` 组合策略占位
2. `WindowSelectionPolicy` 接口与默认实现
3. `TruncationPolicy` 接口与最小实现
4. `HistorySerializationPolicy` 接口与默认实现
5. `ContextSelectionResult` 等中间结果模型
6. `ContextManager` 与 `ContextStore` 契约增强
7. `app/services/request_assembler.py` 升级为正式上下文装配入口
8. 最近 N 条消息窗口治理
9. 可观测的上下文装配 metadata / trace

#### Out of Scope

- RAG 检索链路
- 向量数据库
- Redis / DB persistence
- summary memory
- semantic retrieval memory
- user profile memory
- token-aware 精准预算控制
- distributed state / MQ / workflow engine

#### 本阶段完成标准

1. 服务端 stateful session history 不再以“全量原样拼接”的方式参与请求
2. 上下文 history 的选择、截断、序列化具备清晰接口
3. request assembly 中上下文治理顺序清晰、稳定、可测试
4. context 层与 services 层边界未被打穿
5. 未来 token budget / summary / persistence / RAG 可以在不推翻当前结构的前提下继续演进

### 阶段四-B：Context Engineering Phase 2

#### 目标

将 Context skeleton 升级为 **token-aware**，具备预算感知的窗口选择、截断和摘要/压缩能力，并提供会话重置能力。保证在不破坏现有主链路基础上，引入能够精确控制历史消息长度和成本的策略，为未来长期记忆/RAG/多模态扩展打下基础。

#### 重点

1. **Token-aware context policy**：增加 `TokenAwareWindowSelectionPolicy` 和 `TokenAwareTruncationPolicy`，根据最大 token 预算而不是固定消息数量选择与截断历史。
2. **Summary/Compaction Policy**：定义 `SummaryPolicy` 或 `CompactionPolicy` 接口，引入最小摘要策略以浓缩超出预算的历史消息，并保留关键信息。
3. **Context Reset API**：在 API 层实现会话重置/清空接口，允许用户主动清理服务端会话上下文。
4. **request assembler 升级**：在 `app/services/request_assembler.py` 中集成新的 token-aware pipeline 和摘要/裁剪机制，并暴露 context assembly trace。
5. **文档与测试治理**：同步更新模块文档与 skill，补充 token-aware 选择、截断、摘要以及 reset 行为的测试覆盖。

#### In Scope

- Context policy 抽象和默认实现的增加。
- 新的 `ContextPolicyPipeline` 组合策略流程。
- 概念验证级别的摘要策略或占位。
- API 层新增 reset/clear 路由。
- request assembly 的 token-aware 裁剪流程。
- 文档治理、code review checklist 和基础测试。

#### Out of Scope

- 持久化存储、Redis/DB store 或分布式状态系统。
- 完整语义摘要或大模型 summarization 服务。
- 工具调用、多模态生成或工具链 orchestration。
- 长期记忆平台、RAG memory 或向量检索。

#### 本阶段完成标准

1. `WindowSelectionPolicy`、`TruncationPolicy` 增加 token-aware 默认实现，能基于 token 预算确定历史窗口。
2. 提供 `SummaryPolicy` 或 `CompactionPolicy` 接口，并实现最小摘要策略或示例。
3. request assembler 能根据 token 预算选择/截断/摘要历史，并输出 context assembly trace。
4. API 层新增 reset/clear 会话路由，正确清空服务端会话历史。
5. 基础测试覆盖 token-aware 选择、截断、摘要和 reset 行为。

---

## 阶段五：系统扩展准备

### 目标

在现有七层稳定后，为未来新增能力模块做准备。

### 可能方向

- `app/rag/`
- `app/agents/`
- `app/tooling/`
- `app/evaluation/`
- 更细的内部 contract 分层
- integration tests / e2e tests

### 注意

这些方向不是当前阶段必须立即实现的内容，  
只有在当前基础足够稳定后，才进入正式项目计划。

---

## 6. 当前阶段优先级排序

当前项目级优先级建议如下：

### P0：必须优先完成

- 根目录文档体系正确建立
- 模块级文档体系正确建立
- 当前七层边界清晰（含 observability 横切层）
- 基础主链路清晰
- 基础测试可用
- Context Engineering Phase 1 的文档边界与接口骨架明确

### P1：当前阶段重要但可稍后推进

- Provider 体系进一步统一
- Prompt 资产治理进一步增强
- Context Policy Pipeline 落地
- request assembly 的上下文治理增强
- **Context Engineering Phase 2 的 token-aware 与摘要能力**

### P2：后续阶段能力

- RAG
- Agent
- Tool use
- 更复杂的上下文治理
- 更复杂的调度与治理能力
- 多模态与高级输出能力

---

## 7. 当前阶段不建议做的事情

当前阶段不建议：

1. 提前新增大量未来目录
2. 过早把系统拆成过多抽象层
3. 为没有需求的能力设计复杂框架
4. 在没有文档约束前大规模重构
5. 在模块边界不清晰时继续快速叠功能
6. 把 Context Engineering Phase 1 直接做成 RAG / 长期记忆 / persistence 工程

---

## 8. 项目推进方式

项目建议按以下方式推进：

1. 先固化文档体系
2. 再校正目录与分层
3. 再稳定主链路
4. 再增强 provider / prompt / context
5. 最后再考虑新增系统能力

在 Context Engineering Phase 1 中，继续沿用这一节奏：

1. 先升级根目录文档
2. 再升级 `app/context/AGENTS.md` 与 `app/services/AGENTS.md`
3. 再升级 `skills/python-context-capability/`
4. 再落地 context policy pipeline 代码
5. 最后补测试与文档回写

这样做的目标是降低返工成本，提升后续协作效率。

---

## 9. 里程碑定义

### M1：文档治理完成

标志：

- 根目录四个总文档完成
- 七个模块级 `AGENTS.md` 完成
- 文档边界清晰

### M2：主链路稳定

标志：

- API 到 service 到 provider/prompt/context 的链路稳定
- 现有测试基础可用

### M3：Provider 体系规范化

标志：

- 新增 provider 有明确规范
- 归一化行为稳定

### M4：Prompt / Context 能力可治理

标志：

- Prompt 资产与 Context 结构具备可持续演进基础
- Context Engineering Phase 1 的接口与装配流程完成文档化

### M4-A：Context Engineering Phase 1 完成

标志：

- `request_assembler.py` 具备正式上下文装配入口职责
- 最近 N 条消息 history selection 具备默认策略
- truncation / serialization 具备正式接口
- 主链路测试已覆盖上下文治理行为

### M4-B：Context Engineering Phase 2 完成

标志：

- `TokenAwareWindowSelectionPolicy`、`TokenAwareTruncationPolicy` 提供默认实现
- `SummaryPolicy` / `CompactionPolicy` 定义并提供最小实现
- request assembly 支持 token-aware pipeline 并输出 trace
- reset/clear API 正确落地
- 相关文档和测试更新完备

### M5：扩展能力准备完成

标志：

- 可有序引入 RAG / Agent 等新模块，而不破坏现有体系

---

## 10. 一句话总结

本项目当前的核心计划不是“快速堆功能”，而是先完成 **文档治理、结构治理、主链路稳定化和核心 AI 能力基础设施固化**，为后续更复杂能力建设打基础。

在 Context Engineering Phase 1 中，这一原则的具体体现是：先把“服务端历史如何进入一次模型请求”做成正式的上下文治理流程；在 Context Engineering Phase 2 中，则进一步引入 token-aware 窗口选择、截断和摘要能力以及会话重置能力，仍然不进入长期记忆或 RAG 平台建设。

---

## 11. 文档驱动闭环计划（新增）

从当前轮次开始，项目执行模式固定为：

`根目录文档 -> 模块 AGENTS -> 对应 skill -> 代码实现 -> review -> 文档回写`

### 阶段化落地要求

- 阶段 1：先审查根文档、模块文档、skills 和核心代码现实，输出不一致点
- 阶段 2：先修文档治理体系，再进入代码升级
- 阶段 3：基于新文档体系输出 `P0/P1/P2` 升级清单
- 阶段 4：按优先级做小步代码改造与必要测试
- 阶段 5：交付文档升级、代码升级、验证结果与标准流程模板

### 里程碑门禁（新增）

- 没有完成文档链路定义，不进入代码改动
- 没有完成模块-skill 映射，不进入大于单文件的重构
- 没有完成回写检查，不允许视为任务完成

### Context Engineering Phase 1 专项门禁

- 未定义 `WindowSelectionPolicy` / `TruncationPolicy` / `HistorySerializationPolicy` 的职责边界，不进入上下文主链路重构
- 未明确 `request_assembler.py` 是正式上下文装配入口，不进入 context policy pipeline 落地
- 未明确 RAG 与 context history 的边界，不进入“记忆系统”类设计

### Context Engineering Phase 2 专项门禁（新增）

- 未明确 token-aware 选择、截断、摘要策略的接口和职责，不进入 Phase 2 架构实现
- 未明确 reset/clear API 的边界和触发方式，不进入会话重置能力开发
- 未更新相关文档与 skill，不上线 token-aware 或摘要特性

---