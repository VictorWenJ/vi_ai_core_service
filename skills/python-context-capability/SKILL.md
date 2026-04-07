---
name: python-context-capability
description: 用于为 vi_ai_core_service 搭建和标准化面向 C 端 AI 应用的上下文管理层骨架。重点关注 session 级短期记忆、conversation state、消息历史、多模态消息结构、store 抽象、in-memory 实现、manager 入口，以及为未来压缩/摘要/持久化策略预留扩展点。本版文档更新至 Context Engineering Phase 2，增加了 token‑aware 策略、压缩策略和会话重置相关能力。
last_updated: 2026-04-07
---

# Purpose

本 skill 用于指导 `vi_ai_core_service` 中上下文管理层的新增、整理与标准化工作。

它面向的是当前主流 C 端 AI 应用产品中最常见的 context backend 形态，而不是传统“只存一个 messages list”的简化模型。

本 skill 的目标是为 `app/context/` 建立一个：

- 清晰
- 轻量
- 可扩展
- 面向多轮产品形态
- 不绑死某个 provider

的 context skeleton。

本 skill 重点解决的问题包括：

- 如何区分 conversation/session 级短期上下文
- 如何定义可扩展的 message / turn / attachment 元数据
- 如何建立 store 抽象
- 如何提供 in-memory 最小实现
- 如何通过 manager 暴露统一入口
- 如何为未来 context compaction / summary / token budget / persistence 预留扩展点
- 如何避免把 context 层写成“完整记忆系统”或“业务编排层”
- 如何在第二阶段中引入 token‑aware 窗口选择与截断策略、summary/compaction 策略以及会话重置能力

本 skill 是 **任务执行规范**，不是模块治理文档。  
使用本 skill 前，应先阅读：

1. 项目根目录 `AGENTS.md`
2. 项目根目录 `PROJECT_PLAN.md`
3. 项目根目录 `ARCHITECTURE.md`
4. 项目根目录 `CODE_REVIEW.md`
5. `app/context/AGENTS.md`

---

# Current Phase Constraint (Must Follow)

在 `vi_ai_core_service` 当前阶段（Context Engineering Phase 2），执行本 skill 时必须默认遵守以下范围：

- Context 层仍以 session/conversation 级短期记忆骨架与 in‑memory 最小实现为基准。
- 在完成 Phase 1 功能的基础上，引入 **token‑aware 窗口选择策略**、**token‑aware 截断策略** 和 **简易的 summary/compaction 策略**，并支持会话重置操作。
- 这些能力只针对短期会话窗口控制，**不实现完整的 long‑term memory platform**、RAG 记忆耦合或分布式状态系统。
- summary/compaction 策略可提供简单摘要或压缩 hook，但不实现复杂的自然语言摘要模型调用。重点是保证接口与策略模式的统一，允许未来按需替换算法。
- 上下文重置能力提供在服务层/API 层暴露的 `reset_conversation`/`clear` 操作，仅清除当前 session/conversation 的短期历史，不涉及持久化或跨用户数据。
- 不引入 Redis/DB 等外部持久化依赖；仅在 `stores/in_memory.py` 中实现 token‑aware 对话窗口控制与重置。
- 重点是 manager/store/models 边界清晰、行为可测、与 service 层协作稳定。

---

# Current Task Focus (Context Engineering Phase 2)

在完成 Phase 1 最小骨架的基础上，本轮重点是将“服务端会话历史如何进入一次模型请求”的逻辑升级为 **token‑aware 调度与压缩/重置能力**。具体任务包括：

