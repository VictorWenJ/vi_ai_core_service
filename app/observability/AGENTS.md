# app/observability/AGENTS.md

## 1. 文档定位

本文件定义 `app/observability/` 目录的职责、边界、结构约束、演进方向与代码审查标准。

当前阶段，本文件临时同时承担该模块的：

- AGENTS.md
- PROJECT_PLAN.md
- ARCHITECTURE.md
- CODE_REVIEW.md

功能。

本文件只约束可观测性基础设施层，不替代项目根目录文档。

---

## 2. 模块定位

`app/observability/` 是系统的**可观测性基础设施层**。

它是横切基础设施模块，负责为系统提供统一的：

- logging 初始化
- JSON 结构化日志输出
- request context 管理
- exception logging
- API / services / providers 的通用日志事件支持

技术选型约束（当前阶段强制）：

- 使用 Python 标准库 `logging`
- 日志输出格式统一为 JSON
- 日志开关由 `.env` true/false 标识控制
- `info` 级别用于普通结构化日志
- `error` 级别用于异常日志

---

## 3. 本层职责

可观测性基础设施层负责：

1. 提供统一日志基础设施入口（后续实现）
2. 提供结构化日志字段约束（JSON）
3. 定义 request context 字段贯穿规则（如 `request_id` / `session_id` / `conversation_id` / `provider` / `model`）
4. 定义 startup / API / service / provider / exception 的边界日志规范
5. 为后续 observability 代码实现提供稳定文档治理基础

一句话：**observability 层负责“怎么统一记录、关联和审查日志”，不负责业务流程。**

---

## 4. 本层不负责什么

本层不负责：

1. 不负责业务逻辑编排
2. 不负责 provider 接入逻辑
3. 不负责 prompt 资产管理
4. 不负责 context 存储
5. 不负责 tracing/metrics/alerting/APM 平台建设（当前阶段）
6. 不负责演化为万能 `utils/common` 杂项层

---

## 5. 依赖边界

### 允许依赖

`app/observability/` 可以依赖：

- Python 标准库（重点是 `logging`）
- 极少量配置读取（仅 observability 需要）
- `app/schemas/`（仅在字段契约需要时）

### 禁止依赖

`app/observability/` 不应依赖：

- `app/api/` 的业务路由逻辑
- `app/services/` 的业务编排逻辑
- `app/providers/` 的厂商适配逻辑
- `app/prompts/` 的模板管理逻辑
- `app/context/` 的存储实现逻辑

说明：

- 其他模块可以依赖 observability。
- observability 不能反向依赖业务层实现细节。

---

## 6. 当前建议结构

当前阶段（本轮）：

- `app/observability/AGENTS.md`（已建立）

后续代码实现阶段建议结构（预留）：

- `logging_setup.py`：logging 初始化
- `json_formatter.py`：JSON 日志格式化
- `context.py`：request context 管理
- `events.py`：边界日志事件封装
- `exception_logging.py`：异常日志封装

注意：

- 本轮只做文档层与目录层补齐，不创建上述实现文件。

---

## 7. 设计原则

### 7.1 基础设施独立

observability 必须是独立基础设施模块，不与业务流程混写。

### 7.2 结构化优先

日志必须默认结构化（JSON），禁止长期依赖非结构化字符串拼接日志。

### 7.3 关联优先

日志应能通过 request context 字段关联主链路，避免不可追踪日志。

### 7.4 安全优先

日志输出必须避免敏感信息泄露（如 API key、Authorization、完整隐私 payload）。

### 7.5 当前阶段最小化

当前阶段仅建设 logging/request context/exception logging 的基础设施规则，不进行平台化建设。

---

## 8. 当前阶段演进计划

本层当前阶段目标：

1. 建立 observability 模块级治理文档
2. 建立 observability skill 执行规范与 checklist/reference
3. 明确技术选型与边界约束
4. 为后续代码实现阶段提供清晰落地顺序

### 当前阶段能力声明（强约束）

- 本阶段已完成：
  - 目录与文档治理补齐
  - logging/JSON/request context/exception logging 的规则定义
- 本阶段未实现：
  - 具体 logging 代码
  - API middleware / formatter / contextvars 实现
  - tracing/metrics/alerting/APM 能力

---

## 9. 修改规则

修改 `app/observability/` 时必须遵守：

1. 先判断改动是否属于 observability 基础设施职责
2. 不要把业务逻辑塞入 observability 层
3. 统一沿用 Python 标准库 `logging`
4. 日志结构必须遵守 JSON 约束
5. 保持 `.env` 开关控制策略明确且可审查
6. 涉及边界变化时必须同步回写根文档与 skill 文档

---

## 10. Code Review 清单

评审 `app/observability/` 时，重点检查：

### 边界

- 是否仍是横切基础设施层
- 是否出现业务流程侵入
- 是否反向依赖业务实现细节

### 日志规范

- 是否使用标准库 `logging`
- 是否遵守 JSON 结构化输出
- 是否区分 `info` 与 `error` 级别语义

### 关联与安全

- request context 字段是否可贯穿主链路
- 是否避免敏感信息输出
- 异常日志是否保留定位信息且不过度暴露细节

### 阶段约束

- 是否误引入 tracing/metrics/alerting/APM 平台化实现

---

## 11. 测试要求（后续实现阶段）

后续进入代码实现阶段时，建议至少覆盖：

1. logging 初始化行为
2. JSON 日志格式正确性
3. `.env` 开关行为
4. request context 字段注入与透传
5. exception logging 行为
6. startup/API/service/provider 边界日志断言
7. 敏感字段脱敏或限制输出行为

---

## 12. 禁止事项

以下做法必须避免：

- 在业务代码中到处 `print` 代替统一日志基础设施
- 默认输出完整敏感 payload
- 把 observability 做成“万能工具层”
- 在当前阶段引入 tracing/metrics/alerting/APM 平台
- 通过 observability 包装吞掉所有错误语义

---

## 13. 一句话总结

`app/observability/` 是系统的横切可观测性基础设施层，负责**统一 logging 规则、上下文字段关联与异常日志治理**，不承担业务流程实现。

---

## 14. 本模块任务执行链路（强制）

Observability 类任务必须按以下顺序执行：

1. 先读根目录四文档（`AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`）
2. 再读本文件
3. 再执行 `skills/python-observability-capability/SKILL.md` 与其 checklist/reference
4. 再改 `app/observability/` 代码（后续阶段）
5. 再按根 `CODE_REVIEW.md` + 本文件 + skill checklist 自审
6. 若 observability 规则或边界事实变化，回写对应文档

---

## 15. 本模块交付门禁（新增）

- 未通过 `python-observability-capability` checklist，不视为完成
- 发现 observability 越权承担业务职责，必须先整改
- 发现敏感信息输出风险，必须先处理再交付
- 当前阶段若引入 tracing/metrics/alerting/APM 平台化改动，直接判定越界
