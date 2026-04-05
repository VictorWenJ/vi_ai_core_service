---
name: python-observability-capability
description: 用于为 vi_ai_core_service 搭建和标准化可观测性基础设施层。重点关注 Python 标准库 logging、log4j 风格前缀 + message JSON、.env 开关控制、request context 贯穿、startup/API/service/provider/exception 边界日志，以及与业务层解耦的治理方式。
last_updated: 2026-04-06
---

# Purpose

本 skill 用于指导 `vi_ai_core_service` 中 observability 基础设施的新增、整理与标准化工作。

它面向当前阶段“最小可用可观测性基础设施”，目标是：

- 统一 logging 基础设施入口
- 统一日志前缀结构与 `message=<json>` 结构
- 统一 request context 字段贯穿
- 统一 exception logging 语义
- 统一 API / services / providers 边界日志策略
- 保持 observability 与业务层清晰解耦

本 skill 是任务执行规范，不替代模块治理文档。使用前应先阅读：

1. 根目录 `AGENTS.md`
2. 根目录 `PROJECT_PLAN.md`
3. 根目录 `ARCHITECTURE.md`
4. 根目录 `CODE_REVIEW.md`
5. `app/observability/AGENTS.md`

---

# Use This Skill When

在以下场景中使用本 skill：

- 新增或重构 `app/observability/` 代码
- 建立 logging 初始化流程
- 建立 JSON 结构化日志格式
- 建立 request context 字段注入与透传
- 建立 startup/API/service/provider/exception 边界日志
- 收敛散落的 `print` 或不规范日志输出
- 补齐 observability 相关文档、checklist、review 门禁

---

# Do Not Use This Skill For

以下场景不应使用本 skill：

- tracing 平台建设
- metrics 平台建设
- alerting/APM 平台接入
- 业务流程编排改造
- provider 接入逻辑改造
- prompt/context 业务逻辑改造
- 数据库、队列、工作流引擎建设

---

# Layer Responsibility

Observability 层负责：

- 基于 Python 标准库 `logging` 的统一日志基础设施
- 统一控制台前缀：`<time> <level> [<thread>] <logger> <file>:<line> event=<event>`
- 统一业务日志体：`message=<json>`
- `.env` true/false 开关控制日志行为
- request context 字段贯穿（如 `request_id` / `session_id` / `conversation_id` / `provider` / `model`）
- startup/API/services/providers/exception 关键边界日志规范

Observability 层不负责：

- 业务逻辑编排
- provider 接入实现
- prompt 资产管理
- context 存储实现
- tracing/metrics/alerting/APM 平台建设（当前阶段）

---

# Required Inputs

使用本 skill 前，应明确：

1. 本次改动是否属于 observability 基础设施职责
2. 需要覆盖的日志边界点（startup/API/service/provider/exception）
3. 需要贯穿的 request context 字段集合
4. `.env` 日志开关规则与默认策略
5. 当前阶段日志内容策略（业务 payload 输出开关、凭据字段禁止输出）
6. 当前阶段是否仅做最小基础设施，而非平台化建设

---

# Expected Outputs

使用本 skill 后，交付物应至少包括：

1. 位于 `app/observability/` 的基础设施文件
2. 统一 logging 初始化入口
3. JSON 日志格式化约束
4. request context 贯穿方案
5. exception logging 规则
6. 边界日志策略说明
7. 对应文档与 checklist 更新

---

# Required Workflow

1. 先确认需求归属 observability 层。
2. 先阅读根目录四文档与 `app/observability/AGENTS.md`。
3. 明确本次只做最小 observability 基础设施，不引入重型平台。
4. 设计“前缀字段（系统信息）”与“message JSON（业务信息）”的边界。
5. 在 `app/observability/` 内部落地实现。
6. 对照 checklist 做边界、安全、阶段约束自检。
7. 按 `CODE_REVIEW.md` 做专项 review。
8. 若规则或事实变化，回写根文档、模块文档与 skill 文档。

---

# Design Rules

## 1. 标准库优先

统一使用 Python 标准库 `logging`，避免当前阶段引入重型依赖。

## 2. 结构化优先

日志输出默认为“log4j 风格前缀 + `message=<json>`”，确保可检索、可关联、可审查。

## 3. 上下文贯穿

request context 字段要贯穿关键日志事件，避免不可追踪日志。

## 4. 边界清晰

observability 是横切基础设施，不承载业务流程。

## 5. 输出策略可控

当前阶段默认允许业务 payload 明文输出（调试优先），并受 `.env` 开关控制；API key、Authorization 等凭据字段必须禁止输出。

## 6. 当前阶段不过度建设

当前阶段不构建 tracing/metrics/alerting/APM 平台，不做“万能观测平台”。

---

# Verification Standard

一个合格的 observability 基础设施改动，至少应满足：

- 使用 `logging` 标准库
- 前缀格式与 `message=<json>` 约束清晰
- `.env` 开关控制策略清晰
- request context 字段可贯穿
- startup/API/service/provider/exception 边界日志策略清晰
- 业务 payload 输出行为可控，且凭据字段严格禁止输出
- 未引入平台化过度建设

---

# Done Criteria

本 skill 任务完成，至少表示：

1. observability 改动落在正确目录
2. logging/JSON/context/exception 基础规则明确
3. 边界日志策略明确
4. 阶段约束未被破坏
5. 已通过 checklist 自审
6. 相关文档已同步回写

---

# Notes

本 skill 聚焦“当前阶段最小 observability 基础设施能力”。

后续若阶段升级，可拆分为：

- python-observability-logging-foundation
- python-observability-request-context
- python-observability-exception-logging
- python-observability-tracing-integration（后续阶段）
- python-observability-metrics-alerting（后续阶段）

---

# Governance Linkage

执行本 skill 时必须遵循统一闭环：

`根目录文档 -> app/observability/AGENTS.md -> 本 skill -> 代码实现 -> review -> 文档回写`

强制要求：

1. 未完成根目录文档和模块文档阅读，不进入实现。
2. 改动后必须按根 `CODE_REVIEW.md` + 模块 `AGENTS.md` + 本 skill checklist 联合自审。
3. 若 observability 规则、边界或测试事实变化，必须同步更新对应文档与测试。

