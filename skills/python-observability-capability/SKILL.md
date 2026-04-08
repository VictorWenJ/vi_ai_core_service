---
name: python-observability-capability
description: 用于 vi_ai_core_service 当前阶段 observability 模块改造。聚焦 log_until.py 统一日志上报、前缀+message JSON 输出、日志边界治理与文档回写。
last_updated: 2026-04-07
---

# 目的

本 skill 用于指导 `vi_ai_core_service` 的 observability 相关改动，确保与当前代码事实一致。

当前阶段核心不是平台化观测，而是最小统一日志能力：

- 统一入口：`app/observability/log_until.py`
- 统一格式：`<time> <level> [<thread>] <logger> <file>:<line> event=<event> message=<json>`
- 统一调用：API / services / providers 都通过 `log_report()` 上报

---

# 当前阶段约束（必须遵守）

当前阶段必须遵守：

1. 仅维护最小日志基础设施，不引入 tracing/metrics/alerting/APM。
2. 不新增 request context/middleware 平台能力（除非需求明确升级阶段）。
3. 不引入重型日志依赖（保持标准库 `logging`）。
4. 优先保证日志格式稳定、调用位置可定位、业务 JSON 可解析。

---

# 适用场景

在以下场景使用本 skill：

- 修改 `app/observability/log_until.py`
- 调整日志输出格式或日志字段约束
- 统一业务层日志调用方式
- 修复 observability 文档与代码不一致

---

# 不适用场景

以下场景不应使用本 skill：

- 业务流程编排改造
- provider 功能接入
- prompt/context 业务逻辑改造
- tracing/metrics/alerting/APM 平台建设

---

# 分层职责

Observability 层当前负责：

1. 统一 `log_report(event, message)` 入口
2. 统一日志前缀与 `message=<json>` 输出
3. 通用对象 JSON 化（dict/list/dataclass/pydantic）
4. 保障日志可定位（`<file>:<line>`）

Observability 层当前不负责：

1. request context 贯穿
2. middleware 自动 request_id 注入
3. `.env` 运行时开关实际生效控制
4. 异常治理平台化封装

---

# 必要输入

使用本 skill 前，至少明确：

1. 改动是否属于 observability 层职责
2. 目标日志格式是否保持兼容
3. 是否涉及敏感字段输出风险
4. 是否影响根文档/模块文档/测试文档事实

---

# 预期输出

交付物至少包括：

1. observability 相关代码改动（若有）
2. 文档回写（根文档、模块 AGENTS、skill 文档）
3. 日志样例说明
4. 验证结果（最小导入或测试）

---

# 必要流程

1. 阅读根目录四文档与 `app/observability/AGENTS.md`
2. 核对当前代码事实（重点 `log_until.py`）
3. 识别文档失真点
4. 先回写文档，再做必要代码修订
5. 自审并输出变更说明

---

# 设计规则

1. 标准库优先：仅使用 `logging`。
2. 格式稳定：前缀 + `message=<json>` 不可随意漂移。
3. 业务 JSON 仅承载业务信息，系统信息留在前缀。
4. 默认避免输出凭据字段（API key、Authorization）。
5. 不把 observability 退化成 `utils/common` 杂项层。

---

# 验证标准

合格改动至少满足：

1. `log_report()` 可正常输出
2. 输出格式满足前缀 + `message=<json>`
3. `message` 可被 JSON 解析
4. `<file>:<line>` 能定位日志调用点
5. 文档描述与代码行为一致

---

# 完成标准

任务完成至少表示：

1. observability 文档与代码不再冲突
2. 日志格式约束清晰可执行
3. 关键风险（敏感字段、越界建设）有明确限制
4. 已按治理链路完成回写

---

# 资产与验证索引

1. 检查清单：`assets/observability_capability_checklist.md`
2. 测试矩阵：`assets/observability_test_matrix.md`
3. 参考文档：`references/observability_boundaries_and_acceptance.md`

---

# 治理联动

执行本 skill 时必须遵循：

`根目录文档 -> app/observability/AGENTS.md -> 本 skill -> 代码实现 -> review -> 文档回写`
