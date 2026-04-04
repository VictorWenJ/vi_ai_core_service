---
name: python-context-capability
description: 用于为 vi_ai_core_service 搭建和标准化面向 C 端 AI 应用的上下文管理层骨架。重点关注 session 级短期记忆、conversation state、消息历史、多模态消息结构、store 抽象、in-memory 实现、manager 入口，以及为未来压缩/摘要/持久化策略预留扩展点。
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

本 skill 是 **任务执行规范**，不是模块治理文档。  
使用本 skill 前，应先阅读：

1. 项目根目录 `AGENTS.md`
2. 项目根目录 `PROJECT_PLAN.md`
3. 项目根目录 `ARCHITECTURE.md`
4. 项目根目录 `CODE_REVIEW.md`
5. `app/context/AGENTS.md`

---

# Current Phase Constraint (Must Follow)

在 `vi_ai_core_service` 当前阶段，执行本 skill 时必须默认遵守以下范围：

- Context 层只要求 session/conversation 短期记忆骨架与 in-memory 最小实现可用。
- context persistence、summary、compaction、token budget 治理仅做扩展预留，不做真实能力落地。
- 不引入 long-term memory 平台、RAG 记忆耦合或分布式状态系统。
- 重点是 manager/store/models 边界清晰、行为可测、与 service 层协作稳定。

---

# Use This Skill When

在以下场景中使用本 skill：

- 新增 `app/context/` 下的基础骨架
- 新增或整理 conversation/session 上下文模型
- 新增 store interface
- 新增本地 in-memory store 实现
- 新增 manager 统一入口
- 为未来 session memory / message history / context governance 做结构准备
- 为多模态消息历史、会话压缩、摘要、持久化预留扩展点
- 校正当前 context 层边界，使其更符合主流 C 端 AI 应用后端结构

---

# Do Not Use This Skill For

以下场景不应使用本 skill：

- 一次性实现完整 long-term memory system
- 实现 retrieval pipeline / RAG 检索逻辑
- 直接接入数据库、消息队列、分布式状态系统
- 在本轮就实现复杂的持久化架构
- 在 context 层中实现 provider 调用逻辑
- 在 context 层中实现业务主流程编排
- 在 context 层中混入 prompt 渲染逻辑
- 把用户画像记忆、检索记忆、工具记忆全部一轮做完

---

# Layer Responsibility

Context 层负责：

- 定义 conversation / session / turn / message 等上下文相关模型
- 表示短期会话历史
- 抽象上下文存储接口
- 提供本地基础实现
- 通过 manager 向上层暴露统一访问入口
- 为未来上下文压缩、摘要、裁剪、token budget、持久化预留扩展点
- 保持 provider-agnostic

Context 层不负责：

- HTTP 接口接入
- 业务主流程编排
- provider SDK / HTTP 调用
- prompt 模板管理与渲染
- retrieval / rerank / grounding
- 当前阶段复杂 persistence / distributed state
- 当前阶段完整长期记忆系统

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

---

# Expected Outputs

使用本 skill 后，交付物应至少包括：

1. `models.py` 中清晰的上下文模型
2. `stores/base.py` 中显式、稳定的 store 抽象接口
3. `stores/in_memory.py` 中最小可用的本地实现
4. `manager.py` 中统一的 context manager 入口
5. conversation/session/message 级最小行为约定
6. 为 compaction / summary / persistence 预留扩展点
7. 最小可验证说明
8. 必要时补充对应测试

---

# Required Workflow

1. 先确认本次需求是否真的属于 context 层。
2. 先检查根目录文档与 `app/context/AGENTS.md`。
3. 明确当前要承载的是 stateless 历史输入、stateful conversation，还是两者兼容预留。
4. 在 `app/context/` 下定义最小上下文模型。
5. 在 `stores/base.py` 中定义明确、稳定的 store interface。
6. 在 `stores/in_memory.py` 中实现本地内存版 store。
7. 在 `manager.py` 中提供统一 façade，面向上层暴露最小操作集。
8. 为未来 token budget、裁剪、摘要、持久化预留 hook 或清晰扩展点，但当前不完整实现。
9. 保持实现轻量、确定性、易理解。
10. 对照 checklist 自检。
11. 若改动影响上下文契约、边界或测试行为，需同步更新文档与测试。

---

# Design Rules

## 1. 先建短期会话骨架，再加复杂记忆策略

主流 C 端 AI 产品的第一优先上下文能力通常是：
- conversation/session 级短期记忆
- 消息历史
- 最近若干轮上下文控制

不是一开始就做完整长期记忆系统。

## 2. 同时考虑 stateful 与 stateless 模式

当前主流产品后端常同时面对两类会话方式：
- 客户端把历史随请求带上来
- 服务端用 conversation/session id 保存状态

context 层骨架应允许未来两种模式并存。

## 3. 管理与存储分离

- `manager.py` 负责对上提供访问入口
- `stores/` 负责底层存储抽象与实现

不要把管理逻辑和存储逻辑写在一起。

## 4. Context 层保持 provider-agnostic

context 层管理的是上下文数据，不是厂商协议状态。

## 5. 消息结构要面向真实产品形态

message/turn 模型设计时，应允许未来承载：
- text
- image/file attachment metadata
- tool result reference
- assistant/user/system role
- timestamps / ids / lightweight metadata

当前可以不全部实现，但不能把结构写死成“只有一段字符串”。

## 6. 为压缩与摘要预留扩展点

多轮会话增长后，主流产品通常需要：
- truncate
- summarize
- compact
- token budget control

当前先预留结构，不必完整实现。

## 7. 当前阶段避免过度复杂化

本轮不引入：
- 完整长期记忆系统
- 检索式记忆
- 分布式状态编排
- 复杂 persistence infra

## 8. 行为保持确定性

context skeleton 的实现应尽量可预测、可单测、可推断。

---

# Verification Standard

一个合格的面向 C 端 AI 应用的 context skeleton，至少应满足：

- `models.py` 中存在 conversation/session/message 级基础实体或清晰预留
- `stores/base.py` 中存在清晰 store 抽象
- `stores/in_memory.py` 中存在本地实现
- `manager.py` 暴露最小必要操作
- context 层保持 provider-agnostic
- 对 stateful / stateless 会话模式有清晰思路或预留
- 对 compaction / summary / token budget 有未来扩展意识
- 无复杂 memory platform 混入

---

# Done Criteria

本 skill 任务完成，至少表示：

1. Context 骨架文件落位正确
2. manager / store / models 边界清晰
3. in-memory 实现最小可用
4. 当前阶段未引入过度复杂逻辑
5. context 层保持 provider-agnostic
6. 对主流 C 端 AI 对话产品的会话与消息结构有合理预留
7. 已通过 checklist 自检
8. 必要时已同步测试与文档

---

# Notes

本 skill 适用于当前 `vi_ai_core_service` 的基础上下文管理层建设阶段。  
未来若 context 层复杂度提升，可继续细分为：

- python-context-session-memory-skeleton
- python-context-compaction-skill
- python-context-summary-pipeline
- python-context-persistence-skill
- python-context-user-profile-memory-skill

---

# Governance Linkage

执行本 skill 时必须遵循统一闭环：

`根目录文档 -> app/context/AGENTS.md -> 本 skill -> 代码实现 -> review -> 文档回写`

强制要求：

1. 未完成根目录四文档与模块 AGENTS 阅读，不进入代码实现。
2. 改动后必须按根 `CODE_REVIEW.md`、模块 `AGENTS.md`、本 skill checklist 联合自审。
3. 若上下文模型、边界或测试事实变化，必须同步更新对应文档与测试。