1. **TokenAwareWindowSelectionPolicy**：根据会话历史中每条消息的 token 数量以及最大 token budget，动态选择最近一段历史。应使用如 `tiktoken` 的分词器来计算 token 长度，支持配置最大 token 数。不得再使用简单的“最近 N 条”策略作为默认。
2. **TokenAwareTruncationPolicy**：在窗口选择之后，对超过 token budget 的历史进行截断，确保总 token 数符合要求。截断逻辑应截断最旧的消息或部分消息内容，不得破坏最近用户问题与系统 prompt 的完整性。
3. **SummaryPolicy (optional)**：定义并实现一个摘要/压缩策略接口，用于当窗口仍超出 token budget 时生成摘要消息替代部分原始历史。默认可提供一个占位实现，仅将截断部分用固定字符串或第一句总结作为 summary。避免在此阶段调用外部 LLM 进行真实摘要。
4. **Context reset 支持**：在 `ContextManager` 中添加 `reset_conversation`（或 `clear_session`）方法，能够清除会话历史；在 `app/services` 与 API 层引入对应调用入口（例如 `POST /chat/reset`）。重置操作必须经过合理鉴权与参数校验，不得误删其他用户数据。
5. **ContextPolicyPipeline 扩展**：升级 pipeline，依次执行 `TokenAwareWindowSelectionPolicy → TokenAwareTruncationPolicy → SummaryPolicy → HistorySerializationPolicy`。确保 pipeline 可以根据配置插拔策略，并将执行 trace 写入 metadata。
6. **配置与默认值**：在配置中新增 token budget、默认截断预算、summary 开关等参数；`defaults.py` 应提供合理的默认实例。
7. **request_assembler 接入升级策略**：在 `app/services/request_assembler.py` 中通过新的 pipeline 获取历史，并在 metadata 中附带 summary/compaction trace。
8. **更新文档与 checklist**：同步更新根文档和技能 checklist，以反映 token‑aware 能力和重置逻辑。

本轮仍不做：

- Redis / DB store
- 复杂的 summary memory
- semantic recall
- RAG context source
- user profile memory
- toolkit 等工具召回

---

# Use This Skill When

在以下场景中使用本 skill：

- 新增或维护 `app/context/` 下的基础骨架
- 新增或整理 conversation/session 上下文模型
- 新增 store interface
- 新增本地 in‑memory store 实现
- 新增 manager 统一入口
- 为未来 session memory / message history / context governance 做结构准备
- 为多模态消息历史、会话压缩、摘要、持久化预留扩展点
- 校正当前 context 层边界，使其更符合主流 C 端 AI 应用后端结构
- 为 `request_assembler.py` 提供正式上下文治理输入
- **新增 token‑aware window/truncation 策略**
- **新增 summary/compaction 策略接口与默认实现**
- **新增会话重置接口**

---

# Do Not Use This Skill For

以下场景不应使用本 skill：

- 一次性实现完整 long‑term memory system
- 实现 retrieval pipeline / RAG 检索逻辑
- 直接接入数据库、消息队列、分布式状态系统
- 实现在本轮就完成复杂的持久化架构
- 在 context 层中实现 provider 调用逻辑
- 在 context 层中实现业务主流程编排
- 在 context 层中混入 prompt 渲染逻辑
- 把用户画像记忆、检索记忆、工具记忆全部一轮做完
- 在此阶段调用外部模型进行高质量摘要

---

# Layer Responsibility

Context 层负责：

- 定义 conversation / session / turn / message 等上下文相关模型
- 表示短期会话历史
- 抽象上下文存储接口
- 提供本地基础实现
- 通过 manager 向上层暴露统一访问入口
- 为未来上下文压缩、摘要、裁剪、token budget、持久化预留扩展点
- 保持 provider‑agnostic
- 提供 history selection / truncation / serialization 的策略抽象
- **在 Phase 2 中提供 token‑aware selection/truncation/summary 策略与会话重置能力**

Context 层不负责：

- HTTP 接口接入
- 业务主流程编排
- provider SDK / HTTP 调用
- prompt 模板管理与渲染
- retrieval / rerank / grounding
- 当前阶段复杂 persistence / distributed state
- 当前阶段完整长期记忆系统
- 最终 request message 顺序装配
- 在策略中直接调用外部大型语言模型生成摘要

---

# Required Inputs

使用本 skill 前，应明确以下输入信息：

1. 当前这次改动是否真的属于 `app/context/` 职责范围
2. 当前需要管理的是哪类上下文：
   - session memory
   - conversation history
   - message timeline
   - minimal user/session state
3. 上层当前至少需要哪些操作：
   - get conversation
   - append turn/message
   - clear/reset session
   - list messages
   - compact/summarize hook（若只是预留）
4. 当前是否需要支持：
   - stateless 模式（客户端自带历史）
   - stateful 模式（服务端持有 conversation/session）
   - 两者兼容预留
5. 是否存在附件、图片、文件、工具结果等消息元数据需求
6. 当前阶段是否只需要最小可用骨架，而不是完整 memory platform
7. 当前是否已明确 `request_assembler.py` 作为正式上下文装配入口
8. **新的 token budget 需求：最大 token 数、截断预算等配置**
9. **是否需要启用 summary/compaction 与其参数（摘要长度、启用开关）**
10. **是否需要暴露会话重置 API**

---

# Expected Outputs

使用本 skill 完成 Context Engineering Phase 2 后，交付物至少包括：

