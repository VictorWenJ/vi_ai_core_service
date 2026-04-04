# Observability 层边界与验收标准

## 一、边界定义

### Observability 层负责什么

Observability 层负责：

- 统一 logging 初始化
- 统一 JSON 结构化日志输出规范
- 统一 request context 字段贯穿规则
- 统一 exception logging 规则
- API / services / providers 关键边界日志支持

### Observability 层不负责什么

Observability 层不负责：

- 业务流程编排
- provider 接入实现
- prompt 管理
- context 存储
- tracing/metrics/alerting/APM 平台建设（当前阶段）
- 万能工具层职责承接

---

## 二、必须遵守的原则

1. 使用 Python 标准库 `logging`。
2. 日志格式统一为 JSON。
3. 日志行为由 `.env` true/false 开关控制。
4. request context 字段必须可贯穿关键链路日志。
5. exception logging 要保留定位信息并控制敏感信息输出。
6. observability 是横切基础设施，不得反向依赖业务实现。
7. 当前阶段只做最小基础设施，不做 tracing/metrics/alerting 平台化建设。

---

## 三、典型反模式

### 反模式 1：到处 `print`

问题：

- 结构化与可检索性差
- 无统一格式与等级语义
- 无法稳定做日志治理

### 反模式 2：默认输出完整敏感 payload

问题：

- 安全风险高
- 审计风险高
- 易导致生产信息泄露

### 反模式 3：把 observability 做成万能工具层

问题：

- 边界失真
- 杂项逻辑堆积
- 长期维护成本高

### 反模式 4：当前阶段提前引入 tracing/metrics/alerting 平台

问题：

- 与阶段目标不匹配
- 架构复杂度提前膨胀
- 交付收益与成本失衡

### 反模式 5：全局万能错误包吞并所有错误语义

问题：

- 错误定位语义丢失
- 分层错误边界被破坏
- 上层难以做正确状态码与策略映射

---

## 四、验收标准

一个合格的 observability 基础设施改动，应满足：

- 目录落位正确
- logging/JSON/.env 开关规则清晰
- request context 贯穿规则清晰
- startup/API/service/provider/exception 边界日志策略清晰
- 敏感信息输出受控
- 未引入当前阶段不允许的平台化能力
- 文档、模块规则、skill 规则一致

---

## 五、一句话总结

Observability 在本项目中是横切基础设施层，目标是以标准库 `logging` + JSON 结构化输出 + request context 贯穿为核心，提供可审查、可追踪、可控风险的最小可观测性能力，而不是在当前阶段构建重型观测平台。
