---
name: python-observability-capability
description: 用于 vi_ai_core_service 当前阶段 observability 模块改造。聚焦统一日志入口、前缀+message JSON 输出，以及 Phase 5 流式会话生命周期的结构化定位字段。
last_updated: 2026-04-09
---

# 目的

本 skill 用于指导 observability 相关改动，确保与当前代码事实一致。

当前阶段核心不是平台化观测，而是最小统一日志能力：

- 统一入口：`app/observability/log_until.py`
- 统一格式：前缀 + `message=<json>`
- 为 Phase 5 增加流式会话生命周期定位字段

---

# 当前阶段约束（必须遵守）

1. 仅维护最小日志基础设施，不引入 tracing / metrics / alerting / APM
2. 不新增完整 request context / middleware 平台能力
3. 保持标准库 `logging`
4. 只新增结构化字段，不把 observability 升级成业务状态机

---

# 适用场景

- 修改 `app/observability/log_until.py`
- 调整日志字段约束
- 为 started / completed / error / cancelled 增加标准日志字段

---

# 设计规则

1. 格式稳定：前缀 + `message=<json>` 不漂移
2. 流式定位字段要结构化，不要散落到自由文本
3. 默认避免输出凭据字段
4. 不把 observability 退化成 `utils/common` 杂项层

---

# 验证标准

至少满足：

- `log_report()` 可正常输出
- `message` 可被 JSON 解析
- started / completed / error / cancelled 日志字段可定位
- 文档描述与代码行为一致