1. `app/context/models.py`
   - 升级后的 canonical context models
   - 至少包含可承接 selection/truncation/summary 的中间结果模型（如 WindowedHistory，TruncatedHistory，SummarySegment）

2. `app/context/stores/base.py`
   - 明确、稳定的 store interface
   - 支持未来 replace/clear/save 等扩展操作的接口约束

3. `app/context/stores/in_memory.py`
   - 最小可用实现
   - 对新增 store contract 的完整承接
   - 实现 token‑aware 截断与重置

4. `app/context/manager.py`
   - 统一 façade
   - 不越权承担 prompt/provider/service 编排
   - 新增 `reset_conversation` 或类似方法

5. `app/context/policies/*`
   - **`TokenAwareWindowSelectionPolicy`**
   - **`TokenAwareTruncationPolicy`**
   - **`SummaryPolicy`**（默认简单实现）
   - `HistorySerializationPolicy`
   - 可选 `ContextPolicy`

6. `app/services/request_assembler.py`
   - 升级为正式上下文装配入口
   - 通过新的 context policy pipeline 获取历史
   - 不再直接原样拼接全量 history

7. **`app/api` 与 `app/services` 中的会话重置接口**
   - 例如新增 `/chat/reset` endpoint
   - 在 Service 层实现 reset 调度，并调用 `ContextManager.reset_conversation`

8. 必要测试
   - token‑aware window selection
   - token‑aware truncation
   - summary/compaction fallback
   - selection/truncation/summary 组合顺序
   - reset 接口行为

---

# Required Workflow

1. 先确认本次需求是否真的属于 context 层。
2. 先检查根目录文档与 `app/context/AGENTS.md`。
3. 明确当前要承载的是 stateless 历史输入、stateful conversation，还是两者兼容预留。
4. 在 `app/context/` 下定义最小上下文模型以及必要的中间结果模型（例如 WindowedHistory/TruncatedHistory/SummarySegment）。
5. 在 `stores/base.py` 中定义明确、稳定的 store interface；确保接口中包含 reset/clear 会话的定义。
6. 在 `stores/in_memory.py` 中实现本地内存版 store；加入 token 计数与重置逻辑。
7. 在 `manager.py` 中提供统一 façade，包括 get/append/clear/list 操作；新增 reset 接口。
8. 在 `app/context/policies/` 中实现 `TokenAwareWindowSelectionPolicy`、`TokenAwareTruncationPolicy`、`SummaryPolicy`，并更新默认策略工厂。
9. 在 `ContextPolicyPipeline` 中按照正确顺序执行 token‑aware selection → token‑aware truncation → summary → serialization，确保可配置。
10. 在 `app/services/request_assembler.py` 中接入新的 pipeline，并在 metadata 中记录各策略结果和执行 trace；保持 prompt 组装顺序为 system prompt → selected history (after summarization) → user prompt。
11. 在 API 层新增会话重置接口，并在 Service 层调用 context manager 的 reset 方法。
12. 保持实现轻量、确定性、易理解；所有策略应可单测。
13. 对照 checklist 自检，并更新 `assets/context_capability_checklist.md` 与测试矩阵。
14. 若改动影响上下文契约、边界或测试行为，需同步更新文档与测试。

---

# Design Rules

## 1. 先建短期会话骨架，再引入 token‑aware 能力

主流 C 端 AI 产品的第一优先上下文能力仍然是短期记忆骨架，在此基础上逐步引入 token 控制策略；不要在模型或 provider 层混入 token 计数逻辑。

## 2. Token aware 策略应关注 token 数而非字符数

使用如 `tiktoken` 的 tokenizer 计算 token 长度；确保不同语言或编码情况下 token 计数准确。不要简单使用字符串长度代替 token 数。

## 3. Summary/Compaction 策略仅提供 Hook

在 Phase 2 中，summary 策略只需提供一个接口和默认简单实现，例如返回“[previous history truncated]”或提取每条消息的首句。不得在此阶段接入外部 LLM 或复杂 NLP 算法。

## 4. reset 操作需谨慎

重置会话意味着丢弃历史，需要显式 API 调用并记录 audit log。不要在 manager 层隐式自动 reset。

## 5. 管理与存储仍然分离

`manager.py` 负责对上提供访问入口，包括 reset；`stores/` 负责底层存储与 token 管理逻辑。不要把策略或 reset 逻辑写入服务层或 API 层。

## 6. Context 层保持 provider-agnostic

context 层关注的是对话历史与 token 窗口控制，不关心 OpenAI/Deepseek 等 provider 协议。不得在策略中直接访问 provider 的 token 限制配置，应通过配置文件传入。

## 7. 消息结构面向真实产品形态

message/turn 模型设计时应允许未来承载 text、image/file attachment、tool result 等多模态数据。token‑aware 策略应对多模态消息做合适计数（如图片描述 token 视为空）。

## 8. 行为保持确定性

即使引入 token aware 与 summary 策略，也应保持 deterministic：相同的输入产生相同的输出历史。不要依赖时间戳或随机采样选择历史。

## 9. 策略组合顺序固定

默认策略链必须遵循：selection → truncation → summary → serialization。不要调换顺序或省略某一步骤，除非配置关闭某策略。

## 10. 不越权调用外部 API

summary 策略不能直接调用外部 LLM；reset 操作不能删除跨 session 的数据；context 层不能暴露 HTTP 端点。

---

# Verification Standard

一个合格的面向 C 端 AI 应用的 context skeleton（Phase 2），至少应满足：

- `models.py` 中存在 conversation/session/message 级基础实体或清晰预留
- `stores/base.py` 中存在清晰 store 抽象，并包含 reset 方法定义
- `stores/in_memory.py` 中存在本地实现，支持 token‑aware 截断与重置
- `manager.py` 暴露 get/append/list/reset 等最小必要操作
- context 层保持 provider‑agnostic
- 对 stateful / stateless 会话模式有清晰思路或预留
- 对 compaction / summary / token budget 有未来扩展意识并提供初步实现
- 无复杂 memory platform 混入
- 默认 history 使用 token‑aware 最近窗口，而不是全量 messages
- context policy 执行结果可被测试和观测，并包含 selection/truncation/summary/serialization trace
- request assembler 中存在清晰的上下文装配 trace/metadata
- context 层与 services 层边界未混淆
- 新增 reset 接口通过 service 层暴露

---

# Done Criteria

本 skill 任务完成，至少表示：

1. Context 骨架文件落位正确
2. manager / store / models 边界清晰
3. in-memory 实现支持 token‑aware 截断与重置
4. 当前阶段未引入过度复杂逻辑
5. context 层保持 provider‑agnostic
6. 对主流 C 端 AI 对话产品的会话与消息结构有合理预留
7. 已通过 checklist 自检，并更新测试矩阵
8. `request_assembler.py` 已成为正式上下文装配入口，使用新策略管道
9. 默认 history 不再以“全量原样拼接”方式进入主链路
10. 会话重置 API 正常工作并通过测试
11. 文档和根目录/模块级 AGENTS 已同步更新

---

# Notes

本 skill 适用于 `vi_ai_core_service` 的 Context Engineering Phase 2。未来若 context 层复杂度提升，可继续细分为：

- python-context-session-memory-skeleton
- python-context-token-aware-policies-skill
- python-context-compaction-skill
- python-context-summary-pipeline
- python-context-persistence-skill
- python-context-user-profile-memory-skill

---

# 编码前输出要求

开始编码前，必须先输出：

1. 任务理解与范围边界（短期记忆骨架 + token‑aware 策略 + summary hook + reset API）
2. manager/models/stores/policies/request_assembler/api 的文件级改动计划
3. 风险与假设（例如 tokenizer 选择、summary 简化假设、API 鉴权等）
4. 验证计划（token‑aware selection/truncation/summary 顺序、reset 行为、assembly order）

---

# 编码后输出要求

完成编码后，必须输出：

1. 文件级变更清单与原因
2. 上下文行为变化说明
3. 测试与验证结果
4. 文档回写说明

---

# 资产与验证索引

1. Checklist：`assets/context_capability_checklist.md`（需同步扩展 Phase 2 相关条目）
2. Test Matrix：`assets/context_test_matrix.md`（需新增 token aware、summary、reset 场景）
3. References：`references/context_boundaries_and_acceptance.md`

---

# Governance Linkage

执行本 skill 时必须遵循统一闭环：

`根目录文档 -> app/context/AGENTS.md -> 本 skill -> 代码实现 -> review -> 文档回写`

强制要求：

1. 未完成根目录四文档与模块 AGENTS 阅读，不进入代码实现。
2. 改动后必须按根 `CODE_REVIEW.md`、模块 `AGENTS.md`、本 skill checklist 联合自审。
3. 若上下文模型、边界或测试事实变化，必须同步更新对应文档与测试。
4. 未明确 `request_assembler.py` 与 context policy pipeline 的协作边界，不进入主链路代码改造。
